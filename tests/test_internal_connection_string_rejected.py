"""`internal://` is never offered as the bootcamp's datastore CONNECTION.

The bootcamp is multi-process. `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`
builds its **own** `SzAbstractFactoryCore("bootcamp_viz", settings)` and calls
`create_engine()` in a process separate from the loader, reading the same `CONNECTION` out of
the project's engine-config file or `$SENZING_ENGINE_CONFIGURATION_JSON`. A per-process
in-memory datastore therefore leaves the viz server opening an empty one.

⛔ **The hazard is that the MCP server RECOMMENDS the thing that breaks this.** Server
**1.32.9, 2026-08-14**, `sdk_guide(topic='install', platform='macos_arm', language='java')`
returns, in one `engine_config_notes` entry:

    "For quick single-process dev/test on v4.3+, use internal:// as the connection string —
     zero setup, in-memory, no schema creation needed. Limitation: internal:// is confined to
     a single process via the SDK; it cannot be shared across processes, persisted, or used
     with external tools."

The recommendation reads before the disqualifying clause, and the plugin routes the assistant
to `sdk_guide` at runtime (INV-080), so the advice arrives unprompted. This guard is therefore
**not** enforcing a correction — `internal://` appeared 0 times under `plugins/` when INV-231
was registered. It pins correct behavior that nothing else was holding, against advice the
plugin itself tells the assistant to go and read.

Both halves matter and they fail differently:

* `test_no_file_offers_internal_connection_string` catches the regression — someone adopting
  the server's recommendation.
* `test_ground_rules_forbids_internal_connection_string` catches the prohibition being
  deleted, which would leave the first test passing by accident for as long as nobody acted
  on the advice.

The failure INV-231 prevents is silent and late: both processes exit 0, every load reports
success, and the blank render surfaces three modules later — which **INV-250** makes a
reported failure rather than a passing step. (Corrected 2026-08-15: this read "the outcome
INV-077 forbids". It does not — INV-077 governs which module produces the visualization
and when, and an empty graph satisfies it. See
`specs/inv077-supersession-dropped-the-visualization-verification-guarantee.md`.)

Enforces **INV-231**. Source spec: `specs/internal-connection-string-breaks-the-viz-server.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
GROUND_RULES = (
    PLUGINS
    / "senzing-bootcamp"
    / "skills"
    / "bootcamp-onboarding"
    / "ground-rules.md"
)

# The scheme as it would appear in a connection string. Matched case-insensitively so a
# stray `INTERNAL://` is caught too.
INTERNAL_SCHEME = re.compile(r"internal://", re.IGNORECASE)

# Vendored third-party assets are not ours to police.
SKIP_PARTS = {"vendor", "node_modules", "__pycache__"}


def _shipped_files():
    for path in sorted(PLUGINS.rglob("*")):
        if not path.is_file():
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        if path.suffix.lower() not in {".md", ".py", ".sh", ".json", ".yaml", ".yml"}:
            continue
        yield path


class InternalConnectionStringRejected(unittest.TestCase):
    def test_ground_rules_forbids_internal_connection_string(self):
        """ground-rules.md must carry the prohibition, and cite INV-231."""
        self.assertTrue(GROUND_RULES.is_file(), f"missing {GROUND_RULES}")
        text = GROUND_RULES.read_text(encoding="utf-8")

        self.assertIn(
            "INV-231",
            text,
            "ground-rules.md must cite INV-231 so the rule is reachable from the step that "
            "needs it (INV-183).",
        )

        # The prohibition must actually name the scheme, not merely gesture at it.
        self.assertRegex(
            text,
            INTERNAL_SCHEME,
            "ground-rules.md must name `internal://` explicitly — a rule that does not "
            "name the scheme cannot be matched against the sdk_guide response that "
            "recommends it.",
        )

        # ...and it must be a prohibition, not a mention. Find the paragraph naming the
        # scheme and require prohibitive wording in it.
        paragraphs = re.split(r"\n(?=- |\n)", text)
        naming = [p for p in paragraphs if INTERNAL_SCHEME.search(p)]
        self.assertTrue(naming, "no block in ground-rules.md names `internal://`")
        self.assertTrue(
            any(
                ("MUST NOT" in p or "Never use" in p or "never use" in p)
                and "INV-231" in p
                for p in naming
            ),
            "the block naming `internal://` must forbid it and cite INV-231; a neutral "
            "mention would let the scheme be adopted while this test still passed.",
        )

    def test_no_file_offers_internal_connection_string(self):
        """No shipped file may propose `internal://` as a connection string.

        ground-rules.md is the one permitted mention, because forbidding the scheme
        requires naming it.

        Line-scoped by design (#424): ``internal://`` is one token, which a line break cannot
        split.
        """
        offenders = []
        for path in _shipped_files():
            if path == GROUND_RULES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for num, line in enumerate(text.splitlines(), 1):
                if INTERNAL_SCHEME.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{num}: {line.strip()[:120]}")

        self.assertEqual(
            [],
            offenders,
            "`internal://` is a single-process in-memory datastore and the bootcamp runs "
            "the visualization server in a separate process against the same CONNECTION, "
            "so it renders an empty graph while every load reports success (INV-231, "
            "INV-231). sdk_guide recommends it; the bootcamp must not. Offenders:\n"
            + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
