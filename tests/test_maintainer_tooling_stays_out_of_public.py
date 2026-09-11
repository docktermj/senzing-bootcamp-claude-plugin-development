"""Maintainer tooling under `.claude/` is unreachable by the propagate mirror.

The public access repo ships a participant runtime. `.claude/` is the maintainer half of
this repo -- the development commands (`/implement-spec`, `/propagate-to-public`,
`/retrofit-from-public`), the skills behind them, and `settings.local.json`. Publishing any
of it hands a bootcamper release-path tooling that acts on repos they do not have, and in
the case of `retrofit-from-public` and `propagate-to-public`, tooling that would write
across two checkouts.

Nothing asserted this. It held only because `propagate.sh` happens to name its sources one
at a time: `plugins/`, `.claude-plugin/`, `docs/` and `README.md`. That is an allowlist by
construction, not by rule, and construction is exactly what an edit changes -- a future
`rsync -a --delete "$here/" "$dest/"` to "simplify" the four calls into one would publish
the whole maintainer surface and still pass every other test in this suite.

⛔ **`.claude-plugin/` IS propagated and must stay propagated.** It holds `marketplace.json`,
which is how the plugin is installed. It also string-prefix-matches `.claude`, so a guard
written as `path.startswith(".claude")` fails on the very file the release depends on. This
test compares **path components**, never string prefixes. The script itself documents the
same class of bug one section down, where `SLUG_OLD` must keep its `-development` suffix
because the unsuffixed string still matches as a prefix and publishes a broken slug.

⚠️ **What a green run means.** No `rsync` source in `propagate.sh` reaches into `.claude/`.
It does not mean the mirror is otherwise correct, that the exclusions inside the propagated
roots are right, or that the reverse path (`retrofit.sh`) declines to pull governance back --
those are separate concerns with their own reviews.

The propagated set is compared as a set and its size is never asserted, so adding a
legitimate fifth root is a one-line change here rather than a number to bump.

Stdlib only; the script is read as text (INV-108).

Source issue: #19 (`/retrofit-from-public`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import PurePosixPath
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPAGATE_SH = REPO_ROOT / ".claude" / "skills" / "propagate-to-public" / "propagate.sh"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"

#: An rsync source argument naming a path in THIS repo: "$here/<path>".
#: The destination side is "$dest/..." and is deliberately not matched -- what the public
#: repo receives is the subject, and it is named by the source.
RSYNC_SOURCE = re.compile(r'rsync\s[^\n]*?"\$here/([^"]*)"')

#: The maintainer directory that must never be a propagation source.
MAINTAINER_DIR = ".claude"


def propagated_paths():
    """Every repo-relative path `propagate.sh` hands to rsync as a source."""
    text = PROPAGATE_SH.read_text(encoding="utf-8")
    return {m.rstrip("/") for m in RSYNC_SOURCE.findall(text)}


def reaches_into_maintainer_dir(path):
    """True when `path` is `.claude` or lives under it, by COMPONENT not by prefix.

    `.claude-plugin` is a sibling, not a child: it shares five characters and nothing else.
    """
    parts = PurePosixPath(path).parts
    return bool(parts) and parts[0] == MAINTAINER_DIR


class NeitherSideIsEmpty(unittest.TestCase):
    """INV-265 -- a containment check over an empty set passes without proving anything."""

    def test_the_script_is_where_this_test_thinks(self):
        self.assertTrue(
            PROPAGATE_SH.is_file(),
            "%s is gone; the propagate skill moved and this guard is reading nothing"
            % PROPAGATE_SH)

    def test_rsync_sources_were_parsed(self):
        found = propagated_paths()
        self.assertGreaterEqual(
            len(found), 4,
            "parsed fewer than four rsync sources from %s (found %s); the script states its "
            "sources in a shape this regex no longer matches, and the check below would pass "
            "on an empty set" % (PROPAGATE_SH, sorted(found)))

    def test_the_known_roots_are_recognized(self):
        """Anchored on paths that predate this guard, so it cannot pass tautologically."""
        found = propagated_paths()
        for expected in ("plugins", ".claude-plugin", "docs", "README.md"):
            self.assertIn(
                expected, found,
                "%r is not among the parsed propagation sources %s; either the mirror has "
                "genuinely stopped publishing it, or the parse is wrong"
                % (expected, sorted(found)))

    def test_there_is_maintainer_tooling_to_protect(self):
        commands = sorted(p.name for p in COMMANDS_DIR.glob("*.md"))
        self.assertTrue(
            commands,
            "no maintainer command files found in %s; this guard protects an empty directory"
            % COMMANDS_DIR)


class TheSiblingIsNotMistakenForTheChild(unittest.TestCase):
    """The prefix bug this guard is most likely to be rewritten into."""

    def test_claude_plugin_is_not_treated_as_maintainer_tooling(self):
        self.assertFalse(
            reaches_into_maintainer_dir(".claude-plugin"),
            ".claude-plugin was classified as maintainer tooling. It holds marketplace.json "
            "and MUST keep propagating; this check is matching string prefixes instead of "
            "path components")

    def test_the_maintainer_dir_and_its_children_are_caught(self):
        for path in (".claude", ".claude/commands", ".claude/commands/retrofit-from-public.md",
                     ".claude/skills/propagate-to-public/propagate.sh"):
            self.assertTrue(
                reaches_into_maintainer_dir(path),
                "%r was not recognized as living under %s/; the check cannot see the thing it "
                "exists to catch" % (path, MAINTAINER_DIR))


class MaintainerToolingIsNeverPropagated(unittest.TestCase):
    def test_no_rsync_source_reaches_into_the_maintainer_dir(self):
        leaked = sorted(p for p in propagated_paths() if reaches_into_maintainer_dir(p))
        self.assertEqual(
            [], leaked,
            "propagate.sh names %s as a mirror source, publishing maintainer tooling into the "
            "public repo. The public repo ships a participant runtime; release-path commands "
            "and skills act on checkouts a bootcamper does not have" % leaked)

    def test_the_whole_repo_is_not_propagated_wholesale(self):
        """`rsync "$here/" "$dest/"` reaches .claude/ without ever naming it."""
        wholesale = sorted(p for p in propagated_paths() if p in ("", "."))
        self.assertEqual(
            [], wholesale,
            "propagate.sh mirrors the repo root %s, which carries .claude/ into the public "
            "repo without naming it. Mirror each allowlisted path by name" % wholesale)


if __name__ == "__main__":
    unittest.main()
