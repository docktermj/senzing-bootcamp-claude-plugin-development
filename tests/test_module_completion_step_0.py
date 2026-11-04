"""Module completion's Step 0 catches a required step the module never ran (#856).

One graduation audit found four required steps that never happened and left no trace: a
directing step in two modules, every worked steer, Discover's step 4a-pairs, and the silent
filing of a reversed decision (#855). Module completion then masked the first: it set an unset
`directing_steps` value to `none`, the value a step that never arose gets. #856 makes each of
those steps leave a record, and adds a Step 0 to `module-completion.md`, before Step 1's batched
write, that reads the records and either runs the step late or records the skip.

What this file pins, in `module-completion.md` (from its `## Step 0:` heading to `## Step 1:`):

1. **The frame.** Step 0 sits between the opening and Step 1, and the opening names it. It has
   three sub-steps in a fixed order: 0a the directing step, 0b the worked steer and the reversal
   filings, 0c Discover's step 4a-pairs. Each states its **Condition**, its **Action** and its
   **Turn** handling.
2. **Turn handling.** A sub-step that runs a step ending on a 👉 ends the turn on it (INV-251);
   the next turn finishes that step, resumes at the following sub-step, then Step 1.
3. **Re-entry (INV-006).** A resumed session runs Step 0 again from 0a, and each finished
   sub-step finds its record and does nothing, so it re-enters at the first sub-step whose record
   is still missing; a pending 👉 is re-presented, not re-asked; once Step 1 has added the name
   token to `modules_completed`, Step 0 does not run again.
4. **0a.** Unset `directing_steps.<token>` in the three directing modules: Data processing runs
   step 21's directing step late; the other two record `skipped`, carried by Step 1's write, and
   do not run the step late.
5. **0b.** `steer_triggers.<token>`: in an Act 2 hands-on module with no worked-steer note in the
   checkpoint, the first entry's steer is shown late with no ask-first question, even from Data
   processing on; in every module, each `filed: false` reversal is filed silently through
   `feedback.md` → "Silent in-run append", and a failed filing does not block (INV-373).
6. **0c.** In Query, Visualize and Discover, when `discover_phase` is not `"skipped"` and
   `steps["4a-pairs"]` is missing or not `completed`, step 4a-pairs runs now with all of its
   rules, an `in_progress` record resuming at its next pair, and the last reveal goes in the turn
   that continues module completion, not before step 4b.
7. **Single statement (INV-300).** Each sub-step points at the owner of its record, citing the
   owner's invariant (`ground-rules.md` → "Directing steps", INV-354; → "Worked steers",
   INV-352; `phase2-discover.md` → "Step 4a-pairs: Same entity or not?", INV-357), and carries no
   copy of what the owner defines: the `skipped` form's wording, the `steer_triggers` entry's
   shape, or the 4a-pairs record's shape.

The checks are pure functions over the file's text, so each one also runs on a mutated copy as
its negative control (`TheChecksCatchARegression`). Each mutation must make the check report the
problem it targets, not merely some problem.

⛔ **What this cannot establish:** that a live guide runs Step 0, shows a late steer or runs the
pairs late. Those are properties of a conversation; only `dry-run` phase 3 observes them. This
pins that the skill file STATES them.

The definitions Step 0 points at are pinned where they live: `tests/test_directing_steps.py`
(`skipped`, the fourth form, the site-only `none`), `tests/test_worked_steers.py`
(`steer_triggers`, the `filed` mark), `tests/test_predictions_before_results.py` (the empty
pairs record) and `tests/test_module_completion_step1_lists_every_write.py` (Step 1's write).

Source issue: #856 (part of #855). Invariants applied: INV-354, INV-352, INV-357, INV-413,
INV-300, INV-006, INV-251, INV-225, INV-373, INV-012.

Stdlib only; shipped markdown read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETION = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
              / "module-completion.md")

SUB_STEPS = (("0a", "### 0a. The directing step"),
             ("0b", "### 0b. The worked steer and the reversal filings"),
             ("0c", "### 0c. Discover's step 4a-pairs"))
PARTS = ("**Condition.**", "**Action", "**Turn.**")


def read():
    return COMPLETION.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def step0(text):
    """The text of Step 0, from its heading to Step 1's ('' when absent)."""
    match = re.search(r"^## Step 0:.*?(?=^## Step 1:)", text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else ""


def sub_step(section, key):
    """One sub-step's text, from its heading to the next sub-step's or the end of Step 0."""
    headings = [h for _, h in SUB_STEPS]
    heading = dict(SUB_STEPS)[key]
    start = section.find(heading)
    if start < 0:
        return ""
    ends = [section.find(h, start + 1) for h in headings if h != heading]
    ends = [e for e in ends if e > start]
    return section[start:min(ends)] if ends else section[start:]


def require(text, where, clauses):
    flat = squash(text)
    return ["%s does not state %s" % (where, what)
            for what, pattern in clauses.items() if not re.search(pattern, flat)]


FRAME = {
    "that it runs before Step 1's batched write": r"before Step 1's batched write",
    "that what it records lands before the recap and the transition 👉":
        r"lands before the recap is appended and before the transition 👉",
    "that the sub-steps run in order": r"Run its three sub-steps in order",
    "that a sub-step whose condition fails asks nothing":
        r"a sub-step whose condition does not hold does nothing and asks nothing",
    "that a step ending on a 👉 ends the turn (INV-251)":
        r"When a sub-step runs a step that ends on a 👉, the turn ends on that 👉\*\* \(INV-251\)",
    "that the next turn resumes at the following sub-step, then Step 1":
        r"The next turn finishes that step, then resumes at the following sub-step, then Step 1",
    "where a resumed session re-enters (INV-006)":
        r"Where a resumed session re-enters \(INV-006\)",
    "that a resume runs Step 0 again from 0a": r"a resumed session runs Step 0 again from 0a",
    "that a finished sub-step finds its record and does nothing":
        r"every sub-step that already finished finds its record and does nothing",
    "the re-entry point": r"re-enters at the first sub-step whose record is still missing, or at "
                          r"Step 1 when none is",
    "that a resume re-records 0a's skipped without running anything twice":
        r"The one record a resume can find unwritten is 0a's `skipped`, which Step 1's write "
        r"carries: 0a records it again, which asks nothing and runs nothing twice",
    "that a pending 👉 is re-presented, never asked twice":
        r"re-presented as the ask-once rule says, never asked a second time",
    "that Step 0 is over once Step 1 has written modules_completed":
        r"Once Step 1's write has added this module's name token to `modules_completed`, Step 0 "
        r"is over",
}

ZERO_A = {
    "the three directing modules": r"Data Quality, Mapping, and Transformation, Data processing, "
                                   r"or Query, Visualize and Discover",
    "the unset condition": r"`directing_steps\.<module name token>` in "
                           r"`config/bootcamp_progress\.json` is still unset",
    "the pointer to its owner (INV-300, INV-354)":
        r"stated once in `ground-rules\.md` → \"Directing steps\" \(INV-300, INV-354\)",
    "Data processing runs step 21 late": r"\*\*Action in Data processing\.\*\* Run step 21's "
                                         r"directing step now",
    "the late step is its 👉, lookup and comparison, recorded as at the site":
        r"its 👉, then the lookup and the comparison, recorded as at the site",
    "the other two record skipped": r"\*\*Action in the other two\.\*\* Record `skipped`",
    "Step 1's write carries skipped": r"Step 1's batched write carries it",
    "the other two do not run late": r"Do not run the step late",
    "the late step ends the turn on its 👉": r"late directing step ends this turn on its 👉",
    "the next turn resumes at 0b": r"resumes at 0b",
    "recording skipped asks nothing": r"Recording `skipped` asks nothing: go on to 0b in the "
                                      r"same turn",
}

ZERO_B = {
    "the record is steer_triggers": r"`steer_triggers\.<module name token>` has entries",
    "the pointer to its owner (INV-300, INV-352)":
        r"stated once in `ground-rules\.md` → \"Worked steers\" \(INV-300, INV-352\)",
    "the late steer is for Act 2 hands-on modules only":
        r"the late steer: in an Act 2 hands-on module only",
    "the late steer needs no checkpoint note": r"carries no worked-steer note for this module",
    "the late steer is the first entry's": r"show the first entry's two-line steer now",
    "the late steer has no ask-first question, even from Data processing on":
        r"with no ask-first question, even from Data processing on",
    "the late steer adds its checkpoint note": r"Add the checkpoint note that section requires",
    "the filings run in every module": r"the filings: in every module",
    "each filed: false reversal is filed": r"File each reversal entry with `filed: false` now",
    "the filing is silent, through the silent in-run append":
        r"silently, through `feedback\.md` → \"Silent in-run append\"",
    "a failed filing does not block (INV-373)": r"does not block completion \(INV-373\)",
    "the steer is non-yielding and required at every verbosity":
        r"non-yielding and required output at every verbosity",
    "its writes land before any 👉 0c asks": r"before any 👉 0c asks",
}

ZERO_C = {
    "the module is Query, Visualize and Discover": r"The module is Query, Visualize and Discover",
    "an explicitly skipped Discover is exempt": r"`module_7_query\.discover_phase` is not "
                                                r"`\"skipped\"`",
    "a missing or incomplete record": r"`module_7_query\.steps\[\"4a-pairs\"\]` is missing or its "
                                      r"`status` is not `completed`",
    "the pointer to its owner (INV-300, INV-357)":
        r"`\.\./module-07-query-visualize-discover/phase2-discover\.md` → \"Step 4a-pairs: Same "
        r"entity or not\?\" \(INV-300, INV-357\)",
    "the step runs now with all its rules": r"Run step 4a-pairs now, with all of its rules",
    "the already-shown exclusion applies": r"the already-shown-entities exclusion included",
    "an in_progress record resumes at its next pair":
        r"An `in_progress` record resumes at its next pair",
    "each pair's 👉 ends its turn": r"Each pair's 👉 ends its turn",
    "the last reveal is not before step 4b": r"After the last pair the next 👉 is not step 4b's",
    "the last reveal continues module completion":
        r"the last reveal goes in the turn that continues module completion at Step 1",
}

#: What only the owners define; a copy here would fork the rule (INV-300).
OWNER_ONLY = {
    "the skipped form's wording": r"was skipped, so you were not asked to direct it",
    "the steer_triggers entry's shape": r"\"kind\": \"failure\|reversal\"",
    "the 4a-pairs record's shape": r"\"prediction\": \"same\|different\|skipped\"",
    "the steer's first line": r"What went wrong: \{",
}


def problems(text):
    section = step0(text)
    if not section:
        return ["module-completion.md has no `## Step 0:` before `## Step 1:`"]
    found = []
    opening = text[:text.find("## Step 0:")]
    if "Step 0 first catches a required step this module never ran" not in squash(opening):
        found.append("the opening does not name Step 0")
    starts = [section.find(h) for _, h in SUB_STEPS]
    if min(starts) < 0:
        found.append("Step 0 does not carry all three sub-steps")
        return found
    if starts != sorted(starts):
        found.append("Step 0's sub-steps are not in the order 0a, 0b, 0c")
    found += require(section[:starts[0]], "Step 0", FRAME)
    for (key, _), clauses in zip(SUB_STEPS, (ZERO_A, ZERO_B, ZERO_C)):
        body = sub_step(section, key)
        for part in PARTS:
            if part not in body:
                found.append("%s has no %s part" % (key, part.strip("*.")))
        found += require(body, key, clauses)
    flat = squash(section)
    for what, pattern in OWNER_ONLY.items():
        if re.search(pattern, flat):
            found.append("Step 0 restates %s, which its owner defines (INV-300)" % what)
    if re.search(r"^👉 \*\*", section, re.MULTILINE):
        found.append("Step 0 pins a 👉 of its own")
    return found


class StepZeroIsStated(unittest.TestCase):
    def test_the_shipped_step_0(self):
        self.assertEqual([], problems(read()))

    def test_it_sits_before_step_1(self):
        text = read()
        self.assertLess(text.find("## Step 0:"), text.find("## Step 1:"))
        self.assertGreater(text.find("## Step 0:"), 0)


class TheChecksCatchARegression(unittest.TestCase):
    """Each mutation must produce the problem it targets."""

    def assertReports(self, mutated, needle):
        self.assertNotEqual(mutated, read(), "the mutation no longer applies")
        found = problems(mutated)
        self.assertTrue(any(needle in p for p in found),
                        "expected a problem containing %r, got %r" % (needle, found))

    def replace(self, old, new):
        """Replace ``old`` once, matching any wrap of it (INV-346)."""
        pattern = r"\s+".join(re.escape(word) for word in old.split())
        return re.sub(pattern, lambda _: new, read(), count=1)

    # --- the frame ---------------------------------------------------------------------------

    def test_step_0_removed(self):
        text = re.sub(r"^## Step 0:.*?(?=^## Step 1:)", "", read(), flags=re.MULTILINE | re.DOTALL)
        self.assertReports(text, "has no `## Step 0:`")

    def test_step_0_moved_after_step_1(self):
        section = step0(read())
        text = read().replace(section, "").replace("## Step 2: Append the recap section",
                                                   section + "## Step 2: Append the recap section")
        self.assertReports(text, "has no `## Step 0:` before `## Step 1:`")

    def test_the_opening_forgets_step_0(self):
        self.assertReports(self.replace("Step 0 first catches a required step this module never "
                                        "ran. ", ""), "the opening does not name Step 0")

    def test_sub_steps_out_of_order(self):
        section = step0(read())
        a, c = sub_step(section, "0a"), sub_step(section, "0c")
        swapped = section.replace(a, "\0").replace(c, a).replace("\0", c)
        self.assertReports(read().replace(section, swapped), "not in the order 0a, 0b, 0c")

    def test_a_sub_step_dropped(self):
        section = step0(read())
        self.assertReports(read().replace(sub_step(section, "0b"), ""),
                           "does not carry all three sub-steps")

    def test_the_turn_ending_rule_dropped(self):
        self.assertReports(self.replace("the turn ends on that 👉** (INV-251)",
                                        "the guide continues** (INV-251)"),
                           "ends the turn (INV-251)")

    def test_the_resume_point_dropped(self):
        self.assertReports(self.replace("then resumes at the following sub-step, then Step 1",
                                        "then goes to Step 1"),
                           "resumes at the following sub-step")

    def test_the_re_entry_rule_dropped(self):
        self.assertReports(self.replace("re-enters at the first sub-step whose record is\nstill "
                                        "missing", "re-enters at 0a"), "the re-entry point")

    def test_the_skipped_re_record_dropped(self):
        self.assertReports(self.replace("0a records it again, which asks nothing and runs nothing "
                                        "twice", "0a runs again"),
                           "re-records 0a's skipped")

    def test_step_0_runs_again_after_step_1(self):
        self.assertReports(self.replace("Step 0 is over, and a resume past that point does not "
                                        "run it", "Step 0 runs again"),
                           "Step 0 is over once Step 1")

    def test_a_part_dropped(self):
        section = step0(read())
        body = sub_step(section, "0c")
        self.assertReports(read().replace(body, body.replace("**Turn.**", "**Then.**")),
                           "0c has no Turn part")

    # --- 0a ----------------------------------------------------------------------------------

    def test_data_processing_records_skipped_instead(self):
        self.assertReports(self.replace("**Action in Data processing.** Run step 21's directing "
                                        "step now", "**Action in Data processing.** Record "
                                        "`skipped`"), "Data processing runs step 21 late")

    def test_the_other_two_run_late(self):
        self.assertReports(self.replace("Do not run the\n  step late.", "Run the step late."),
                           "the other two do not run late")

    def test_unset_defaults_to_none_again(self):
        self.assertReports(self.replace("**Action in the other two.** Record `skipped`",
                                        "**Action in the other two.** Record `none`"),
                           "the other two record skipped")

    def test_0a_loses_its_pointer(self):
        self.assertReports(self.replace('"Directing steps" (INV-300, INV-354).\n- **Action in',
                                        '"Directing steps".\n- **Action in'),
                           "0a does not state the pointer to its owner")

    # --- 0b ----------------------------------------------------------------------------------

    def test_the_late_steer_asks_first(self):
        self.assertReports(self.replace("with no\n  ask-first question, even from Data processing "
                                        "on", "with the\n  ask-first question from Data "
                                        "processing on"), "has no ask-first question")

    def test_the_late_steer_shown_in_act_1(self):
        self.assertReports(self.replace("the late steer: in an Act 2 hands-on module only",
                                        "the late steer: in every module"),
                           "Act 2 hands-on modules only")

    def test_a_second_steer_after_one_was_shown(self):
        self.assertReports(self.replace("carries no worked-steer note for\n  this module, ", ""),
                           "needs no checkpoint note")

    def test_the_filings_dropped(self):
        self.assertReports(self.replace("File each reversal entry with `filed: false` now",
                                        "Leave each reversal entry with `filed: false`"),
                           "each filed: false reversal is filed")

    def test_a_failed_filing_blocks(self):
        self.assertReports(self.replace("does not block completion (INV-373)",
                                        "stops completion"), "does not block (INV-373)")

    def test_0b_loses_its_pointer(self):
        self.assertReports(self.replace('"Worked steers" (INV-300, INV-352).\n- **Action',
                                        '"Worked steers".\n- **Action'),
                           "0b does not state the pointer to its owner")

    def test_0b_copies_the_entry_shape(self):
        self.assertReports(self.replace("has entries.", 'has entries, each `{"kind": '
                                        '"failure|reversal", "evidence": "…"}`.'),
                           "restates the steer_triggers entry's shape")

    # --- 0c ----------------------------------------------------------------------------------

    def test_a_skipped_discover_not_exempt(self):
        self.assertReports(self.replace("`module_7_query.discover_phase` is\n  not `\"skipped\"`, "
                                        "and ", ""), "an explicitly skipped Discover is exempt")

    def test_only_a_missing_record_counts(self):
        self.assertReports(self.replace("is missing or its `status` is not\n  `completed`",
                                        "is missing"), "a missing or incomplete record")

    def test_the_pairs_restart(self):
        self.assertReports(self.replace("An `in_progress` record resumes at its next pair",
                                        "An `in_progress` record starts again at item 1"),
                           "an in_progress record resumes at its next pair")

    def test_the_last_reveal_goes_before_step_4b(self):
        self.assertReports(self.replace("After the last pair the next 👉 is not\n  step 4b's",
                                        "After the last pair the next 👉 is\n  step 4b's"),
                           "the last reveal is not before step 4b")

    def test_the_exclusion_dropped(self):
        self.assertReports(self.replace(", the already-shown-entities exclusion\n  included", ""),
                           "the already-shown exclusion applies")

    def test_0c_copies_the_record_shape(self):
        self.assertReports(self.replace("An `in_progress` record",
                                        'Each pair is `{"prediction": "same|different|skipped"}`. '
                                        "An `in_progress` record"),
                           "restates the 4a-pairs record's shape")

    def test_0c_loses_its_pointer(self):
        self.assertReports(self.replace('not?" (INV-300, INV-357).', 'not?".'),
                           "0c does not state the pointer to its owner")

    def test_step_0_pins_a_question(self):
        self.assertReports(self.replace("### 0a. The directing step\n",
                                        "### 0a. The directing step\n\n👉 **Ready?**\n"),
                           "pins a 👉 of its own")


if __name__ == "__main__":
    unittest.main()
