#!/usr/bin/env python3
"""Cut one release of the Senzing Bootcamp Claude Plugin (maintainer tool).

Bumps the version everywhere it is asserted, writes the CHANGELOG entry, commits
the three files together and tags that commit -- as ONE operation with ONE code
path, because the defect this exists to prevent is precisely a release that did
half of it.

The defect, concretely
----------------------
The sibling repo ``Senzing/senzing-bootcamp-kiro-power`` carries a CHANGELOG entry
reading ``[0.5.3] - 2026-09-10`` while its newest git tag is still ``0.5.1``. The
changelog moved; the tag did not. That is not tidiness: under the porting model the
downstream development repositories (Kiro, ChatGPT, Copilot) pull from a **tagged
release** of Claude rather than from HEAD, so an untagged version is invisible to
the mechanism that governs the whole system. A port cannot target a release that
was never tagged.

Two halves of the problem were already guarded and one was not:

* ``tests/test_example_recap_sync.py`` pins the shipped example recap's
  ``**Plugin version:**`` header to ``plugin.json``, so bumping one without the
  other already turns the suite red.
* **The tag was the unguarded half.** Nothing in the repo related a version to a
  tag at all. Hence this script: the tag is not a step a human may skip, it is the
  last thing the same function does.

⛔ A TAG MUST POINT AT A COMMIT THAT CONTAINS THE BUMP.
Editing the files and then running ``git tag`` tags **HEAD**, which is the commit
*before* the bump -- a tag whose tree still states the old version. So this script
commits the edits first and tags the commit it just made. There is no flag to
separate those two, and adding one would reintroduce the class.

⛔ DRY RUN IS THE DEFAULT. ``--apply`` is what writes.
This script is fronted by a skill, so it can be invoked by a model. Git tags are
repository-global -- a tag is not scoped to a worktree and, once fetched, cannot be
taken back from anyone who has it. A destructive default is not acceptable under
those conditions. ``--dry-run`` is accepted explicitly so a caller can state the
intent rather than depend on a default staying what it is.

⛔ NEVER PUSHES. Not the branch, not the tag. Publishing is a separate, deliberate
step (``/propagate-to-public``, then a push the maintainer makes). The script stops
at a clean local tree at the new version and says so.

Usage:
    release.py --minor                    # preview a minor bump (writes nothing)
    release.py 0.6.0                      # preview an explicit target
    release.py --patch --apply            # do it: edit, changelog, commit, tag
    release.py --minor --repo /path/to/checkout
"""
import argparse
import datetime
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
#: .claude/skills/release/release.py -> repo root
DEFAULT_REPO = SKILL_DIR.parent.parent.parent

#: A release tag belongs on the branch the downstream repos port from. A tag made on a
#: feature branch survives a squash-merge as a pointer to a commit that never lands on
#: main, so a downstream repo targeting it gets a tree main does not contain.
RELEASE_BRANCH = "main"

CHANGELOG_NAME = "CHANGELOG.md"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

MANIFEST_REL = "plugins/senzing-bootcamp/.claude-plugin/plugin.json"

#: Every place in the repo that ASSERTS the plugin version, with the pattern that finds
#: it. ``tests/test_release_covers_every_version_site.py`` compares this table against
#: the repo itself, so a new assertion site fails the suite instead of being released
#: stale.
#:
#: Each entry's pattern captures (prefix, version, suffix) and MUST match at least once.
#: A site that stops matching is a hard error, never a silent skip -- silence is how the
#: example recap would go stale while the manifest advanced.
VERSION_SITES = (
    {
        "path": MANIFEST_REL,
        "pattern": re.compile(r'^(\s*"version":\s*")(\d+\.\d+\.\d+)(")', re.M),
        "why": "the plugin manifest -- the version Claude Code reports for the install",
    },
    {
        "path": "plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.md",
        "pattern": re.compile(r'^(\*\*Plugin version:\*\*[ \t]*)(\d+\.\d+\.\d+)([ \t]*)$', re.M),
        "why": ("the shipped reference recap's meta row -- "
                "tests/test_example_recap_sync.py pins it to the manifest"),
    },
)

