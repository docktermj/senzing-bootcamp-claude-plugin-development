"""The certificate must print the name the Bootcamper was asked for.

Graduation's pre-check judges the auto-detected name, and when it is a handle rather
than a display name it asks the pinned INV-113 question and persists the answer as
`name` in `config/bootcamp_preferences.yaml`. But `generate_recap_pdf.py` took the
certificate name from the recap's `**Bootcamper:**` preamble line — written by Bootcamp
preparation at the *start* of the run, from the pre-detection value.

So the two never met. A run that correctly rejected `docktermj`, asked, and recorded the
answer still printed `docktermj` on the signed certificate, at exit 0, with 99% content
retention and no warning. Only an artifact probe (`pdftotext | grep`) caught it — an
INV-065 violation reached through a documented, correctly-followed path.

Retention could not catch it either: the wrong name *does* render, so nothing is
missing. INV-110 measures loss, not correctness.

These tests pin the precedence (preferences first, recap second, placeholder last), the
tolerant read, and the divergence note.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "generate_recap_pdf.py")
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")

RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** {header_name}
**Started:** 2026-07-28

## Graduation

### Information Shared

The recap was reconciled and the certificate rendered from the recorded name, which is
the value the pre-check either accepted or replaced by asking.

### Questions & Responses

- **Q:** What name would you like printed on your Certificate of Completion?
- **A:** the recorded answer

### Actions Taken

- Asked the certificate-name question and persisted the answer.

### End-of-Module Summary

**What you accomplished:** Completed the bootcamp and produced the keepsake.

**Files produced:** `docs/bootcamp_recap.pdf`

**Why it matters:** The certificate carries the name the bootcamper chose.
"""


def load_generator():
    spec = importlib.util.spec_from_file_location("recap_gen_name_source", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_name_source"] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def project(header_name="docktermj", prefs=None):
    """A project dir with a recap and (optionally) a preferences file."""
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "docs"))
    os.makedirs(os.path.join(root, "config"))
    with open(os.path.join(root, "docs", "bootcamp_recap.md"), "w", encoding="utf-8") as fh:
        fh.write(RECAP.format(header_name=header_name))
    if prefs is not None:
        with open(os.path.join(root, "config", "bootcamp_preferences.yaml"), "w",
                  encoding="utf-8") as fh:
            fh.write(prefs)
    return root


def render(root, args=()):
    proc = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True, cwd=root,
    )
    return proc.returncode, proc.stdout, proc.stderr, os.path.join(
        root, "docs", "bootcamp_recap.pdf"
    )


def certificate_text(pdf_path):
    """Text of every page that looks like the certificate, or None without poppler."""
    if subprocess.run(["which", "pdftotext"], capture_output=True).returncode != 0:
        return None
    out = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True).stdout
    pages = [p for p in out.split("\f") if "ertificate" in p or "CERTIFICATE" in p]
    return "\n".join(pages)


class PreferencesOutrankTheRecapHeader(unittest.TestCase):
    """The answer to the INV-113 question wins over what was detected before it."""

    def setUp(self):
        GEN.set_certificate_name_override("")

    def test_resolver_prefers_the_preferences_name(self):
        recap = GEN.parse_recap(RECAP.format(header_name="docktermj"))
        GEN.set_certificate_name_override("Dana Reyes")
        self.assertEqual("Dana Reyes", GEN.certificate_name(recap))

    def test_resolver_falls_back_to_the_recap_header(self):
        recap = GEN.parse_recap(RECAP.format(header_name="Ada Lovelace"))
        self.assertEqual("Ada Lovelace", GEN.certificate_name(recap))

    def test_cert_fields_prints_the_preferences_name(self):
        recap = GEN.parse_recap(RECAP.format(header_name="docktermj"))
        GEN.set_certificate_name_override("Dana Reyes")
        name, _date, _labels = GEN._cert_fields(recap)
        self.assertEqual("Dana Reyes", name)

    def test_a_preferences_name_means_the_name_is_not_missing(self):
        """Otherwise the generator warns about a name it is about to print."""
        recap = GEN.parse_recap(RECAP.format(header_name=""))
        GEN.set_certificate_name_override("Dana Reyes")
        self.assertFalse(GEN.recap_missing_certificate_name(recap))

    @unittest.skipUnless(
        subprocess.run(["which", "pdftotext"], capture_output=True).returncode == 0,
        "pdftotext unavailable; cannot probe the rendered certificate",
    )
    @requires_fpdf2
    def test_rendered_certificate_prints_the_preferences_name(self):
        """The probe that originally caught the defect (INV-129)."""
        root = project(header_name="docktermj", prefs="name: Dana Reyes\nlanguage: python\n")
        code, _out, err, pdf = render(root)
        self.assertEqual(0, code, err)
        text = certificate_text(pdf)
        self.assertIn("Dana Reyes", text)
        self.assertNotIn("docktermj", text)


