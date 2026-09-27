#!/usr/bin/env python3
"""Build a realistic scratch bootcamp project for a dry run (maintainer tool).

An empty directory exercises each hook's gating branch and nothing else. Most of the
plugin's scripts only misbehave when the state they read is *mid-flight*, so every
fixture written here exists because a naive one hid a defect. Run with --explain to
print the fixture-to-invariant map without writing anything.

Standard library only. Lives under .claude/, which propagate.sh does not mirror, so
this never ships to bootcampers.

Usage:
    python3 scaffold_project.py ~/senzing-bootcamp-dryrun
    python3 scaffold_project.py ~/senzing-bootcamp-phase3 --fresh
    python3 scaffold_project.py ~/senzing-bootcamp-phase3 --seeded
    python3 scaffold_project.py --explain
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

DIRS = (
    "config",
    "data/raw",
    "data/mapping",
    "data/samples",
    "data/temp",
    "database",
    "docs/progress",
    "docs/feedback",
    "docs/visualizations",
    "docs/mapping",
    "logs",
    "src/transform",
    "src/load",
    "src/system_verification",
)

# The recap cover clips module chips at 46 characters. No real module NAME reaches
# that — the longest is "Data Quality, Mapping, and Transformation" at 41, and even a
# numbered legacy heading ("10. …") only reaches 45. That is precisely why a renderer
# crash hid behind the shipped example fixture for so long.
#
# ⚠️ The UNFINALIZED heading below does NOT reach the clip either, by any documented
# sequence (measured 2026-09-24). Folded, it sits inside the RECAP-CHECKPOINT fence,
# which generate_recap_pdf.py strips before module parsing. Unfenced, as
# module-completion step 2d leaves it, parse_recap splits the "— in progress" suffix
# off into the date slot, so the chip is built from the bare 41-character title. The
# heading is 55 characters; the chip label is 41. The chip-clip path is covered by unit
# test in tests/test_recap_pdf_font_safety.py, not by this fixture, and
# tests/test_dry_run_scaffold.py fails if this title is ever lengthened past the clip.
LONG_MODULE_NAME = "Data Quality, Mapping, and Transformation"
IN_PROGRESS_HEADING = f"{LONG_MODULE_NAME} — in progress"  # parses to the 41-char title

PROGRESS = {
    "current_module": "data_quality_mapping",
    "current_step": "11",
    "modules_completed": [
        "entity_resolution_concepts",
        "business_problem",
        "sdk_setup",
        "system_verification",
        "truthset_visualization",
        "data_collection",
    ],
    "selected_modules": [
        "bootcamp_preparation",
        "entity_resolution_concepts",
        "business_problem",
        "sdk_setup",
        "system_verification",
        "truthset_visualization",
        "data_collection",
        "data_quality_mapping",
        "data_processing",
        "query_visualize_discover",
        "graduation",
    ],
    # Names a container that does not exist -> exercises warn-and-continue (INV-101).
    "docker_containers": [
        {"name": "bootcamp-dryrun-absent", "image": "postgres:16", "purpose": "repository"}
    ],
    "license_record_limit": 0,
    "step_history": {
        "data_quality_mapping": {
            "last_completed_step": "11",
            "updated_at": "2026-01-01T00:00:00-07:00",
        }
    },
}

PREFERENCES = """path: core
programming_language: Python
name: Ada Lovelace
os: Linux
arch: x86_64
git_init: true
verbosity:
  preset: standard
"""

# Pre-seeds exactly the preferences INV-133 makes honorable, so a phase-3 walk can
# exercise the honor-don't-ask path: Steps 1, 3 and 4 must all be skipped and the Step 7
# recap must mark each as "from your saved preferences". Deliberately NOT a full mid-run
# state -- progress stays empty so onboarding still runs from the top.
SEEDED_PREFERENCES = """path: core
selected_modules:
  - bootcamp_preparation
  - entity_resolution_concepts
  - business_problem
  - sdk_setup
  - system_verification
  - truthset_visualization
  - data_collection
  - data_quality_mapping
  - data_processing
  - query_visualize_discover
  - graduation
