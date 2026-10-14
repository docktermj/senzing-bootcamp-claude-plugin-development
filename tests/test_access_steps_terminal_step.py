"""Follow the response's own `access_steps`, check `hash` where a step asks, and only then give up.

`find_examples` file retrieval and `generate_scaffold` both answer with an ordered
`access_steps` array instead of the file's bytes. #197 (server 1.37.14, 2026-09-28) wrote that
route into the plugin as a fixed list, "`raw_url`, then clone", and added the terminal step:
once both had failed, report the example as unreachable (INV-160). By server 1.37.28
(2026-10-13) the server had put an MCP-hosted `url` first, with a `hash` to check the saved
file against, so the fixed list skipped a step and gave up one step early. A Bootcamper whose
network allows `mcp.senzing.com` and blocks GitHub was told a reachable example was
unreachable. Issue #565.

The fix states the route **as the response's own order**, not as a list of today's steps, so
the next reordering or added step does not make the text wrong again. Today's steps appear
only as a dated example. These tests pin the behavior, not the server's sentence (INV-219):

* `ground-rules.md` states the route once, as a ⛔ paragraph citing INV-160: take the
  response's steps in turn, run each check a step asks for, go on only when a step fails. The
  rule itself names no particular step, so it holds whatever the server lists;
* the `hash` check: the saved file's SHA-256 must equal `hash`, with the Linux, macOS and
  Windows commands; a mismatch is that step failing (discard, go on); checked exactly where
  the response's step asks for it;
* the dated example lists today's order: the hosted `url`, `raw_url`, `git clone`, then the
  final `inline` step, and says it is an example, not the rule;
* the terminal step fires only once every fetch and clone step has failed, and is stated
  after the route;
* the Module 2 and Module 3 sites cite both statements and name no fixed route, no numbered
  step, and no copy of either rule (INV-300); their field lists name `url` and `hash`;
* no shipped file quotes a retired step-3 note, or names `inline` by step number;
* INV-160 carries the 2026-09-28 dated note that records the unreachable step. (Its
  2026-10-13 note is a queued amendment in `specs/IMPLEMENTED.md`, for `/review-invariants`.)

Every predicate is a function of the text, and the negative controls at the bottom run each
one on a mutant: the old two-step route restored, the hash check removed, the terminal step
moved early, a fixed route restored at a module site, and the old quote restored.

Enforces the 2026-09-28 note on **INV-160**, and the route and `hash` check #565 adds to it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
MODULE_02 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"
MODULE_03 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"

#: The module sites that fetch `generate_scaffold` output, with the number of route pointers
#: and terminal-step pointers each holds. A floor, so a pointer dropped by a rewrite is noticed.
#: Module 2: Step 4 (both) and Step 9 (route). Module 3: Steps 3 and 4 (both), and Step 1a's
#: re-obtained initialization code (route; #618).
ROUTE_FILES = {MODULE_02: (2, 1), MODULE_03: (3, 2)}

#: The route's ⛔ lead, by its words.
ROUTE_LEAD = re.compile(
    r"⛔ \*\*Follow each response's own `access_steps`, in the order it gives them "
    r"\(INV-160\)\.\*\*")
#: Where the dated example begins inside the route paragraph. Text before it is the rule.
EXAMPLE_LEAD = "**An example of the steps, dated: not the rule.**"
#: The ⛔ lead that states the terminal step. Its paragraph runs to the next ⛔ or the next
#: list item, so a clause moved out of it no longer counts.
TERMINAL_LEAD = re.compile(r"⛔ \*\*[^*]*\bunreachable\b[^*]*\*\*")
PARAGRAPH_END = re.compile(r"⛔|\n\s*- ")

#: A module's pointer to each statement: the owning file, and the statement's lead, named whole
#: since #615 (`tests/test_section_pointers_resolve.py`), not by its opening words.
ROUTE_POINTER = re.compile(
    r"ground-rules\.md` → \"Follow each response's own `access_steps`, in the order it gives "
    r"them\"")
TERMINAL_POINTER = re.compile(
    r"ground-rules\.md` → \"Once every fetch and clone step in the response's `access_steps` "
    r"has failed, report the example as unreachable\"")

#: A fixed route written into a module site: a `raw_url`-then-clone list, a URL named as the
#: thing to fetch, or a step named by its number.
FIXED_ROUTE = re.compile(
    r"`raw_url`.{0,120}?\bclone\b"
    r"|(?i:fetch (?:each|its|the|a candidate's) `(?:raw_)?url`)"
    r"|`access_steps` step \d"
    r"|step \d's `git clone`")

#: Retired server wording. 1.32.8's step-3 note, and 1.37.14's, which counted the routes.
OLD_WORDINGS = (
    "cannot use this step",
    "steps 1 and 2 (raw_url / git clone) have already failed",
)
#: `inline` named by step number: its number differs per tool and moves with the server.
INLINE_BY_NUMBER = re.compile(
    r"(?i)\bstep \d\b[^.]{0,30}`inline`|`inline`[^.]{0,30}\bstep \d\b"
    r"|`access_steps` step \d[^.]{0,40}\binline\b")


def flat(text):
    return re.sub(r"\s+", " ", text)


def prose(text):
    """``text`` without HTML comments: dated `MCP-NEGATIVE` evidence stays as it was observed."""
    return re.sub(r"<!--.*?-->", " ", text, flags=re.S)


def paragraph_at(text, match):
    end = PARAGRAPH_END.search(text, match.end())
    return text[match.start(): end.start() if end else len(text)]


def route_paragraphs(text):
    return [paragraph_at(text, m) for m in ROUTE_LEAD.finditer(text)]


def terminal_steps(text):
    """Every ⛔ paragraph whose bold lead says to report something as unreachable."""
    return [paragraph_at(text, m) for m in TERMINAL_LEAD.finditer(text)]


def inv160(text):
    m = re.search(r"^- \*\*INV-160\*\* —.*$", text, re.MULTILINE)
    return m.group(0) if m else None


# --- Predicates. Each returns a list of problems; [] means the text holds the rule. -------


def route_problems(text):
    """The route defers to the response's own order, and the rule names no particular step."""
    found = route_paragraphs(text)
    if len(found) != 1:
        return ["ground-rules.md must state the access_steps route exactly once, as a ⛔ "
                "paragraph citing INV-160; found %d" % len(found)]
    par = flat(found[0])
    problems = []
    for pattern, what in (
        (r"(?i)take the steps in turn", "take the steps in turn"),
        (r"(?i)run every check that step's own note asks for", "run each step's own checks"),
        (r"(?i)go on to the next step only when that one fails", "go on only on a failure"),
        (r"(?i)never reorder, skip or add a step", "never reorder, skip or add a step"),
        (r"`find_examples`", "name find_examples"),
        (r"`generate_scaffold`", "name generate_scaffold"),
    ):
        if not re.search(pattern, par):
            problems.append("the route paragraph does not say: " + what)
    if EXAMPLE_LEAD not in par:
        problems.append("the route paragraph carries no dated example marked as not the rule")
        return problems
    rule = par[: par.index(EXAMPLE_LEAD)]
    for step in ("`raw_url`", "hosted", "`git clone`, then", "then clone"):
        if step in rule:
            problems.append(
                "the rule names a particular step (%s), so the next reordering makes it wrong; "
                "name today's steps only in the dated example" % step)
    return problems


