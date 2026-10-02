"""Visual defaults must survive the bootcamper's data, not just the Truth Set.

Every default in the visualization was chosen against 84 entities, and Module 7
points the same app at the bootcamper's own data — 2,799 entities and 4,464
relationships in the reported session. Two defaults did not travel:

* **Match Keys.** Real keys run to 70+ characters. A fixed 190px gutter with
  `text-anchor:end` pushed the head of each key off the left edge of the SVG, so
  the four highest bars all rendered as `...ISTRATION_COUNTRY+LEI_NUMBER`. The
  counts were right and the chart looked fine — which is worse than omitting the
  labels, because nothing signals that the tab is unreadable.
* **Entity Graph.** The scale-aware *label* default worked, but hiding labels does
  not thin 4,464 edges. The graph was a mesh conveying shape only.

The label fix is subtler than "truncate the other way": match keys are `+A+B+C…`
sequences that often share a long prefix and differ only in the last segment, so
head-only truncation renders the top bars identically — the same defect from the
other end. Middle-ellipsis is what actually distinguishes them, and that is why
the distinctness property, not the ellipsis strategy, is what these tests pin.

The JS is exercised by transcribing the shipped expressions rather than running a
browser: the guarantees are arithmetic, and a headless browser is not available on
every machine that runs this suite (INV-052/INV-066).

Enforces **INV-154**'s uncapped note ("Showing the N entities that have relationships, of M
total"), which its 2026-10-02 note (#327) keeps for an uncapped payload. The capped branch is
`tests/test_viz_capped_graph_notes.py`'s. Transcribing the JS does **not** establish what a browser
renders.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SERVER = os.path.join(PLUGIN, "scripts", "senzing_viz_server.py")
CONTRACT = os.path.join(
    PLUGIN, "skills", "module-03b-truthset-visualization", "visualization-api-reference.md"
)

REAL_KEYS = [
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY+LEI_NUMBER",
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY+OTHER_ID2",
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY",
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+LEI_NUMBER",
    "+NAME+ADDRESS",
    "+NAME",
]


def source():
    with open(SERVER, encoding="utf-8") as handle:
        return handle.read()


def fit_labels(keys, width=720):
    """Transcription of `drawMatchKeys`'s gutter sizing and `fitKey`."""
    longest = max((len(k) for k in keys), default=0)
    gutter = max(150, min(320, longest * 5.9 + 14))
    left = min(gutter, width * 0.55)
    max_chars = max(8, int((left - 10) / 5.9))

    def fit(k):
        if len(k) <= max_chars:
            return k
        tail = max(6, int((max_chars - 1) * 0.5))
        head = max_chars - 1 - tail
        return k[:head] + "…" + k[-tail:]

    return [fit(k) for k in keys], max_chars


class MatchKeyLabelsStayDistinguishable(unittest.TestCase):

    def test_no_two_labels_collide_unless_the_keys_are_identical(self):
        """The property that matters; the ellipsis strategy is not."""
        labels, _ = fit_labels(REAL_KEYS)
        groups = {}
        for key, label in zip(REAL_KEYS, labels):
            groups.setdefault(label, set()).add(key)
        collisions = {lbl: keys for lbl, keys in groups.items() if len(keys) > 1}
        self.assertEqual(
            {}, collisions,
            f"different match keys render as the same label: {collisions}",
        )

    def test_identical_keys_may_share_a_label(self):
        labels, _ = fit_labels([REAL_KEYS[0], REAL_KEYS[0]])
        self.assertEqual(labels[0], labels[1])

    def test_head_only_truncation_would_not_pass(self):
        """Guards the fix that looks right and is not.

        Right-trimming preserves the prefix — the direction the report asked for —
        and still renders the top four bars identically, because they share a
        52-character prefix.
        """
        _, max_chars = fit_labels(REAL_KEYS)
        head_only = [
            k if len(k) <= max_chars else k[: max_chars - 1] + "…" for k in REAL_KEYS
        ]
        self.assertLess(
            len(set(head_only)), len(set(REAL_KEYS)),
            "the head-only strategy no longer collides — this test's premise is "
            "stale, or the fixture keys stopped sharing a prefix",
        )

    def test_the_distinguishing_prefix_survives(self):
        labels, _ = fit_labels(REAL_KEYS)
        for key, label in zip(REAL_KEYS, labels):
            with self.subTest(key=key[:24]):
                self.assertTrue(label.startswith(key[:8]), "left-trimmed")

    def test_short_keys_are_untouched(self):
        labels, _ = fit_labels(REAL_KEYS)
        self.assertIn("+NAME", labels)
        self.assertIn("+NAME+ADDRESS", labels)

    def test_labels_fit_the_gutter(self):
        labels, max_chars = fit_labels(REAL_KEYS)
        self.assertLessEqual(max(len(l) for l in labels), max_chars)

    def test_the_full_key_is_reachable_on_hover(self):
        text = source()
        self.assertRegex(
            text,
            r'append\("title"\)\.text\(function\(z\)\{return z\.match_key;\}\)',
            "the truncated label must expose the untruncated key on hover, or the "
            "information is simply gone",
        )


