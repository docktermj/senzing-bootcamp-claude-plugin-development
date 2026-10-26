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

**Every other license route points here (#789).** Module 6 Phase A still wrote a support address
into its expansion paths, and Module 2's license note named "the MCP server or Senzing support",
while the server's route field names neither. `EveryLicenseRouteReachesSubStep6` scans every
paragraph and list item under `plugins/senzing-bootcamp/skills/` that offers a way to obtain or
request a license: each names no email address or URL as the channel, and each points at this
sub-step — by `../module-04-data-collection/SKILL.md` → "Obtain a Senzing License Key", citing
INV-403 and INV-300, from outside Module 4, or by "sub-step 6" inside it — unless it sits in Step
8a itself (the gate, sub-step 6, and sub-step 6a's in-flow request), is the in-flow
`submit_feedback(category='license_request')` route alone, or is on `EXEMPT` with its reason.
The Step 8a exemption covers the pointer only; the channel check runs there too.
This enforces INV-403's dated note of 2026-10-23 (#789), applied 2026-10-26. It reads shipped
prose and does NOT establish that a live guide follows the pointer.
`ground-rules.md`'s MCP-failure fallback and `feedback.md`'s reply path name the support address
for other purposes and are asserted not to be route units. Negative controls restore Phase A's
address, drop each pointer, restore Module 2's own channel and add a new route paragraph that
names one; `ReWrapping` re-runs the scan one word per line (INV-346).

Source issues: #679, #789. Invariants: INV-006, INV-056, INV-080, INV-108, INV-125, INV-135,
INV-213, INV-265, INV-291, INV-300, INV-321, INV-346, INV-403.

INV-403 (a structured field that answers the step's question is named and read before the results
list, with an explicit absent-field fallback) names this file as its enforcer. It asserts that the
step states each clause; it does not establish that a live guide reads the field, which only
`dry-run` phase 3 observes, and asserts nothing about the server.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _corpus

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


#: A line's lead: indentation and blockquote markers, then an optional list marker (#789).
LEAD = re.compile(r"^(\s*(?:>\s?)*)((?:[-*+]|\d+[.)])\s+)?")


def rewrap(text):
    """One word per line for every prose line; headings, tables and fences are kept.

    A blockquote's `>` and a list item's marker stay with the first word, and every continuation
    line keeps the `>` (#789): split off on its own line, a `>` reads as a blank quote line and a
    bare `-` as no list item, which would merge or split the paragraphs the route scan reads.
    """
    out = []
    fenced = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        match = LEAD.match(line)
        lead, rest = match.group(1), line[match.end():]
        if (fenced or stripped.startswith(("#", "|", "<a ", "```")) or not rest.strip()
                or rest.lstrip().startswith(("#", "|", "<a "))):
            out.append(line)
            continue
        words = rest.split()
        out.append(("\n" + lead).join([line[:match.end()] + words[0]] + words[1:]))
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
        start = passage.index("⛔ **(INV-403) When the call fails")
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

    def test_the_route_scan_is_unchanged_on_rewrapped_text(self):
        """INV-346: one word per line finds the same route units and the same (empty) problems."""
        for path, text in skill_texts().items():
            wrapped = rewrap(text)
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertEqual(len(route_units(path, text)), len(route_units(path, wrapped)))
                self.assertEqual([], route_problems(path, wrapped))


# ------------------------------------------------------ every license-route paragraph (#789)
#
# #679 fixed sub-step 6, the one step that reads the channel from the server. Module 6 Phase A
# kept its own copy of the channel — a support address written into the file — and Module 2's
# license note named "the MCP server or Senzing support". Live, 2026-10-22 and 2026-10-23 (server
# 1.39.1), the server's route field names neither. So every paragraph under `skills/` that offers
# a way to obtain or request a license is found by scanning, and each one:
#
# * names no email address or URL as the channel (the channel is a Senzing fact sourced at runtime,
#   INV-080, and sub-step 6 is where it is read, INV-403);
# * points at Module 4 Step 8a sub-step 6 (INV-300) — unless it sits in Step 8a itself (the gate
#   whose option 3 leads to sub-step 6, sub-step 6, and sub-step 6a's in-flow request), or it is
#   the in-flow `submit_feedback(category='license_request')` route alone, or it is on `EXEMPT`.
#
# ⚠️ Out of scope by the issue, and checked below rather than assumed: `ground-rules.md`'s
# MCP-failure fallback and `feedback.md`'s reply path both name `support@senzing.com`, and neither
# offers a license, so neither is a route unit.

#: Words that make a paragraph offer a way to obtain or request a license.
ROUTE = re.compile(
    r"\b(?:request|obtain)\w*\s+(?:[\w'()-]+\s+){0,6}?licen[cs]e"
    r"|\blicen[cs]e\s+(?:key\s+)?request|license_request"
    r"|\b(?:request|obtain)\w*\s+one\b|\bexternal channel\b", re.I)

#: A route unit must mention a license at all; "request one" alone is about anything.
LICENSE = re.compile(r"licen[cs]e", re.I)

#: An email address or a URL written into the file as the channel.
CHANNEL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]*\w|https?://|\b[\w-]+\.senzing\.com\b", re.I)

#: The pointer a file outside Module 4 writes (INV-300), as `flat()` renders it.
POINTER = '../module-04-data-collection/SKILL.md → "Obtain a Senzing License Key"'

#: Inside Module 4, the pointer is the sub-step's number (never 6a, which is the in-flow route).
LOCAL_POINTER = re.compile(r"\bsub-step 6(?![a-z0-9.])", re.I)

#: The in-flow route names its tool category; it offers no external channel of its own.
IN_FLOW = re.compile(r"license_request|\bin-flow\b|sub-step 6a|8a\.6a", re.I)
EXTERNAL = re.compile(r"external channel|another way|elsewhere|\bsupport\b", re.I)

STEP_8A = ("### 8a. Senzing License Key gate", "### 8b.")

#: (file under skills/, a phrase from the unit, why it is not a license route to point).
EXEMPT = (
    ("bootcamp-onboarding/ground-rules.md",
     "Recorded because it happened at the worst possible place (2026-08-25)",
     "an incident record quoting the option a bootcamper chose; it offers no route"),
    ("graduation/SKILL.md",
     "obtain a production license",
     "a production license in the graduation report's next steps; sub-step 6 serves the "
     "evaluation channel, and it says the eval and production channels differ"),
)

ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
HEADING = re.compile(r"#{1,6}\s")


def skill_texts():
    return {p: p.read_text(encoding="utf-8")
            for p in _corpus.corpus_files("plugins/senzing-bootcamp/skills", suffixes={".md"})}


def units(text):
    """(first line, text) of each paragraph or list item, blockquote markers dropped."""
    out, current, first, fenced = [], [], 0, False
    for number, line in enumerate(text.split("\n"), 1):
        body = re.sub(r"^\s*>\s?", "", line) if line.lstrip().startswith(">") else line
        stripped = body.strip()
        if stripped.startswith(("```", "~~~")):
            fenced = not fenced
        breaks = not stripped or (not fenced and (ITEM.match(body) or HEADING.match(stripped)))
        if breaks and current:
            out.append((first, " ".join(current)))
            current = []
        if not stripped:
            continue
        if not current:
            first = number
        current.append(stripped)
    if current:
        out.append((first, " ".join(current)))
    return out


def step_8a_lines(path, text):
    """The line range of Module 4's Step 8a, or None for any other file."""
    if path.resolve() != MODULE_4.resolve():
        return None
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines, 1) if l.startswith(STEP_8A[0])), None)
    end = next((i for i, l in enumerate(lines, 1) if l.startswith(STEP_8A[1])), None)
    return (start, end) if start and end else None


