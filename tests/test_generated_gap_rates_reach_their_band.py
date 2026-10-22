"""Any absence rates Module 4 offers as an example must reach the band that example claims.

Module 4 requires the generated data to put at least one source in the **70-79%** band, and
illustrated it with *"a phone absent on roughly a third of its records, an address missing on a
handful"*. Generating to those rates and scoring with Module 5's formula produced **94.9%** --
squarely inside the `>=80` band the requirement exists to avoid. The illustration was off by roughly
a factor of six.

**The defect was arithmetic, not wording.** The illustration and the requirement are separated by a
0.70 completeness weight and a per-record denominator, and nothing in either module did the
multiplication. With clean formatting and distinct keys (which INV-239 requires of the keys) the
composite reduces to `score = 100 - (70/n)m` on `n` applicable fields, where `m` is the summed
per-field absence in whole fields.

**The denominator counts the record key (#757).** Module 5 Phase 1 step 6 puts every structural key
in the completeness denominator, so a generated source with seven non-key fields scores on eight
applicable fields, `100 - 8.75m`, and the band needs `m` between 2.4 and about 3.43. Module 4 once
divided by seven: its sample summed 2.20 and claimed 78.0, which Module 5 scored at 80.75, outside
the band. So `n` here is never a constant: it is the non-key count Module 4 states plus the key, and
every figure is recomputed from it.

**Two consequences the prose now states:** no single field can reach the band at any rate (a field
absent from every record moves the score by at most `0.70 x 100/n`, 8.75 points on eight fields,
against a band that starts twenty-one points down); and the requirement is scale-free while the
illustration was not -- what the generator needs is a slot-emptiness fraction, 30-43%.

⚠️ **This guard COMPUTES; it does not pattern-match the prose.** The acceptance criterion was
"verified by computing it, not by reading it", and a test that merely greps for the figures would
pass on a table that had drifted. It parses the shipped worked table and the shipped
`quality_intent` sample and runs both through the formula.

Source spec: `specs/module4-example-gap-rates-cannot-reach-the-band-they-illustrate.md`; the key in
the denominator is #757.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
QUALITY = SKILLS / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"

#: Module 5's composite, which this file must never re-implement from prose.
#: score = 0.70*completeness + 0.25*format_consistency + 0.05*(100 - duplicate_rate)
WEIGHT_COMPLETENESS, WEIGHT_FORMAT, WEIGHT_DUP = 0.70, 0.25, 0.05


def score(completeness, fmt=100.0, dup=0.0):
    return WEIGHT_COMPLETENESS * completeness + WEIGHT_FORMAT * fmt + WEIGHT_DUP * (100.0 - dup)


#: Number words Module 4 uses for its field counts.
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10}


def flat(path):
    """Collapse spaces only -- LINE STRUCTURE IS LOAD-BEARING for the table regex below."""
    return re.sub(r"[ \t]+", " ", path.read_text(encoding="utf-8"))


def squash(path):
    """Collapse all whitespace, for prose assertions that wrap across lines."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def non_key_fields():
    """The non-key field count Module 4's worked figures state, e.g. "seven non-key fields"."""
    found = re.search(r"(?i)Worked, for (\w+) non-key fields plus the record key", squash(MODULE4))
    assert found, "Module 4 no longer states how many non-key fields its worked figures use"
    return WORDS[found.group(1).lower()]


def applicable_fields():
    """`n` as Module 5 counts it: the non-key fields plus the record key, which is never gapped."""
    return non_key_fields() + 1


def completeness(rates, n):
    """Mean per-record completeness, in percent, for summed absence `sum(rates)` on `n` fields."""
    return 100.0 * (1.0 - sum(rates) / n)


def in_band(rates, n, lo, hi):
    return lo <= score(completeness(rates, n)) <= hi


class TheFormulaStillLivesInModule5(unittest.TestCase):
    """If Module 5's weights change, this guard's arithmetic is stale and must fail loudly."""

    def test_module5_states_the_weights_this_guard_assumes(self):
        text = flat(QUALITY)
        self.assertIn("0.70", text, "Module 5 no longer states a 0.70 completeness weight")
        self.assertIn("0.25", text, "Module 5 no longer states a 0.25 format weight")
        self.assertIn("0.05", text, "Module 5 no longer states a 0.05 duplicate weight")

    def test_module4_routes_to_it_rather_than_restating_it(self):
        """A formula stated twice drifts in one of them."""
        self.assertRegex(
            squash(MODULE4),
            r"(?i)stated once in `\.\./module-05-data-quality-mapping/phase1-quality-assessment\.md`",
            "Module 4 does not route to Module 5 for the arithmetic")


