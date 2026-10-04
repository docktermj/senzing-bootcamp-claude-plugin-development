"""The Senzing license env var is SENZING_LICENSE_FILE; SENZING_LICENSE_PATH is a confabulation.

Only ONE MCP route returns the correct name: the `compatibility_notes` of
`sdk_guide(topic='load', language=..., record_count=<above the default limit>)`, which tell a
licensed user to "place the license file at the path specified by SENZING_LICENSE_FILE or in the
etc/ directory". Verified on server 1.32.9, 2026-08-13 at (python, 1000) and (java, 600) --
language-independent, and present only when the count exceeds the limit.

`SENZING_LICENSE_PATH` is returned by nothing and shipped in graduation's `.env.example` for a
time. That is the real defect this file guards: a fabricated variable in a deliverable the
bootcamper carries into production, where setting it licenses nothing and the failure surfaces much
later as `SENZ9000|LIMIT` with nothing pointing back at the unread variable.

⚠️ **This test previously asserted the opposite and was wrong.** Its first version banned the whole
`SENZING_LICENSE_` prefix on the premise that Senzing reads no license environment variable at all.
That premise came from asking the wrong tools -- `sdk_guide(topic='configure')` returns only
`LD_LIBRARY_PATH`/`PYTHONPATH`, `sdk_guide(topic='install')` shows only the `PIPELINE` keys, and
`search_docs` returns no variable name -- and concluding absence from their silence. That is exactly
the **INV-194** failure mode: an empty or absent field in one tool's response is NOT evidence the
server lacks the fact, and the tool that owns the fact must be asked before recording a negative.
The prefix ban was therefore banning the correct name, and the module-02 note it "corrected" had
been right all along.

The lesson is why the ban is now a single exact spelling rather than a family: a prefix ban is only
sound when every member really is wrong, and establishing *that* requires the same
ask-the-owning-tool discipline the original version skipped.

Enforces **INV-208**. Complements INV-080 (Senzing facts route through the MCP server) and INV-194
(one tool's silence is not absence) -- and stands as the worked example of INV-194 costing a shipped
invariant, caught the same day by a phase-3 dry-run walk that happened to call the owning route for
an unrelated reason.

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
# The correct spelling, per sdk_guide(topic='load', record_count > default limit).
GOOD_SPELLING = "SENZING_LICENSE_FILE"
# The PIPELINE keys, the other supported route.
PIPELINE_KEYS = ("LICENSEFILE", "LICENSESTRINGBASE64")

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
            f"correct spelling is {GOOD_SPELLING}, from sdk_guide(topic='load', record_count above "
            "the default limit):\n  " + "\n  ".join(offenders),
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


class TheCorrectSpellingAndItsRouteAreRecorded(unittest.TestCase):
    def test_graduation_env_example_uses_the_correct_spelling(self):
        text = GRADUATION.read_text(encoding="utf-8")
        block = env_example_key_list(text)
        self.assertIsNotNone(
            block,
            "could not locate graduation's `.env.example` bullet -- retarget this test rather than "
            "letting it pass vacuously.",
        )
        self.assertIn(
            GOOD_SPELLING,
            block,
            f"graduation's .env.example KEY LIST must name {GOOD_SPELLING} -- the spelling the MCP "
            "server actually returns. Mentioning it only in the surrounding prose is not enough: "
            f"the generated file is what the bootcamper gets.\nBullet was:\n{block}",
        )
        self.assertNotRegex(
            block,
            r"no license-path environment variable",
            "graduation must not assert that no license environment variable exists: "
            f"sdk_guide(topic='load', record_count>limit) returns {GOOD_SPELLING} (INV-194).",
        )

    def test_module_02_names_the_single_route_that_returns_it(self):
        """The name is only reachable via one topic, so the note must say which."""
        text = MODULE_02.read_text(encoding="utf-8")
        self.assertIn(GOOD_SPELLING, text, f"module-02 Step 5 must name {GOOD_SPELLING}.")
        self.assertNotRegex(
            text,
            r"There is no license-path environment variable",
            "module-02 must not assert the variable does not exist -- the earlier version of this "
            "guard enshrined that false premise (INV-194).",
        )
        self.assertRegex(
            text,
            r"record_count",
            "module-02 must name the route that returns the variable: sdk_guide(topic='load', "
            "language=..., record_count=<above the default limit>). Without the record_count "
            "condition the note sends the reader to a call that omits the name.",
        )
        self.assertTrue(
            any(key in text for key in PIPELINE_KEYS),
            "module-02 must still name the PIPELINE route as the other supported option.",
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
            "module-02's LICENSE NOTE must keep the warning that the topics which omit "
            f"{GOOD_SPELLING} (configure, install, search_docs) are not evidence it does not "
            "exist. That inference produced a false invariant and a guard that banned the correct "
            f"name.\nNote was:\n{note[:600]}",
        )
        self.assertRegex(
            note,
            r"INV-194",
            "the note must cite INV-194 by ID, so the rule it violated is traceable from the place "
            "it was violated.",
        )


if __name__ == "__main__":
    unittest.main()
