"""`package_bootcamp.py` and `write-gate.py` scan for the SAME secrets (INV-109).

The write gate blocks a *write* whose content matches a secret pattern. The packager excludes a
*member* whose content matches them. Two consumers of one rule -- and if they drift, the packager
quietly protects less than the gate, in the one artifact the Bootcamper hands to someone else.

⚠️ **The gate keeps its own inline copy on purpose, and this test is the reason that is safe.**
`write-gate.py` is a `PreToolUse` control: an ImportError there does not degrade to "no secret
scan", it degrades to a hook that cannot run at all, on every write in the bootcamp. The plugin
already uses exactly this shape for `brand_tokens.py`, whose palette is inlined into every generator
that carries a fallback copy, with `tests/test_brand_sync.py` discovering the carriers and asserting
the copies stay equal. This test does that job for the secret patterns, so the duplication cannot
become drift.

⛔ The comparison is on the pattern **string**, not on behavior sampled from a few examples: a
sampled comparison passes while a fourth alternation branch exists on one side only.

⛔ **What this file proves, and what it does NOT.** It establishes that the two consumers scan for
the same *patterns*. It does **not** establish that they apply them to the same *inputs*, and on
2026-08-26 they did not: the gate scanned every payload while the packager scanned only members
whose extension appeared in an allowlist, so a `.pem` private key was packaged while the identical
key in a `.py` was excluded. This file was green throughout, and its docstring claimed the
packager "cannot protect less than the gate" — true of the constants, false of the behavior.

So the equality below is necessary and not sufficient, and
`TheApplicationIsNotNarrowedByFileType` guards the half that was missing. The general lesson is
worth more than the fix: **a sync test on a shared constant says nothing about how each consumer
uses it.**

Stdlib only.

Source spec: `specs/the-bootcamp-cannot-leave-the-machine-it-was-built-on.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
WRITE_GATE = SCRIPTS / "write-gate.py"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PATTERNS = load("secret_patterns_under_test", "secret_patterns.py")


def gate_inline_pattern():
    """The alternation `write-gate.py` compiles, read out of its source.

    Read as text rather than imported: the gate reads stdin at import time, so importing it inside
    a test would consume the runner's stdin and block.
    """
    text = WRITE_GATE.read_text(encoding="utf-8")
    # The trailing comma sits at the END of the last raw-string line, not on its own line.
    match = re.search(r'if re\.search\(\s*(.*?),\s*\n\s*data,', text, re.S)
    assert match, "the write gate's secret re.search() call no longer parses out of its source"
    body = match.group(1)
    parts = re.findall(r'r"([^"]*)"', body)
    assert parts, "no raw-string fragments found in the gate's pattern"
    return "".join(parts)


class TheTwoListsAreTheSameList(unittest.TestCase):
    def test_the_pattern_strings_are_identical(self):
        self.assertEqual(
            PATTERNS.SECRET_PATTERN,
            gate_inline_pattern(),
            "the packager's secret pattern and write-gate.py's inline copy have drifted. They must "
            "stay byte-identical: the packager writes the one artifact that leaves the machine, so "
            "it must never scan for less than the gate does",
        )

    def test_the_extraction_is_not_vacuous(self):
        """INV-265 — an empty string on both sides would satisfy the equality above."""
        extracted = gate_inline_pattern()
        self.assertGreater(len(extracted), 60,
                           "the gate pattern extracted to something implausibly short; the "
                           "equality test above is comparing nothing")
        for fragment in ("PRIVATE KEY", "AKIA", "AQAAAD"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, extracted)

    def test_all_three_classes_are_named(self):
        self.assertEqual(3, len(PATTERNS.SECRET_PATTERN_NAMES))


class TheApplicationIsNotNarrowedByFileType(unittest.TestCase):
    """Equal patterns, unequal application — the gap the pattern comparison cannot see.

    `write-gate.py` scans the whole payload with no notion of file type. The packager must not be
    narrower, and it was: `TEXT_SUFFIXES` decided whether a member was scanned at all, and
    `_scan()` returned None -- indistinguishable from clean -- for anything unlisted.
    """

    def setUp(self):
        self.packager = (SCRIPTS / "package_bootcamp.py").read_text(encoding="utf-8")

    def test_the_packager_has_no_extension_allowlist(self):
        """Asserted on the CODE, not the whole file.

        The module comment names `TEXT_SUFFIXES` deliberately — that rationale is what stops it
        being re-added — so a bare substring check fires on the explanation of the fix. What must
        not exist is the assignment.
        """
        self.assertIsNone(
            re.search(r"(?m)^TEXT_SUFFIXES\s*=", self.packager),
            "package_bootcamp.py defines an extension allowlist again. An allowlist answering "
            "'is this worth reading as text?' cannot answer 'can this contain a secret?', and "
            "the one that existed skipped .pem, .key and the empty extension -- the file types "
            "whose purpose is to hold a credential")

    def test_the_removal_rationale_survives(self):
        """⛔ Never cut the reason. Without it, a later editor re-adds the allowlist as tidying."""
        self.assertIn("There is deliberately NO extension allowlist here", self.packager)
        self.assertIn(".pem", self.packager,
                      "the comment no longer names the file type that was being skipped, which "
                      "is the concrete fact that makes the rule hard to argue away")

    def test_the_scan_is_not_gated_on_a_suffix(self):
        self.assertNotRegex(
            self.packager, r"def _scan\(path\):(?:.|\n){0,400}?path\.suffix",
            "the packager's secret scan consults the file suffix again; every member must be "
            "scanned regardless of extension")

    def test_an_unreadable_member_is_not_treated_as_clean(self):
        """The third outcome. Collapsing it into None is what made 'not scanned' read as 'clean'."""
        self.assertIn(
            "UNEXAMINED", self.packager,
            "the packager no longer distinguishes 'could not read it' from 'read it and found "
            "nothing'; an unexamined member must be excluded, not included")

    def test_the_write_gate_still_scans_every_payload(self):
        """The baseline the packager is measured against — assert it, do not assume it."""
        gate = WRITE_GATE.read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"(?m)^\s*(?:if|elif).*\.suffix", gate),
            "write-gate.py has grown a suffix filter. If that is deliberate, the comparison in "
            "this file needs rethinking; if not, the gate now protects less than it did")


class TheClassifierNamesTheRightClass(unittest.TestCase):
    """The manifest says WHICH kind of secret was found; a reader cannot act on "a secret"."""

    def test_each_class_is_identified(self):
        cases = (
            ("-----BEGIN RSA PRIVATE KEY-----", "PEM private key"),
            ("-----BEGIN PRIVATE KEY-----", "PEM private key"),
            ("aws_access_key_id=AKIAIOSFODNN7EXAMPLE", "AWS access-key ID"),
            ("AQAAAD" + "A" * 20, "Senzing license payload"),
        )
        for text, expected in cases:
            with self.subTest(text=text[:30]):
                self.assertEqual(expected, PATTERNS.find_secret(text))

    def test_clean_text_matches_nothing(self):
        self.assertIsNone(PATTERNS.find_secret("just some ordinary bootcamp prose"))

    def test_prose_mentioning_the_license_prefix_is_not_a_secret(self):
        """⛔ The long base64 tail is load-bearing, and this is what it buys.

        Without it the pattern fires on documentation *about* licenses and on `.lic` file paths --
        so the gate would block the plugin's own guidance and the packager would exclude it.
        """
        for benign in (
            "the documented AQAAAD prefix marks a license blob",
            "place it at licenses/g2.lic",
            "AQAAAD",
        ):
            with self.subTest(text=benign):
                self.assertIsNone(PATTERNS.find_secret(benign))

    def test_the_matched_secret_is_never_echoed_back(self):
        """The manifest may be handed to someone else; echoing the match defeats the exclusion."""
        secret = "AQAAAD" + "S3CR3T" * 6
        result = PATTERNS.find_secret(secret)
        self.assertIsNotNone(result)
        self.assertNotIn("S3CR3T", result)


if __name__ == "__main__":
    unittest.main()
