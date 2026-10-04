"""Shipped Markdown carries no mangled punctuation or trailing whitespace.

The cheapest of the six guards, and it pins a defect that reached the Bootcamper's ears.
A mechanical em-dash replacement left four sites reading ``… the common attributes , ``
with the comma orphaned after a space and trailing whitespace behind it. Three sat inside
quoted dialogue the guide reads aloud:

    "I'll use Entity [ID], which contains records from [Source A] and [Source B] ,
    let's see why Senzing decided these belong to the same real-world entity."

Nothing failed. The Markdown is valid, the meaning survives, and no reviewer scanning for
logic errors looks at spacing — which is exactly why it needs a machine. INV-004 is the
production-ready bar, and a guide that speaks mangled punctuation is not at it.

Scoped to what was actually found, so it stays a hygiene check rather than a style
opinion: space-before-comma, and trailing whitespace. Both are unambiguous defects in this
codebase — the audit sweep found zero legitimate instances of either.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
NORMALIZER = PLUGIN / "scripts" / "normalize_docs_markdown.py"


def load_normalizer():
    spec = importlib.util.spec_from_file_location("normalizer_for_hygiene", NORMALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NORM = load_normalizer()


def shipped_markdown():
    for path in sorted(PLUGIN.rglob("*.md")):
        if "pytest_cache" in path.parts or "__pycache__" in path.parts:
            continue
        yield path


#: A space before a comma. Matched by ``match_lines`` across line wraps (#424): Markdown
#: renders a line break as a space, so a comma that opens a line reads "word ," aloud just as
#: the orphaned comma on one line does.
SPACE_BEFORE_COMMA = re.compile(r" ,")


class TestPunctuationHygiene(unittest.TestCase):

    def test_no_space_before_a_comma(self):
        offenders = []
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.split("\n")
            for n in match_lines(text, SPACE_BEFORE_COMMA):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)}:{n}: {lines[n - 1].strip()[:100]}"
                )
        self.assertEqual(
            [],
            offenders,
            "space before a comma — the signature of a mechanical em-dash replacement, "
            "which put mangled punctuation into spoken dialogue:\n  "
            + "\n  ".join(offenders),
        )

    def test_a_comma_that_opens_a_line_is_caught(self):
        """Negative control (#424): "[Source B]" ends line 1 and the comma opens line 2."""
        wrapped = "records from [Source A] and [Source B]\n, let's see why Senzing decided.\n"
        self.assertEqual([1], match_lines(wrapped, SPACE_BEFORE_COMMA))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        self.assertFalse(any(" ," in line for line in wrapped.split("\n")))

    def test_a_comma_after_a_word_that_ends_a_line_is_not_flagged(self):
        """Must-not-flag (INV-282): a comma, then a wrap, is ordinary prose."""
        self.assertEqual([], match_lines("records from [Source A],\nlet's see why.\n",
                                         SPACE_BEFORE_COMMA))

    def test_no_trailing_whitespace(self):
        """Line-scoped by design (#424): trailing whitespace is a property of a line."""
        offenders = []
        for path in shipped_markdown():
            for n, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if line != line.rstrip():
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{n}")
        self.assertEqual(
            [],
            offenders,
            "trailing whitespace in shipped Markdown (a two-space Markdown line break is "
            "not used anywhere in this codebase, so these are edit residue):\n  "
            + "\n  ".join(offenders),
        )


class TestNoShippedMarkdownIsMojibake(unittest.TestCase):
    """The detector existed and the corpus was enumerated; nothing pointed them at
    each other.

    `mojibake_lines` catches the Windows-1252 round-trip corruption `ground-rules.md`
    documents — UTF-8 read as Windows-1252 and written back as UTF-8, which turned 25
    em dashes into `a<TM>"` in a real run. It was run over the shipped example recap and
    over a project's own `docs/` at bootcamp time, but never over the plugin's own ~200
    Markdown files, any one of which is edited on Windows through exactly that trap.
    """

    # The one legitimate instance: `ground-rules.md` teaches the Windows-1252 trap by
    # quoting the corruption it produces (`25 em dashes became ...`), inside a backtick
    # span. The gate structurally cannot represent that input, so it is exempted rather
    # than satisfied by altering the documentation to suit the check (INV-173). The
    # exemption is as narrow as the case: this file only, and only where every mojibake
    # character sits inside inline code — corrupted *prose* here still fails — and
    # `test_the_exemption_is_not_stale` fails if the example ever goes away, so a dead
    # exemption cannot quietly cover a real defect later.
    TEACHES_THE_CORRUPTION = "skills/bootcamp-onboarding/ground-rules.md"
    INLINE_CODE = re.compile(r"`[^`]*`")

    def _exempt(self, path, line):
        if not path.as_posix().endswith(self.TEACHES_THE_CORRUPTION):
            return False
        return not NORM.mojibake_lines(self.INLINE_CODE.sub("", line))

    # Line-scoped by design (#424): mojibake is a character-level defect, with no phrase in it
    # for a line break to split.
    def _offenders(self):
        found = []
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            for n in NORM.mojibake_lines(text):
                line = lines[n - 1]
                if self._exempt(path, line):
                    continue
                found.append(f"{path.relative_to(REPO_ROOT)}:{n}: {line.strip()[:100]}")
        return found

    def test_no_shipped_markdown_is_mojibake(self):
        offenders = self._offenders()
        self.assertEqual(
            [],
            offenders,
            "Windows-1252 mojibake in shipped Markdown — UTF-8 read as Windows-1252 and "
            "written back as UTF-8 (see ground-rules.md's PowerShell section):\n  "
            + "\n  ".join(offenders),
        )

    def test_the_detector_would_catch_the_known_corruption(self):
        """Guard the guard: a detector that returns [] for everything passes silently."""
        corrupted = "Senzing Bootcamp — a recap".encode("utf-8").decode("cp1252")
        self.assertEqual([1], NORM.mojibake_lines(corrupted))
        self.assertEqual([], NORM.mojibake_lines("Senzing Bootcamp — a recap"))

    def test_the_exemption_is_not_stale(self):
        """The exempted file must still carry the example it is exempted for."""
        ground_rules = PLUGIN / self.TEACHES_THE_CORRUPTION
        text = ground_rules.read_text(encoding="utf-8")
        lines = text.splitlines()
        exempted = [
            n for n in NORM.mojibake_lines(text) if self._exempt(ground_rules, lines[n - 1])
        ]
        self.assertTrue(
            exempted,
            f"{self.TEACHES_THE_CORRUPTION} no longer quotes the corruption it teaches — "
            "drop TEACHES_THE_CORRUPTION rather than leaving an exemption that now "
            "covers nothing and would hide the next real one",
        )

    def test_corrupted_prose_in_the_exempted_file_still_fails(self):
        """The exemption covers inline code, not the whole file."""
        ground_rules = PLUGIN / self.TEACHES_THE_CORRUPTION
        in_code = "25 em dashes became `%s`." % "—".encode("utf-8").decode("cp1252")
        as_prose = "25 em dashes became %s." % "—".encode("utf-8").decode("cp1252")
        self.assertTrue(self._exempt(ground_rules, in_code))
        self.assertFalse(self._exempt(ground_rules, as_prose))

    def test_the_exemption_does_not_apply_to_other_files(self):
        other = PLUGIN / "skills" / "bootcamp-onboarding" / "SKILL.md"
        in_code = "became `%s`." % "—".encode("utf-8").decode("cp1252")
        self.assertFalse(self._exempt(other, in_code))


class TestTheScanIsNotVacuous(unittest.TestCase):
    """A glob that stops matching would make both checks pass silently."""

    def test_markdown_is_actually_being_scanned(self):
        files = list(shipped_markdown())
        self.assertGreaterEqual(
            len(files),
            30,
            f"only {len(files)} shipped .md files found; the glob has drifted and these "
            "checks are now vacuous",
        )

    def test_the_known_regression_would_be_caught(self):
        """Self-check on the exact string that shipped."""
        regression = "explain the common attributes , "
        self.assertIn(" ,", regression)
        self.assertNotEqual(regression, regression.rstrip())


if __name__ == "__main__":
    unittest.main()
