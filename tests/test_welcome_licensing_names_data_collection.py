"""The welcome's licensing bullet must name Data collection, never SDK setup.

`bootcamp-onboarding/onboarding-flow.md`'s welcome overview read: "Licensing: a built-in
evaluation license covers the bootcamp's demos; more capacity options exist and **SDK setup
walks through them**." That line dates from a28a3c0 (2026-07-21), one day before **INV-093**
moved the License Key prompt out of SDK setup:

    SDK setup (Module 2) MUST establish only the built-in evaluation license with no license
    prompt ... at the start of Data collection (Module 4) ... and only when that volume
    exceeds the active license's record limit.

So the bootcamper's first mention of licensing pointed at a module that, by design, asks
nothing about it. The prompt is also volume-gated (Module 4 Step 8a asks only when the
collected total exceeds the active limit, and in the common case asks nothing), so the bullet
now names Data collection AND makes the options conditional on the bootcamper's data needing
more capacity.

This guard locates the `- Licensing:` bullet (failing if it is missing rather than passing
vacuously), requires "Data collection", and forbids "SDK setup" and "Module 2". A negative
control runs the same check against the pre-fix line and proves it fails.

⚠️ **This checks the welcome's wording, not the conversation.** Whether the guide actually
says it, and whether Module 4 then asks, are conversational outcomes for `dry-run` phase 3.

Source: issue #389 (production-readiness audit 2026-10-02, finding C-F4).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ONBOARDING_FLOW = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
                   "bootcamp-onboarding" / "onboarding-flow.md")

#: The bullet: its `- Licensing:` line plus any indented continuation lines.
LICENSING_BULLET = re.compile(r"^- Licensing:.*(?:\n[ \t]+\S.*)*", re.M)

#: The line as it read before #389, kept so the negative control tests the real defect.
PRE_FIX_TEXT = (
    "- Licensing: a built-in evaluation license covers the bootcamp's demos; more capacity "
    "options\n  exist and SDK setup walks through them.\n")

REQUIRED = "Data collection"
FORBIDDEN = ("SDK setup", "Module 2")


def licensing_bullet(text):
    """The bullet with its whitespace collapsed, or None when the file has none."""
    match = LICENSING_BULLET.search(text)
    if match is None:
        return None
    return " ".join(match.group(0).split())


def problems(text):
    """Every way `text`'s licensing bullet breaks the rule; empty when it complies."""
    bullet = licensing_bullet(text)
    if bullet is None:
        return ["no `- Licensing:` bullet found"]
    found = []
    if REQUIRED not in bullet:
        found.append("does not name %r" % REQUIRED)
    for phrase in FORBIDDEN:
        if phrase in bullet:
            found.append("names %r" % phrase)
    return found


class TheWelcomeLicensingBullet(unittest.TestCase):

    def test_the_bullet_is_present(self):
        self.assertIsNotNone(
            licensing_bullet(ONBOARDING_FLOW.read_text(encoding="utf-8")),
            "onboarding-flow.md has no `- Licensing:` bullet. If it was renamed, point this "
            "guard at the new bullet; it must not pass by inspecting nothing")

    def test_the_bullet_names_data_collection_and_not_sdk_setup(self):
        found = problems(ONBOARDING_FLOW.read_text(encoding="utf-8"))
        self.assertEqual(
            [], found,
            "the welcome's licensing bullet %s. Per INV-093 the only License Key prompt is at "
            "Data collection (Module 4), volume-gated; SDK setup establishes the built-in "
            "evaluation license and asks nothing" % "; ".join(found))

    def test_the_options_are_conditional_on_the_data(self):
        """Step 8a asks nothing in the common case, so the bullet must not promise it."""
        bullet = licensing_bullet(ONBOARDING_FLOW.read_text(encoding="utf-8")) or ""
        self.assertIn(
            "If your own data needs more capacity", bullet,
            "the licensing bullet no longer makes the capacity options conditional on the "
            "bootcamper's data needing more; Module 4 Step 8a asks only then")


class NegativeControl(unittest.TestCase):

    def test_the_pre_fix_line_fails(self):
        found = problems(PRE_FIX_TEXT)
        self.assertIn("names 'SDK setup'", found)
        self.assertIn("does not name 'Data collection'", found)

    def test_a_missing_bullet_fails(self):
        self.assertEqual(["no `- Licensing:` bullet found"],
                         problems("- Goal: something else.\n"))

    def test_module_2_alone_fails(self):
        text = ("- Licensing: Data collection checks your record count; Module 2 walks\n"
                "  through the options.\n")
        self.assertEqual(["names 'Module 2'"], problems(text))


if __name__ == "__main__":
    unittest.main()
