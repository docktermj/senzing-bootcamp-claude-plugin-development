"""Module 4 Step 8a's License Key gate is described the way it runs (#780).

The production-readiness audit of 2026-10-22 (sweep C) found the gate described three ways,
none of them what Step 8a does:

1. **Step 8a's total pointed at a definition that does not exist.** Sub-step 1 computed the
   collected total "per the canonical framing at the top of this module", and the framing
   defines no total. After a Step 6 smaller-slice choice, that reading can count the unsampled
   figure and ask the License Key question the Bootcamper just answered by sampling. 9137ee18
   (#617) fixed the same pointer for Step 8b only, pointing it at Step 8b sub-step 4's
   sample-aware `collected_total`; Step 8a now points there too.
2. **Module 1 said leaving `license_guidance_deferred` unset suppresses Step 8a.** Step 8a reads
   that flag and clears it, but never branches on it: it decides from the measured collected
   total. So the flag is Module 1's recorded expectation, and a wrong comparison in Module 1
   records a wrong expectation. (A measured `license_record_limit` above the dataset size does
   suppress the gate, through Step 8a's volume skip. That claim is true and is not checked here.)
3. **Module 1 promised that Module 4 reconciles `license_stated_limit`.** Nothing reads that
   field; it stays the Bootcamper's claim that no gate reads (INV-278).
4. **Three lines placed the License Key prompt "at the start of Data collection".** INV-093's
   2026-10-22 note reads that as Data collection's Step 8a, after every source is collected
   and its volume measured, and before any load, so each line now names Step 8a.

Each check below runs once against the shipped text and once against the pre-fix text, which
must fail it (negative control).

⚠️ **This checks wording, not the conversation.** Whether a live Step 8a counts the sampled
figure is a conversational outcome for `dry-run` phase 3.

Source: issue #780 (production-readiness audit 2026-10-22, sweep C).

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _corpus import corpus_files  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_1 = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"

#: Step 8b sub-step 1's pointer, which Step 8a sub-step 1 now matches.
POINTER = "sample-aware definition Step 8b sub-step 4 gives for `collected_total`"

#: The pre-fix texts, kept so each negative control tests the real defect.
PRE_FIX_8A = (
    "1. **Read state and compute the total.** Read `license_record_limit` from\n"
    "   `config/bootcamp_progress.json`. Compute the collected total record count from\n"
    "   `config/data_sources.yaml` (per the canonical framing at the top of this module). If "
    "the total\n   cannot be computed, note the warning and proceed to Step 8b (non-blocking).\n")
PRE_FIX_DEFERRED = (
    "⛔ **What this comparison decides.** Leaving `license_guidance_deferred` unset "
    "**suppresses**\nModule 4's Step 8a License Key gate — the single volume-gated prompt in "
    "the whole bootcamp.\n")
PRE_FIX_PICK_UP = (
    "This step only records whether the anticipated\nvolume looks likely to exceed the limit, so "
    "Module 4's gate can pick it up (`license_guidance_deferred`).\n")
PRE_FIX_STATED = (
    "⛔ **(INV-278) Record a stated entitlement as `license_stated_limit` in\n"
    "`config/bootcamp_preferences.yaml`, and say plainly that no gate reads it.** It is the "
    "Bootcamper's claim, worth keeping — it is why they\nsized the scenario the way they did, and "
    "Module 4 can reconcile it against the measurement later —\nbut it is a *statement*.\n")
PRE_FIX_START = (
    "> Senzing License Key prompt is presented once, at the start of Data collection (Module 4),\n"
    "> per INV-093.\n")


def _read(path):
    return path.read_text(encoding="utf-8")


def _flat(text):
    """Collapse whitespace so a phrase wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


def _shipped_markdown():
    return corpus_files("plugins/senzing-bootcamp", suffixes=(".md",))