CHANGELOG_HEADER = """\
# Changelog

Every released version of the Senzing Bootcamp Claude Plugin, newest first. The
downstream development repositories (Kiro, ChatGPT, Copilot) port from a **tagged**
release rather than from HEAD, so an entry here with no matching git tag is not a
release anyone can target.

Written by `.claude/skills/release/release.py`. Do not hand-edit an entry's heading:
the version, this file and the tag are written together on purpose.
"""

#: ⛔ VERSION-ANCHORED, not positional. Written as "entries below" it read as true on the
#: day the file was seeded and became a lie on the next release, because a prepended entry
#: lands between the note and the entries it describes. Naming the newest seeded version
#: keeps the sentence true for the life of the file.
SEED_NOTE = (
    "> Entries **%s and earlier** were reconstructed from git history when this file was\n"
    "> first created. They were not authored at release time, so they list commit subjects\n"
    "> rather than curated release notes.\n")


class Refusal(Exception):
    """A precondition the maintainer has to resolve; reported, never raised as a crash."""


# --------------------------------------------------------------------------- #
# git plumbing
# --------------------------------------------------------------------------- #
def git(repo, *args, check=True):
    done = subprocess.run(["git", "-C", str(repo)] + list(args),
                          capture_output=True, text=True)
    if check and done.returncode != 0:
        raise Refusal("git %s failed: %s" % (" ".join(args), done.stderr.strip()))
    return done.stdout.strip(), done.returncode


def semver(text):
    match = SEMVER.match(text.strip())
    return tuple(int(part) for part in match.groups()) if match else None


def tags_in_order(repo):
    """Every semver tag, sorted NUMERICALLY.

    Sorting ``git tag -l`` as text is right for 0.3.5 < 0.5.3 and wrong the day 0.10.0
    exists, which is the sort of thing a release tool gets one chance to have right.
    """
    out, _ = git(repo, "tag", "--list")
    parsed = [(semver(tag), tag) for tag in out.splitlines() if semver(tag)]
    return [tag for _, tag in sorted(parsed)]


def bump(current, part):
    major, minor, patch = current
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def fmt(version):
    return "%d.%d.%d" % version


# --------------------------------------------------------------------------- #
# version sites
# --------------------------------------------------------------------------- #
def read_sites(repo):
    """[(site, text, [matches])] -- every site present and matching, or a Refusal."""
    found = []
    for site in VERSION_SITES:
        path = repo / site["path"]
        if not path.is_file():
            raise Refusal(
                "version site is missing: %s (%s). Either the file moved -- in which case "
                "VERSION_SITES in %s must move with it -- or this is not the plugin repo."
                % (site["path"], site["why"], Path(__file__).name))
        text = path.read_text(encoding="utf-8")
        matches = list(site["pattern"].finditer(text))
        if not matches:
            raise Refusal(
                "version site %s no longer states a version in the shape this script edits "
                "(%s). Releasing now would advance the other site(s) and leave this one "
                "stale -- the exact split this script exists to prevent."
                % (site["path"], site["why"]))
        found.append((site, text, matches))
    return found


def current_version(repo):
    manifest = json.loads((repo / MANIFEST_REL).read_text(encoding="utf-8"))
    version = semver(manifest.get("version", ""))
    if version is None:
        raise Refusal("%s has no parseable MAJOR.MINOR.PATCH version" % MANIFEST_REL)
    return version