def route_units(path, text):
    """Every unit that offers a way to obtain or request a license, found by scanning."""
    found = []
    for first, unit in units(text):
        body = flat(unit)
        if LICENSE.search(body) and ROUTE.search(body):
            found.append((first, body))
    return found


def exempt(path, body):
    rel = path.relative_to(SKILLS).as_posix()
    return any(rel == f and flat(phrase) in body for f, phrase, _ in EXEMPT)


def route_problems(path, text):
    """Each route unit that names a channel, or reaches the channel without the pointer."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    owner = step_8a_lines(path, text)
    problems = []
    for first, body in route_units(path, text):
        where = "%s:%d" % (rel, first)
        named = CHANNEL.search(body)
        if named:
            problems.append("%s names %r as a license request channel" % (where, named.group()))
        if owner and owner[0] <= first < owner[1]:
            continue  # Step 8a is the gate, sub-step 6 itself and the in-flow request (6a)
        if IN_FLOW.search(body) and not EXTERNAL.search(body):
            continue  # the in-flow submit_feedback(category='license_request') route alone
        if exempt(path, body):
            continue
        if path.resolve() == MODULE_4.resolve():
            if not LOCAL_POINTER.search(body):
                problems.append("%s offers a license route without pointing at sub-step 6" % where)
        elif flat(POINTER) not in body:
            problems.append("%s offers a license route without the pointer %s" % (where, POINTER))
        elif not ("INV-403" in body and "INV-300" in body):
            problems.append("%s points at sub-step 6 without citing INV-403 and INV-300" % where)
    return problems


def all_route_problems(texts):
    return [p for path, text in sorted(texts.items()) for p in route_problems(path, text)]


PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
FEEDBACK = SKILLS / "bootcamp-onboarding" / "feedback.md"


class EveryLicenseRouteReachesSubStep6(unittest.TestCase):
    """#789: no shipped license-route paragraph names a channel; each points at sub-step 6."""

    def setUp(self):
        self.texts = skill_texts()

    def units_of(self, path):
        return route_units(path, self.texts[path])

    def test_the_scan_is_not_vacuous(self):
        """⛔ INV-265: the scan finds the sites the issue names, so a pass is not a missed scan."""
        self.assertTrue(self.units_of(PHASE_A), "Phase A's expansion paths are not a route unit")
        self.assertTrue(any("Where the License Key is handled now" in body
                            for _, body in self.units_of(MODULE_2)),
                        "Module 2's license note is not a route unit")
        self.assertTrue(any("Obtain a Senzing License Key" in body
                            for _, body in self.units_of(MODULE_4)),
                        "Module 4's sub-step 6 is not a route unit")
        self.assertGreaterEqual(sum(len(route_units(p, t)) for p, t in self.texts.items()), 8)

    def test_no_route_names_a_channel_and_each_points_at_sub_step_6(self):
        self.assertEqual([], all_route_problems(self.texts))

    def test_phase_a_and_module_2_carry_the_cited_pointer(self):
        for path in (PHASE_A, MODULE_2):
            with self.subTest(path=path.name):
                cited = [body for _, body in self.units_of(path)
                         if flat(POINTER) in body and "INV-403" in body and "INV-300" in body]
                self.assertTrue(cited, "%s has no cited pointer to sub-step 6" % path.name)

    def test_phase_a_keeps_its_other_paths_in_order(self):
        """The other expansion paths and their order are unchanged (#789's scope)."""
        body = flat(self.texts[PHASE_A])
        order = [body.find(flat(p)) for p in (
            "apply an existing license", "request one through the external channel",
            "request one in-flow via the Senzing MCP server", "before any mention of downsizing")]
        self.assertNotIn(-1, order, order)
        self.assertEqual(sorted(order), order)

    def test_the_two_non_license_addresses_are_not_flagged(self):
        """`ground-rules.md`'s MCP-failure fallback and `feedback.md`'s reply path stay."""
        for path in (GROUND_RULES, FEEDBACK):
            with self.subTest(path=path.name):
                self.assertIn("support@senzing.com", self.texts[path],
                              "the address moved; this check would pass vacuously")
                self.assertEqual([], [b for _, b in self.units_of(path)
                                      if "support@senzing.com" in b])
                self.assertEqual([], route_problems(path, self.texts[path]))

    def test_each_exemption_still_matches_a_route_unit(self):
        """A stale exemption hides nothing and should be deleted."""
        for rel, phrase, _ in EXEMPT:
            path = SKILLS / rel
            with self.subTest(path=rel):
                self.assertTrue(any(flat(phrase) in body for _, body in self.units_of(path)),
                                "exemption %r no longer matches a route unit" % phrase)