class TheRecordKeyIsInTheDenominator(unittest.TestCase):
    """#757: Module 4's `n` is Module 5's denominator, structural keys included."""

    def test_module5_counts_structural_keys(self):
        """The `+ 1` below is only right while Module 5 counts the key."""
        self.assertRegex(
            squash(QUALITY), r"it is a \*\*structural key\*\* — `DATA_SOURCE`, `RECORD_ID`",
            "Module 5's denominator no longer names the structural keys, so counting the record "
            "key in Module 4's n is no longer Module 5's rule")

    def test_module4_says_the_key_counts_and_is_never_gapped(self):
        text = squash(MODULE4)
        self.assertRegex(
            text, r"`n` counts every field Module 5 counts, the record key included",
            "Module 4 Step 2 does not say its completeness denominator counts the record key")
        self.assertRegex(text, r"(?i)A key is \*\*never gapped\*\*")

    def test_the_stated_applicable_count_is_non_key_plus_key(self):
        n = applicable_fields()
        words = {v: k for k, v in WORDS.items()}
        self.assertIn("%s applicable fields" % words[n], squash(MODULE4),
                      "Module 4 does not state the %d-field count its arithmetic needs" % n)

    def test_the_stated_coefficient_is_the_formula_on_n(self):
        n = applicable_fields()
        found = re.search(r"score reduces to `100 − ([\d.]+)m`", squash(MODULE4))
        self.assertIsNotNone(found, "the reduced score `100 − km` is no longer stated")
        self.assertAlmostEqual(WEIGHT_COMPLETENESS * 100.0 / n, float(found.group(1)), delta=1e-9)

    def test_negative_control_a_sample_in_band_only_without_the_key_fails(self):
        """The #757 sample: 2.20 summed absence scored 78.0 on seven fields, 80.75 on eight."""
        old = [0.60, 0.50, 0.45, 0.35, 0.30]
        n = applicable_fields()
        self.assertTrue(in_band(old, n - 1, 70, 79), "the control no longer models the defect")
        self.assertFalse(in_band(old, n, 70, 79),
                         "a sample that reaches the band only with the key left out passed")


class TheWorkedTableIsArithmeticallyTrue(unittest.TestCase):
    """Parses the shipped table and recomputes every row."""

    #: `| label | m | completeness | score |` with bold and % tolerated.
    ROW = re.compile(
        r"^[ \t]*\|\s*(?P<label>[^|]+?)\s*\|\s*\*{0,2}(?P<m>[\d.]+(?:\s*[–-]\s*[\d.]+)?)\*{0,2}\s*\|"
        r"\s*\*{0,2}(?P<c>[\d.]+%?(?:\s*[–-]\s*[\d.]+%?)?)\*{0,2}\s*\|"
        r"\s*\*{0,2}(?P<s>[\d.]+(?:\s*[–-]\s*[\d.]+)?)\*{0,2}\s*\|",
        re.M)

    def rows(self):
        out = []
        for m in self.ROW.finditer(MODULE4.read_text(encoding="utf-8")):
            label = m.group("label")
            if label.startswith("-") or "Gapping" in label:
                continue
            out.append(m)
        return out

    @staticmethod
    def _nums(raw):
        return [float(x) for x in re.findall(r"[\d.]+", raw)]

    def test_the_table_is_found(self):
        self.assertGreaterEqual(
            len(self.rows()), 4,
            "the worked gap-rate table was not located, so this guard asserts nothing")

    def test_every_row_recomputes(self):
        n = applicable_fields()
        for m in self.rows():
            label = m.group("label").strip()
            with self.subTest(row=label[:44]):
                ms, cs, ss = (self._nums(m.group(g)) for g in ("m", "c", "s"))
                for i, mv in enumerate(ms):
                    expected_c = completeness([mv], n)
                    expected_s = score(expected_c)
                    self.assertAlmostEqual(
                        expected_c, cs[i], delta=0.1,
                        msg="row %r: m=%.2f implies completeness %.2f%%, table says %.2f%%"
                            % (label, mv, expected_c, cs[i]))
                    self.assertAlmostEqual(
                        expected_s, ss[i], delta=0.1,
                        msg="row %r: m=%.2f implies score %.1f, table says %.1f"
                            % (label, mv, expected_s, ss[i]))

    def test_the_band_row_actually_spans_the_band(self):
        band = [m for m in self.rows() if "70-79" in m.group("label")]
        self.assertEqual(1, len(band), "the 70-79 band row was not found")
        scores = self._nums(band[0].group("s"))
        self.assertEqual({70.0, 79.0}, set(scores),
                         "the band row's score column does not span 70-79: %s" % scores)


