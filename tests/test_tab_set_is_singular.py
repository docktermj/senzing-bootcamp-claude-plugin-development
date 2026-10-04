"""The tab set must be stated once and agree everywhere it is stated.

This test exists because a previous change consolidated the visualization from eight tabs
to six in the reference server and in `visualization-api-reference.md`, and the whole suite
passed — while **nine** locations across four module-instruction files still told the agent
to build the removed tabs. An agent following
`module-07-query-visualize-discover/phase1-query-visualize.md` would have rebuilt them,
contradicting the contract it was told to build to.

The lesson generalized: the earlier tests asserted the two surfaces that had been *edited*
and inferred the rest was consistent. Consistency between files is exactly what cannot be
inferred, so it gets asserted here — across **every** shipped skill file, not a listed few.

What this pins:

* No shipped skill, command, or bundled doc presents a removed tab as a live tab.
* The reference server's `ALL_TABS`, the contract's active inventory, and the screenshot
  helper's tab catalog all describe the same set.
* A removed tab id may survive only as an explicit removal/reserved note.
* Anything that enumerates the tab set names the same six.

Enforces **INV-188** (a user-visible string a shipped script *emits* is bound by the same
content invariants as the plugin's prose, and conformance is verified by **executing** the
script -- this file runs `--help` and the unknown-id error path), which names this file.

Run:  python3 -m unittest discover -s tests
"""
import ast
import importlib.util
import os
import re
import sys
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CAPTURE = PLUGIN / "scripts" / "capture_screenshots.py"
CONTRACT = (
    PLUGIN / "skills" / "module-03b-truthset-visualization" / "visualization-api-reference.md"
)

LIVE_TAB_IDS = ["graph", "stats", "matchkeys", "features", "overlap", "probe"]
LIVE_TAB_LABELS = [
    "Entity Graph",
    "Merge Statistics",
    "Match Keys",
    "Feature Scores",
    "Cross-Source",
    "Search / Probe",
]
REMOVED_TAB_LABELS = ["Relationship Network", "Record Merges"]

# A mention of a removed tab is legitimate only when it is *about* the removal. Each phrase
# below marks such a context; a mention on a line matching none of them is a live reference.
REMOVAL_CONTEXT = (
    "REMOVED",
    'no "Relationship Network" tab',
    'no "Record Merges" tab',
    "reverses an earlier ruling",
    "strict **superset**",
    "former Record Merges",
    "removed Record Merges",
    "standalone \"Relationship Network\"",
    "Relationship Network, or Record Merges tab",
    "relationship-network",   # the screenshot slug, in the identifier table
    "record-merges",          # ditto
    "Relationship Networks (exploring",  # the Discover demo of find_network, not a tab
)


#: A removed tab's label. Matched by ``match_lines`` across line wraps (#424): each label is
#: two words, and "Record\nMerges cards" stood in `visualization-api-reference.md` as a live
#: surface, unseen by a line-at-a-time read, until the conversion found it.
REMOVED_LABEL = re.compile("|".join(re.escape(label) for label in REMOVED_TAB_LABELS))
#: A stale tab count.
EIGHT_TABS = re.compile(r"(?i)\b(eight|8) tabs\b")


def live_removed_tab_lines(text):
    """1-based lines where a removed tab's label starts outside a removal context.

    The removal context is read on that line, as before #424, so a context phrase that wraps
    away from it fails closed.
    """
    lines = text.split("\n")
    return [n for n in match_lines(text, REMOVED_LABEL)
            if not any(marker in lines[n - 1] for marker in REMOVAL_CONTEXT)]


def shipped_markdown():
    """Every Markdown file that ships to a bootcamper."""
    out = []
    for sub in ("skills", "commands", "docs"):
        out += sorted((PLUGIN / sub).rglob("*.md"))
    return out


