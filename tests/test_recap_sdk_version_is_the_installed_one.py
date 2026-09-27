"""The recap's ``Senzing SDK`` line reports the version the installed SDK reported about itself.

Graduation Step 1a writes a Run environment block into ``docs/bootcamp_recap.md``. Its
``**Senzing SDK:**`` line used to say the version was "obtained from the Senzing MCP tools".
The MCP server is remote: it can report current or available versions, never the one
installed on the Bootcamper's machine. A guide following that instruction either reports
the server's current version as the installed one, or records "Unknown" beside a working
install. The walk of 2026-09-25 hit it (#168).

The fix has two halves, and this test asserts both:

1. SDK setup's Step 4, where ``SzProduct.get_version()`` first answers, writes the
   ``VERSION`` it returned into ``config/bootcamp_progress.json`` as ``sdk_version``, with
   ``sdk_version_measured_at`` naming where it came from. That follows the
   ``license_record_limit`` / ``license_record_limit_measured_at`` pattern of Step 5a.
2. Graduation Step 1a reads ``sdk_version`` from that file, falls back to "Unknown" when it
   is absent, does not re-run the version call, and no longer names the MCP tools as the
   source.

An installed version is an environment reading, not a Senzing fact, so INV-080 itself is
unchanged. The response shape (``VERSION`` a top-level string beside ``BUILD_VERSION``) is
``get_sdk_reference(topic='response_schemas', filter='getVersion')``, server 1.37.13,
2026-09-26.

⚠️ This establishes that the instructions SHIP at both sites. Whether a live walk writes
the key at Step 4 is a claim about a turn, and ``dry-run`` phase 3's.

Stdlib only, and nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"
SDK_SETUP = SKILLS / "module-02-sdk-setup" / "SKILL.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

FIELD = "sdk_version"
MARKER = "sdk_version_measured_at"
PROGRESS = "config/bootcamp_progress.json"

#: A sentence that instructs a WRITE of the field, as opposed to merely mentioning it.
WRITES_FIELD = re.compile(
    r"(?:write|writes|writing|written|persist|persists|persisted)\b(?:(?!\.\s).){0,200}"
    r"`" + FIELD + r"`",
    re.IGNORECASE,
)


def step_section(text, number):
    """The body of ``## Step <number>:`` up to the next ``## `` heading."""
    match = re.search(
        r"^## Step " + re.escape(str(number)) + r":.*?$(.*?)(?=^## )",
        text,
        flags=re.M | re.S,
    )
    return match.group(1) if match else None


def paragraphs(text):
    """Blank-line-delimited blocks, each joined onto one line so a wrapped sentence matches."""
    return [" ".join(p.split("\n")) for p in text.split("\n\n") if p.strip()]


def recap_sdk_bullet(text):
    """The Step 1a bullet that defines the recap's ``**Senzing SDK:**`` line, wrap included."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("- `**Senzing SDK:**`"):
            out = [line]
            for follow in lines[i + 1:]:
                if not follow.strip() or follow.startswith("- "):
                    break
                out.append(follow)
            return " ".join(part.strip() for part in out)
    return None


class SdkSetupStep4RecordsTheInstalledVersion(unittest.TestCase):
    def setUp(self):
        self.step4 = step_section(SDK_SETUP.read_text(encoding="utf-8"), 4)
        self.assertIsNotNone(self.step4, "SDK setup has no `## Step 4:` section to check")

    def _writing_paragraph(self):
        """The Step 4 paragraph that instructs the write, the checkpoint line excluded.

        The checkpoint line also names `sdk_version`, so letting it satisfy this lookup
        would pass with the instruction itself deleted: it says WHEN to write, not WHAT.
        """
        return next(
            (p for p in paragraphs(self.step4)
             if WRITES_FIELD.search(p) and not p.startswith("**Checkpoint:**")),
            None,
        )

    def test_step_4_writes_sdk_version_to_the_progress_file(self):
        paragraph = self._writing_paragraph()
        self.assertIsNotNone(
            paragraph,
            "SDK setup Step 4 must instruct a write of `sdk_version`. It is the first step where "
            "the installed SDK reports its own version, and graduation's recap reads the field; "
            "with no write, the recap can only say 'Unknown'.",
        )
        self.assertIn(
            PROGRESS, paragraph,
            "Step 4's `sdk_version` write must name `config/bootcamp_progress.json`, the file "
            "graduation Step 1a reads it from.",
        )

    def test_step_4_names_the_product_version_call_as_the_source(self):
        paragraph = self._writing_paragraph() or ""
        self.assertIn(
            "SzProduct.get_version()", paragraph,
            "Step 4's `sdk_version` write must name `SzProduct.get_version()` as its source: the "
            "value is the installed SDK's own report, not a package-manager or MCP figure.",
        )
        self.assertIn(
            "`VERSION`", paragraph,
            "Step 4 must say which field of the version document is recorded (`VERSION`), or a "
            "guide may store the build number or the whole JSON document.",
        )

    def test_step_4_records_where_the_reading_came_from(self):
        paragraph = self._writing_paragraph() or ""
        self.assertIn(
            "`%s:" % MARKER, paragraph,
            "Step 4 must write `sdk_version_measured_at` beside `sdk_version`, following the "
            "`license_record_limit_measured_at` pattern, so a reader can tell a measured value "
            "from one written some other way.",
        )

    def test_step_4_checkpoint_names_the_new_field(self):
        checkpoint = next(
            (p for p in paragraphs(self.step4) if p.startswith("**Checkpoint:**")), None
        )
        self.assertIsNotNone(checkpoint, "SDK setup Step 4 lost its checkpoint line")
        self.assertIn(
            "`%s`" % FIELD, checkpoint,
            "Step 4's checkpoint line must name `sdk_version`, so the checkpoint write carries "
            "the reading rather than only the step number.",
        )


class GraduationRecapReadsTheRecordedVersion(unittest.TestCase):
    def setUp(self):
        self.bullet = recap_sdk_bullet(GRADUATION.read_text(encoding="utf-8"))
        self.assertIsNotNone(
            self.bullet,
            "graduation Step 1a no longer defines a `**Senzing SDK:**` line; the renderer groups "
            "the Run environment block by that key name",
        )

    def test_the_line_reads_sdk_version_from_the_progress_file(self):
        self.assertIn(
            "`%s`" % FIELD, self.bullet,
            "graduation Step 1a's `**Senzing SDK:**` line must read the `sdk_version` SDK setup "
            "recorded; that is the only source that knows the installed version.",
        )
        self.assertIn(
            PROGRESS, self.bullet,
            "graduation Step 1a must cite `config/bootcamp_progress.json` as where `sdk_version` "
            "is read from.",
        )

    def test_the_line_falls_back_to_unknown_without_re_running_the_call(self):
        self.assertIn(
            '"Unknown"', self.bullet,
            "with `sdk_version` absent, graduation Step 1a must record \"Unknown\" and continue.",
        )
        self.assertRegex(
            self.bullet, r"(?i)do not re-?run",
            "graduation Step 1a must say a missing `sdk_version` is not a reason to re-run the "
            "version call at graduation.",
        )

    def test_the_line_no_longer_names_the_mcp_tools_as_its_source(self):
        self.assertNotRegex(
            self.bullet, r"(?i)(obtained|taken|read|sourced)\s+from\s+the\s+Senzing\s+MCP",
            "graduation Step 1a's `**Senzing SDK:**` line must not source the installed version "
            "from the Senzing MCP tools. The server is remote and cannot know what is installed "
            "on the Bootcamper's machine (#168).",
        )


if __name__ == "__main__":
    unittest.main()