verbosity:
  preset: minimal
programming_language: Java
"""

RECAP = f"""# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-01-01T09:00:00-07:00
**Programming language:** Python
**Path:** Core
**Plugin version:** 0.0.0-dryrun

---

## Data collection — 2026-01-01T11:00:00-07:00

### Information Shared
- CORD datasets and the Senzing Entity Specification.

### Questions & Responses
- **Q:** How would you like to provide the data for this source?
    - **R:** Option 2, a file path.

### Actions Taken
- Registered `data/raw/customers.csv` in `config/data_sources.yaml`.

### End-of-Module Summary
**What you accomplished:**
- Collected one source into `data/raw/`.

**Files produced:**
- `data/raw/customers.csv` — the raw source.

**Why it matters:** Nothing downstream runs without the data in the project.

---
"""

# An UNFINALIZED checkpoint block: what the durability hooks leave behind and
# module-completion step 2d is supposed to clear (INV-059). Its heading does NOT reach
# the PDF cover's 46-character chip clip, folded or unfenced: the parser strips the
# "— in progress" suffix, leaving the 41-character title (see LONG_MODULE_NAME above).
CHECKPOINT = f"""<!-- RECAP-CHECKPOINT:START -->
## {IN_PROGRESS_HEADING}

### Information Shared
- A line with an em dash — an ellipsis … and a middle dot ·
- Mapping CUSTOMERS to the Senzing Entity Specification.

### Questions & Responses
- **Q:** Which mapping mode would you like?
    - **R:** Verbose.

### Actions Taken
- Profiled `data/raw/customers.csv`.

### End-of-Module Summary
**What you accomplished:**
- Mapping in progress.
<!-- RECAP-CHECKPOINT:END -->
"""

FEEDBACK = """# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp.

**Started:** 2026-01-01

## Your Feedback

## Improvement: A precious entry that must survive graduation untouched

**Date:** 2026-01-01
**Module:** Data collection
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the banner did not appear
**Upstream:** not applicable

### What happened