def load(path):
    spec = importlib.util.spec_from_file_location(f"mod_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def server_tabs():
    src = SERVER.read_text()
    payload = re.search(r"const ALL_TABS=(\[\[.*?\]\]);", src).group(1)
    return re.findall(r'\["(\w+)","([^"]+)"\]', payload)


def contract_active_rows():
    text = CONTRACT.read_text()
    start = text.index("| Tab | Endpoint(s) | Shown when |")
    section = text[start : text.index("**De-duplication", start)]
    rows = re.findall(r"^\| \*\*(.+?)\*\*", section, re.M)
    return [r.replace(" (default)", "").strip() for r in rows]


class NoShippedFilePresentsARemovedTabAsLive(unittest.TestCase):
    """The check that the earlier suite was missing."""

    def test_no_live_reference_to_a_removed_tab(self):
        offenders = []
        for path in shipped_markdown():
            text = path.read_text()
            for lineno in live_removed_tab_lines(text):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)}:{lineno}: "
                    f"{text.split(chr(10))[lineno - 1].strip()[:110]}"
                )
        self.assertEqual(
            [],
            offenders,
            "these lines present a removed tab as a live tab; an agent reading them would "
            "rebuild it, contradicting visualization-api-reference.md:\n  "
            + "\n  ".join(offenders),
        )

    def test_no_shipped_file_claims_eight_tabs(self):
        offenders = []
        for path in shipped_markdown():
            for lineno in match_lines(path.read_text(), EIGHT_TABS):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
        self.assertEqual([], offenders, f"stale tab count: {offenders}")

    def test_the_wrapped_live_reference_the_conversion_found_is_caught(self):
        """Negative control (#424): the sentence as it shipped before this fix, wrapped."""
        shipped = ("That set applies to: the Entity Graph node detail (in either mode), Record\n"
                   "Merges cards, the Merge Statistics bucket drill-down.\n")
        self.assertEqual([1], live_removed_tab_lines(shipped))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(label in line for line in shipped.split("\n")
                             for label in REMOVED_TAB_LABELS))

    def test_the_corrected_sentence_names_no_removed_tab(self):
        """Must-not-flag (INV-282): the cards are Search / Probe's merged-entity cards now."""
        self.assertEqual([], live_removed_tab_lines(
            "That set applies to: the Entity Graph node detail (in either mode), the "
            "merged-entity cards on\nSearch / Probe, the Merge Statistics bucket drill-down.\n"))

    def test_a_wrapped_tab_count_is_caught(self):
        """Negative control (#424): "eight" ends line 1 and "tabs" begins line 2."""
        wrapped = "The app opens with all eight\ntabs visible.\n"
        self.assertEqual([1], match_lines(wrapped, EIGHT_TABS))
        self.assertFalse(any(EIGHT_TABS.search(l) for l in wrapped.split("\n")))


class EveryTabInventoryAgrees(unittest.TestCase):
    def test_server_and_contract_agree(self):
        self.assertEqual(LIVE_TAB_LABELS, [label for _id, label in server_tabs()])
        self.assertEqual(LIVE_TAB_LABELS, contract_active_rows())

    def test_capture_helper_default_matches_the_live_set(self):
        module = load(CAPTURE)
        self.assertEqual(LIVE_TAB_IDS, list(module.DEFAULT_TABS))

    def test_capture_helper_catalog_matches_the_contract_identifier_table(self):
        """Removed ids stay in the catalog so an older snapshot is still capturable —
        but they must be marked REMOVED in the contract, never offered as defaults."""
        module = load(CAPTURE)
        text = CONTRACT.read_text()
        start = text.index("### Tab identifiers and deep-linking")
        section = text[start : text.index("Headline counts belong", start)]
        documented = {}
        # Line-scoped by design (#424): the contract is a table, and a table row is one line.
        for line in section.splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 5 and cells[1].startswith("`") and cells[1] != "`Id`":
                documented[cells[1].strip("`")] = cells[4].strip("`")
        self.assertEqual(
            {tab: slug for tab, (slug, _label) in module.TABS.items()}, documented
        )
        for removed in ("network", "merges"):
            with self.subTest(removed=removed):
                self.assertIn(removed, module.TABS, "kept for older snapshots")
                self.assertNotIn(removed, module.DEFAULT_TABS, "must not be a default")

    def test_module_instructions_that_enumerate_tabs_name_the_live_six(self):
        """A file listing 3+ tab labels is enumerating the set; it must not miss one or add one.

        Line-scoped by design (#424): every line this flags carries a removed label outside a
        removal context, which ``test_no_live_reference_to_a_removed_tab`` already reports
        across line wraps; this adds only the enumeration framing, judged on the line.
        """
        problems = []
        for path in shipped_markdown():
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                if any(m in line for m in REMOVAL_CONTEXT):
                    continue
                named = [l for l in LIVE_TAB_LABELS + REMOVED_TAB_LABELS if l in line]
                if len(named) >= 3 and any(r in named for r in REMOVED_TAB_LABELS):
                    problems.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
        self.assertEqual([], problems, f"tab enumeration includes a removed tab: {problems}")