def step_8a_sub_step_1(text):
    """Step 8a sub-step 1, from its bold label to its first rule or sub-step 2."""
    match = re.search(r"^1\. \*\*Read state and compute the total\.\*\*", text, re.M)
    if match is None:
        return None
    rest = text[match.start():]
    stop = re.search(r"^   ⛔|^2\. ", rest, re.M)
    return _flat(rest[: stop.start()] if stop else rest)


def step_8b_sub_step_1(text):
    match = re.search(r"^1\. \*\*Read the persisted inputs\.\*\*", text, re.M)
    if match is None:
        return None
    rest = text[match.start():]
    stop = re.search(r"^   - ", rest, re.M)
    return _flat(rest[: stop.start()] if stop else rest)


def pointer_problems(sub_step):
    """Every way a sub-step 1 fails to point at the one sample-aware total."""
    if sub_step is None:
        return ["sub-step 1 not found"]
    found = []
    if POINTER not in sub_step:
        found.append("does not point at Step 8b sub-step 4's `collected_total`")
    if "canonical framing" in sub_step:
        found.append("points at the canonical framing, which defines no total")
    if "record_count" in sub_step:
        # Naming the field makes the read look like a registry write to
        # test_per_source_figures_are_reconciled.py, as 9137ee18 recorded for Step 8b.
        found.append("names the `record_count` field")
    return found


def _sentences(text):
    return re.split(r"(?<=[.!?])\s+", _flat(text))


#: A positive suppression claim: "suppresses" not directly negated.
SUPPRESSES = re.compile(r"(?<!not )(?<!never )\bsuppress(?:es|ed|ing)?\b", re.I)
PICK_UP = re.compile(r"(?i)gate can pick it up")


def deferred_flag_claims(text):
    """Sentences that give `license_guidance_deferred` an effect on Step 8a it does not have."""
    return [s for s in _sentences(text)
            if "license_guidance_deferred" in s and (SUPPRESSES.search(s) or PICK_UP.search(s))]


RECONCILE = re.compile(r"(?i)(module 4|data collection|step 8a)[^.]{0,80}\breconcil")


def stated_limit_reconcile_claims(text):
    """Paragraphs naming `license_stated_limit` that say Module 4 reconciles it."""
    return [_flat(p)[:160] for p in re.split(r"\n\s*\n", text)
            if "license_stated_limit" in p and RECONCILE.search(_flat(p))]


START = re.compile(r"(?i)\bstart of Data collection\b")


def start_claims(text):
    return [m.group(0) for m in START.finditer(_flat(text))]


class StepEightAUsesTheSampleAwareTotal(unittest.TestCase):
    def test_step_8a_points_at_step_8b_sub_step_4(self):
        self.assertEqual([], pointer_problems(step_8a_sub_step_1(_read(MODULE_4))))

    def test_step_8b_does_not_point_at_the_framing(self):
        sub_step = step_8b_sub_step_1(_read(MODULE_4))
        self.assertIsNotNone(sub_step, "Step 8b sub-step 1 not found; the check is vacuous")
        self.assertNotIn("canonical framing", sub_step)
        self.assertIn("sample-aware definition sub-step 4 gives for `collected_total`", sub_step)

    def test_the_definition_still_sits_at_step_8b_sub_step_4(self):
        self.assertIn("each source's `sample:` `record_count` where it has a `sample:` block",
                      _flat(_read(MODULE_4)))


class TheDeferralFlagIsARecord(unittest.TestCase):
    def test_the_sites_are_found(self):
        """A scan that matches nothing certifies nothing."""
        holders = [p for p in _shipped_markdown() if "license_guidance_deferred" in _read(p)]
        self.assertIn(MODULE_1, holders)
        self.assertIn(MODULE_4, holders)

    def test_no_shipped_sentence_says_the_flag_suppresses_the_gate(self):
        bad = []
        for path in _shipped_markdown():
            for sentence in deferred_flag_claims(_read(path)):
                bad.append(f"{path.relative_to(REPO_ROOT)}: {sentence[:160]}")
        self.assertEqual(
            [], bad,
            "a shipped sentence gives `license_guidance_deferred` an effect on Module 4's "
            "Step 8a gate. Step 8a reads and clears the flag but decides from the measured "
            "collected total:\n  " + "\n  ".join(bad))

    def test_module_1_states_what_the_comparison_decides(self):
        flat = _flat(_read(MODULE_1))
        self.assertIn("The comparison records Module 1's expectation in "
                      "`license_guidance_deferred`", flat)
        self.assertIn("It does not decide whether Module 4's Step 8a License Key gate fires",
                      flat)