def hash_problems(text):
    """SHA-256 must equal `hash`, per platform; a mismatch fails the step; checked where asked."""
    found = route_paragraphs(text)
    if len(found) != 1:
        return ["no single route paragraph to hold the hash check"]
    par = flat(found[0])
    problems = []
    for pattern, what in (
        (r"SHA-256 must equal `hash`", "the saved file's SHA-256 must equal `hash`"),
        (r"`sha256sum <file>` on Linux", "the Linux command"),
        (r"`shasum -a 256 <file>` on macOS", "the macOS command"),
        (r"`Get-FileHash -Algorithm SHA256 <file>` in Windows PowerShell",
         "the Windows command"),
        (r"(?i)a `hash` mismatch counts as that step failing", "a mismatch is a failed step"),
        (r"(?i)discard the saved file and go on to the next step", "discard and go on"),
        (r"(?i)never presented or used \(INV-245\)", "a failed file is never used (INV-245)"),
        (r"(?i)exactly where the response's own step asks for it", "check only where asked"),
        (r"(?i)a step whose note asks for no check gets none", "no check where none is asked"),
    ):
        if not re.search(pattern, par):
            problems.append("the hash check does not say: " + what)
    return problems


def example_problems(text):
    """The dated example lists today's order, and defers to a live response that differs."""
    found = route_paragraphs(text)
    if len(found) != 1 or EXAMPLE_LEAD not in flat(found[0]):
        return ["no dated example in the route paragraph"]
    par = flat(found[0])
    example = par[par.index(EXAMPLE_LEAD):]
    problems = []
    if not re.search(r"MCP server 1\.\d+\.\d+, \d{4}-\d{2}-\d{2}", example):
        problems.append("the example carries no server version and date (INV-108: the date "
                        "is the re-check mechanism)")
    for tool in ("find_examples", "generate_scaffold"):
        start = example.find("`%s" % tool)
        if start < 0:
            problems.append("the example does not give %s's steps" % tool)
            continue
        steps = example[start:]
        order = [steps.find(s) for s in
                 ("hosted `url`", "`raw_url`", "`git clone`", "the final `inline` step")]
        if -1 in order or order != sorted(order):
            problems.append("the example does not give %s's order as hosted `url`, `raw_url`, "
                            "`git clone`, then the final `inline` step" % tool)
    if not re.search(r"(?i)follow the live response", example):
        problems.append("the example does not defer to a live response that differs")
    return problems


