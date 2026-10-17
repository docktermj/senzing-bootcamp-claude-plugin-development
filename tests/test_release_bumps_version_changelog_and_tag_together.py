"""`/release` moves the version, the changelog and the git tag, or moves none of them.

The defect this guards is live in a sibling repo. `Senzing/senzing-bootcamp-kiro-power`
carries a CHANGELOG entry reading ``[0.5.3] - 2026-09-10`` while its newest git tag is
still ``0.5.1``. The changelog moved; the tag did not.

That is not tidiness. Under the porting model the downstream development repositories
(Kiro, ChatGPT, Copilot) port from a **tagged release** of Claude rather than from HEAD,
so a version that was never tagged is invisible to the mechanism governing the whole
system: a port cannot target it.

⛔ **THE TAG WAS THE ONLY UNGUARDED HALF, AND IT IS THE HALF THAT MATTERS.**
`tests/test_example_recap_sync.py` already pins the example recap's ``**Plugin
version:**`` row to `plugin.json`, so bumping one of those without the other has been red
for a long time. Nothing in this repo related a version to a *tag* at all -- a release
could bump both files, pass the entire suite, and ship untagged. That is exactly the
kiro-power shape, and it is what this file exists to make impossible.

⛔ **THE TAG'S TREE IS THE SUBJECT, NOT THE TAG'S EXISTENCE.**
The obvious implementation -- edit the files, then ``git tag`` -- tags **HEAD**, which is
the commit *before* the bump. The tag exists, the tag name is right, and checking out the
tag gives you the old version. So `test_the_tagged_tree_carries_the_bump` reads the three
files *out of the tag*, never out of the working tree. A test that asserted only "a tag
named 0.5.0 exists" would pass against the broken implementation.

⚠️ **Everything here runs against a THROWAWAY repository built in a temp directory.**
Git tags are repository-global -- they are not scoped to a worktree -- so a test that
tagged this repo would create a real release tag every time anyone ran the suite. The
fixture also lets the failure cases (a dirty tree, a manifest that has already diverged
from the newest tag) be *constructed* rather than waited for.

⚠️ **What a green run does NOT mean.** It means the script, run against a repo shaped
like this one, produces a consistent version/changelog/tag triple and refuses the
preconditions it claims to refuse. It does not mean the CHANGELOG wording is good, that
the seeded history is an accurate account of what those releases contained (it is
reconstructed commit subjects and says so), that the real repo's `VERSION_SITES` table is
complete -- `tests/test_release_covers_every_version_site.py` is the guard for that -- or
that anything was ever published. `/release` deliberately stops before publishing.

No count of refusals or of version sites is asserted. The behaviors are named
individually so that adding a refusal is adding a test, not editing a number.

⚠️ **Enforces INV-301**, and not all of it. This module asserts the mechanical half: the
records move together, the tag is annotated, it points at the release commit, and the three
refusals fire. It does **NOT** establish that a maintainer invoking `/release` follows the
skill's procedure, that the tag was ever **pushed** (`/release` deliberately stops before
pushing, so the release it produces is not yet targetable), or that the tag is signed —
`tag.gpgsign` comes from the maintainer's git config and is not asserted here. An `Enforced by`
clause naming this file is therefore not a compliance claim about a real release.

Stdlib only (INV-108); git builds the fixture, as in
`tests/test_since_last_audit_widens_past_a_work_commit.py`.

Source issue: #27 (`/release`).

No phrase-level pattern (#438): its line reads are of `release.py`'s source lines, as #424 recorded
(INV-346).

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_PY = REPO_ROOT / ".claude" / "skills" / "release" / "release.py"

MANIFEST_REL = "plugins/senzing-bootcamp/.claude-plugin/plugin.json"
EXAMPLE_REL = "plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.md"
#: BLUEPRINT.md copies plugin.json verbatim in its section 3, so it is a version site too
#: (#446) -- and carries two prose assertions besides, which is why the fixture below
#: writes all three of them into one file (#697).
BLUEPRINT_REL = "BLUEPRINT.md"
CHANGELOG_REL = "CHANGELOG.md"
#: The rendered version site: a shipped artifact whose version is DRAWN, so no text
#: substitution can reach it and `/release` re-renders it instead (#697).
EXAMPLE_PDF_REL = "plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.pdf"
GENERATOR_REL = "plugins/senzing-bootcamp/scripts/generate_recap_pdf.py"

#: A stand-in for the recap generator, written into every fixture repo. It reproduces only
#: the contract `release.py` depends on: read ``--input``, write ``--output``, print
#: ``PDF generated: <out> (renderer: <name>, ...)`` on stdout, exit 0. Rendering a real
#: PDF here would pull in fpdf2 and about ten seconds per fixture, and would be testing
#: the renderer rather than the release step. `TheGeneratorContractReleasePyReads` below
#: runs the REAL generator once, so the stand-in cannot drift away from the line it
#: imitates without that failing.
STUB_GENERATOR = "\n".join((
    "import argparse",
    "import re",
    "",
    "parser = argparse.ArgumentParser()",
    'parser.add_argument("--input", required=True)',
    'parser.add_argument("--output", required=True)',
    "args = parser.parse_args()",
    'with open(args.input, encoding="utf-8") as handle:',
    "    source = handle.read()",
    'found = re.search(r"[*][*]Plugin version:[*][*]\\s*(\\S+)", source)',
    'stated = found.group(1) if found else "none"',
    'with open(args.output, "wb") as handle:',
    '    handle.write(b"%PDF-1.4\\n% rendered from a source stating ")',
    "    handle.write(stated.encode())",
    '    handle.write(b"\\n%%EOF\\n")',
    'print("PDF generated: %s (renderer: RENDERER, rendered 1 of 1)" % args.output)',
    "",
))


def git(repo, *args, check=True):
    done = subprocess.run(["git"] + list(args), cwd=str(repo),
                          capture_output=True, text=True)
    if check and done.returncode != 0:
        raise AssertionError("git %s failed in fixture: %s" % (" ".join(args), done.stderr))
    return done.stdout.strip()


def release(repo, *args):
    """Run release.py against `repo`. Returns (returncode, stdout, stderr)."""
    done = subprocess.run(
        [sys.executable, str(RELEASE_PY), "--repo", str(repo)] + list(args),
        capture_output=True, text=True)
    return done.returncode, done.stdout, done.stderr


def write_sites(repo, version):
    manifest = Path(repo) / MANIFEST_REL
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({"name": "senzing-bootcamp", "version": version,
                    "license": "Apache-2.0"}, indent=2) + "\n", encoding="utf-8")
    example = Path(repo) / EXAMPLE_REL
    example.parent.mkdir(parents=True, exist_ok=True)
    example.write_text("# Senzing Bootcamp Recap\n\n**Plugin version:** %s\n" % version,
                       encoding="utf-8")
    # Three sites in ONE file, as BLUEPRINT.md really carries: the verbatim manifest copy
    # and the two prose sentences. Planned independently and written in order, the last
    # one would overwrite the other two and release this file one-third bumped (#697) --
    # `test_every_version_site_advanced` is what notices.
    (Path(repo) / BLUEPRINT_REL).write_text(
        "# Blueprint\n\n```json\n{\n  \"name\": \"senzing-bootcamp\",\n"
        "  \"version\": \"%s\",\n}\n```\n\n"
        "The plugin manifest. It declares the name `senzing-bootcamp`, the version\n"
        "`%s` (the single version every other version assertion must match), the\n"
        "same description as the marketplace entry.\n\n"
        "`examples/bootcamp_recap.example.md` is a sanitized finished recap\n"
        "from a Python, Core-path, SQLite run on plugin version %s: the header\n"
        "fields, one section per module.\n" % (version, version, version),
        encoding="utf-8")
    # The rendered site. Real bytes are a PDF; what matters to `release.py` is that the
    # file EXISTS -- that is what makes the re-render a step rather than a no-op -- and
    # what matters here is that the version it carries came from the `.md`.
    pdf = Path(repo) / EXAMPLE_PDF_REL
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4\n% rendered from a source stating "
                    + version.encode("ascii") + b"\n%%EOF\n")


def write_generator(repo, renderer="fpdf2"):
    """The stand-in generator, reporting `renderer` on its success line."""
    script = Path(repo) / GENERATOR_REL
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(STUB_GENERATOR.replace("RENDERER", renderer), encoding="utf-8")


def build_fixture(prefix):
    """A repo shaped like this one: five version sites, two lightweight tags, no CHANGELOG.

    Five, not three: BLUEPRINT.md carries the verbatim manifest copy and two prose
    sentences, and the shipped example recap carries its version twice over -- once as
    text in the ``.md`` and once DRAWN into the ``.pdf`` beside it (#697).

    The tags are LIGHTWEIGHT on purpose -- all seven tags this repo already carries are,
    so the changelog seeder has to read dates off the commit rather than off a tag object.
    """
    tmp = tempfile.mkdtemp(prefix=prefix)
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "--quiet", "--initial-branch", "main")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "fixture")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "tag.gpgsign", "false")

    write_sites(repo, "0.3.5")
    write_generator(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "feat(fixture): the first release")
    git(repo, "tag", "0.3.5")

    (repo / "work.txt").write_text("a\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "fix(fixture): an early fix")
    write_sites(repo, "0.4.1")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "chore(fixture): bump to 0.4.1 the old way")
    git(repo, "tag", "0.4.1")

    (repo / "work.txt").write_text("a\nb\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "feat(fixture): work for the next release")
    return tmp, repo


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheScriptIsPresent(unittest.TestCase):
    """INV-265 -- every check below would 'pass' by erroring identically without it."""

    def test_release_py_exists_and_is_executable_as_a_script(self):
        self.assertTrue(RELEASE_PY.is_file(),
                        "%s is missing; the release skill has no script" % RELEASE_PY)
        code, out, err = release(REPO_ROOT, "--help")
        self.assertEqual(0, code, "release.py --help failed: %s" % err)
        self.assertIn("--apply", out, "release.py has no --apply flag; the tests below "
                                      "would be exercising a different interface")


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class ADryRunChangesNothing(unittest.TestCase):
    """The default must be safe: this script is fronted by a skill and can be model-run."""

    def setUp(self):
        self.tmp, self.repo = build_fixture("release-dry-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_the_default_is_a_dry_run(self):
        head = git(self.repo, "rev-parse", "HEAD")
        code, out, _ = release(self.repo, "--minor")
        self.assertEqual(0, code, out)
        self.assertIn("dry run", out.lower())
        self.assertEqual("", git(self.repo, "status", "--porcelain"),
                         "a dry run left the working tree dirty")
        self.assertEqual(head, git(self.repo, "rev-parse", "HEAD"),
                         "a dry run created a commit")
        self.assertEqual(["0.3.5", "0.4.1"],
                         sorted(git(self.repo, "tag", "--list").split()),
                         "a dry run created a tag -- tags are repository-global and cannot "
                         "be taken back from anyone who has fetched them")
        self.assertFalse((self.repo / CHANGELOG_REL).exists(),
                         "a dry run created CHANGELOG.md")
        self.assertIn(b"0.4.1", (self.repo / EXAMPLE_PDF_REL).read_bytes(),
                      "a dry run re-rendered the example recap PDF; the preview must "
                      "write nothing at all, and a rendered artifact is still a write")

    def test_the_dry_run_states_what_it_would_change(self):
        """A preview that shows nothing is not a preview; the maintainer approves on it."""
        _, out, _ = release(self.repo, "--minor", "--dry-run")
        for expected in (MANIFEST_REL, EXAMPLE_REL, BLUEPRINT_REL, CHANGELOG_REL,
                         EXAMPLE_PDF_REL, "0.4.1", "0.5.0"):
            self.assertIn(expected, out,
                          "the dry run did not mention %r, so it does not show what the "
                          "release would do" % expected)

    def test_apply_and_dry_run_together_are_refused(self):
        code, _, err = release(self.repo, "--minor", "--apply", "--dry-run")
        self.assertNotEqual(0, code, "contradictory flags were accepted")
        self.assertIn("contradict", err)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class AReleaseMovesAllThreeTogether(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.repo = build_fixture("release-apply-")
        cls.code, cls.out, cls.err = release(cls.repo, "--minor", "--apply")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_release_succeeded(self):
        self.assertEqual(0, self.code, "release failed: %s%s" % (self.out, self.err))

    def test_every_version_site_advanced(self):
        manifest = json.loads((self.repo / MANIFEST_REL).read_text(encoding="utf-8"))
        self.assertEqual("0.5.0", manifest["version"])
        self.assertIn("**Plugin version:** 0.5.0",
                      (self.repo / EXAMPLE_REL).read_text(encoding="utf-8"),
                      "the manifest advanced and the shipped example recap did not -- the "
                      "split tests/test_example_recap_sync.py already fails on")
        blueprint = (self.repo / BLUEPRINT_REL).read_text(encoding="utf-8")
        self.assertIn('"version": "0.5.0"', blueprint,
                      "the manifest advanced and BLUEPRINT.md's verbatim copy of it did not")
        # ⛔ The other two sites in the SAME file. A release that planned each entry
        # against the original text would write them in order and keep only the last, so
        # exactly one of these three assertions would pass and the file would ship
        # part-bumped -- the half-release defect, reintroduced inside the tool (#697).
        self.assertIn("the version\n`0.5.0` (the single version", blueprint,
                      "BLUEPRINT.md's section 5.2 prose did not advance; another site in "
                      "the same file overwrote it")
        self.assertIn("run on plugin version 0.5.0:", blueprint,
                      "BLUEPRINT.md's example-recap prose did not advance; another site "
                      "in the same file overwrote it")
        self.assertNotIn("0.4.1", blueprint,
                         "BLUEPRINT.md still states the previous version somewhere")

    def test_the_rendered_version_site_was_re_rendered_from_the_bumped_markdown(self):
        """⛔ A drawn version is a version site no text substitution can reach (#697).

        The 0.7.0 release of this repository moved the manifest, the `.md` and
        BLUEPRINT.md's copy, and left the committed example PDF drawing 0.6.1 -- the
        artifact `README.md` offers as the sample deliverable. Ordering is the whole of
        it: the PDF is rendered FROM the `.md`, so it has to be rendered after the `.md`
        is rewritten. Re-rendered first, it would carry the previous version and every
        other assertion here would still pass.
        """
        rendered = (self.repo / EXAMPLE_PDF_REL).read_bytes()
        self.assertIn(b"0.5.0", rendered,
                      "the committed example PDF was not re-rendered from the bumped "
                      "Markdown; it still carries %r" % rendered[:120])

    def test_the_changelog_was_created_and_seeded_from_the_existing_tags(self):
        text = (self.repo / CHANGELOG_REL).read_text(encoding="utf-8")
        for tag in ("0.5.0", "0.4.1", "0.3.5"):
            self.assertIn("## [%s]" % tag, text,
                          "CHANGELOG.md has no entry for %s; a file seeded from the tags "
                          "must account for every tag that already existed" % tag)
        self.assertLess(text.index("## [0.5.0]"), text.index("## [0.4.1]"),
                        "CHANGELOG.md is not newest-first")
        self.assertIn("fix(fixture): an early fix", text,
                      "the 0.4.1 entry does not list the commits it contained; the seed "
                      "read no history")

    def test_the_seed_note_names_the_versions_it_covers(self):
        """⛔ 'Entries below' stops being true the moment an entry is prepended above."""
        text = (self.repo / CHANGELOG_REL).read_text(encoding="utf-8")
        self.assertIn("0.4.1 and earlier", text,
                      "the reconstructed-history note is positional rather than "
                      "version-anchored, so the next release makes it a false statement")

    def test_a_tag_was_created(self):
        self.assertIn("0.5.0", git(self.repo, "tag", "--list").split(),
                      "no tag 0.5.0 -- this is the kiro-power defect exactly: the version "
                      "and the changelog moved and the tag did not")

    def test_the_tagged_tree_carries_the_bump(self):
        """⛔ The whole point. Tagging HEAD tags the commit BEFORE the bump.

        Everything is read out of the tag, never out of the working tree, so an
        implementation that edits the files and then tags HEAD fails here while passing
        every other assertion in this class.
        """
        manifest = json.loads(git(self.repo, "show", "0.5.0:%s" % MANIFEST_REL))
        self.assertEqual(
            "0.5.0", manifest["version"],
            "the tag 0.5.0 points at a tree whose manifest says %s. A downstream repo "
            "porting from this tag gets the previous release under the new name."
            % manifest["version"])
        self.assertIn("**Plugin version:** 0.5.0",
                      git(self.repo, "show", "0.5.0:%s" % EXAMPLE_REL))
        self.assertIn("## [0.5.0]", git(self.repo, "show", "0.5.0:%s" % CHANGELOG_REL))

    def test_the_tag_is_annotated(self):
        """⛔ A lightweight tag is silently skipped by ``git push --follow-tags``.

        Git has two kinds of tag. A lightweight one is a name pointing straight at a
        commit, so ``cat-file -t`` reports ``commit``; an annotated one is an object of
        its own carrying an author, a date and a message, and reports ``tag``.

        ``git push --follow-tags`` pushes annotated tags and **silently skips lightweight
        ones** -- no warning, no error, exit 0. Measured in a throwaway repo carrying one
        of each: the annotated tag reached the remote and the lightweight one did not,
        with nothing in the output naming the omission. A release tag that stays on the
        maintainer's machine is invisible to the downstream repositories that port from a
        tagged release rather than from HEAD, which is the whole failure this tooling
        exists to prevent -- and it presents as a successful push.

        ⚠️ All seven tags this repository carried before ``release.py`` are lightweight,
        so this assertion pins a NEW convention rather than an existing one. It is
        deliberate, and it is why the rule says MUST.

        ⚠️ What a green run does NOT mean: that the tag was pushed, or that it is signed.
        ``tag.gpgsign`` is read from the maintainer's git config and is not asserted here.
        """
        self.assertEqual(
            "tag", git(self.repo, "cat-file", "-t", "0.5.0"),
            "the release tag is lightweight, not annotated. `git push --follow-tags` "
            "skips lightweight tags silently, so this release would never reach the "
            "remote and no downstream port could target it -- while the push reports "
            "success")

    def test_the_tag_points_at_head(self):
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"),
                         git(self.repo, "rev-parse", "0.5.0^{commit}"))

    def test_the_release_commit_carries_the_release_and_nothing_else(self):
        touched = sorted(git(self.repo, "show", "--name-only", "--format=", "HEAD").split())
        self.assertEqual(
            sorted([CHANGELOG_REL, MANIFEST_REL, EXAMPLE_REL, BLUEPRINT_REL,
                    EXAMPLE_PDF_REL]), touched,
            "the release commit touched %s; a release commit that sweeps in other work "
            "cannot be reverted as a unit" % touched)

    def test_the_working_tree_is_left_clean_and_ready_to_publish(self):
        self.assertEqual("", git(self.repo, "status", "--porcelain"),
                         "the release left uncommitted changes behind")
        self.assertIn("propagate-to-public", self.out,
                      "the run does not name the next step, so the maintainer is left "
                      "guessing whether publishing already happened")

    def test_nothing_was_pushed(self):
        self.assertIn("Nothing was pushed", self.out)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class ASecondReleasePrependsRatherThanReseeds(unittest.TestCase):
    def setUp(self):
        self.tmp, self.repo = build_fixture("release-second-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        code, out, err = release(self.repo, "--minor", "--apply")
        self.assertEqual(0, code, out + err)

    def test_the_second_entry_is_prepended_and_the_first_survives(self):
        (self.repo / "work.txt").write_text("a\nb\nc\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "feat(fixture): after the first release")
        code, out, err = release(self.repo, "--patch", "--apply")
        self.assertEqual(0, code, out + err)
        text = (self.repo / CHANGELOG_REL).read_text(encoding="utf-8")
        self.assertLess(text.index("## [0.5.1]"), text.index("## [0.5.0]"))
        self.assertEqual(1, text.count("# Changelog"),
                         "the header was written twice; the file was re-seeded instead of "
                         "prepended to")
        self.assertIn("feat(fixture): after the first release", text)
        self.assertNotIn("chore(release): 0.5.0", text,
                         "the previous release commit was listed as a change in the next "
                         "release; the range must start at the tag, not before it")


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class ItRefusesRatherThanReleasingHalfOfIt(unittest.TestCase):
    def setUp(self):
        self.tmp, self.repo = build_fixture("release-refuse-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def assertRefused(self, args, needle):
        head = git(self.repo, "rev-parse", "HEAD")
        tags = sorted(git(self.repo, "tag", "--list").split())
        code, out, err = release(self.repo, *args)
        self.assertNotEqual(0, code, "expected a refusal, got success:\n%s" % out)
        self.assertIn(needle, (out + err).lower(),
                      "the refusal did not explain itself in terms of %r:\n%s"
                      % (needle, out + err))
        self.assertEqual(head, git(self.repo, "rev-parse", "HEAD"),
                         "a refusal still created a commit")
        self.assertEqual(tags, sorted(git(self.repo, "tag", "--list").split()),
                         "a refusal still created a tag")

    def test_a_dirty_working_tree_is_refused(self):
        (self.repo / "uncommitted.txt").write_text("x\n", encoding="utf-8")
        self.assertRefused(["--minor", "--apply"], "dirty")

    def test_a_version_that_does_not_advance_is_refused(self):
        self.assertRefused(["0.4.1", "--apply"], "advance")

    def test_a_version_that_goes_backwards_is_refused(self):
        self.assertRefused(["0.4.0", "--apply"], "advance")

    def test_a_version_that_is_not_semver_is_refused(self):
        self.assertRefused(["v0.5", "--apply"], "major.minor.patch")

    def test_no_bump_at_all_is_refused(self):
        """Defaulting to a patch bump would make a bare `/release` cut a release."""
        self.assertRefused(["--apply"], "nothing to release")

    def test_two_bump_sizes_at_once_are_refused(self):
        self.assertRefused(["--minor", "--major", "--apply"], "exactly one")

    def test_an_existing_tag_is_refused(self):
        """Re-pointing a tag rewrites what a downstream repo may already have fetched."""
        git(self.repo, "tag", "0.9.9")
        self.assertRefused(["0.9.9", "--apply"], "already exists")

    def test_a_tag_ahead_of_the_manifest_is_refused(self):
        """The kiro-power shape as a STARTING state: releasing from it hides the split."""
        git(self.repo, "tag", "0.6.0")
        self.assertRefused(["0.7.0", "--apply"], "diverged")

    def test_a_branch_other_than_main_is_refused(self):
        git(self.repo, "checkout", "--quiet", "-b", "feature")
        self.assertRefused(["--minor", "--apply"], "refusing to tag")

    def test_a_version_site_that_stopped_matching_is_refused(self):
        """⛔ The half-release: bump the manifest, leave the example recap stale."""
        example = self.repo / EXAMPLE_REL
        example.write_text(example.read_text(encoding="utf-8").replace(
            "**Plugin version:**", "**Plugin build:**"), encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): rename the meta row")
        self.assertRefused(["--minor", "--apply"], "stale")

    def test_a_missing_version_site_is_refused(self):
        (self.repo / EXAMPLE_REL).unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): drop the example recap")
        self.assertRefused(["--minor", "--apply"], "missing")

    def test_version_sites_that_already_disagree_are_refused(self):
        example = self.repo / EXAMPLE_REL
        example.write_text("# Recap\n\n**Plugin version:** 0.4.0\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): desync the example")
        self.assertRefused(["--minor", "--apply"], "diverged")

    def test_a_render_that_falls_back_to_the_stdlib_writer_is_refused(self):
        """⛔ Exit 0 is not the contract; the RICH renderer is (#697).

        The generator always produces a valid PDF: with fpdf2 absent it falls back to a
        stdlib writer that embeds no images and draws no branded certificate. Accepting
        that would swap the shipped keepsake for a plainer one at exit 0 -- a silent
        degradation of the artifact `README.md` offers as the sample deliverable.
        """
        write_generator(self.repo, renderer="stdlib")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): lose fpdf2")
        self.assertRefused(["--minor", "--apply"], "stdlib")
        self.assertEqual(
            "", git(self.repo, "diff", "--name-only"),
            "the refusal left edited files behind; a release that cannot finish must roll "
            "all the way back rather than leave a part-bumped tree")

    def test_a_missing_generator_is_refused_when_a_rendered_site_ships(self):
        """A shipped PDF with no way to re-render it would ship stating the old version."""
        (self.repo / GENERATOR_REL).unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): drop the generator")
        self.assertRefused(["--minor", "--apply"], "generate_recap_pdf.py")

    def test_a_directory_that_is_not_the_plugin_repo_is_refused(self):
        other = Path(self.tmp) / "elsewhere"
        other.mkdir()
        code, out, err = release(other, "--minor", "--apply")
        self.assertNotEqual(0, code)
        self.assertIn("does not look like the plugin repo", out + err)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class ThereIsNoPathThatMovesOnlySomeOfThem(unittest.TestCase):
    """Atomicity is structural here: one function does all three, and no flag splits them."""

    def test_the_interface_offers_no_flag_that_skips_a_step(self):
        _, out, _ = release(REPO_ROOT, "--help")
        offered = set(re.findall(r"--[a-z][a-z-]+", out))
        forbidden = sorted(flag for flag in offered
                           if re.match(r"^--(no|skip|without|only)-", flag)
                           or flag in ("--tag-only", "--files-only", "--changelog-only"))
        self.assertEqual(
            [], forbidden,
            "release.py offers %s. Any flag that performs part of a release reintroduces "
            "the defect: the acceptance criterion is that there is NO path which updates "
            "one of version/changelog/tag without the others" % ", ".join(forbidden))

    def test_the_script_never_pushes(self):
        """Publishing is a separate, deliberate step; an automatic push is unrecallable."""
        source = RELEASE_PY.read_text(encoding="utf-8")
        pushes = [line.strip() for line in source.splitlines()
                  if re.search(r'git\(\s*repo\s*,\s*"push"', line)]
        self.assertEqual([], pushes,
                         "release.py invokes git push: %s" % "; ".join(pushes))


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TagsAreOrderedNumerically(unittest.TestCase):
    """0.10.0 sorts BEFORE 0.9.0 as text. A release tool gets one chance to have this right."""

    def setUp(self):
        self.tmp, self.repo = build_fixture("release-order-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_the_newest_tag_is_the_numerically_newest(self):
        git(self.repo, "tag", "0.9.0")
        git(self.repo, "tag", "0.10.0")
        # 0.10.0 is the newest, so a release of 0.9.1 must be refused as going backwards.
        code, out, err = release(self.repo, "0.9.1", "--apply")
        self.assertNotEqual(
            0, code,
            "0.9.1 was accepted while 0.10.0 already exists; tags are being compared as "
            "text, so every release after 0.9.x would be mis-ordered:\n%s" % out)
        self.assertIn("0.10.0", out + err)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheRenderedSiteIsDrivenByTheArtifactItself(unittest.TestCase):
    """Which repositories get a re-render, and how a repository without one is reported."""

    def setUp(self):
        self.tmp, self.repo = build_fixture("release-render-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_a_repo_with_no_rendered_site_releases_without_one(self):
        """⚠️ Not a silent skip, which is the shape every other rule here forbids.

        A repository that ships no example PDF has nothing to re-render. The run says so
        in as many words, so a reader can tell "there was nothing to do" from "the step
        was passed over", which are the same output otherwise.
        """
        (self.repo / EXAMPLE_PDF_REL).unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore(fixture): drop the example PDF")
        code, out, err = release(self.repo, "--minor", "--apply")
        self.assertEqual(0, code, out + err)
        self.assertIn("nothing to re-render", out,
                      "the run passed over the rendered site without saying so")
        touched = sorted(git(self.repo, "show", "--name-only", "--format=", "HEAD").split())
        self.assertEqual(
            sorted([CHANGELOG_REL, MANIFEST_REL, EXAMPLE_REL, BLUEPRINT_REL]), touched,
            "a repository with no rendered site still staged one")


class TheGeneratorContractReleasePyReads(unittest.TestCase):
    """⛔ The stand-in generator above imitates a line; this is the line itself.

    `release.py` reads two things out of the real generator's stdout -- the
    ``PDF generated:`` prefix, which is also the graduation skill's success signal, and
    the ``renderer: <name>`` field it refuses a stdlib fallback on. Both are a contract
    between two files that no other test relates, and the fixtures above would keep
    passing against a stand-in that had drifted away from it.

    ⚠️ Runs in BOTH legs: the fallback writer prints the same line with a different
    renderer name, which is exactly the distinction being pinned, so this carries no
    fpdf2 requirement.
    """

    def test_the_generator_prints_the_line_release_py_parses(self):
        generator = REPO_ROOT / GENERATOR_REL
        self.assertTrue(generator.is_file(),
                        "%s is gone; release.py has nothing to call" % GENERATOR_REL)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "recap.pdf"
            done = subprocess.run(
                [sys.executable, str(generator),
                 "--input", str(REPO_ROOT / EXAMPLE_REL), "--output", str(out)],
                capture_output=True, text=True, cwd=tmp)
            self.assertEqual(0, done.returncode,
                             "the generator failed on the shipped example:\n%s"
                             % done.stderr[-2000:])
            self.assertRegex(
                done.stdout, r"PDF generated: .*\(renderer: (fpdf2|stdlib),",
                "the generator's success line no longer carries the prefix and the "
                "renderer name release.py keys on, so a stdlib render would be committed "
                "as though it were the designed one:\n%s" % done.stdout)


if __name__ == "__main__":
    unittest.main()