def rewrite_sites(repo, old, new):
    """[(relpath, old_text, new_text)] -- computed in memory, written by the caller.

    Everything is planned before anything is written, so a site that would fail cannot
    leave an earlier site already bumped.
    """
    planned = []
    for site, text, matches in read_sites(repo):
        stale = sorted({match.group(2) for match in matches if match.group(2) != old})
        if stale:
            raise Refusal(
                "version site %s states %s, but the manifest states %s. The version sites "
                "have already diverged; reconcile them before releasing, or the release "
                "records a version that was never consistent."
                % (site["path"], ", ".join(stale), old))
        new_text = site["pattern"].sub(lambda m: m.group(1) + new + m.group(3), text)
        if new_text == text:
            raise Refusal("rewriting %s changed nothing" % site["path"])
        planned.append((site["path"], text, new_text))
    return planned


# --------------------------------------------------------------------------- #
# changelog
# --------------------------------------------------------------------------- #
def subjects_between(repo, start, end):
    """Commit subjects in (start, end]. Merges are excluded -- they carry no content."""
    span = end if start is None else "%s..%s" % (start, end)
    out, _ = git(repo, "log", "--no-merges", "--format=%s", span)
    return [line.strip() for line in out.splitlines() if line.strip()]


def tag_date(repo, ref):
    """The COMMIT date of what ``ref`` points at.

    Read from the commit rather than from the tag object because the seven tags this
    repo already carries are lightweight and have no date of their own. New tags are
    annotated (see ``main``), so this keeps working across both shapes.
    """
    out, _ = git(repo, "log", "-1", "--format=%ad", "--date=short", "%s^{commit}" % ref)
    return out