def terminal_problems(text):
    """The terminal step fires only after every fetch and clone step, and follows the route."""
    steps = terminal_steps(text)
    if len(steps) != 1:
        return ["ground-rules.md must state the access_steps terminal step exactly once, as a "
                "⛔ line whose bold lead says to report the example as unreachable; found %d"
                % len(steps)]
    step = flat(steps[0])
    lead = TERMINAL_LEAD.search(step).group(0)
    problems = []
    if "(INV-160)" not in lead:
        problems.append("the terminal step's lead does not cite INV-160")
    if not re.search(r"Once every fetch and clone step in the response's `access_steps` has "
                     r"failed", lead):
        problems.append("the terminal step does not wait for every fetch and clone step the "
                        "response gives: %r" % lead)
    if not re.search(r"(?i)a failed `hash` check included, sends the guide to the next step",
                     step):
        problems.append("the terminal step does not say a failed step, hash included, goes to "
                        "the next step first")
    route = ROUTE_LEAD.search(text)
    if route and route.start() > TERMINAL_LEAD.search(text).start():
        problems.append("the terminal step is stated before the route it ends")
    return problems


def module_problems(path, text):
    """A module site cites both statements, names no fixed route, and copies neither rule."""
    body = flat(prose(text))
    problems = []
    for m in FIXED_ROUTE.finditer(body):
        problems.append("%s names a fixed route (%r); cite ground-rules.md's route instead"
                        % (path.name, m.group(0)[:70]))
    routes, terminals = ROUTE_FILES[path]
    if len(ROUTE_POINTER.findall(body)) < routes:
        problems.append("%s has fewer than %d pointers to the route statement"
                        % (path.name, routes))
    if len(TERMINAL_POINTER.findall(body)) < terminals:
        problems.append("%s has fewer than %d pointers to the terminal step"
                        % (path.name, terminals))
    for m in TERMINAL_POINTER.finditer(body):
        if not ROUTE_POINTER.search(body[max(0, m.start() - 400): m.start()]):
            problems.append("%s points at the terminal step with no route pointer before it"
                            % path.name)
    for copy in (r"(?i)which example could not be reached",
                 r"(?i)do not retry (?:any of those steps|either step)",
                 r"SHA-256 must equal", r"sha256sum", r"Get-FileHash"):
        if re.search(copy, body):
            problems.append("%s restates a clause ground-rules.md owns (%s); point at it "
                            "instead (INV-300)" % (path.name, copy))
    if not re.search(r"`source_url`, `url`, `raw_url`, `size_bytes`, `line_count` and `hash`",
                     body):
        problems.append("%s's generate_scaffold field list does not name `url` and `hash`"
                        % path.name)
    return problems


