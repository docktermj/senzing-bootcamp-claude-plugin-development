"""Module 4 sub-step 6 option 3 names the `eval_license` field, not the EULA prose, as the channel.

Option 3 told the guide to call
`search_docs(query='temporary evaluation license for a dataset larger than the default limit')`,
read *"the top hit"* — the EULA's *Senzing Non-Production License* section — and **present the
returned guidance on the external channel**. The channel therefore had to be inferred from
license-agreement prose, which states terms and names no route.

The server now serves the route itself. The same response carries a **top-level** `eval_license`
object, a sibling of `metadata` and `results`, whose `message` names a self-service way to a free
evaluation license and whose `url` is its address. ⛔ **It is not a search hit**, so a guide
following the old sentence to the letter — read the top hit — never looks at it. That is the
failure shape **INV-213** exists for one level down: a fact read off the wrong route, where the
route that carries it was never asked.

What the step now says, and what this file asserts it says:

* **the field, before the results** — `eval_license.message` and `eval_license.url` are read
  before `results[]`, with the reason (a top-level field, not a hit, so the top-hit reader misses
  it); the `message` is relayed **verbatim** as the external channel, with its `url`;
* **the terms stay the terms** — the EULA top hit is kept as what accompanies that channel (the
  license period, the DSR cap, the "time bomb" and the buffer clauses), not as the channel;
* **the zero-disclosure line** — this route asks the bootcamper for nothing, which is the
  distinction sub-step 6a turns on: option 4's in-flow request is the one step that sends their
  name and work email off the machine (INV-135, INV-321), and option 3 is now its
  no-personal-details counterpart;
* **the absent-field fallback (INV-125)** — when the call fails or the response carries no
  `eval_license`, the step falls back to exactly what it did before the field existed and says
  which path produced what is presented. ⛔ **A missing advisory field is never reported as an
  unavailable license route**, which is the way a fallback turns a working path into a dead end;
* **what does not change** — the option-3/option-4 split is not re-opened (INV-006), the runtime
  sourcing rule stands (INV-080), and `license: evaluation` / `license_key_requested` recording is
  untouched.

⛔ **Every check is a function of the file's text, and each negative control runs the SAME check
on a copy mutated back toward the text that shipped before this change** (INV-265). A check that
cannot find the step's passage is a FAILURE, never a skip: a scan of a section that moved
certifies nothing.

⚠️ **Every phrase is matched across line wraps (INV-346):** the passage is flattened before
matching, and `ReWrapping` re-flows it to one word per line and asserts the checks still pass.

⚠️ **What this establishes:** the skill file *states* these rules. It **cannot** establish that a
live guide reads the field, relays it verbatim, or falls back as written — only `dry-run` phase 3
observes that. It also establishes nothing about the server: that `eval_license` is returned is a
runtime fact, re-verified against the live server when this change was made and recorded in
`specs/IMPLEMENTED.md`, never asserted offline (INV-108).

Source issue: #679. Invariants: INV-006, INV-056, INV-080, INV-108, INV-125, INV-135, INV-213,
INV-265, INV-291, INV-300, INV-321, INV-346.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"

STEP_START = "6. **Obtain a Senzing License Key"
STEP_END = "### 6a."

#: The route option 3 calls. Its measured record lives in `test_prescribed_search_queries.py`;
#: this file only checks that the step still makes the call it reads the field from.
QUERY_CALL = ("`search_docs(query='temporary evaluation license for a dataset larger than the "
              "default limit')`")


def plain(text):
    return text.replace("**", "")


def flat(text):
    """Passage text as a reader sees it: no emphasis, no code ticks, no line wraps."""
    text = plain(text).replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def read():
    return MODULE_4.read_text(encoding="utf-8")


def find(text, phrase, start=0):
    """The first match of `phrase` at or after `start`, across line wraps (INV-346).

    Only whitespace is relaxed, so the emphasis and punctuation in a phrase still have to be
    there — and the offsets it returns index `text` itself, never a normalized copy.
    """
    pattern = r"\s+".join(re.escape(word) for word in phrase.split())
    return re.compile(pattern).search(text, start)


def step(text):
    """Sub-step 6 up to sub-step 6a, or None when the step moved (INV-265)."""
    opening = find(text, STEP_START)
    if opening is None:
        return None
    closing = find(text, STEP_END, opening.end())
    return text[opening.start():closing.start() if closing else len(text)]


def missing(passage, phrases):
    """Each phrase the passage does not state, matched across wraps (INV-346)."""
    body = flat(passage)
    return [phrase for phrase in phrases if flat(phrase) not in body]


# ------------------------------------------------------------------------------------- checks


FIELD_PHRASES = (
    "Read `eval_license.message` and `eval_license.url` from that response BEFORE `results[]`",
    "`eval_license` is a **top-level field**, a sibling of `metadata` and `results`",
    "not a search hit",
    "a guide that reads only the top hit never sees it",
    "relay its `message` verbatim",
    "together with its `url`",
)

TERMS_PHRASES = (
    "keep the top hit",
    "the EULA's *Senzing Non-Production License* section",
    "as the **terms that accompany that channel**",
)

NO_PII_PHRASES = (
    "This route asks the bootcamper for nothing",
    "Unlike option 4's in-flow request (sub-step 6a)",
    "transmits no name, no work email address and nothing else about them off their machine",
    "(INV-135, INV-321)",
    "the no-personal-details counterpart to that path",
)

FALLBACK_PHRASES = (
    "When the call fails, or the response carries no `eval_license`, fall back to the top hit "
    "alone",
    "present its guidance and take the external channel from it",
    "exactly as this step did before the field existed",
    "say which of the two produced what is presented (INV-125)",
    "The field is advisory",
    "a license route MUST NOT be reported as unavailable because `eval_license` was missing",
)

UNCHANGED_PHRASES = (
    "Give guidance for the chosen path only",
    "never re-offer the paths (INV-006)",
    "**Option 4** goes to sub-step 6a",
    "Source the request channel's address and any capacity/validity figures from MCP at runtime "
    "rather than this file",
    "Record `license: evaluation` when no custom key is applied",
)


def field_problems(text):
    """Option 3 names the field and says to read it before the results list."""
    passage = step(text)
    if passage is None:
        return ["module 4 has no sub-step 6"]
    problems = ["option 3 does not say %r" % p for p in missing(passage, FIELD_PHRASES)]
    if flat(QUERY_CALL) not in flat(passage):
        problems.append("option 3 no longer makes the call the field is read from")
    return problems


def terms_problems(text):
    """The EULA top hit is kept, as the terms rather than as the channel."""
    passage = step(text)
    if passage is None:
        return ["module 4 has no sub-step 6"]
    problems = ["option 3 does not say %r" % p for p in missing(passage, TERMS_PHRASES)]
    if flat("present the returned guidance on the external channel") in flat(passage):
        problems.append("option 3 still leaves the channel to be inferred from the top hit")
    return problems


def no_pii_problems(text):
    """The one line saying this route transmits nothing about the Bootcamper."""
    passage = step(text)
    if passage is None:
        return ["module 4 has no sub-step 6"]
    return ["option 3 does not say %r" % p for p in missing(passage, NO_PII_PHRASES)]


def fallback_problems(text):
    """The absent-field fallback is today's behavior, and absence is not unavailability."""
    passage = step(text)
    if passage is None:
        return ["module 4 has no sub-step 6"]
    return ["option 3 does not say %r" % p for p in missing(passage, FALLBACK_PHRASES)]