def entry(version, date, bullets):
    lines = ["## [%s] - %s" % (version, date), ""]
    lines.extend("- %s" % bullet for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def seed_changelog(repo, tags):
    """Reconstruct one entry per existing tag, newest first.

    The earliest tag is deliberately NOT itemized: every commit before the first
    release would land in it, which is noise rather than history.
    """
    blocks = []
    for index, tag in enumerate(tags):
        if index == 0:
            bullets = ["Earliest tagged release; history before this tag is not itemized."]
        else:
            bullets = subjects_between(repo, tags[index - 1], tag) or [
                "No non-merge commits recorded between %s and %s." % (tags[index - 1], tag)]
        blocks.append(entry(tag, tag_date(repo, tag), bullets))
    blocks.reverse()
    if not blocks:
        return CHANGELOG_HEADER
    return CHANGELOG_HEADER + "\n" + (SEED_NOTE % tags[-1]) + "\n" + "\n".join(blocks)


def plan_changelog(repo, new, today, tags):
    """(old_text, new_text, entry_text) for CHANGELOG.md, creating the file if absent."""
    path = repo / CHANGELOG_NAME
    latest = tags[-1] if tags else None
    bullets = subjects_between(repo, latest, "HEAD") or [
        "No non-merge commits since %s." % (latest or "the start of history")]
    block = entry(new, today, bullets)

    if path.is_file():
        old_text = path.read_text(encoding="utf-8")
        base = old_text
    else:
        old_text = ""
        base = seed_changelog(repo, tags)

    head, separator, rest = base.partition("\n## ")
    if separator:
        new_text = head.rstrip("\n") + "\n\n" + block + "\n## " + rest
    else:
        # A header-only file has no entry to prepend in front of.
        new_text = base.rstrip("\n") + "\n\n" + block
    return old_text, new_text, block


# --------------------------------------------------------------------------- #
# preconditions
# --------------------------------------------------------------------------- #
def check_preconditions(repo, allow_branch):
    if not (repo / MANIFEST_REL).is_file():
        raise Refusal(
            "%s does not look like the plugin repo: %s is missing. Refusing rather than "
            "releasing something else." % (repo, MANIFEST_REL))
    _, code = git(repo, "rev-parse", "--git-dir", check=False)
    if code != 0:
        raise Refusal("%s is not a git repository, so no tag can be created" % repo)

    dirty, _ = git(repo, "status", "--porcelain")
    if dirty:
        raise Refusal(
            "the working tree is dirty; refusing to release.\n"
            "A release commit must carry the version bump and nothing else, and the tree "
            "is what /propagate-to-public mirrors, so an uncommitted file would either be "
            "swept into the release commit or published untracked. Commit or discard "
            "first:\n\n%s" % dirty)

    branch, _ = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != RELEASE_BRANCH and not allow_branch:
        raise Refusal(
            "on branch %r, not %r; refusing to tag.\n"
            "A tag made here survives a squash-merge as a pointer to a commit that never "
            "lands on %s, so a downstream repo that ports from the tag gets a tree %s does "
            "not contain. Merge first, or pass --allow-branch if you mean it."
            % (branch, RELEASE_BRANCH, RELEASE_BRANCH, RELEASE_BRANCH))
    return branch


def check_target(repo, old, new, tags):
    if new <= old:
        raise Refusal(
            "%s does not advance the version: the manifest already states %s. A release "
            "must move forward, or the version stops being a key."
            % (fmt(new), fmt(old)))
    if fmt(new) in tags:
        raise Refusal(
            "tag %s already exists. Re-pointing a tag rewrites what downstream repos have "
            "already fetched; pick the next version instead." % fmt(new))
    if tags:
        newest = semver(tags[-1])
        if new <= newest:
            raise Refusal(
                "%s does not advance past the newest tag %s. Tags are the key the "
                "downstream repos port from, so a release must be newer than every tag, "
                "not only newer than the manifest." % (fmt(new), tags[-1]))
        if newest != old:
            raise Refusal(
                "the manifest states %s but the newest tag is %s -- they have already "
                "diverged, which is the defect this tool exists to prevent (the "
                "kiro-power instance in the module docstring). Reconcile the base before "
                "releasing: either tag the current manifest version, or correct the "
                "manifest. Pass --allow-divergent-base only once you have decided which "
                "of the two is right." % (fmt(old), tags[-1]))


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
DIFF_LINE_BUDGET = 60


def show_diff(relpath, old_text, new_text):
    lines = list(difflib.unified_diff(
        old_text.splitlines(True), new_text.splitlines(True),
        fromfile="a/" + relpath, tofile="b/" + relpath, n=1))
    if len(lines) > DIFF_LINE_BUDGET:
        elided = len(lines) - DIFF_LINE_BUDGET
        lines = lines[:DIFF_LINE_BUDGET] + ["... (%d more diff lines)\n" % elided]
    sys.stdout.write("".join(lines))
    print()


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Bump the version, write the CHANGELOG entry, commit and tag -- as one "
                    "operation. Dry run unless --apply is given.")
    parser.add_argument("version", nargs="?", help="explicit target version, e.g. 0.6.0")
    parser.add_argument("--major", action="store_true", help="bump the major component")
    parser.add_argument("--minor", action="store_true", help="bump the minor component")
    parser.add_argument("--patch", action="store_true", help="bump the patch component")
    parser.add_argument("--apply", action="store_true",
                        help="actually edit, commit and tag (default: dry run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="explicitly request the default: print and change nothing")
    parser.add_argument("--repo", default=str(DEFAULT_REPO),
                        help="repository to release (default: this skill's own repo)")
    parser.add_argument("--allow-branch", action="store_true",
                        help="tag from a branch other than %s" % RELEASE_BRANCH)
    parser.add_argument("--allow-divergent-base", action="store_true",
                        help="release even though the manifest and the newest tag disagree")
    parser.add_argument("--message",
                        help="release commit subject (default: 'chore(release): <version>')")
    return parser.parse_args(argv)


def resolve_target(args, old):
    parts = [name for name in ("major", "minor", "patch") if getattr(args, name)]
    if args.version and parts:
        raise Refusal("give an explicit version OR one of --major/--minor/--patch, not both")
    if len(parts) > 1:
        raise Refusal("give exactly one of --major/--minor/--patch; got %s"
                      % ", ".join("--" + part for part in parts))
    if args.version:
        target = semver(args.version)
        if target is None:
            raise Refusal("%r is not a MAJOR.MINOR.PATCH version" % args.version)
        return target
    if not parts:
        raise Refusal("nothing to release: give a version, or one of --major/--minor/--patch")
    return bump(old, parts[0])


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.apply and args.dry_run:
        print("refusing: --apply and --dry-run contradict each other", file=sys.stderr)
        return 2
    repo = Path(args.repo).resolve()

    try:
        branch = check_preconditions(repo, args.allow_branch)
        old = current_version(repo)
        tags = tags_in_order(repo)
        new = resolve_target(args, old)
        try:
            check_target(repo, old, new, tags)
        except Refusal as refusal:
            if not (args.allow_divergent_base and "diverged" in str(refusal)):
                raise
            print("WARNING (--allow-divergent-base): %s\n" % refusal)

        planned = rewrite_sites(repo, fmt(old), fmt(new))
        today = datetime.date.today().isoformat()
        changelog_old, changelog_new, block = plan_changelog(repo, fmt(new), today, tags)
        subject = args.message or "chore(release): %s" % fmt(new)
    except Refusal as refusal:
        print("refusing: %s" % refusal, file=sys.stderr)
        return 1

    print("Repository:   %s" % repo)
    print("Branch:       %s" % branch)
    print("Version:      %s  ->  %s" % (fmt(old), fmt(new)))
    print("Newest tag:   %s" % (tags[-1] if tags else "(none)"))
    print("CHANGELOG:    %s" % ("prepend an entry" if changelog_old else
                                "CREATE, seeded from %d existing tag(s)" % len(tags)))
    print("Mode:         %s" % ("APPLY" if args.apply else "dry run -- nothing is written"))
    print()
    for relpath, old_text, new_text in planned:
        show_diff(relpath, old_text, new_text)
    print("--- %s entry ---" % CHANGELOG_NAME)
    print(block)
    print("Then, as one unit:")
    print("  git add %s %s" % (" ".join(path for path, _, _ in planned), CHANGELOG_NAME))
    print("  git commit -m %r" % subject)
    print("  git tag -a %s -m %r   <- what a downstream repo ports from"
          % (fmt(new), subject))
    print()

    if not args.apply:
        print("Dry run: nothing was written. Re-run with --apply to release.")
        return 0

    before, _ = git(repo, "rev-parse", "HEAD")
    try:
        for relpath, _, new_text in planned:
            (repo / relpath).write_text(new_text, encoding="utf-8")
        (repo / CHANGELOG_NAME).write_text(changelog_new, encoding="utf-8")
        git(repo, "add", "--", *[path for path, _, _ in planned], CHANGELOG_NAME)
        git(repo, "commit", "--quiet", "-m", subject)
        # Annotated, unlike the seven lightweight tags already here: an annotated tag
        # records when the tag was made, independently of the commit date, so a tag
        # created days later is not silently misdated.
        git(repo, "tag", "-a", fmt(new), "-m", subject)
    except Refusal as refusal:
        # ⛔ Roll all the way back rather than leave a half-release behind -- a bumped
        # tree with no tag is the kiro-power defect. The tree was verified clean above,
        # so resetting to the recorded SHA cannot discard anyone's work.
        git(repo, "tag", "-d", fmt(new), check=False)
        git(repo, "reset", "--hard", before, check=False)
        print("refusing: %s\n(rolled back to %s; nothing was released)"
              % (refusal, before[:12]), file=sys.stderr)
        return 1

    sha, _ = git(repo, "rev-parse", "HEAD")
    print("Released %s" % fmt(new))
    print("  commit %s  %s" % (sha[:12], subject))
    print("  tag    %s -> %s" % (fmt(new), sha[:12]))
    print()
    print("Nothing was pushed. Next step: /propagate-to-public to mirror the shippable")
    print("plugin into the public access repo, then push this branch AND the tag --")
    print("`git push` alone does not send tags, and an unpushed tag is invisible to the")
    print("downstream repositories that port from it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