class TheGraphDefaultIsScaleAware(unittest.TestCase):

    def threshold(self):
        match = re.search(r"GRAPH_SUBGRAPH_DEFAULT_ABOVE=(\d+)", source())
        self.assertIsNotNone(match, "the scale threshold is not defined")
        return int(match.group(1))

    def default_mode(self, entities, links):
        return "network" if entities > self.threshold() and links else "all"

    def test_the_truth_set_still_opens_on_the_full_population(self):
        self.assertEqual("all", self.default_mode(84, 71))

    def test_production_scale_opens_on_the_relationship_subgraph(self):
        self.assertEqual("network", self.default_mode(2799, 4464))

    def test_no_relationships_means_no_subgraph_default(self):
        """Defaulting to an empty subgraph would show a blank tab."""
        self.assertEqual("all", self.default_mode(5000, 0))

    def test_the_default_is_applied_once_and_never_overrides_a_choice(self):
        self.assertRegex(
            source(),
            r"graphModeAutoSet",
            "the scale default must latch, or every redraw would undo the "
            "bootcamper's toggle",
        )

    def test_the_note_states_both_counts(self):
        self.assertRegex(
            source(),
            r"entities that have relationships, of \"\+\s*\n?\s*STATS\.entities_total",
            "without both counts the bootcamper reads a default as their data",
        )


class TheContractCarriesBothForAnyLanguage(unittest.TestCase):
    """INV-090/INV-124: a non-Python server must inherit the same defaults."""

    def contract(self):
        with open(CONTRACT, encoding="utf-8") as handle:
            return re.sub(r"\s+", " ", handle.read())

    def test_the_threshold_is_stated_as_a_number(self):
        self.assertRegex(
            self.contract(),
            r"[Aa]bove 400 entities",
            "a threshold described only in prose cannot be implemented identically",
        )

    def test_the_contract_matches_the_reference_implementation(self):
        stated = re.search(r"[Aa]bove (\d+) entities", self.contract())
        shipped = re.search(r"GRAPH_SUBGRAPH_DEFAULT_ABOVE=(\d+)", source())
        self.assertEqual(
            stated.group(1), shipped.group(1),
            "the contract's threshold and the reference server's have drifted",
        )

    def test_middle_ellipsis_is_required_not_merely_suggested(self):
        text = self.contract()
        self.assertRegex(text, r"\*\*[Mm]iddle-ellipsize\*\*")
        self.assertRegex(
            text,
            r"[Rr]ight-truncation alone is \*\*not\*\* sufficient",
            "the contract must record why, or an implementer repeats the head-only fix",
        )

    def test_the_distinctness_property_is_the_stated_requirement(self):
        self.assertRegex(
            self.contract(),
            r"no two rendered labels are identical unless their keys are identical",
        )


if __name__ == "__main__":
    unittest.main()
