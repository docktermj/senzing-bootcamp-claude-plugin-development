"""Retired vocabulary may appear only on a line that marks it as retired.

Three full audits have now found the same defect class, and it is the largest one by
count: an invariant supersedes another, the new behavior is implemented, and prose
somewhere else keeps describing the retired model. Nothing catches it, because every
test asserts the *new* behavior and the stale sentence is grammatical, plausible, and
sitting in a file nobody edited.

The worst instance found so far shipped for eight days through two audits.
`module-07-query-visualize-discover/SKILL.md` still said "Path A (full bootcamp)
proceeds to graduation; Paths B/C (shorter paths) may stop here with working query
programs. Preserve that gate exactly." — the A/B/C track model INV-076 replaced. It
contradicted INV-076 (Graduation is Required in every path), contradicted its own
module's phase file two directories away, and instructed the agent to preserve a gate
that no longer existed. An agent could have ended a bootcamp before a mandatory module.

So this is not a re-read; it is a registry. The rule it enforces:

    A retired term may appear in a shipped file ONLY on a line that frames it as
    retired.

That keeps the honest uses — "superseded by INV-076", "older sessions may store this as
`track`", "legacy recaps titled it Journal" — and fails the bare ones, which are exactly
the stale-instruction case. When an invariant retires a concept, add its vocabulary here
in the same change; the registry is the durable half of the supersession.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

# A line carrying any of these frames its retired term as retired, so the term is
# allowed there. Deliberately generous: the defect this test hunts is a term used with
# NO retirement framing at all, and a false failure on an honest back-compat note would
# just train people to add exemptions.
RETIREMENT_MARKERS = (
    "retired",
    "supersede",
    "superseding",
    "legacy",
    "formerly",
    "former ",
    "deprecat",
    "no longer",
    "older session",
    "older recap",
    "replaces the old",
    "replaced the",
    "was renamed",
    "renamed to",
    "removed",
    "alias",
    "historical",
    "used to",
    "once ",
    "pre-inv",
    "not reintroduce",
    "reintroduce",
)

# (label, pattern, superseding invariant, what to say instead)
RETIRED_TERMS = (
    (
        "A/B/C track model",
        re.compile(r"\bPaths? [ABC]\b"),
        "INV-076",
        "the Core-vs-Customized path choice; Graduation is Required in every path",
    ),
    (
        "`track` preference key",
        re.compile(r"`track`"),
        "INV-076",
        "the `path` preference (`core` / `customized`)",
    ),
    (
        "data/transformed directory",
        re.compile(r"\bdata/transformed\b"),
        "INV-084",
        "`data/senzing-ready/`",
    ),
    (
        "Journal recap subsection",
        re.compile(r"^#{2,4}\s+Journal\b", re.MULTILINE),
        "INV-103",
        "the End-of-Module Summary subsection",
    ),
    (
        "bootcamp_journal.md narrative",
        re.compile(r"\bbootcamp_journal\.md\b"),
        "INV-085",
        "the consolidated `docs/bootcamp_recap.md`",
    ),
    (
        "multi_source_results.html static page",
        re.compile(r"\bmulti_source_results\.html\b"),
        "INV-104",
        "the single tabbed app's Entity Graph / Cross-Source tabs",
    ),
    (
        "separate numbered Modules 8-11",
        re.compile(r"\bModules? 8\s*[-–]\s*11\b"),
        "INV-013",
        "production-hardening delivered at graduation",
    ),
    (
        "Module 0 skip/keep gate",
        re.compile(r"skip/keep gate"),
        "INV-078",
        "inclusion driven by the Bootcamp preparation selection",
    ),
    (
        '"Claude app" / "Claude application" for an interface',
        re.compile(r"\bClaude app(?:lication)?\b", re.IGNORECASE),
        "INV-158",
        'the interface by name: "Claude Desktop", "Claude Code CLI", '
        '"the Claude web app", "a Claude IDE extension"',
    ),
)


def shipped_files():
    """Every file a bootcamper receives, excluding generated caches and binaries.

    Includes the repo-root install docs (`README.md`, `docs/*.md`): `propagate-to-public`
    mirrors both into the public repo as user-facing content, so a retired term reads to a
    bootcamper there exactly as it would inside the plugin. Leaving them out is how
    "the Claude app" survived in the install instructions (INV-158).
    """
    roots = list(sorted(PLUGIN.rglob("*")))
    roots += [REPO_ROOT / "README.md"] + sorted((REPO_ROOT / "docs").glob("*.md"))
    for path in roots:
        if not path.is_file():
            continue
        if path.suffix not in (".md", ".py", ".json"):
            continue
        if "pytest_cache" in path.parts or "__pycache__" in path.parts:
            continue
        yield path


def retired_term_lines(text, pattern):
    """1-based lines where a retired term starts.

    Multiline heading patterns are matched against the whole text, since a heading is one
    line. The rest go through ``match_lines`` (#424), so a term of two words ("Path\nA",
    "Claude\napp") is found across a line wrap at the line it starts on. The allow-rule still
    reads that line, as before, so retirement framing that wraps away from it fails closed.
    """
    if pattern.flags & re.MULTILINE:
        return [text[: m.start()].count("\n") + 1 for m in pattern.finditer(text)]
    return match_lines(text, pattern)


def marked_as_retired(line):
    low = line.lower()
    return any(marker in low for marker in RETIREMENT_MARKERS)


class TestRetiredVocabulary(unittest.TestCase):
    """Every superseded concept's vocabulary, checked across all shipped files."""

    def test_retired_terms_are_always_framed_as_retired(self):
        offenders = []
        for path in shipped_files():
            rel = path.relative_to(REPO_ROOT)
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, pattern, invariant, instead in RETIRED_TERMS:
                hits = retired_term_lines(text, pattern)
                for lineno in hits:
                    line = text.split("\n")[lineno - 1]
                    if marked_as_retired(line):
                        continue
                    offenders.append(
                        f"{rel}:{lineno} uses the retired {label} "
                        f"(retired by {invariant}) with no retirement framing.\n"
                        f"      line: {line.strip()[:110]}\n"
                        f"      say instead: {instead}"
                    )
        self.assertEqual(
            [],
            offenders,
            "Retired vocabulary used as though it were current — the stale-instruction "
            "defect class:\n  " + "\n  ".join(offenders),
        )

    def test_registry_is_not_silently_empty(self):
        """A registry that stopped matching anything is a registry nobody maintains."""
        self.assertGreaterEqual(len(RETIRED_TERMS), 8)
        for label, pattern, invariant, instead in RETIRED_TERMS:
            with self.subTest(term=label):
                self.assertTrue(label and instead, "each entry needs a label and advice")
                self.assertRegex(invariant, r"^INV-\d{3}$")

    def test_a_wrapped_retired_term_is_caught_at_its_first_line(self):
        """Negative control (#424): "Path" ends line 1 and "A" begins line 2."""
        wrapped = "At the module transition, Path\nA proceeds to graduation.\n"
        pattern = next(p for label, p, _, _ in RETIRED_TERMS if label.startswith("A/B/C"))
        self.assertEqual([1], retired_term_lines(wrapped, pattern))
        self.assertFalse(marked_as_retired(wrapped.split("\n")[0]))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(pattern.search(l) for l in wrapped.split("\n")))

    def test_a_wrapped_term_framed_as_retired_is_allowed(self):
        """Must-not-flag (INV-282): the honest back-compat note, wrapped."""
        wrapped = "Older sessions may store this as the legacy Claude\napp wording.\n"
        pattern = next(p for label, p, _, _ in RETIRED_TERMS if label.startswith('"Claude app"'))
        (n,) = retired_term_lines(wrapped, pattern)
        self.assertTrue(marked_as_retired(wrapped.split("\n")[n - 1]))

    def test_the_known_regression_would_be_caught(self):
        """Self-check: the exact sentence that shipped must fail the rule.

        Without this, a future edit could loosen RETIREMENT_MARKERS until the rule
        accepts everything and the suite would still be green.
        """
        shipped_regression = (
            "module transition: Path A (full bootcamp) proceeds to graduation; Paths B/C"
        )
        pattern = next(p for label, p, _, _ in RETIRED_TERMS if label.startswith("A/B/C"))
        self.assertTrue(pattern.search(shipped_regression))
        self.assertFalse(
            marked_as_retired(shipped_regression),
            "RETIREMENT_MARKERS has been loosened until the original defect passes",
        )


if __name__ == "__main__":
    unittest.main()