If graduation's normalization pass rewrites, empties or deletes this file, INV-067 is
broken and this sentence will be missing.
"""

MESSY_MARKDOWN = """## Messy heading
text immediately after a heading, no blank line
- a list with no blank line before it
```
a fenced block with no info string
```
**Label :** colon spacing is wrong
"""

# Synthetic verification records, in the shape System verification Step 2 specifies: a
# 3-record merge cluster for one invented person plus one distractor that must stay a
# singleton, every record `DATA_SOURCE: VERIFY` with a unique `RECORD_ID`, so a resumed
# mid-bootcamp run reads data the module recognizes (4 records -> 2 entities).
#
# Attribute names and record structure are the Senzing Entity Specification's, confirmed
# this session rather than copied: `DATA_SOURCE`/`RECORD_ID` at the root of each record,
# features in a `FEATURES` array, `NAME_FULL` for a single-field name of unknown type,
# `DATE_OF_BIRTH`, and `ADDR_FULL` for a single-field address — which the spec says must
# never be mixed with parsed `ADDR_*` fields in the same object
# (`search_docs(category='data_mapping')` -> "Attributes for the record key", "Name >
# Feature: NAME", "Contact methods > Feature: ADDRESS"; MCP server 1.32.9, docs index
# 2026-08-11 20:52 UTC, verified 2026-08-14).
#
# The names are invented and PII-free, as Step 2 requires. The variation between cluster
# members is deliberately trivial — a nickname, a middle initial, an unabbreviated street
# — because the point is a resolution outcome that is known in advance.
RECORDS = "\n".join(
    json.dumps(r)
    for r in (
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1001",
            "FEATURES": [
                {"NAME_FULL": "Aurelia Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Way, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1002",
            "FEATURES": [
                {"NAME_FULL": "Relia Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Way, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1003",
            "FEATURES": [
                {"NAME_FULL": "Aurelia B Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Street, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-2001",
            "FEATURES": [
                {"NAME_FULL": "Tobias Fennimore"},
                {"DATE_OF_BIRTH": "1962-11-02"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "884 Kestrel Row, Reno, NV 89502, US"},
            ],
        },
    )
)

#: The three modes `build()` can produce. `--fresh` and `--seeded` were added after this
#: banner was written, and the banner was not revisited: it described the mid-bootcamp
#: fixtures in every mode, so `--fresh` claimed 8 fixtures over a 4-file project and
#: described an empty preferences file as carrying saved preferences — the exact inverse.
#: An over-claiming banner is worse here than no banner, because it is the operator's
#: primary input for the "coverage limits" section a dry-run report must state.
MODES = ("mid", "fresh", "seeded")
ALL_MODES = frozenset(MODES)

#: (display, path, modes, why). `path` is the project-relative file the row describes, or
#: None for a row annotating a key *inside* another fixture. Keeping the real path here —
#: rather than only the display string — is what lets a test compare the banner against
#: what `build()` actually writes, in every mode.
#: PIPELINE paths for the complete fixture, from `sdk_guide(topic='install',
#: platform='linux_apt')` -> `default_paths` on MCP server **1.36.0, 2026-09-02**
#: (config_path `/etc/opt/senzing`, resource_path `/opt/senzing/er/resources`,
#: support_path `/opt/senzing/data`). Re-asked at implementation time, not copied from the spec.
#: ⚠️ These are the **linux_apt** defaults, and deliberately literal. The fixture's job is to
#: satisfy the completeness pre-flight so the SDK gate is the one reached, and complete paths do
#: that on every platform. Only the "SDK present -> exit 0" case is Linux-specific; on macOS the
#: same call returns `$(brew --prefix)/opt/senzing/{er/etc,er/resources}` with SUPPORTPATH at the
#: sibling `opt/senzing/data`, and on Windows `%SENZING_DIR%\\{etc,resources}` with SUPPORTPATH at
#: `%SENZING_DIR%\\..\\data` -- a maintainer running phase 2 there should expect the SDK gate too,
#: reached for the same reason.
PIPELINE_DEFAULTS = (
    ("CONFIGPATH", "/etc/opt/senzing"),
    ("RESOURCEPATH", "/opt/senzing/er/resources"),
    ("SUPPORTPATH", "/opt/senzing/data"),
)

FIXTURE_MAP = [
    ("config/engine_config.json", "config/engine_config.json", ALL_MODES,
     "COMPLETE PIPELINE -> passes the config pre-flight and reaches the SDK gate "
     "(exit 1, libSz.so) or initializes where the SDK is present"),
    ("config/engine_config_incomplete.json", "config/engine_config_incomplete.json", ALL_MODES,
     "empty PIPELINE -> stops AT the config pre-flight (exit 2); the other gate, kept "
     "so both stay covered"),
    ("config/bootcamp_progress.json", "config/bootcamp_progress.json", frozenset({"mid"}),
     "makes every hook consider the bootcamp active; mid-module so resume paths run"),
    ("  └ docker_containers", None, frozenset({"mid"}),
     "names an ABSENT container -> warn-and-continue (INV-101)"),
    ("config/bootcamp_progress.json", "config/bootcamp_progress.json", frozenset({"fresh", "seeded"}),
     "empty {} -> hooks see a project with NO active bootcamp; onboarding runs from the top"),
    ("config/bootcamp_preferences.yaml", "config/bootcamp_preferences.yaml", frozenset({"mid", "seeded"}),
     "saved verbosity + language to test honor-don't-ask (INV-133)"),
    ("config/bootcamp_preferences.yaml", "config/bootcamp_preferences.yaml", frozenset({"fresh"}),
     "deliberately EMPTY -> every question must be asked (the INERT direction of INV-133)"),
    ("docs/bootcamp_recap.md", "docs/bootcamp_recap.md", frozenset({"mid"}),
     "a completed section carrying all four subsections (INV-103)"),
    ("docs/progress/recap_checkpoint.md", "docs/progress/recap_checkpoint.md", frozenset({"mid"}),
     "an UNFINALIZED block -> fold idempotency, run it 3x (INV-059). This fixture does "
     "NOT reach the PDF cover's 46-char chip clip by any documented sequence, so do not "
     "report that path as exercised. Folded, its heading sits inside the "
     "RECAP-CHECKPOINT fence, which generate_recap_pdf.py strips before module parsing, "
     "so the section is absent from the cover, the contents and the body (audit_recap "
     "warns, correctly, that a module was folded but never finalized). Unfenced, as "
     "module-completion step 2d leaves it, parse_recap strips the '— in progress' "
     "suffix, so the chip is the bare 41-character title, and no real module title is "
     "long enough to clip. The chip-clip path is covered by unit test in "
     "tests/test_recap_pdf_font_safety.py. Measured 2026-09-24"),
    ("docs/feedback/...FEEDBACK.md", "docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md", ALL_MODES,
     "a precious entry the normalizer must leave byte-identical (INV-067)"),
    ("docs/loading_strategy.md", "docs/loading_strategy.md", frozenset({"mid"}),
     "deliberately messy Markdown for the normalizer (INV-060)"),
    ("src/system_verification/verification_data.jsonl",
     "src/system_verification/verification_data.jsonl", frozenset({"mid"}),
     "the file System verification Step 2 writes, so a resumed run finds it; also the "
     "records for the viz server's --no-serve snapshot build"),
]


def mode_name(fresh: bool, seeded: bool) -> str:
    """The mode key for the flags given. `--seeded` wins, matching build()'s own order."""
    if seeded:
        return "seeded"
    if fresh:
        return "fresh"
    return "mid"