def unchanged_problems(text):
    """What the field must not have displaced: the split, the gate's answer, the runtime rule."""
    passage = step(text)
    if passage is None:
        return ["module 4 has no sub-step 6"]
    problems = ["sub-step 6 no longer says %r" % p for p in missing(passage, UNCHANGED_PHRASES)]
    if "\U0001F449" in passage:
        problems.append("sub-step 6 asks a question of its own, re-opening the gate (INV-006)")
    return problems


CHECKS = {
    "field": field_problems,
    "terms": terms_problems,
    "no_pii": no_pii_problems,
    "fallback": fallback_problems,
    "unchanged": unchanged_problems,
}


def run(name, text):
    return CHECKS[name](text)


def rewrap(text):
    """One word per line for every prose line; headings, tables and fences are kept."""
    out = []
    fenced = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        if fenced or stripped.startswith(("#", "|", "<a ", "```")) or not stripped:
            out.append(line)
            continue
        indent = line[:len(line) - len(stripped)]
        words = stripped.split(" ")
        out.append(("\n" + indent).join([indent + words[0]] + words[1:]))
    return "\n".join(out)


# ----------------------------------------------------------------------------------- the file


class Option3ReadsTheEvalLicenseField(unittest.TestCase):
    def setUp(self):
        self.text = read()

    def test_the_step_is_found(self):
        """⛔ INV-265: a scan of a moved step certifies nothing."""
        passage = step(self.text)
        self.assertIsNotNone(passage, "sub-step 6 moved; every check below would pass vacuously")
        self.assertIn("eval_license", passage)

    def test_option_3_names_the_field_and_reads_it_before_the_results(self):
        self.assertEqual([], run("field", self.text))

    def test_the_eula_top_hit_is_kept_as_the_terms(self):
        self.assertEqual([], run("terms", self.text))

    def test_the_route_is_stated_as_asking_the_bootcamper_for_nothing(self):
        self.assertEqual([], run("no_pii", self.text))

    def test_the_absent_field_falls_back_to_todays_behavior(self):
        self.assertEqual([], run("fallback", self.text))

    def test_the_split_the_gate_and_the_runtime_rule_are_untouched(self):
        self.assertEqual([], run("unchanged", self.text))

    def test_the_field_is_named_in_exactly_one_step(self):
        """INV-300: option 3 owns this route; no other step restates how to read it."""
        sites = sorted(p.relative_to(REPO_ROOT) for p in SKILLS.rglob("*.md")
                       if "eval_license" in p.read_text(encoding="utf-8"))
        self.assertEqual([MODULE_4.relative_to(REPO_ROOT)], sites)