def old_wording_problems(texts):
    problems = []
    for path, text in texts.items():
        body = flat(text)
        for old in OLD_WORDINGS:
            if old in body:
                problems.append("%s quotes the retired server note %r" % (path, old))
        for m in INLINE_BY_NUMBER.finditer(flat(prose(text))):
            problems.append("%s names `inline` by step number (%r); say \"the final `inline` "
                            "step\"" % (path, m.group(0)[:60]))
    return problems


def shipped_texts():
    texts = {}
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file():
            continue
        try:
            texts[str(path.relative_to(REPO_ROOT))] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return texts


# --- The shipped files hold. -------------------------------------------------------------


class GroundRulesDefersToTheResponsesOrder(unittest.TestCase):
    def setUp(self):
        self.text = GROUND_RULES.read_text(encoding="utf-8")

    def test_the_route_is_the_responses_own_order(self):
        self.assertEqual([], route_problems(self.text))

    def test_the_hash_check(self):
        self.assertEqual([], hash_problems(self.text))

    def test_the_dated_example_gives_todays_order(self):
        self.assertEqual([], example_problems(self.text))


class GroundRulesStatesTheTerminalStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = GROUND_RULES.read_text(encoding="utf-8")
        steps = terminal_steps(cls.text)
        cls.step = flat(steps[0]) if len(steps) == 1 else ""

    def test_it_fires_only_after_every_route(self):
        self.assertEqual([], terminal_problems(self.text))

    def test_it_covers_both_tools(self):
        for tool in ("find_examples", "generate_scaffold"):
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", self.step)

    def test_it_names_the_file_and_what_was_tried(self):
        self.assertRegex(self.step, r"(?i)which example could not be reached")
        self.assertRegex(self.step, r"(?i)what was tried")

    def test_it_forbids_retrying_and_inline(self):
        self.assertRegex(self.step, r"(?i)do not retry any of those steps")
        self.assertRegex(self.step, r"(?i)do not pass `inline`, which neither schema declares")

    def test_it_forbids_reconstructing_from_memory(self):
        self.assertRegex(self.step, r"(?i)never reconstruct[^.]*from memory")

    def test_the_calling_step_keeps_its_own_fallback(self):
        self.assertRegex(self.step, r"(?i)continues on its own fallback")


class EveryModuleSiteCitesTheGroundRules(unittest.TestCase):
    """INV-300: the route and the terminal step are stated once, in ground-rules.md."""

    def test_each_site(self):
        for path in ROUTE_FILES:
            with self.subTest(file=path.name):
                self.assertEqual([], module_problems(path, path.read_text(encoding="utf-8")))


class TheRetiredWordingIsGone(unittest.TestCase):
    def test_no_shipped_file_quotes_an_old_note_or_numbers_inline(self):
        self.assertEqual([], old_wording_problems(shipped_texts()))


class Inv160RecordsTheUnreachableStep(unittest.TestCase):
    """Negative-controlled by deleting the 2026-09-28 note from INV-160."""

    def test_the_dated_note_names_the_unreachable_step(self):
        body = inv160(INVARIANTS.read_text(encoding="utf-8"))
        self.assertIsNotNone(body, "INV-160 is missing from specs/INVARIANTS.md")
        m = re.search(r"Dated note, 2026-09-28.*?(?=\(Source:|$)", body)
        self.assertIsNotNone(m, "INV-160 carries no 2026-09-28 dated note")
        note = m.group(0)
        self.assertRegex(note, r"MUST report the example as unreachable")
        self.assertRegex(note, r"MUST NOT retry either step")
        self.assertIn("`find_examples`", note)
        self.assertIn("`generate_scaffold`", note)


