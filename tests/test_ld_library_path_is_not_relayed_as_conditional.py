"""`LD_LIBRARY_PATH` is required on a stock linux_apt Python install, not conditional.

On a **default** apt install — `senzingsdk-runtime` at `/opt/senzing`, no custom location —
`import senzing_core` failed with `libSz.so: cannot open shared object file` until
`LD_LIBRARY_PATH=/opt/senzing/er/lib` was exported. It was not conditional there; it was
required.

⚠️ **The failure lands a module later.** The environment script is written in SDK setup; the
missing variable surfaces at the first real import, where it reads as a broken SDK install
rather than an incomplete environment.

⛔ **One `sdk_guide` payload carries both readings**, re-verified on server 1.32.9,
2026-08-17:

* `install.platform.env_vars.LD_LIBRARY_PATH` — *"(only needed if native lib not found
  automatically)"*, and `gotchas[0]` repeats that as a general note;
* the **Python SDK** entry in the same `gotchas[]` array — *"set PYTHONPATH=… **and**
  LD_LIBRARY_PATH=/opt/senzing/er/lib:$LD_LIBRARY_PATH"*, unconditional.

`topic='configure'` returns the identical hedged string, so switching topics does not
resolve it. That contradiction is reported upstream (2026-08-16) and is **not** re-filed;
what this guard protects is the plugin's own half — it re-stated the hedge in its own voice
and routed the env-script author to the hedged field.

⚠️ **The plugin's fix stands whatever the server does.** A corrected server response would
fix it for everyone reading the tool directly, but the plugin does not merely pass the
response through, and the upstream change has no delivery date. A plugin spec and an
upstream report are not alternatives.

Source spec: `specs/ld-library-path-relayed-as-conditional-on-a-stock-linux-apt-install.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
         "module-02-sdk-setup" / "SKILL.md")


def text():
    return SKILL.read_text(encoding="utf-8")


def flat():
    return " ".join(text().split())


#: The server's hedge. Matched by ``match_lines`` across line wraps (#424): the hedge is
#: prose, and "only needed\nif the native lib" was invisible to a line-at-a-time read.
HEDGE = re.compile(r"only needed if (?:the )?native lib")


def unattributed_hedges(body):
    """["<line>: <text>"] for each hedge whose passage names no source and is not quoted."""
    lines = body.split("\n")
    offenders = []
    for lineno in match_lines(body, HEDGE):
        index, line = lineno - 1, lines[lineno - 1]
        window = " ".join(lines[max(0, index - 3):index + 3])
        attributed = (line.lstrip().startswith(">") or "env_vars" in window
                      or "gotchas" in window)
        if not attributed:
            offenders.append(f"{lineno}: {line.strip()}")
    return offenders


class TheConditionalGlossIsGone(unittest.TestCase):
    """⛔ The plugin's own words, which reproduced the reading that breaks the install."""

    def test_the_plugin_no_longer_glosses_it_as_conditional(self):
        self.assertNotIn(
            "`LD_LIBRARY_PATH` for when the native library is not found automatically",
            flat(),
            "the plugin still states the hedge in its own voice")

    def test_no_unquoted_sentence_calls_it_only_needed(self):
        """The hedge may appear ONLY as an attributed quotation of the server.

        ⚠️ Judged over a WINDOW, not a line: the attribution ("env_vars", "gotchas") is
        prose and wraps, so a line-level check reported a correctly-attributed relay whose
        attribution sat on the line above.
        """
        offenders = unattributed_hedges(text())
        self.assertEqual([], offenders,
                         "the hedge appears unattributed, as though it were the plugin's "
                         "own claim:\n  " + "\n  ".join(offenders))

    def test_a_wrapped_unattributed_hedge_is_reported_at_its_first_line(self):
        """Negative control (#424): "only needed" ends line 2 and "if the native" begins line 3."""
        wrapped = ("Set the variables below.\nLD_LIBRARY_PATH is only needed\n"
                   "if the native library is not found automatically.\n")
        self.assertEqual(["2: LD_LIBRARY_PATH is only needed"], unattributed_hedges(wrapped))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(HEDGE.search(l) for l in wrapped.split("\n")))

    def test_an_attributed_wrapped_hedge_is_not_reported(self):
        """Must-not-flag (INV-282): the server's `gotchas` line, quoted with its source."""
        self.assertEqual([], unattributed_hedges(
            "The server's `gotchas` reads: LD_LIBRARY_PATH is only needed\n"
            "if the native library is not found automatically.\n"))

    def test_the_attribution_check_is_not_vacuous(self):
        """A bare hedge with nothing naming its source must be reported."""
        window = "LD_LIBRARY_PATH is only needed if native lib not found automatically."
        self.assertNotIn("env_vars", window)
        self.assertNotIn("gotchas", window)