class SnapshotKeepsTheNoQueryBrowse(unittest.TestCase):
    """Removing Record Merges is only lossless if its unique capability survives — and it
    has to survive in the **snapshot**, which is the artifact the bootcamper keeps. The
    first implementation lost it there: `#probe-btns` existed only in the live probe body,
    so `loadProbes()` had nowhere to render and the browse silently vanished offline."""

    def setUp(self):
        self.module = load(SERVER)

    def snapshot_probe_body(self):
        entities = [
            {
                "entity_id": 1,
                "entity_name": "Robert Smith",
                "record_count": 3,
                "data_sources": ["CUSTOMERS", "REFERENCE"],
                "records": [
                    {
                        "data_source": "CUSTOMERS",
                        "record_id": "1001",
                        "name": "Robert Smith",
                        "match_key": "+NAME+ADDRESS",
                    }
                ],
            }
        ]

        class FakeModel:
            def merges(self_inner):
                return {"entities": entities}

        return self.module._snapshot_probe_html(FakeModel(), None, None)

    def test_snapshot_probe_body_has_the_browse_container(self):
        self.assertIn('id="probe-btns"', self.snapshot_probe_body())

    def test_snapshot_probe_body_has_no_live_search_box(self):
        """It cannot work in a static file; its absence is what makes the chips live-only."""
        self.assertNotIn('id="search-in"', self.snapshot_probe_body())

    def test_live_probe_body_has_both(self):
        self.assertIn('id="probe-btns"', self.module.PROBE_BODY_LIVE)
        self.assertIn('id="search-in"', self.module.PROBE_BODY_LIVE)

    def test_chips_are_suppressed_without_a_search_box(self):
        page = self.module.render_page("T", sources=["CUSTOMERS"])
        self.assertRegex(
            page, r'const live=!!document\.getElementById\("search-in"\);'
        )
        # Chip construction must sit inside the `live` guard, so the snapshot — which has
        # no search box — never renders them as dead controls. Asserted structurally
        # rather than by pinning the guard's exact one-liner, which changed when chips
        # gained live verification (organization-search-requires-name-org).
        probes = page[
            page.index("async function loadProbes") : page.index("function showAllMerges")
        ]
        self.assertLess(
            probes.index("if(live)"),
            probes.index(".text(e.entity_name)"),
            "chips must be created only inside the live guard",
        )

    def test_show_all_merges_does_not_require_a_search_box(self):
        """It runs in the snapshot, where #search-in does not exist."""
        page = self.module.render_page("T", sources=["CUSTOMERS"])
        body = page[page.index("function showAllMerges") :][:400]
        self.assertNotRegex(
            body,
            r'document\.getElementById\("search-in"\)\.value',
            "must not dereference the search box unguarded",
        )
        self.assertIn("if(si)si.value", body)

    def test_contract_states_the_offline_browse_requirement(self):
        text = CONTRACT.read_text()
        squashed = re.sub(r"\s+", " ", text)
        self.assertIn("that browse works offline", squashed.replace("**", ""))
        self.assertIn("MUST therefore include the `#probe-btns` container", squashed)


