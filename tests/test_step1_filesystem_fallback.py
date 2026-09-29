"""Module 2 Step 1's filesystem fallback must be able to detect an install on every platform.

INV-001 makes Linux, macOS and Windows supported. Step 1 is the module's first action, marked
"MUST DO FIRST", and it opens "There is no reason to re-install it." Its filesystem fallback used
to name two Linux paths only — `/opt/senzing/er/lib/libSz.so` and `/opt/senzing/er/szBuildVersion.json`
— and required *both* to be present to conclude the SDK was installed. On macOS and Windows neither
can ever exist, so the fallback always reached "SDK is not installed yet. Let's set it up", and a
Bootcamper with a working install was routed into reinstalling it.

The trigger is likelier off Linux, which is what made it worth fixing rather than noting: the
fallback exists for a failed import check, and the two non-Linux platforms are where the module
documents that failure mode most (`DYLD_LIBRARY_PATH` must be exported before the JVM starts on
macOS; Windows needs a `CLASSPATH` export for Java).

Nothing caught it in either direction. No test pinned the sentinel list, while
`tests/test_sdk_update_offer.py` already asserted the *contradicting* fact — that on Windows
`szBuildVersion.json` is a sibling of `er`, not under `SENZING_DIR`. One side was guarded and the
other was not, so the two could drift apart and stay that way.

⚠️ **Asserts the platform is REACHABLE, not the exact path string.** The artifact names come from
`sdk_guide(topic='install', platform=…)` and are the server's to change; what must not regress is
that all three platforms are represented and that an unchecked platform yields "unknown" rather
than "not installed" (INV-163).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_02 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
             / "module-02-sdk-setup" / "SKILL.md")


def step_1_section():
    """Step 1 only — the fallback belongs to it, and Step 1b has its own platform table."""
    text = MODULE_02.read_text(encoding="utf-8")
    m = re.search(r"^## Step 1: Check for Existing Installation.*?(?=^## Step 1b:)",
                  text, re.M | re.S)
    assert m, "Step 1 heading not found in module-02-sdk-setup/SKILL.md"
    return m.group(0)


class TheFallbackCoversEveryPlatform(unittest.TestCase):
    def setUp(self):
        self.section = step_1_section()

    def test_each_inv001_platform_has_a_native_library_to_probe(self):
        """One artifact per supported platform. A missing row is a false 'not installed'."""
        for platform, artifact in (
            ("Linux", "libSz.so"),
            ("macOS", "libSz.dylib"),
            ("Windows", "Sz.dll"),
        ):
            with self.subTest(platform=platform):
                self.assertIn(
                    artifact, self.section,
                    "Step 1's filesystem fallback names no %s artifact, so on %s it can only "
                    "conclude the SDK is absent — the defect this guard exists for. INV-001 "
                    "makes all three platforms supported." % (platform, platform),
                )

    def test_the_macos_path_is_prefix_relative_not_hardcoded(self):
        """`sdk_guide`'s macos_arm anti-patterns name the hardcoded form as an error.

        ⚠️ Asserts the **artifact path itself** is prefix-relative, rather than banning the string
        `/opt/homebrew` from the line. The first version banned the string and failed on correct
        guidance: the row names the hardcoded form in order to forbid it, and a substring ban
        cannot tell a prohibition from a use. Same lesson as
        `tests/test_dated_negatives_are_marked.py` — assert what must be true, not what must be
        absent.
        """
        macos_paths = re.findall(r"`([^`]*libSz\.dylib)`", self.section)
        self.assertTrue(macos_paths, "no backticked macOS artifact path found")
        for path in macos_paths:
            with self.subTest(path=path):
                self.assertTrue(
                    path.startswith("$(brew --prefix)"),
                    "the macOS artifact path must be resolved through $(brew --prefix); got %r. "
                    "Homebrew's prefix differs between Apple Silicon and Intel and between "
                    "installs, and sdk_guide's own anti-patterns name the hardcoded form an "
                    "error." % path,
                )

    def test_windows_says_senzing_dir_is_already_the_er_subdirectory(self):
        """The commonest Windows path error is appending `er` to a var that already includes it."""
        self.assertRegex(self.section, r"(?i)SENZING_DIR[^\n]*\ber\b")

    def test_docker_is_stated_as_not_applicable(self):
        """There is no host artifact to probe in a container; silence here reads as an omission."""
        self.assertRegex(self.section, r"(?i)docker[^\n]*(not applicable|no host)")

    def test_an_unchecked_platform_yields_unknown_not_absent(self):
        """INV-163. Reporting 'not installed' for an unprobed platform is the original defect."""
        flat = " ".join(self.section.split())
        self.assertRegex(flat, r"(?i)(unknown|undetermined)")
        self.assertIn("INV-163", self.section,
                      "the say-what-you-could-not-verify rule governs here and must be cited")

    def test_the_step_cites_the_invariant_that_makes_three_platforms_mandatory(self):
        self.assertIn("INV-001", self.section,
                      "a platform-dispatched list must name the rule binding it, so the next "
                      "editor knows why every platform has a row (INV-183's principle)")


class TheVersionFileIsNotPresentedAsAnMcpFact(unittest.TestCase):
    """The build-metadata file's location is an environment observation, not a tool's answer.

    `search_docs` returns no document giving that file's path on any platform — the version fact
    the corpus serves is the SDK's own version call. So the paths may be named as observations and
    must not be presented as MCP-sourced, and the reader must be routed to the SDK when the file is
    not where expected.
    """

    def setUp(self):
        self.section = step_1_section()

    def test_the_file_paths_are_marked_as_observations(self):
        flat = " ".join(self.section.split())
        self.assertRegex(flat, r"(?i)environment observations?, not MCP-sourced")

    def test_the_primary_version_route_is_the_sdk_not_the_file(self):
        self.assertRegex(self.section, r"get_version\(\)")

    def test_the_version_call_points_to_step_4_for_its_fields(self):
        """Step 4 states the `get_version()` fields once; Step 1 points there (INV-300, #234).

        Step 1 listed four fields cited to an older `search_docs` read, one of which,
        `NATIVE_API_VERSION`, the live `response_schemas` route does not return. Negative-
        controlled by restoring that list.
        """
        flat = " ".join(self.section.split())
        m = re.search(r"`SzProduct\.get_version\(\)`[^.]*\.", flat)
        self.assertIsNotNone(m, "Step 1 no longer names `SzProduct.get_version()`")
        sentence = m.group(0)
        self.assertIn("Step 4", sentence,
                      "Step 1's version route must point to Step 4 for the response fields")
        self.assertNotRegex(sentence, r"`[A-Z][A-Z_]+`",
                            "Step 1 names a get_version() field of its own; Step 4 states "
                            "them, so a second list can only drift from it (INV-300)")
        self.assertNotIn("NATIVE_API_VERSION", MODULE_02.read_text(encoding="utf-8"),
                         "get_version() returns no NATIVE_API_VERSION "
                         "(get_sdk_reference(topic='response_schemas', filter='get_version'))")

    def test_windows_metadata_is_the_sibling_data_directory(self):
        """Agrees with tests/test_sdk_update_offer.py and with Step 1b's own correction."""
        flat = " ".join(self.section.split())
        self.assertRegex(flat, r"(?i)sibling[^.]{0,40}`?data`?")


if __name__ == "__main__":
    unittest.main()