class EachCheckSeesTheTextItWasWrittenFor(unittest.TestCase):
    """Negative controls: the same checks, on copies mutated back toward the old wording."""

    def setUp(self):
        self.text = read()

    def mutated(self, old, new=""):
        self.assertIn(old, self.text, "negative control is stale: %r is gone" % old[:60])
        return self.text.replace(old, new, 1)

    def test_the_wording_before_679_fails_the_field_check(self):
        """The sentence that shipped before this change: read the top hit, present its guidance."""
        passage = step(self.text)
        start = passage.index("`search_docs(query=")
        end = passage.index("Source the request channel's address")
        before = self.text.replace(passage[start:end], (
            "`search_docs(query='temporary evaluation license for a dataset larger than the "
            "default limit')`,\n   whose top hit is the EULA's *Senzing Non-Production License* "
            "section, and present the returned\n   guidance on the external channel. "), 1)
        self.assertTrue(run("field", before))
        self.assertTrue(run("terms", before))
        self.assertTrue(run("no_pii", before))
        self.assertTrue(run("fallback", before))
        # The pre-#679 sentence left the rest of sub-step 6 intact, so nothing else regresses.
        self.assertEqual([], run("unchanged", before))

    def test_reading_the_field_after_the_results_is_reported(self):
        text = self.mutated("from that response BEFORE `results[]`", "from `results[0]`")
        self.assertTrue(run("field", text))

    def test_dropping_the_not_a_hit_reason_is_reported(self):
        text = self.mutated("a sibling of `metadata` and `results` — not a search\n   hit — so a "
                            "guide that reads only the top hit never sees it",
                            "one of the results")
        self.assertTrue(run("field", text))

    def test_paraphrasing_the_message_instead_of_relaying_it_is_reported(self):
        text = self.mutated("**relay its\n   `message` verbatim**", "**summarize its message**")
        self.assertTrue(run("field", text))

    def test_losing_the_call_the_field_comes_from_is_reported(self):
        text = self.mutated("`search_docs(query='temporary evaluation license for a dataset "
                            "larger than the default limit')`", "the Senzing MCP server")
        problems = run("field", text)
        self.assertTrue(any("no longer makes the call" in p for p in problems), problems)

    def test_making_the_top_hit_the_channel_again_is_reported(self):
        text = self.mutated("as the **terms that accompany that\n   channel**",
                            "and present the returned guidance on the external channel")
        self.assertTrue(run("terms", text))

    def test_dropping_the_eula_section_name_is_reported(self):
        text = self.mutated("the EULA's *Senzing Non-Production License* section",
                            "the license agreement")
        self.assertTrue(run("terms", text))

    def test_dropping_the_zero_disclosure_line_is_reported(self):
        text = self.mutated("⚠️ **This\n   route asks the bootcamper for nothing.**", "")
        self.assertTrue(run("no_pii", text))

    def test_dropping_the_contrast_with_option_4_is_reported(self):
        text = self.mutated("Unlike option 4's in-flow request (sub-step 6a), it",
                            "It")
        self.assertTrue(run("no_pii", text))

    def test_dropping_the_fallback_is_reported(self):
        passage = step(self.text)
        start = passage.index("⛔ **When the call fails")
        end = passage.index("Source the request channel's address")
        text = self.text.replace(passage[start:end], "", 1)
        self.assertTrue(run("fallback", text))

    def test_reporting_a_missing_field_as_an_unavailable_route_is_reported(self):
        text = self.mutated(
            "a license route MUST NOT be reported as unavailable because `eval_license` was "
            "missing",
            "tell the bootcamper no evaluation license route is available")
        self.assertTrue(run("fallback", text))

    def test_dropping_which_path_produced_the_answer_is_reported(self):
        text = self.mutated("and say which of the two produced what is presented (INV-125)", "")
        self.assertTrue(run("fallback", text))

    def test_re_offering_the_paths_is_reported(self):
        text = self.mutated("never re-offer the paths (INV-006)",
                            "present the paths as selectable options")
        self.assertTrue(run("unchanged", text))

    def test_dropping_the_runtime_sourcing_rule_is_reported(self):
        text = self.mutated("Source the request channel's address and any capacity/validity "
                            "figures from MCP at runtime\n   rather than this file",
                            "Use the address in this file")
        self.assertTrue(run("unchanged", text))


class ReWrapping(unittest.TestCase):
    """INV-346: re-flowed to one word per line, the live text still passes every check."""

    def setUp(self):
        self.text = rewrap(read())

    def test_every_check_passes_on_rewrapped_text(self):
        for name in CHECKS:
            with self.subTest(check=name):
                self.assertEqual([], run(name, self.text))


if __name__ == "__main__":
    unittest.main()