class YesNoHintConventionIsDocumented(unittest.TestCase):
    """INV-051 exempts the `(respond yes or no)` hint, but the exemption lived only in
    INVARIANTS.md — not in the file the agent actually reads each turn."""

    def test_ground_rules_documents_the_exemption(self):
        text = (PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md").read_text()
        self.assertIn("The one sanctioned \"or\"", text)
        self.assertIn("(respond yes or no)", text)
        self.assertIn("INV-051", text)

    def test_it_forbids_editing_a_pinned_question_to_add_or_remove_it(self):
        text = (PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md").read_text()
        squashed = re.sub(r"[*\s]+", " ", text)
        self.assertIn("do not add or remove it from a question whose wording is pinned", squashed)


class TheMarkdownSweepIsNotVacuous(unittest.TestCase):
    """`shipped_markdown()` spans skills, commands and docs; a rename in any one of them
    silently shrinks the corpus these checks run over."""

    def test_all_three_subtrees_contribute(self):
        found = shipped_markdown()
        self.assertGreater(len(found), 20, "corpus shrank to %d files" % len(found))
        for sub in ("skills", "commands", "docs"):
            with self.subTest(subtree=sub):
                self.assertTrue(
                    any(sub in p.parts for p in found),
                    "no .md found under %s/ — the glob drifted and this subtree is "
                    "no longer checked at all" % sub,
                )


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------------------
# The shipped PYTHON is scanned too (viz-reference-help-text-names-removed-tabs).
#
# `shipped_markdown()` above globs `*.md` under skills/, commands/ and docs/ — so the
# bundled reference server's own module docstring was never examined, and it still said
# "(Entity Graph + Relationship Network tabs)" and "The Relationship Network tab reuses
# /api/graph" long after INV-155 fixed the set at six with the network view as a *mode*.
#
# That docstring is not a comment: `argparse.ArgumentParser(description=__doc__)` prints it
# as `--help`, and INV-090 makes this file the model a Java or C# server is built from. A
# reader following it would build a seventh tab — the route INV-164 records for a defect
# that lives in the reference and in no written rule.
#
# Matching is done on FLATTENED text with a window, not per line: every legitimate mention
# here is framed ("the *removed* Relationship Network tab"), and once the prose or a comment
# wraps, the framing word and the mention land on different lines. A per-line rule reports
# the correct sentences as violations — it did, twice, while this was being written.
# ---------------------------------------------------------------------------------------

# Framing vocabulary for the Python sources, in addition to REMOVAL_CONTEXT above.
PY_REMOVAL_CONTEXT = REMOVAL_CONTEXT + (
    "removed Relationship Network",
    "standalone Relationship Network",
    "former Relationship Network",
    "were removed",
    "was removed",
    "RESERVED",
    "reserved rather than reused",
    "no Results Dashboard",
    "Two former tabs",
)

SHIPPED_PY = ("senzing_viz_server.py", "capture_screenshots.py")


def shipped_python():
    return [PLUGIN / "scripts" / name for name in SHIPPED_PY]


def unframed_mentions(text, window=200):
    """Removed-tab labels whose surrounding text never says they were removed.

    Comment markers are stripped before flattening. A wrapped JS or Python comment puts
    `//` (or `#`) between the framing word and the mention — "from the removed // Relationship
    Network tab" — and leaving them in makes "removed Relationship Network" fail to match text
    that plainly says it. Two correct comments were reported as violations before this.
    """
    text = re.sub(r"(?m)^\s*(//|#)\s?", " ", text)
    flat = re.sub(r"\s+", " ", text)
    out = []
    for label in REMOVED_TAB_LABELS + ["Results Dashboard"]:
        for m in re.finditer(re.escape(label), flat):
            near = flat[max(0, m.start() - window):m.end() + window]
            if not any(phrase in near for phrase in PY_REMOVAL_CONTEXT):
                out.append((label, flat[max(0, m.start() - 70):m.end() + 70]))
    return out


class ShippedPythonDoesNotPresentARemovedTabAsLive(unittest.TestCase):
    def test_no_shipped_script_presents_a_removed_tab_as_live(self):
        problems = []
        for path in shipped_python():
            for label, excerpt in unframed_mentions(path.read_text(encoding="utf-8")):
                problems.append(f"{path.name}: {label} — …{excerpt}…")
        self.assertEqual(
            [],
            problems,
            "a shipped script refers to a removed tab as if it were live (INV-155):\n  "
            + "\n  ".join(problems),
        )

    def test_the_reference_help_text_names_the_live_six(self):
        """The docstring IS the --help text, and the model INV-090 points implementers at."""
        doc = ast.get_docstring(ast.parse(SERVER.read_text(encoding="utf-8")))
        self.assertIsNotNone(doc, "the reference server lost its module docstring")
        flat = re.sub(r"\s+", " ", doc)
        for label in LIVE_TAB_LABELS:
            self.assertIn(
                label,
                flat,
                f"`--help` must name the live tab {label!r} (INV-155's six)",
            )
        self.assertIn(
            "INV-155",
            flat,
            "the docstring should cite the invariant that fixes the tab set, so a reader "
            "building in another language knows the six are binding",
        )

    def test_the_docstring_really_is_the_help_text(self):
        """If this wiring changes, the test above stops testing `--help`."""
        self.assertIn(
            "description=__doc__",
            SERVER.read_text(encoding="utf-8"),
            "the docstring is no longer argparse's description — re-point this test",
        )


# ---------------------------------------------------------------------------------------
# The capture helper's RUNTIME strings (deep-dive-audit-2026-07-30b).
#
# `viz-reference-help-text-names-removed-tabs` (2026-07-29) fixed the reference server's
# docstring and extended the guard above to `capture_screenshots.py` — but that guard reads
# comments and docstrings, and the helper's two user-visible tab lists are neither. They are
# f-strings interpolated from the `TABS` dict at runtime:
#
#     --tabs   "… Known: {','.join(TABS)}."          -> eight ids
#     error    "… Known ids: {', '.join(TABS)}"      -> eight ids
#
# `TABS` legitimately still holds `network` and `merges` so an eight-tab snapshot keeps its
# slugs, and the comment above it frames them "⛔ RESERVED" — which is exactly why the
# comment-scanning guard passed. A reader of `--help` sees none of that framing: they see
# eight capturable tabs for an app INV-155 fixes at six.
#
# These run the strings rather than reading the source, because the defect was that the
# source's framing and the emitted string had come apart.
# ---------------------------------------------------------------------------------------


def _capture_module():
    spec = importlib.util.spec_from_file_location("_capture_probe", CAPTURE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CaptureHelperRuntimeStringsNameTheLiveSix(unittest.TestCase):
    def setUp(self):
        self.mod = _capture_module()

    def test_reserved_ids_are_still_accepted(self):
        """Old snapshots must keep their slugs — the fix is about wording, not behavior."""
        self.assertEqual(["network"], self.mod.resolve_tabs("network"))
        self.assertEqual(("network", "merges"), self.mod.RESERVED_TABS)

    def test_help_text_lists_only_the_live_six(self):
        import subprocess

        out = subprocess.run(
            [sys.executable, str(CAPTURE), "--help"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertIn("graph,stats,matchkeys,features,overlap,probe", out)
        for retired in self.mod.RESERVED_TABS:
            self.assertNotRegex(
                out,
                rf"(?<![a-z]){retired}(?![a-z])",
                f"`--help` presents the removed tab id {retired!r} as available "
                "(INV-155 fixes the set at six)",
            )

    def test_unknown_id_error_lists_only_the_live_six(self):
        with self.assertRaises(ValueError) as caught:
            self.mod.resolve_tabs("bogus")
        message = str(caught.exception)
        for retired in self.mod.RESERVED_TABS:
            self.assertNotIn(
                retired,
                message,
                f"the unknown-tab error offers {retired!r} as a valid id",
            )
        for live in self.mod.DEFAULT_TABS:
            self.assertIn(live, message)

    def test_a_reserved_id_is_reported_as_retired(self):
        """Accepting it silently is how a stale list stays believed."""
        import io
        import contextlib

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.mod.resolve_tabs("merges")
        self.assertIn("no longer serves", err.getvalue())