def fixtures_for(mode: str):
    return [row for row in FIXTURE_MAP if mode in row[2]]


def explain(mode: str = "mid"):
    print(f"Fixtures this {mode} project carries, and the invariant each one exercises:\n")
    for display, _path, _modes, why in fixtures_for(mode):
        print(f"  {display:47} {why}")
    omitted = sorted(
        {row[0] for row in FIXTURE_MAP if mode not in row[2] and row[1]}
        - {row[0] for row in fixtures_for(mode)}
    )
    if omitted:
        # Naming what is absent is the point: a dry-run report must state its coverage
        # limits, and the operator writes that section from this banner.
        print("\n  NOT in this mode (so their invariants are NOT exercised here):")
        for display in omitted:
            print(f"    {display}")
    print(
        "\nEvery fixture is here because a naive one hid a defect. An empty project\n"
        "exercises only each hook's gating branch."
    )


def build(root: Path, fresh: bool, seeded: bool = False) -> None:
    if root.exists():
        shutil.rmtree(root)
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    # ⛔ The PIPELINE must be COMPLETE. `senzing_viz_server.py` runs a config-completeness
    # pre-flight (`REQUIRED_PIPELINE_KEYS` = CONFIGPATH, RESOURCEPATH, SUPPORTPATH) BEFORE it
    # touches the SDK, so `{"PIPELINE": {}}` exits 2 having never reached the SDK — while the
    # banner claimed the fixture existed to reach "their real failure". Both gates fail loudly
    # and write nothing, which is why no prior phase-2 run separated them: on a machine with no
    # `libSz.so` they are indistinguishable without reading the exit code. The 2026-09-02 run
    # was the first with a working SDK, and the SDK-missing branch turned out to have been
    # unverified by every dry run that listed it as checked.
    (root / "config/engine_config.json").write_text(
        json.dumps(
            {"PIPELINE": dict(PIPELINE_DEFAULTS),
             "SQL": {"CONNECTION": "sqlite3://na:na@%s" % (root / "database" / "G2C.db")}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # The pre-flight gate is good behavior and stays covered by its own named fixture, rather
    # than being deleted along with the defect it was masking.
    (root / "config/engine_config_incomplete.json").write_text(
        json.dumps({"PIPELINE": {}}, indent=2) + "\n", encoding="utf-8"
    )

    if fresh or seeded:
        # The fresh-start path: hooks must see no active bootcamp, and onboarding runs
        # from the top. With --seeded, preferences are pre-filled so Bootcamp preparation
        # must HONOR them instead of asking (INV-133) -- the opposite direction to --fresh.
        (root / "config/bootcamp_progress.json").write_text("{}\n", encoding="utf-8")
        (root / "config/bootcamp_preferences.yaml").write_text(
            SEEDED_PREFERENCES if seeded else "", encoding="utf-8"
        )
    else:
        (root / "config/bootcamp_progress.json").write_text(
            json.dumps(PROGRESS, indent=2) + "\n", encoding="utf-8"
        )
        (root / "config/bootcamp_preferences.yaml").write_text(
            PREFERENCES, encoding="utf-8"
        )
        (root / "docs/bootcamp_recap.md").write_text(RECAP, encoding="utf-8")
        (root / "docs/progress/recap_checkpoint.md").write_text(
            CHECKPOINT, encoding="utf-8"
        )
        (root / "docs/loading_strategy.md").write_text(MESSY_MARKDOWN, encoding="utf-8")
        (root / "src/system_verification/verification_data.jsonl").write_text(
            RECORDS + "\n", encoding="utf-8"
        )

    # The feedback file exists in both modes: nothing may ever delete or empty it.
    (root / "docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md").write_text(
        FEEDBACK, encoding="utf-8"
    )

    if seeded:
        label = "seeded (phase 3: honor-don't-ask path, INV-133)"
    elif fresh:
        label = "fresh (phase 3: onboarding from zero)"
    else:
        label = "mid-bootcamp (phase 2)"
    print(f"Built {label} project at {root}\n")
    explain(mode_name(fresh, seeded))
    print(
        "\nReminders:\n"
        "  - test the hooks from a directory with NO bootcamp_progress.json first\n"
        "  - commit or `cp` aside before mutating the repo to negative-control a guard\n"
        "  - clear __pycache__ after any same-size revert\n"
        f"  - clean up with: rm -rf {root}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("directory", nargs="?", help="where to build the project")
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="empty config for the phase-3 onboarding path (no saved state)",
    )
    ap.add_argument(
        "--seeded",
        action="store_true",
        help="pre-seed the honorable preferences so the honor-don't-ask path is exercised",
    )
    ap.add_argument(
        "--explain",
        action="store_true",
        help=(
            "print the fixture-to-invariant map for the mode implied by --fresh/--seeded "
            "(default: mid-bootcamp) and exit without writing"
        ),
    )
    args = ap.parse_args()

    if args.explain:
        # The map is mode-dependent, so --explain must name the mode it is describing —
        # otherwise it reproduces the over-claim it was changed to fix.
        explain(mode_name(args.fresh, args.seeded))
        return 0
    if not args.directory:
        ap.error("a directory is required (or pass --explain)")

    root = Path(args.directory).expanduser().resolve()
    repo = Path(__file__).resolve().parents[3]
    if root == repo or repo in root.parents:
        print(
            f"Refusing to build inside the repo ({repo}). Use a path outside it, "
            "e.g. ~/senzing-bootcamp-dryrun.",
            file=sys.stderr,
        )
        return 2
    if str(root).startswith(("/tmp/", "/var/tmp/")):
        print(
            "Refusing to build under /tmp: a maintainer hook blocks system-temp "
            "writes, and the plugin's file-placement rules assume a project dir.",
            file=sys.stderr,
        )
        return 2

    build(root, args.fresh, args.seeded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
