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

**No label is clipped (#463, INV-153).** The gutter was sized at an assumed 5.9px per
character, below every monospace font's advance (about 0.6em, 6.6px at 11px), so the
25-character `+NAME+ADDRESS+PHONE+EMAIL` started 11px left of the chart. The check that
should have caught it compared `len(label)` with a limit derived from the same constant,
so it could not fail. `NoMatchKeyLabelIsClipped` now asserts each label's left edge in
pixels at stated advances (0.60em and 0.62em) that are not the code's own value, shows
the former sizing clipped the reported key, and checks the source for the measured
advance and its 0.62em fallback.

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


def match_keys_body():
    """The text of `drawMatchKeys`, up to the next top-level function."""
    text = source()
    start = text.find("async function drawMatchKeys(")
    assert start >= 0, "drawMatchKeys not found"
    end = text.find("\nfunction ", start)
    assert end > start, "end of drawMatchKeys not found"
    return text[start:end]


# Stated per-character advances of the 11px label font, NOT the code's own value
# (the code measures its advance in the browser). 0.60em is the advance of common
# monospace fonts; 0.62em is the fallback the code uses when it cannot measure.
FONT_PX = 11
ADVANCE_060 = 0.60 * FONT_PX  # 6.6px
ADVANCE_062 = 0.62 * FONT_PX  # 6.82px
STATED_ADVANCES = (ADVANCE_060, ADVANCE_062)
WIDTHS = (720, 300)

# The key that clipped on the 2026-10-05 run (#463): the most frequent key, and the
# longest present.
CLIPPED_KEY = "+NAME+ADDRESS+PHONE+EMAIL"

# Two keys sharing a long head AND a long tail, differing only in the middle that
# middle-ellipsis elides, so they collide after fitting and the second one needs
# the positional suffix.
COLLIDING_KEYS = [
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+PASSPORT+REGISTRATION_DATE+REGISTRATION_COUNTRY+LEI_NUMBER",
    "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+DRLIC+REGISTRATION_DATE+REGISTRATION_COUNTRY+LEI_NUMBER",
]


def layout(keys, width, advance):
    """Transcription of `drawMatchKeys`'s gutter sizing: returns (mm.l, maxChars)."""
    longest = max((len(k) for k in keys), default=0)
    gutter = max(150, min(320, longest * advance + 14))
    left = min(gutter, width * 0.55)
    return left, max(8, int((left - 10) / advance))


def fit_key(k, n):
    """Transcription of `fitKey`: middle-ellipsis to at most `n` characters."""
    n = max(1, n)
    if len(k) <= n:
        return k
    tail = max(min(6, n - 2), int((n - 1) * 0.5))
    head = n - 1 - tail
    return k[:head] + "…" + k[len(k) - tail:]


def fit_labels(keys, advance, width=720):
    """`fitKey` applied at the gutter `advance` sizes, before disambiguation."""
    _, max_chars = layout(keys, width, advance)
    return [fit_key(k, max_chars) for k in keys], max_chars


def rendered_labels(keys, advance, width=720):
    """Transcription of the whole label path: fit, then disambiguate collisions.

    A colliding label is re-fitted to `maxChars` minus the suffix's length before the
    positional suffix is appended. Returns (labels, mm.l, maxChars).
    """
    left, max_chars = layout(keys, width, advance)
    fitted = [fit_key(k, max_chars) for k in keys]
    seen = {}
    for i, label in enumerate(list(fitted)):
        if label not in seen:
            seen[label] = i
            continue
        if keys[seen[label]] == keys[i]:
            continue
        sfx = f" ({i + 1})"
        fitted[i] = fit_key(keys[i], max_chars - len(sfx)) + sfx
    return fitted, left, max_chars


def left_edge(label, left, render_advance):
    """Where a right-anchored label at x = mm.l - 8 starts, in pixels."""
    return (left - 8) - len(label) * render_advance


class MatchKeyLabelsStayDistinguishable(unittest.TestCase):

    def test_no_two_labels_collide_unless_the_keys_are_identical(self):
        """The property that matters; the ellipsis strategy is not."""
        for advance in STATED_ADVANCES:
            with self.subTest(advance=advance):
                labels, _ = fit_labels(REAL_KEYS, advance)
                groups = {}
                for key, label in zip(REAL_KEYS, labels):
                    groups.setdefault(label, set()).add(key)
                collisions = {lbl: keys for lbl, keys in groups.items() if len(keys) > 1}
                self.assertEqual(
                    {}, collisions,
                    f"different match keys render as the same label: {collisions}",
                )

    def test_colliding_keys_are_disambiguated_after_fitting(self):
        """Middle-ellipsis cannot separate these; the positional suffix must."""
        for advance in STATED_ADVANCES:
            with self.subTest(advance=advance):
                fitted, _ = fit_labels(COLLIDING_KEYS, advance)
                self.assertEqual(
                    fitted[0], fitted[1],
                    "the fixture no longer collides after fitting, so the suffix "
                    "path is no longer exercised",
                )
                labels, _, _ = rendered_labels(COLLIDING_KEYS, advance)
                self.assertNotEqual(labels[0], labels[1])
                self.assertTrue(labels[1].endswith(" (2)"))

    def test_identical_keys_may_share_a_label(self):
        labels, _, _ = rendered_labels([REAL_KEYS[0], REAL_KEYS[0]], ADVANCE_060)
        self.assertEqual(labels[0], labels[1])

    def test_head_only_truncation_would_not_pass(self):
        """Guards the fix that looks right and is not.

        Right-trimming preserves the prefix — the direction the report asked for —
        and still renders the top four bars identically, because they share a
        52-character prefix.
        """
        _, max_chars = fit_labels(REAL_KEYS, ADVANCE_060)
        head_only = [
            k if len(k) <= max_chars else k[: max_chars - 1] + "…" for k in REAL_KEYS
        ]
        self.assertLess(
            len(set(head_only)), len(set(REAL_KEYS)),
            "the head-only strategy no longer collides — this test's premise is "
            "stale, or the fixture keys stopped sharing a prefix",
        )

    def test_the_distinguishing_prefix_survives(self):
        keys = REAL_KEYS + COLLIDING_KEYS
        for advance in STATED_ADVANCES:
            labels, _, _ = rendered_labels(keys, advance)
            for key, label in zip(keys, labels):
                with self.subTest(advance=advance, key=key[:24]):
                    self.assertTrue(label.startswith(key[:8]), "left-trimmed")

    def test_short_keys_are_untouched(self):
        for advance in STATED_ADVANCES:
            with self.subTest(advance=advance):
                labels, _, _ = rendered_labels(REAL_KEYS, advance)
                self.assertIn("+NAME", labels)
                self.assertIn("+NAME+ADDRESS", labels)


class NoMatchKeyLabelIsClipped(unittest.TestCase):
    """#463: no label glyph starts left of the chart's left edge (INV-153).

    The former check compared `len(label)` with a `max_chars` derived from the same
    5.9px-per-character constant the code used, so it could not fail. These checks
    measure in pixels at stated advances that are not the code's own value: the
    advance the code measures is the font's real one, so the sizing advance equals
    the rendering advance; when it cannot measure, it sizes at 0.62em while the font
    renders at about 0.60em.
    """

    KEYS = REAL_KEYS + [CLIPPED_KEY] + COLLIDING_KEYS

    def cases(self):
        """(width, sizing advance, rendering advance) for every stated case."""
        for width in WIDTHS:
            for render in STATED_ADVANCES:
                yield width, render, render          # measured
                yield width, ADVANCE_062, render     # fallback

    def assert_inside(self, keys):
        checked = 0
        for width, sizing, render in self.cases():
            labels, left, _ = rendered_labels(keys, sizing, width)
            for label in labels:
                checked += 1
                edge = left_edge(label, left, render)
                with self.subTest(width=width, sizing=sizing, render=render, label=label):
                    self.assertGreaterEqual(
                        edge, 0,
                        f"{label!r} starts at x = {edge:.1f}px, left of the chart",
                    )
        self.assertGreater(checked, 0, "no label was checked")

    def test_every_label_starts_inside_the_chart(self):
        self.assert_inside(self.KEYS)

    def test_the_clipped_key_alone_starts_inside_the_chart(self):
        """The 2026-10-05 chart: the 25-character key was the longest present."""
        self.assert_inside([CLIPPED_KEY, "+NAME+ADDRESS", "+NAME"])

    def test_suffixed_labels_stay_inside_the_budget(self):
        suffixed = 0
        for width, sizing, _ in self.cases():
            labels, _, max_chars = rendered_labels(self.KEYS, sizing, width)
            for label in labels:
                if re.search(r" \(\d+\)$", label):
                    suffixed += 1
                    with self.subTest(width=width, sizing=sizing, label=label):
                        self.assertLessEqual(len(label), max_chars)
        self.assertGreater(suffixed, 0, "the colliding pair produced no suffixed label")

    def test_the_former_sizing_clipped_the_reported_key(self):
        """Guards against the test going circular again.

        The former code sized at 5.9px per character. At 6.6px per character
        rendered, that put `+NAME+ADDRESS+PHONE+EMAIL` left of x = 0, so a check that
        passes at 6.6px cannot be passing under the old sizing.
        """
        keys = [CLIPPED_KEY, "+NAME+ADDRESS", "+NAME"]
        labels, left, _ = rendered_labels(keys, 5.9)
        self.assertEqual(CLIPPED_KEY, labels[0], "the old sizing did not truncate it")
        self.assertLess(left_edge(labels[0], left, ADVANCE_060), 0)

    def test_the_code_measures_the_advance_with_a_fallback(self):
        body = match_keys_body()
        self.assertIn("measureText(", body, "drawMatchKeys must measure the advance")
        self.assertRegex(
            body, r'\.font="11px __CODE_FONT__"',
            "the measurement must use the labels' own font",
        )
        self.assertRegex(
            body, r"11\*0\.62\b",
            "the 0.62em fallback is missing",
        )
        self.assertRegex(
            body, r"isFinite\(a\)&&a>0",
            "a non-finite or non-positive measurement must fall back",
        )
        self.assertRegex(body, r"longest\*adv\+14", "the gutter must use the advance")
        self.assertRegex(
            body, r"Math\.floor\(\(mm\.l-10\)/adv\)", "maxChars must use the advance",
        )
        self.assertRegex(
            body, r"fitKey\(items\[i\]\.match_key,maxChars-sfx\.length\)\+sfx",
            "the suffix must be fitted inside the budget",
        )
        self.assertNotIn("5.9", body, "the assumed 5.9px advance is back")

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

    def test_rule_2_forbids_clipping_and_sizes_from_rendered_width(self):
        """#463: a server in another language must not repeat the estimate."""
        text = self.contract()
        rule = re.search(
            r"\*\*2\. Match-key labels must stay distinguishable\.\*\*(.*?)\*\*3\. ", text,
        )
        self.assertIsNotNone(rule, "contract rule 2 not found")
        rule = rule.group(1)
        self.assertRegex(
            rule,
            r"⛔ \*\*\(INV-153\) No label glyph may start left of the chart's left edge\.\*\*",
        )
        self.assertRegex(rule, r"Size the gutter from the \*\*rendered\*\* width")
        self.assertRegex(rule, r"measure the label font's per-character advance")
        self.assertRegex(rule, r"no less than 0\.62 em")
        self.assertRegex(rule, r"one advance for both the gutter and the truncation limit")
        self.assertRegex(rule, r"suffix counts inside the width budget")

    def test_the_distinctness_property_is_the_stated_requirement(self):
        self.assertRegex(
            self.contract(),
            r"no two rendered labels are identical unless their keys are identical",
        )


if __name__ == "__main__":
    unittest.main()