class TheStatedLimitIsReadByNoGate(unittest.TestCase):
    def test_no_shipped_paragraph_promises_a_module_4_reconcile(self):
        bad = []
        for path in _shipped_markdown():
            for para in stated_limit_reconcile_claims(_read(path)):
                bad.append(f"{path.relative_to(REPO_ROOT)}: {para}")
        self.assertEqual(
            [], bad,
            "a shipped paragraph says Module 4 reconciles `license_stated_limit`. Nothing reads "
            "that field; it is the Bootcamper's claim that no gate reads (INV-278):\n  "
            + "\n  ".join(bad))

    def test_module_1_still_says_no_gate_reads_it(self):
        flat = _flat(_read(MODULE_1))
        i = flat.index("license_stated_limit")
        self.assertIn("no gate reads it", flat[i:i + 400])


class ThePromptIsPlacedAtStepEightA(unittest.TestCase):
    def test_no_shipped_line_says_start_of_data_collection(self):
        bad = []
        for path in _shipped_markdown():
            if start_claims(_read(path)):
                bad.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            [], bad,
            "a shipped file places the License Key prompt at the start of Data collection. Per "
            "INV-093's 2026-10-22 note it runs at Data collection's Step 8a, after every source "
            "is collected and measured, and before any load: " + ", ".join(bad))

    def test_each_corrected_site_names_step_8a(self):
        sites = {
            MODULE_1: (r"does not ask about a Senzing License Key here\.\*\*", 1),
            MODULE_2: (r"License Key prompt is presented once|volume-gated gate at", 2),
        }
        for path, (anchor, count) in sites.items():
            flat = _flat(_read(path))
            hits = [m.start() for m in re.finditer(anchor, flat)]
            with self.subTest(file=path.name):
                self.assertEqual(count, len(hits), f"expected {count} site(s) in {path.name}")
                for i in hits:
                    self.assertIn("Data collection's Step 8a", flat[i:i + 200])


class NegativeControl(unittest.TestCase):
    def test_the_pre_fix_8a_pointer_fails(self):
        found = pointer_problems(step_8a_sub_step_1(PRE_FIX_8A))
        self.assertIn("points at the canonical framing, which defines no total", found)
        self.assertIn("does not point at Step 8b sub-step 4's `collected_total`", found)

    def test_a_pointer_naming_the_field_fails(self):
        text = PRE_FIX_8A.replace(
            "(per the canonical framing at the top of this module)",
            "by the " + POINTER + ", each source's `record_count`")
        self.assertEqual(["names the `record_count` field"],
                         pointer_problems(step_8a_sub_step_1(text)))

    def test_the_pre_fix_suppression_claim_fails(self):
        self.assertEqual(1, len(deferred_flag_claims(PRE_FIX_DEFERRED)))

    def test_the_pre_fix_pick_up_claim_fails(self):
        self.assertEqual(1, len(deferred_flag_claims(PRE_FIX_PICK_UP)))

    def test_a_negated_suppression_passes(self):
        text = "Leaving `license_guidance_deferred` unset does not suppress Step 8a."
        self.assertEqual([], deferred_flag_claims(text))

    def test_the_pre_fix_reconcile_promise_fails(self):
        self.assertEqual(1, len(stated_limit_reconcile_claims(PRE_FIX_STATED)))

    def test_the_pre_fix_start_line_fails(self):
        self.assertEqual(["start of Data collection"], start_claims(PRE_FIX_START))


if __name__ == "__main__":
    unittest.main()