# --- Negative controls: each predicate fires on a mutant of the shipped text. -----------


def _replace(text, old, new):
    assert old in text, "negative control's anchor is gone: %r" % old[:60]
    return text.replace(old, new, 1)


class TheGuardsFireOnMutants(unittest.TestCase):
    def setUp(self):
        self.text = GROUND_RULES.read_text(encoding="utf-8")

    def test_the_old_two_step_route_restored(self):
        rule = _replace(self.text, "Take the\n  steps in turn:",
                        "Follow `access_steps`: `raw_url`, then clone. Take the\n  steps in turn:")
        self.assertTrue(route_problems(rule))
        lead = re.sub(r"\(INV-160\) Once every fetch and clone step in the response's "
                      r"`access_steps` has failed,\s+report the example as unreachable\.",
                      "Once `raw_url` and `git clone` have both failed, report the example as "
                      "unreachable (INV-160).", self.text)
        self.assertNotEqual(lead, self.text)
        self.assertTrue(terminal_problems(lead))

    def test_the_order_rule_removed(self):
        mutant = _replace(self.text, "Go on to the next step only when that one fails. ", "")
        self.assertTrue(route_problems(mutant))

    def test_the_hash_check_removed(self):
        start = self.text.index("**The `hash` check.**")
        end = self.text.index(EXAMPLE_LEAD)
        self.assertTrue(hash_problems(self.text[:start] + self.text[end:]))
        mismatch = _replace(self.text, "**A `hash` mismatch counts as that\n  step failing:**",
                            "**A `hash` mismatch is reported:**")
        self.assertTrue(hash_problems(mismatch))

    def test_the_example_reordered(self):
        mutant = _replace(self.text, "fetch the hosted `url` (served by the\n  MCP server",
                          "fetch the `git clone` hosted `url` (served by the\n  MCP server")
        mutant = _replace(mutant, "gave four steps: fetch", "gave four steps: `raw_url`, fetch")
        self.assertTrue(example_problems(mutant))

    def test_the_terminal_step_moved_early(self):
        early = re.sub(r"Once every fetch and clone step in the response's `access_steps` has "
                       r"failed",
                       "Once the hosted `url` has failed", self.text)
        self.assertTrue(terminal_problems(early))
        step = terminal_steps(self.text)[0]
        moved = self.text.replace(step, "", 1)
        route = ROUTE_LEAD.search(moved).start()
        moved = moved[:route] + step + moved[route:]
        self.assertTrue(terminal_problems(moved))

    def test_a_fixed_route_restored_at_a_module_site(self):
        text = MODULE_03.read_text(encoding="utf-8")
        mutant = _replace(text, "fetch each\n     file by the response's own `access_steps`,",
                          "fetch each\n     `raw_url` (or `git clone` per `access_steps` step 2),")
        self.assertTrue(module_problems(MODULE_03, mutant))
        uncited = _replace(text, "→ \"Once every fetch", "→ \"Once fetch")
        self.assertTrue(module_problems(MODULE_03, uncited))
        copied = _replace(text, "**Fetch before saving.**",
                          "**Fetch before saving.** The saved file's SHA-256 must equal `hash`.")
        self.assertTrue(module_problems(MODULE_03, copied))

    def test_the_old_quote_restored(self):
        old = {"x.md": "steps 1 and 2 (raw_url / git clone) have\n  already failed by the time"}
        self.assertTrue(old_wording_problems(old))
        numbered = {"x.md": "Do not take the `inline` route the response's step 3 describes."}
        self.assertTrue(old_wording_problems(numbered))
        # The marker token is built by concatenation, so this line is not itself a marker.
        comment = {"x.md": "<!-- MCP-" + "NEGATIVE: access_steps step 3 advertises the inline -->"}
        self.assertEqual([], old_wording_problems(comment))


if __name__ == "__main__":
    unittest.main()