class TheQualityIntentSampleReachesItsBand(unittest.TestCase):
    """The criterion the previous sample failed: gaps consistent with target_band."""

    def sample(self):
        text = MODULE4.read_text(encoding="utf-8")
        i = text.index("quality_intent:")
        return text[i:text.index("```", i)]

    def test_the_sample_is_found(self):
        self.assertIn("target_band", self.sample())

    def test_its_gap_rates_land_inside_its_target_band(self):
        block = self.sample()
        band = re.search(r'target_band:\s*"(?P<lo>\d+)-(?P<hi>\d+)"', block)
        self.assertIsNotNone(band, "target_band not parseable")
        lo, hi = float(band.group("lo")), float(band.group("hi"))
        rates = [float(p) / 100.0 for p in re.findall(r"missing ~(\d+)%", block)]
        self.assertGreaterEqual(
            len(rates), 2,
            "fewer than two absence rates in the sample; a single-field gap cannot reach any "
            "low band, which is the wrong intuition the old sample created")
        n = applicable_fields()
        computed = score(completeness(rates, n))
        self.assertTrue(
            in_band(rates, n, lo, hi),
            "the sample's gaps sum to %.2f of %d fields -> completeness %.1f%% -> score %.1f, "
            "which is OUTSIDE its own target_band %g-%g. That is the defect this spec fixed: a "
            "recorded intent its own gaps could not have produced makes a generation fault "
            "indistinguishable from a scoring fault."
            % (sum(rates), n, completeness(rates, n), computed, lo, hi))

    def test_the_measured_score_field_agrees(self):
        block = self.sample()
        m = re.search(r"measured_score:\s*([\d.]+)", block)
        self.assertIsNotNone(m, "the sample carries no measured_score for the self-check to write")
        rates = [float(p) / 100.0 for p in re.findall(r"missing ~(\d+)%", block)]
        self.assertAlmostEqual(
            score(completeness(rates, applicable_fields())), float(m.group(1)), delta=0.05,
            msg="measured_score disagrees with the sample's own gap rates")

    def test_the_check_paragraph_states_the_computed_figures(self):
        """The prose under the sample quotes its summed absence, completeness and score."""
        rates = [float(p) / 100.0 for p in re.findall(r"missing ~(\d+)%", self.sample())]
        n = applicable_fields()
        found = re.search(
            r"Those (\w+) absence rates sum to \*\*([\d.]+)\*\* of (\w+) applicable fields .*?"
            r"completeness \*\*([\d.]+)%\*\* → score \*\*([\d.]+)\*\*", squash(MODULE4))
        self.assertIsNotNone(found, "the check paragraph under the sample was not located")
        count, m, fields, c, s = found.groups()
        self.assertEqual(len(rates), WORDS[count])
        self.assertEqual(n, WORDS[fields])
        self.assertAlmostEqual(sum(rates), float(m), delta=1e-9)
        self.assertAlmostEqual(completeness(rates, n), float(c), delta=0.05)
        self.assertAlmostEqual(score(completeness(rates, n)), float(s), delta=0.05)


class TheSingleFieldCeilingIsStated(unittest.TestCase):
    def test_it_says_no_single_field_reaches_the_band(self):
        self.assertRegex(
            squash(MODULE4), r"(?i)No single field can get you there, at any rate",
            "the specific wrong intuition the old example created is not closed")

    def test_the_ceiling_arithmetic_is_right(self):
        """A field absent from every record costs 0.70 * 100/n, on n counted with the key."""
        n = applicable_fields()
        found = re.search(r"`0\.70 × 100/n` — ([\d.]+) points on an? (\w+)-field source",
                          squash(MODULE4))
        self.assertIsNotNone(found, "the single-field ceiling is no longer stated with its figure")
        self.assertEqual(n, WORDS[found.group(2)],
                         "the ceiling is stated on a field count other than non-key plus the key")
        self.assertAlmostEqual(WEIGHT_COMPLETENESS * 100.0 / n, float(found.group(1)), delta=1e-9)


class TheSelfCheckIsRequired(unittest.TestCase):
    def test_generation_verifies_against_the_recorded_band(self):
        self.assertRegex(
            squash(MODULE4), r"(?i)Verify the generated data against the band before this module closes",
            "nothing requires the generator to check its output against the band it recorded")

    def test_it_widens_the_gaps_rather_than_adjusting_a_score(self):
        self.assertRegex(
            squash(MODULE4), r"(?i)widen the gaps and regenerate\*\* — never adjust a score",
            "the self-check does not forbid adjusting the score, which would falsify a "
            "measurement the Bootcamper is told is real (INV-239)")


if __name__ == "__main__":
    unittest.main()