class BothVariablesAreRequiredForPythonOnLinuxApt(unittest.TestCase):

    def setUp(self):
        self.text = flat()

    def test_it_states_both_are_required(self):
        self.assertIn("On `linux_apt` with Python, BOTH `PYTHONPATH` and "
                      "`LD_LIBRARY_PATH` are required", self.text)

    def test_it_quotes_the_governing_gotchas_line(self):
        self.assertIn("LD_LIBRARY_PATH=/opt/senzing/er/lib:$LD_LIBRARY_PATH", self.text)
        self.assertIn("the one that governs for `language='python'`", self.text)

    def test_it_records_that_the_same_response_says_otherwise(self):
        """⛔ Do not silently pick a side — the contradiction is the fact the reader needs."""
        self.assertIn("The **same response** hedges the same variable twice", self.text)
        self.assertIn("do not silently pick one", self.text)

    def test_it_records_that_configure_carries_the_same_hedge(self):
        self.assertIn("changing topic does not resolve it", self.text)

    def test_the_claim_carries_its_route_version_and_date(self):
        """INV-080 — quoted with provenance, not adopted as a plugin-owned fact."""
        self.assertIn("MCP server **1.32.9, 2026-08-17**", self.text)
        self.assertIn("sdk_guide(topic='install', platform='linux_apt', "
                      "language='python')", self.text)

    def test_it_says_not_to_re_file_upstream(self):
        self.assertIn("Reported upstream 2026-08-16", self.text)
        self.assertIn("do not re-file", self.text)


class TheSymptomIsFramedAsAnIncompleteEnvironment(unittest.TestCase):

    def setUp(self):
        self.text = flat()

    def test_the_observed_error_is_named(self):
        self.assertIn("libSz.so: cannot open shared object file", self.text)

    def test_it_is_framed_as_environment_not_a_broken_install(self):
        self.assertIn("reads as a **broken SDK install** rather than an incomplete "
                      "environment", self.text)

    def test_the_loader_behavior_is_marked_observation_only(self):
        """INV-149 — an engine/loader behavior no MCP route owns."""
        self.assertIn("the loader behavior itself is observation-only", self.text)


class TheEnvScriptRoutesToTheLanguageSpecificGotchas(unittest.TestCase):

    def setUp(self):
        self.text = flat()

    def test_the_template_names_gotchas_not_env_vars_alone(self):
        self.assertIn("READ gotchas[] FOR YOUR LANGUAGE, NOT env_vars ALONE", self.text)

    def test_the_env_script_snippet_still_names_no_programming_language(self):
        """⚠️ INV-001/INV-052 — the env script is about the SHELL, not the language.

        The first draft of this routing note said "linux_apt + Python" and named
        `PYTHONPATH`, which `test_env_script_shell_portability` correctly rejected: the
        snippet must route the author to their language's gotchas without picking one.
        """
        body = text()
        start = body.index("# Platform-specific exports")
        block = body[start:body.index("unset _sz_self", start)].lower()
        for language in ("python", "java", "csharp", "c#", "rust", "typescript", "node"):
            with self.subTest(language=language):
                self.assertNotIn(language, block)

    def test_it_passes_language_to_the_lookup(self):
        self.assertIn("sdk_guide(topic='install', platform=…, language=…)", self.text)

    def test_it_names_the_consequence_at_the_site_that_writes_the_script(self):
        # Strip the shell comment markers before flattening: the sentence wraps across
        # comment lines, so matching raw text would depend on where the `#` fell.
        body = text()
        start = body.index("# Platform-specific exports")
        block = body[start:body.index("unset _sz_self", start)]
        prose = " ".join(re.sub(r"(?m)^\s*#\s?", "", block).split())
        self.assertIn("one module after this script was written", prose,
                      "the env-script comment does not say when the failure surfaces")
        self.assertIn("libSz.so: cannot open shared object file", prose)


class TheOtherPlatformBranchesAreUndisturbed(unittest.TestCase):
    """⚠️ Scoped to Linux/Python — macOS and Windows guidance must be untouched."""

    def test_the_macos_variable_is_still_named(self):
        self.assertIn("DYLD_LIBRARY_PATH", flat())

    def test_the_windows_bat_guidance_survives(self):
        flat_text = flat()
        self.assertIn("the DYLD/LD variables do not apply at all and the env script is a "
                      "`.bat`", flat_text)
        self.assertIn("the classpath separator is `;`, not `:`", flat_text)

    def test_the_linux_note_is_reachable_from_the_non_jvm_path(self):
        """It sat in the JVM subsection, so a Python author never reached it."""
        self.assertIn("This is not a JVM-only concern", flat())


class ThePathsAreQuotedNotAdopted(unittest.TestCase):
    """INV-080 — every path figure carries the route that produced it."""

    def test_each_senzing_path_appears_with_provenance_nearby(self):
        # Line-scoped by design (#424): the anchor is a path, one token with no space in it,
        # and the window it opens spans lines.
        body = text()
        for number, line in enumerate(body.splitlines(), 1):
            if "/opt/senzing/er/lib" not in line:
                continue
            window = " ".join(body.splitlines()[max(0, number - 30):number + 10])
            with self.subTest(line=number):
                self.assertTrue(
                    "sdk_guide" in window,
                    f"line {number} states a Senzing path with no route in view")


if __name__ == "__main__":
    unittest.main()
