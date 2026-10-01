"""Module 2's language-binding sites name every language the server supports.

Module 2 Step 3 Phase 3 ("Install language bindings") gave steps for Python and sent Java, C#
and TypeScript to "that ecosystem's package manager as normal". It said nothing about Rust,
one of the five languages `sdk_guide` serves (Python, Java, C#, Rust, TypeScript), and the two
existing-install lines that say which bindings are per-project named only Java, C# and
TypeScript. INV-002 says the plugin is language-agnostic, so a Rust bootcamper reached Phase 3
with no step to follow (#287).

What these tests pin, and what they deliberately do not:

* Phase 3, the existing-install path's "Still run Step 3's Phase 3" bullet and the Required
  stops' Phase 3 bullet each name all five languages. ⚠️ They pin **language names**, never
  the wording of a server claim: where each language's bindings come from is the server's fact
  (INV-080), read at run time, and a guard that pinned it would go stale the day the server
  changed it.
* Phase 3's Rust step routes through `sdk_guide(…, language='rust')` and its
  `compatibility_notes`, and carries no Cargo git-dependency line to copy: the server's line is
  quoted only as dated evidence, the way Python's paths are.

Negative controls take one language out of each site, and put a Cargo dependency line into
Phase 3, and require the checks to fail.

Companion to `tests/test_no_pip_install_senzing.py` (INV-222), whose
`test_the_other_languages_are_unchanged` pins the route rule itself.

Source issue: #287. Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE2 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-02-sdk-setup", "SKILL.md"
)

#: The five languages `sdk_guide` serves, each with a pattern that cannot match another one
#: (`\bJava\b` does not match "JavaScript").
LANGUAGES = {
    "Python": r"\bPython\b",
    "Java": r"\bJava\b",
    "C#": r"C#",
    "Rust": r"\bRust\b",
    "TypeScript": r"\bTypeScript\b",
}

#: (site name, start marker, end marker). Each span runs from its start marker to the first
#: end marker after it.
SITES = (
    ("Step 3 Phase 3",
     "**Phase 3: Install language bindings",
     "**TypeScript/Node.js warning:**"),
    ("existing-install path, 'Still run Step 3's Phase 3'",
     "- **Still run Step 3's Phase 3**",
     "- **Still do Step 3's environment-script work**"),
    ("Required stops, Step 3's Phase 3",
     "> - **Step 3's Phase 3** (install language bindings)",
     "> - **Step 4**"),
)

#: A Cargo dependency on the Rust SDK, in any spacing: the line the server returns, which
#: Phase 3 must read at run time rather than ship.
CARGO_DEPENDENCY = re.compile(r"sz-rust-sdk\s*=\s*\{")


def read():
    with open(MODULE2, encoding="utf-8") as handle:
        return handle.read()


def flat(text):
    return re.sub(r"\s+", " ", text)


def span(text, start_marker, end_marker):
    start = text.index(start_marker)
    return text[start : text.index(end_marker, start + len(start_marker))]


def missing_languages(text):
    """[(site, language)] for every site that does not name a language."""
    missing = []
    for site, start, end in SITES:
        body = span(text, start, end)
        for language, pattern in LANGUAGES.items():
            if not re.search(pattern, body):
                missing.append((site, language))
    return missing


def rust_step_problems(text):
    """What is wrong with Phase 3's Rust step, as a list of reasons (empty when it is right)."""
    phase3 = span(text, SITES[0][1], SITES[0][2])
    problems = []
    bullet = re.search(r"(?ms)^\s*- \*\*Rust:\*\*(.*?)(?=^\s*- \*\*|\Z)", phase3)
    if not bullet:
        return ["Phase 3 has no Rust step"]
    rust = flat(bullet.group(1))
    if "sdk_guide(topic='install', platform='<platform>', language='rust')" not in rust:
        problems.append("the Rust step does not call sdk_guide with language='rust'")
    if "compatibility_notes" not in rust:
        problems.append("the Rust step does not send the reader to compatibility_notes")
    if not re.search(r"server \d+\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)", rust):
        problems.append("the Rust step's quote carries no server version and date")
    if CARGO_DEPENDENCY.search(phase3):
        problems.append("Phase 3 ships a Cargo dependency line to copy (INV-080)")
    return problems


class EveryBindingSiteNamesEveryLanguage(unittest.TestCase):
    def setUp(self):
        self.text = read()

    def test_every_site_exists(self):
        for site, start, end in SITES:
            with self.subTest(site=site):
                self.assertIn(start, self.text, "the site's start marker is gone")
                self.assertTrue(span(self.text, start, end).strip())

    def test_every_site_names_all_five_languages(self):
        self.assertEqual(
            [], missing_languages(self.text),
            "a Module 2 language-binding site stops naming a language the server supports "
            "(INV-002). Phase 3 and both existing-install lines must name Python, Java, C#, "
            "Rust and TypeScript (#287).",
        )

    def test_the_per_project_lines_name_rust(self):
        """The two existing-install lines are the ones #287 found without Rust."""
        flat_text = flat(re.sub(r"(?m)^\s*>\s?", "", self.text))   # unquote the stops block
        self.assertIn("The Java, C#, Rust and TypeScript bindings are per-project", flat_text)
        self.assertIn("the Java, C#, Rust and TypeScript bindings belong to the project",
                      flat_text)


class PhaseThreeHasARustStep(unittest.TestCase):
    def test_the_rust_step_reads_its_route_at_run_time(self):
        self.assertEqual([], rust_step_problems(read()))


class NegativeControls(unittest.TestCase):
    """Each check fails on the defect it exists for."""

    def setUp(self):
        self.text = read()

    def test_removing_a_language_from_any_site_is_caught(self):
        for site, start, end in SITES:
            for language, pattern in LANGUAGES.items():
                with self.subTest(site=site, language=language):
                    at = self.text.index(start)
                    stop = self.text.index(end, at + len(start))
                    body = re.sub(pattern, "LANG", self.text[at:stop])
                    broken = self.text[:at] + body + self.text[stop:]
                    self.assertIn((site, language), missing_languages(broken))

    def test_the_pre_fix_lists_are_caught(self):
        broken = (self.text
                  .replace("Java, C#, Rust and TypeScript\n  bindings are per-project",
                           "Java, C# and TypeScript\n  bindings are per-project")
                  .replace("Java, C#, Rust and TypeScript bindings\n>   belong",
                           "Java, C# and TypeScript bindings\n>   belong"))
        self.assertNotEqual(broken, self.text, "the control did not change the file")
        missing = missing_languages(broken)
        self.assertIn(("existing-install path, 'Still run Step 3's Phase 3'", "Rust"), missing)
        self.assertIn(("Required stops, Step 3's Phase 3", "Rust"), missing)

    def test_a_copied_cargo_line_is_caught(self):
        at = self.text.index("   - **Rust:**")
        broken = (self.text[:at]
                  + '   sz-rust-sdk = { git = "<repository>" }\n'
                  + self.text[at:])
        self.assertIn("Phase 3 ships a Cargo dependency line to copy (INV-080)",
                      rust_step_problems(broken))

    def test_a_missing_rust_step_is_caught(self):
        broken = self.text.replace("   - **Rust:**", "   - **Removed:**")
        self.assertEqual(["Phase 3 has no Rust step"], rust_step_problems(broken))


if __name__ == "__main__":
    unittest.main()