class TheReadIsTolerant(unittest.TestCase):
    """A preferences problem must never break the render (INV-048)."""

    def setUp(self):
        GEN.set_certificate_name_override("")

    def test_missing_file_yields_no_override(self):
        self.assertEqual("", GEN.read_preferences_name("/nonexistent/prefs.yaml"))

    def test_absent_key_yields_no_override(self):
        root = project(prefs="language: python\npath: Core\n")
        self.assertEqual(
            "", GEN.read_preferences_name(
                os.path.join(root, "config", "bootcamp_preferences.yaml"))
        )

    def test_nested_name_key_is_ignored(self):
        """Only a top-level `name:` is the certificate name."""
        root = project(prefs="database:\n  name: G2C\nlanguage: python\n")
        self.assertEqual(
            "", GEN.read_preferences_name(
                os.path.join(root, "config", "bootcamp_preferences.yaml"))
        )

    def test_quotes_and_inline_comments_are_stripped(self):
        root = project(prefs='name: "Dana Reyes"  # chosen at graduation\n')
        self.assertEqual(
            "Dana Reyes", GEN.read_preferences_name(
                os.path.join(root, "config", "bootcamp_preferences.yaml"))
        )

    def test_commented_out_name_is_ignored(self):
        root = project(prefs="# name: Someone Else\nlanguage: python\n")
        self.assertEqual(
            "", GEN.read_preferences_name(
                os.path.join(root, "config", "bootcamp_preferences.yaml"))
        )

    def test_render_still_succeeds_with_no_preferences_file(self):
        root = project(header_name="Ada Lovelace", prefs=None)
        code, stdout, err, _pdf = render(root)
        self.assertEqual(0, code, err)
        self.assertIn("PDF generated:", stdout)

    def test_no_third_party_yaml_parser_is_required(self):
        """INV-052: python3 only — stop-nudge.py's line-scan precedent."""
        with open(SCRIPT, encoding="utf-8") as fh:
            self.assertNotIn("import yaml", fh.read())


class TheDivergenceIsReported(unittest.TestCase):
    """INV-111: choosing between two sources must not be silent."""

    def test_differing_names_produce_a_note_naming_both(self):
        root = project(header_name="docktermj", prefs="name: Dana Reyes\n")
        _code, _out, err, _pdf = render(root)
        self.assertIn("Dana Reyes", err)
        self.assertIn("docktermj", err)
        self.assertRegex(err, r"(?i)differs from")

    def test_matching_names_produce_no_note(self):
        root = project(header_name="Dana Reyes", prefs="name: Dana Reyes\n")
        _code, _out, err, _pdf = render(root)
        self.assertNotIn("differs from", err)

    def test_the_note_says_which_value_was_printed(self):
        root = project(header_name="docktermj", prefs="name: Dana Reyes\n")
        _code, _out, err, _pdf = render(root)
        self.assertRegex(err, r"(?i)printing the preferences value")


class GraduationPersistsToBothPlaces(unittest.TestCase):
    """Preferences alone leaves the recap showing the rejected handle."""

    def setUp(self):
        with open(GRADUATION, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_it_requires_updating_the_recap_line_too(self):
        self.assertRegex(self.text, r"(?i)\*\*Bootcamper:\*\*\W{0,3}preamble line")

    def test_it_says_both_not_either(self):
        self.assertRegex(self.text, r"(?i)\*\*Both, not either\.\*\*|both, not either")

    def test_it_states_the_generator_prefers_preferences(self):
        self.assertRegex(self.text, r"(?i)reads this \*\*first\*\*|outranks anything detected")

    def test_amending_the_preamble_is_allowed(self):
        """A meta line is not a completed module section (INV-085)."""
        self.assertRegex(self.text, r"(?i)append-only rule \(INV-085\) does not forbid it")


if __name__ == "__main__":
    unittest.main()
