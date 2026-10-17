"""The license routes to the engine config's PIPELINE keys; SENZING_LICENSE_PATH is a confabulation.

⚠️ **Rescoped 2026-10-15 (#654): the premise this file used to pin has lapsed.** Until then it held
that the license environment variable is `SENZING_LICENSE_FILE` and that exactly ONE MCP route
returns it: the `compatibility_notes` of `sdk_guide(topic='load', language=...,
record_count=<above the default limit>)`, which told a licensed user to "place the license file at
the path specified by SENZING_LICENSE_FILE or in the etc/ directory" (server 1.32.9, 2026-08-13;
last confirmed 1.36.0, 2026-09-02). On server 1.39.0, 2026-10-15 that note instead says to add the
license "as LICENSESTRINGBASE64 (inline base64 string, preferred for containers and automation) or
LICENSEFILE (path to a .lic file) in the PIPELINE section of the engine config", and no route names
`SENZING_LICENSE_FILE` (`search_docs`, `find_examples`, `sdk_guide(topic='install'|'configure')`,
`explain_error_code('SENZ9000')`). So the plugin now:

- routes the license to the PIPELINE keys, `LICENSESTRINGBASE64` (preferred) then `LICENSEFILE`, in
  Module 2's license check order and in graduation's `.env.example`;
- names `SENZING_LICENSE_FILE` only inside Module 2's `MCP-NEGATIVE` marker, which records the
  lapse. That is a loss of SOURCING, not evidence the engine ignores the variable, so no shipped
  file may assert that no license environment variable exists either.

`SENZING_LICENSE_PATH` is returned by nothing and shipped in graduation's `.env.example` for a
time. That is the real defect this file guards: a fabricated variable in a deliverable the
bootcamper carries into production, where setting it licenses nothing and the failure surfaces much
later as `SENZ9000|LIMIT` with nothing pointing back at the unread variable.

⚠️ **This test asserted the opposite once before and was wrong.** Its first version banned the whole
`SENZING_LICENSE_` prefix on the premise that Senzing reads no license environment variable at all.
That premise came from asking the wrong tools -- `sdk_guide(topic='configure')` returns only
`LD_LIBRARY_PATH`/`PYTHONPATH`, `sdk_guide(topic='install')` shows only the `PIPELINE` keys, and
`search_docs` returns no variable name -- and concluding absence from their silence. That is exactly
the **INV-194** failure mode: an empty or absent field in one tool's response is NOT evidence the
server lacks the fact, and the tool that owns the fact must be asked before recording a negative.

The lesson is why the ban is a single exact spelling rather than a family: a prefix ban is only
sound when every member really is wrong, and establishing *that* requires the same
ask-the-owning-tool discipline the original version skipped.

Enforces **INV-208**, as amended by its registered 2026-10-15 note (#654). Complements INV-080
(Senzing facts route through the MCP server) and INV-194 (one tool's silence is not absence).

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
MODULE_02 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"

# The confabulated spelling. Word-boundary-anchored and case-sensitive (env vars are uppercase).
BAD_SPELLING = re.compile(r"\bSENZING_LICENSE_PATH\b")
# The variable sdk_guide(topic='load', record_count > default limit) named through server 1.36.0
# (2026-09-02) and no route names on 1.39.0 (2026-10-15). Word-boundary-anchored so that the
# PIPELINE key LICENSEFILE never matches it.
LAPSED_SPELLING = re.compile(r"\bSENZING_LICENSE_FILE\b")
# The PIPELINE keys the server now names, preferred first.
PIPELINE_KEYS = ("LICENSESTRINGBASE64", "LICENSEFILE")
# A negative marker in an HTML comment: the one place the lapsed name may be recorded. The
# token and its colon are split by `\s*` so the marker scanner does not read this line as one.
NEGATIVE_MARKER = re.compile(r"<!--\s*MCP-NEGATIVE\s*:.*?-->", re.S)
# A sentence asserting that no license environment variable exists. Not preceded by a quote mark,
# so the module-02 note may still quote the retracted claim it records.
NO_VARIABLE_CLAIM = re.compile(
    r'(?i)(?<!")\b(?:there is no|senzing reads no) license[\w -]{0,20}environment variable'
)

# Files permitted to quote the bad spelling, because their subject IS the bad spelling.
# Both must also state that it is wrong, which is asserted below.
ALLOWED_TO_NAME_BAD = {GRADUATION, MODULE_02}


def plugin_text_files():
    """Every Markdown and script file that ships in the plugin."""
    for path in sorted(PLUGIN.rglob("*")):
        if path.is_file() and path.suffix in {".md", ".py", ".sh", ".json", ".yaml", ".yml"}:
            yield path


class TheConfabulatedSpellingIsNeverUsedAsAVariable(unittest.TestCase):
    def test_no_file_uses_the_bad_spelling_except_to_warn_against_it(self):
        """SENZING_LICENSE_PATH appears only in the two notes whose subject is that it is wrong.

        Line-scoped by design (#424): the pattern is one identifier, which a line break cannot
        split.
        """
        offenders = []
        for path in plugin_text_files():
            if path in ALLOWED_TO_NAME_BAD:
                continue
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if BAD_SPELLING.search(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()[:110]}")
        self.assertEqual(
            [],
            offenders,
            "SENZING_LICENSE_PATH is returned by no MCP tool (server 1.32.9, 2026-08-13). The "
            "license goes in the engine config's PIPELINE keys, LICENSESTRINGBASE64 or LICENSEFILE, "
            "which sdk_guide(topic='load', record_count above the default limit) names:\n  "
            + "\n  ".join(offenders),
        )

    def test_each_file_that_names_the_bad_spelling_marks_it_as_wrong(self):
        """Quoting it is allowed only alongside a statement that it must not be used."""
        for path in sorted(ALLOWED_TO_NAME_BAD):
            text = path.read_text(encoding="utf-8")
            if not BAD_SPELLING.search(text):
                continue  # not quoting it at all is fine
            self.assertRegex(
                text,
                r"(?s)SENZING_LICENSE_PATH.{0,200}?(confabulation|never use|no MCP tool|not\b)",
                f"{path.relative_to(REPO_ROOT)} names SENZING_LICENSE_PATH without marking it "
                "wrong nearby. An unmarked mention is liftable by a guide skimming the file.",
            )


def env_example_key_list(text):
    """The `.env.example` bullet's own text: the bullet line plus its wrapped continuations.

    Anchored to the bullet rather than to a character window from the first occurrence of
    ".env.example". A window is too weak: `.env.example` is mentioned again further down, and a
    window wide enough to reach the bullet also swallows the surrounding ⛔ prose -- which itself
    mentions the variable, so removing the key from the LIST still left the assertion satisfied.
    That miss was found by negative control, not review.

    The bullet's wrapped continuations are joined here, so this is no line-at-a-time read
    (#424).
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^- \*\*`\.env\.example`", line):
            block = [line]
            for nxt in lines[i + 1 :]:
                # A wrapped continuation is indented and does not start a new bullet.
                if nxt.startswith("- ") or not nxt.strip():
                    break
                block.append(nxt)
            joined = "\n".join(block)
            # ⛔ Truncate at the explanatory prose. The bullet WRAPS into a ⛔ note that also names
            # the variable, so testing the whole bullet still passed when the key was deleted from
            # the list -- the second time this same "satisfied by adjacent text" shape defeated a
            # negative control in this file. Only the key list is the generated artifact's content.
            for boundary in ("⛔", "with safe example"):
                cut = joined.find(boundary)
                if cut != -1:
                    joined = joined[:cut]
            return joined
    return None


def module_02_license_note(text):
    """Step 5's license blockquote: from the check-order line to the EULA-contrast note.

    Anchored for the same reason as above -- "not evidence" and similar phrases occur elsewhere in
    this 1000+ line file, so a whole-file regex can pass on unrelated text.
    """
    start = text.find("**License check order:**")
    if start == -1:
        return None
    end = text.find('**"Senzing License Key" vs. the EULA:**', start)
    return text[start : end if end != -1 else start + 4000]


def outside_markers(text):
    """The text with every MCP-NEGATIVE HTML-comment marker removed."""
    return NEGATIVE_MARKER.sub("", text)


class TheLapsedNameIsNotPresentedAsServerSourced(unittest.TestCase):
    """#654: SENZING_LICENSE_FILE lost its only source, so prose may not cite one for it."""

    def test_the_lapsed_name_appears_only_inside_a_negative_marker(self):
        """Restoring "only ONE tool route returns it" puts the name back in prose and fails here.

        Whole-text read, not line by line: a marker spans one line, but the prose it guards wraps.
        """
        offenders = []
        for path in plugin_text_files():
            text = outside_markers(path.read_text(encoding="utf-8"))
            if LAPSED_SPELLING.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            [],
            offenders,
            "SENZING_LICENSE_FILE is named outside an MCP-NEGATIVE marker. No route names it on "
            "server 1.39.0, 2026-10-15 -- sdk_guide(topic='load', record_count above the limit) "
            "now names LICENSESTRINGBASE64 and LICENSEFILE -- so prose that offers it presents an "
            "unsourced name as a server fact (INV-080, INV-208 as amended):\n  "
            + "\n  ".join(offenders),
        )

    def test_module_02_marker_records_the_lapse(self):
        """The lapse is recorded in Module 2's marker, with both dates, and only there."""
        markers = [
            m.group(0)
            for m in NEGATIVE_MARKER.finditer(MODULE_02.read_text(encoding="utf-8"))
            if LAPSED_SPELLING.search(m.group(0))
        ]
        self.assertEqual(1, len(markers), "module-02 must carry exactly one marker naming the lapse")
        marker = markers[0]
        self.assertIn("1.36.0, 2026-09-02", marker, "the marker must say when the name was last served")
        self.assertRegex(marker, r"server 1\.39\.0, 2026-10-15 -->$", "the marker must be stamped 1.39.0")
        owner = marker.split("owner:", 1)[1]
        for key in PIPELINE_KEYS:
            self.assertIn(key, owner, f"the owner clause must name {key}, as the route returns it")
        self.assertIn("topic='load'", owner)


class ThePipelineRouteIsRecorded(unittest.TestCase):
    def test_graduation_env_example_routes_the_license_to_the_pipeline_keys(self):
        """The key list carries no license variable; the bullet names both PIPELINE keys."""
        text = GRADUATION.read_text(encoding="utf-8")
        block = env_example_key_list(text)
        self.assertIsNotNone(
            block,
            "could not locate graduation's `.env.example` bullet -- retarget this test rather than "
            "letting it pass vacuously.",
        )
        self.assertNotRegex(
            block,
            r"SENZING_LICENSE_\w+",
            "graduation's .env.example KEY LIST must not carry a license environment variable: the "
            "license goes in the PIPELINE section of SENZING_ENGINE_CONFIGURATION_JSON, and an "
            f"unread variable licenses nothing in production.\nKey list was:\n{block}",
        )
        self.assertIn("SENZING_ENGINE_CONFIGURATION_JSON", block)
        bullet = text[text.index("- **`.env.example`:**") :]
        bullet = bullet[: bullet.index("\n- ")]
        preferred, existing = (bullet.find(key) for key in PIPELINE_KEYS)
        self.assertNotEqual(-1, preferred, "graduation must name LICENSESTRINGBASE64")
        self.assertNotEqual(-1, existing, "graduation must name LICENSEFILE")
        self.assertIn("preferred", bullet)
        self.assertNotIn(
            "confirm it there",
            bullet,
            "graduation must not send the guide to confirm a variable against a route that no "
            "longer returns it.",
        )

    def test_module_02_check_order_names_the_pipeline_keys_preferred_first(self):
        text = MODULE_02.read_text(encoding="utf-8")
        note = module_02_license_note(text)
        self.assertIsNotNone(note, "could not locate module-02's license note -- retarget this test.")
        order = " ".join(note[: note.index("<!--")].split())
        self.assertLess(
            order.find("LICENSESTRINGBASE64"),
            order.find("LICENSEFILE"),
            f"the check order must name LICENSESTRINGBASE64 (preferred) then LICENSEFILE:\n{order}",
        )
        self.assertNotEqual(-1, order.find("LICENSESTRINGBASE64"))
        self.assertIn("PIPELINE", order)
        self.assertRegex(
            outside_markers(note),
            r"record_count",
            "module-02 must name the route that carries the license note: sdk_guide(topic='load', "
            "language=..., record_count=<above the default limit>). Without the record_count "
            "condition the note sends the reader to a call that omits it.",
        )

    def test_no_file_asserts_that_no_license_variable_exists(self):
        """INV-208's never-say-none rule survives the lapse: a lost source is not an absence."""
        offenders = []
        for path in plugin_text_files():
            text = " ".join(path.read_text(encoding="utf-8").split())
            for m in NO_VARIABLE_CLAIM.finditer(text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: ...{text[m.start():m.end() + 40]}")
        self.assertEqual(
            [],
            offenders,
            "a shipped file asserts that no license environment variable exists. The sourcing "
            "lapsed; nothing shows the engine ignores the variable (INV-194, INV-208):\n  "
            + "\n  ".join(offenders),
        )
        self.assertNotRegex(
            MODULE_02.read_text(encoding="utf-8"),
            r"There is no license-path environment variable",
            "module-02 must not assert the variable does not exist -- the earlier version of this "
            "guard enshrined that false premise (INV-194).",
        )


class TheOwningToolMustBeAskedBeforeRecordingAnAbsence(unittest.TestCase):
    """Pins the INV-194 lesson in the place that got it wrong, so it cannot regress quietly."""

    def test_module_02_records_why_the_absence_conclusion_was_wrong(self):
        text = MODULE_02.read_text(encoding="utf-8")
        note = module_02_license_note(text)
        self.assertIsNotNone(note, "could not locate module-02's license note -- retarget this test.")
        # Scoped to the note. "not evidence" also appears at two unrelated places in this file
        # (INV-129 exit codes, and an engine-init caution), so a whole-file regex passes on text
        # that has nothing to do with licensing -- caught by negative control.
        self.assertRegex(
            note,
            r"(?i)do not conclude|not evidence",
            "module-02's LICENSE NOTE must keep the warning that the routes which name no license "
            "variable (configure, install, search_docs) are not evidence that none exists. That "
            "inference once produced a false invariant and a guard that banned a correct name."
            f"\nNote was:\n{note[:600]}",
        )
        self.assertRegex(
            note,
            r"INV-194",
            "the note must cite INV-194 by ID, so the rule it violated is traceable from the place "
            "it was violated.",
        )


if __name__ == "__main__":
    unittest.main()