class TheRouteScanSeesWhatItWasWrittenFor(unittest.TestCase):
    """Negative controls: the same scan, on copies mutated toward what #789 removed."""

    def setUp(self):
        self.texts = skill_texts()

    def mutated(self, path, old, new):
        text = self.texts[path]
        self.assertIn(old, text, "negative control is stale: %r is gone" % old[:60])
        return {**self.texts, path: text.replace(old, new, 1)}

    def test_restoring_the_address_in_phase_a_is_reported(self):
        texts = self.mutated(PHASE_A, "request one through the external channel, and",
                             "request one through the external channel\n  "
                             "(<support@senzing.com>), and")
        problems = all_route_problems(texts)
        self.assertTrue(any("support@senzing.com" in p and "phaseA" in p for p in problems),
                        problems)

    def test_dropping_phase_a_s_pointer_is_reported(self):
        texts = self.mutated(PHASE_A, '`../module-04-data-collection/SKILL.md` → "Obtain a '
                             'Senzing\n  License Key"', "Module 4")
        self.assertTrue(any("phaseA" in p for p in all_route_problems(texts)))

    def test_dropping_phase_a_s_citations_is_reported(self):
        texts = self.mutated(PHASE_A, "(INV-403, INV-300)", "")
        self.assertTrue(any("without citing" in p for p in all_route_problems(texts)))

    def test_restoring_module_2_s_own_channel_is_reported(self):
        text = self.texts[MODULE_2]
        start = text.index("The request channel is the one")
        end = text.index("names no channel of its own.", start) + len("names no channel of its own.")
        texts = {**self.texts, MODULE_2: text[:start] + text[end:]}
        texts[MODULE_2] = texts[MODULE_2].replace(
            "requesting\n> an evaluation license (sub-step 6))",
            "requesting\n> an evaluation license via the MCP server or Senzing support)", 1)
        self.assertNotEqual(texts[MODULE_2], self.texts[MODULE_2])
        self.assertTrue(any("module-02" in p for p in all_route_problems(texts)))

    def test_a_new_route_paragraph_naming_a_channel_is_reported(self):
        texts = {**self.texts, PHASE_A: self.texts[PHASE_A] + (
            "\n\nTo obtain an evaluation license, email <licensing@example.com> or visit "
            "<https://example.com/license>.\n")}
        problems = all_route_problems(texts)
        self.assertTrue(any("licensing@example.com" in p for p in problems), problems)
        self.assertTrue(any("without the pointer" in p for p in problems), problems)

    def test_a_channel_inside_step_8a_is_still_reported(self):
        """The Step 8a exemption covers the pointer, never the channel check."""
        texts = self.mutated(MODULE_4, "together with its `url`",
                             "together with its `url` (or <support@senzing.com>)")
        self.assertTrue(any("module-04" in p and "support@senzing.com" in p
                            for p in all_route_problems(texts)))

    def test_dropping_module_4_s_local_pointer_is_reported(self):
        texts = self.mutated(MODULE_4, "external channel (its\n  sub-step 6)", "external channel")
        self.assertTrue(any("without pointing at sub-step 6" in p
                            for p in all_route_problems(texts)))


if __name__ == "__main__":
    unittest.main()
