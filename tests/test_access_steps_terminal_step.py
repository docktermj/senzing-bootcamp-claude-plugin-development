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
* every paragraph in the shipped skills that tells the guide to obtain code from
  `generate_scaffold` carries the route pointer citing INV-160 and INV-300. The sites are found
  by scanning, not listed (INV-246; #806), and every other mention of the tool is on a reasoned
  exemption list keyed by its text;
* no shipped file quotes a retired step-3 note, or names `inline` by step number;
* INV-160 carries the 2026-09-28 dated note that records the unreachable step. (Its
  2026-10-13 note is a queued amendment in `specs/IMPLEMENTED.md`, for `/review-invariants`.)

Every predicate is a function of the text, and the negative controls at the bottom run each
one on a mutant: the old two-step route restored, the hash check removed, the terminal step
moved early, a fixed route restored at a module site, the old quote restored, the route pointer
removed from each scanned site in turn, and a new unpointed `generate_scaffold` instruction added.

**Which paragraphs are sites (#806).** A paragraph is a run of non-blank prose lines, cut again
at each list item; HTML comments and fenced code are not prose. A paragraph tells the guide to
obtain code from `generate_scaffold` when one of its sentences puts an instruction verb (call,
fetch, use, using, generate, obtain, re-obtain, get, run, request) in imperative position, at
the sentence's start or after an opening bracket, clause punctuation, "and", "or", "then" or
"keep", and names `generate_scaffold` after it in the same sentence, in call form or not. A verb
with a subject ("Entity queries use"), after "to" ("the reason to use") or after the tool
("`generate_scaffold` returns") does not count. The skills are the guide's instructions, so an
imperative there is addressed to the guide; text addressed to the Bootcamper goes on the list.
Each such paragraph carries the route pointer itself, unless the exemption list names it. Every
paragraph that names the tool without the pointer is on that list, with a reason, in one of
three groups: the rule does not flag it; the rule flags it but it is a sourcing rule, a summary
or advice, not a step that fetches a response; or a Module 2 or 3 step whose pointer follows in
the same step, which is checked. An entry in the wrong group, or whose text is gone, fails.
An instruction the rule does not flag is named on a fourth list, `SITES_THE_RULE_MISSES`, and is
a site like any other: Module 2 Step 8's "Either route is fine", which offers a
`generate_scaffold` fetch as the alternative to `sdk_guide`. An entry the rule flags fails.

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

#: Modules 2 and 3, with the number of route pointers and terminal-step pointers each holds. A
#: floor, so a pointer dropped by a rewrite is noticed. Module 2: Step 4 (both) and Step 9
#: (route). Module 3: Steps 3 and 4 (both), and Step 1a's re-obtained initialization code
#: (route; #618). Not the list of sites: since #806 the scan below derives those.
MODULE_FLOORS = {MODULE_02: (2, 1), MODULE_03: (3, 2)}

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
    routes, terminals = MODULE_FLOORS[path]
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


# --- Every `generate_scaffold` instruction points at the route (#806). ---------------------

SKILLS = PLUGIN / "skills"
TOOL = "`generate_scaffold"
#: The route pointer as a site carries it, citing both invariants (the Module 6 form).
CITED_ROUTE_POINTER = re.compile(ROUTE_POINTER.pattern + r" says \(INV-160, INV-300\)")
#: The same pointer in raw text, where a line break may fall between any two words.
RAW_ROUTE_POINTER = re.compile(
    r"`\.\./bootcamp-onboarding/ground-rules\.md`\s+→\s+\"Follow\s+each\s+response's\s+own\s+"
    r"`access_steps`,\s+in\s+the\s+order\s+it\s+gives\s+them\"\s+says\s+\(INV-160,\s+INV-300\)")
LIST_ITEM = re.compile(r"[ \t]*(?:[-*]|\d+\.)[ \t]")
HEADING = re.compile(r"^#{1,6} ", re.MULTILINE)
SENTENCE_BREAK = re.compile(r"(?<=[.!?])(?:\*\*)?\s+(?=\**[A-Z⛔⚠`])")
LEAD_MARKER = re.compile(r"^(?:(?:[-*]|\d+\.)\s+)?(?:(?:⛔|⚠️)\s*)?")
INSTRUCTION_VERB = re.compile(
    r"(?i)\b(?:call|fetch|use|using|generate|re-obtain|obtain|get|run|request)\b")
#: What may stand before a verb in imperative position: nothing, an opening bracket or clause
#: punctuation, or a joining word, with bold markers between.
IMPERATIVE_LEAD = re.compile(r"(?:^|[(:;—,]|\b(?:and|or|then|keep))[\s*]*$")


def mention_paragraphs(text):
    """Each prose paragraph naming `generate_scaffold`, as ``(start, end, flat text)``.

    A paragraph is a run of non-blank lines, cut again at each list item. HTML comments are
    blanked in place, so offsets still index ``text``; fenced code is skipped.
    """
    text = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    found, start, end, fenced, offset = [], None, None, False, 0
    for line in text.splitlines(keepends=True):
        here, offset = offset, offset + len(line)
        if line.lstrip().startswith("```"):
            fenced = not fenced
        breaks = fenced or line.lstrip().startswith("```") or not line.strip()
        if start is not None and (breaks or LIST_ITEM.match(line)):
            found.append((start, end))
            start = None
        if not breaks:
            if start is None:
                start = here
            end = offset
    if start is not None:
        found.append((start, end))
    return [(s, e, flat(text[s:e]).strip()) for s, e in found if TOOL in text[s:e]]


def instruction(paragraph):
    """The sentence by which ``paragraph`` tells the guide to obtain code from the tool, or None.

    The rule is stated in the module docstring: an instruction verb in imperative position, with
    `generate_scaffold` named after it in the same sentence.
    """
    for sentence in SENTENCE_BREAK.split(LEAD_MARKER.sub("", paragraph)):
        sentence = LEAD_MARKER.sub("", sentence)
        tool = sentence.find(TOOL)
        if tool < 0:
            continue
        for verb in INSTRUCTION_VERB.finditer(sentence, 0, tool):
            if IMPERATIVE_LEAD.search(sentence[: verb.start()]):
                return sentence
    return None


GROUND = "bootcamp-onboarding/ground-rules.md"
M02 = "module-02-sdk-setup/SKILL.md"
M03 = "module-03-system-verification/phase1-verification.md"
M03B = "module-03b-truthset-visualization/phase1-visualization.md"
M05_1 = "module-05-data-quality-mapping/phase1-quality-assessment.md"
M05_2 = "module-05-data-quality-mapping/phase2-data-mapping.md"
M05_3 = "module-05-data-quality-mapping/phase3-test-load.md"
M06 = "module-06-data-processing/SKILL.md"
M06_A = "module-06-data-processing/phaseA-build-loading.md"
M06_B = "module-06-data-processing/phaseB-load-first-source.md"
M06_D = "module-06-data-processing/phaseD-validation.md"
M07 = "module-07-query-visualize-discover/phase1-query-visualize.md"

ROUTING = ("a tool-routing list or a \"never guess\" rule: says which tool SDK code comes from "
           "(INV-080), not a step that fetches a response")
STATEMENT = "the ground-rules statement itself, which every pointer points at"
SCHEMA = "a parameter or schema note"
HEADER = "a file-header summary; the phase's own steps carry the pointer"
BOOTCAMPER = "advice to the Bootcamper about their own later work"
FETCHED = "a note about a response or code already fetched, not an instruction to obtain it"
M23 = "one of Modules 2 and 3's existing route and terminal statements, or a note beside them"

#: Paragraphs naming the tool that the rule does not flag and that carry no pointer, keyed by
#: (file under `skills/`, a quote from the paragraph), with the reason each is not a site.
NOT_INSTRUCTIONS = {
    (GROUND, "SDK calls from `generate_scaffold` and `get_sdk_reference`"): ROUTING,
    (GROUND, "SDK code -> `generate_scaffold` or `sdk_guide`"): ROUTING,
    (GROUND, "**Working examples: search mode is the reliable route (INV-160).**"): STATEMENT,
    (GROUND, "Three tools answer with a listing instead of content"): STATEMENT,
    (GROUND, "This is the terminal step for both `find_examples` and `generate_scaffold`"):
        STATEMENT,
    (GROUND, "`generate_scaffold` shows the same split **inside one schema**"): SCHEMA,
    (GROUND, "Add the dependency line from the `dependency_note` of the `generate_scaffold` "
             "response"): FETCHED,
    (M02, "`generate_scaffold(language='python', workflow=<any>)` carries the same rule"):
        FETCHED,
    (M02, "The server's `platform_note` on `generate_scaffold(language='python', …)`"): FETCHED,
    (M02, "The authoritative Java snippets from `generate_scaffold`"): FETCHED,
    (M02, "which is exactly the failure `generate_scaffold` exists to prevent"): FETCHED,
    (M02, "So Step 4 needs **one** `generate_scaffold` call:"): M23,
    (M02, "`generate_scaffold(language='<chosen_language>', workflow='information', "
          "version='current')` — the **version-print** half"): M23,
    (M02, "**Never pass `inline=true` to `generate_scaffold`**"): M23,
    (M02, "If `generate_scaffold`, `ExampleEnvironment` or `sdk_guide` defaults to `/tmp/`"):
        FETCHED,
    (M02, "The response is a LISTING and nothing in it marks which snippet does this"): M23,
    (M02, "Fetch it like any other scaffold snippet, by the response's own `access_steps` as "
          "Step 4 says"):
        M23 + "; it fetches by Step 4's statement, which carries the route pointer",
    (M03, "Rewriting the SDK calls to clear an import error is the failure `generate_scaffold`"):
        FETCHED,
    (M05_1, "the rule for `generate_scaffold` and `find_examples`, whose schemas do not declare "
            "`inline`"): SCHEMA,
    (M06_A, "All loading, redo, and query code comes from the MCP tools (`generate_scaffold` / "
            "`sdk_guide`)"): HEADER,
    (M06_A, "**`record_count` is a parameter of `sdk_guide`, not of `generate_scaffold`.**"):
        SCHEMA,
    (M06_A, "that fidelity is the whole reason to use `generate_scaffold`"): FETCHED,
    (M06_B, "Loading and redo code comes from the MCP tools (`generate_scaffold` / `sdk_guide`)"):
        HEADER,
    (M06_D, "Entity queries use SDK code generated via `generate_scaffold`"): HEADER,
    (M07, "point them at `generate_scaffold` for code generation"): BOOTCAMPER,
}

#: Paragraphs the rule flags that are not steps fetching a response, with the reason each is
#: exempt. The rule reads verbs, so a sourcing rule worded as an imperative is flagged too.
INSTRUCTION_SHAPED = {
    (GROUND, "then the install command from the `dependency_note` of the `generate_scaffold` "
             "response"): FETCHED,
    (M02, "Generate SDK code via `generate_scaffold` instead."): ROUTING,
    (M03, "Use the exact config classes/methods returned by `sdk_guide`/`generate_scaffold`"):
        FETCHED,
    (M03B, "Get the exact SDK method, flag, and attribute names from the Senzing MCP tools"):
        ROUTING,
    (M05_2, "Never guess SDK method signatures: use `generate_scaffold` / `get_sdk_reference`."):
        ROUTING,
    (M05_3, "NEVER guess method signatures: use `generate_scaffold` / `get_sdk_reference`."):
        ROUTING,
    (M06, "Use `generate_scaffold` (workflows `add_records`, `redo`, `query`) and `sdk_guide`"):
        HEADER,
    (M06_D, "use `search_docs` and `generate_scaffold` for current guidance on adding new "
            "records"): BOOTCAMPER,
}

#: Module 2 and 3 instructions whose pointer follows later in the same step, under the floors
#: above; the scan checks a cited route pointer follows before the next heading.
POINTER_LATER_IN_STEP = {
    (M02, "Use `generate_scaffold(language='<chosen_language>', workflow='initialize', "
          "version='current')` to get the current V4 initialization"):
        "Step 9; its listing bullet carries the pointer",
    (M02, "keep using `generate_scaffold(workflow='initialize')` (INV-080)"):
        "Step 9; its listing bullet carries the pointer",
    (M03, "Generate an SDK initialization script using `generate_scaffold(workflow='initialize')`"):
        "Step 3; item 2 carries the pointer",
    (M03, "Call `generate_scaffold(workflow='full_pipeline')`"):
        "Step 4; item 2's fetch carries the pointer",
}

#: Instructions to obtain code that the rule does not flag, named here so they are sites all the
#: same: each must carry the pointer, as a flagged site does. An entry the rule flags fails.
SITES_THE_RULE_MISSES = {
    (M02, "Either route is fine"):
        "Step 8 offers a `generate_scaffold` fetch as the alternative to its `sdk_guide` call; "
        "the paragraph opens on the tool as a subject (\"reaches the same code by another "
        "route\"), so no verb is in imperative position",
}

#: The sites #806 named, the two its scan added, and Module 2 Step 8's alternative route. Each
#: must be a site the scan finds.
NAMED_SITES = (
    (M07, "Use `generate_scaffold` with `workflow='query'` and the chosen language"),
    (M05_2, "Use `generate_scaffold` or the mapping workflow output as the foundation"),
    (M05_3, "or generate SDK code with `generate_scaffold` / `find_examples`"),
    (M03B, "and `generate_scaffold` if it exposes a registration workflow"),
    (M03B, "generate the loader via `generate_scaffold`"),
    (M03, "(and `generate_scaffold` if it exposes a data-source registration workflow"),
    (M06_A, "(and `generate_scaffold` if it exposes a data-source registration workflow"),
    (M02, "Either route is fine, a `generate_scaffold` file fetched"),
)
#: How many sites the scan finds today. A floor, so a scan that stops finding them is noticed.
SITE_FLOOR = 14


def skill_texts():
    return {str(p.relative_to(SKILLS)).replace("\\", "/"): p.read_text(encoding="utf-8")
            for p in sorted(SKILLS.rglob("*.md"))}


def missed_site(name, par):
    """The `SITES_THE_RULE_MISSES` quote that names ``par``, or None."""
    return next((q for f, q in SITES_THE_RULE_MISSES if f == name and q in par), None)


def scaffold_sites(texts):
    """Every paragraph the rule flags that no exemption names, and every paragraph
    `SITES_THE_RULE_MISSES` names, as ``(file, start, end, text)``."""
    exempt = {**INSTRUCTION_SHAPED, **POINTER_LATER_IN_STEP}
    return [(name, start, end, par)
            for name, text in texts.items()
            for start, end, par in mention_paragraphs(text)
            if (instruction(par) or missed_site(name, par))
            and not any(f == name and q in par for f, q in exempt)]


def scan_problems(texts):
    """Each mention of the tool is a pointed site or a listed exemption in its right group."""
    groups = (NOT_INSTRUCTIONS, INSTRUCTION_SHAPED, POINTER_LATER_IN_STEP)
    problems, seen = [], set()
    for name, text in texts.items():
        for start, end, par in mention_paragraphs(text):
            said = instruction(par)
            missed = missed_site(name, par)
            if missed:
                seen.add((name, missed))
                if said:
                    problems.append("%s: %r is listed as a site the rule misses, but the rule "
                                    "flags %r" % (name, missed[:60], said[:90]))
                said = said or missed
            keys = [k for g in groups for k in g if k[0] == name and k[1] in par]
            seen.update(keys)
            if missed and keys:
                problems.append("%s: %r is listed both as a site and as an exemption: %r"
                                % (name, missed[:60], [k[1] for k in keys]))
                continue
            if len(keys) > 1:
                problems.append("%s: more than one exemption names one paragraph: %r"
                                % (name, [k[1] for k in keys]))
                continue
            if not keys:
                if CITED_ROUTE_POINTER.search(par):
                    continue
                if said:
                    problems.append(
                        "%s tells the guide to obtain code from `generate_scaffold` with no route "
                        "pointer (%r); add the ground-rules route pointer citing INV-160 and "
                        "INV-300, as the Module 6 sites do" % (name, said[:90]))
                else:
                    problems.append(
                        "%s names `generate_scaffold` with no route pointer and is on no exemption "
                        "list: %r" % (name, par[:90]))
                continue
            key = keys[0]
            if key in NOT_INSTRUCTIONS and said:
                problems.append("%s: %r is listed as no instruction, but the rule flags %r"
                                % (name, key[1][:60], said[:90]))
            if key not in NOT_INSTRUCTIONS and not said:
                problems.append("%s: %r is listed as an instruction the rule flags, and it does "
                                "not" % (name, key[1][:60]))
            if key in POINTER_LATER_IN_STEP:
                step = HEADING.search(text, end)
                if not CITED_ROUTE_POINTER.search(flat(prose(
                        text[end: step.start() if step else len(text)]))):
                    problems.append("%s: no route pointer follows %r before the next heading"
                                    % (name, key[1][:60]))
    for group in groups + (SITES_THE_RULE_MISSES,):
        for key in group:
            if key[0] in texts and key not in seen:
                problems.append("%s: the list entry %r names no paragraph; remove it"
                                % key)
    return problems


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
        for path in MODULE_FLOORS:
            with self.subTest(file=path.name):
                self.assertEqual([], module_problems(path, path.read_text(encoding="utf-8")))


class TheRetiredWordingIsGone(unittest.TestCase):
    def test_no_shipped_file_quotes_an_old_note_or_numbers_inline(self):
        self.assertEqual([], old_wording_problems(shipped_texts()))


class EveryScaffoldInstructionPointsAtTheRoute(unittest.TestCase):
    """#806: the sites are found by scanning (INV-246), each carries the route pointer."""

    @classmethod
    def setUpClass(cls):
        cls.texts = skill_texts()
        cls.sites = scaffold_sites(cls.texts)

    def test_every_mention_is_a_pointed_site_or_a_reasoned_exemption(self):
        self.assertEqual([], scan_problems(self.texts))

    def test_every_site_carries_the_cited_route_pointer(self):
        for name, _, _, par in self.sites:
            with self.subTest(file=name, site=par[:70]):
                self.assertRegex(par, CITED_ROUTE_POINTER)

    def test_the_named_sites_are_found_by_the_scan(self):
        for name, quote in NAMED_SITES:
            with self.subTest(file=name, site=quote):
                self.assertTrue(any(f == name and quote in par for f, _, _, par in self.sites),
                                "the scan does not find %s: %r" % (name, quote))

    def test_the_scan_finds_at_least_todays_sites(self):
        self.assertGreaterEqual(len(self.sites), SITE_FLOOR)

    def test_every_exemption_has_a_reason(self):
        for group in (NOT_INSTRUCTIONS, INSTRUCTION_SHAPED, POINTER_LATER_IN_STEP,
                      SITES_THE_RULE_MISSES):
            for key, reason in group.items():
                with self.subTest(exemption=key):
                    self.assertTrue(reason.strip())


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


class TheScaffoldScanFiresOnMutants(unittest.TestCase):
    """Each control runs the scan on a mutated in-memory copy of the shipped skills."""

    @classmethod
    def setUpClass(cls):
        cls.texts = skill_texts()

    def mutant(self, name, old, new):
        texts = dict(self.texts)
        texts[name] = _replace(texts[name], old, new)
        return texts

    def test_the_pointer_removed_from_each_site(self):
        sites = scaffold_sites(self.texts)
        self.assertGreaterEqual(len(sites), SITE_FLOOR)
        for name, start, end, par in sites:
            with self.subTest(file=name, site=par[:70]):
                text = self.texts[name]
                cut = RAW_ROUTE_POINTER.sub("ground-rules.md` says (INV-160, INV-300)",
                                            text[start:end], count=1)
                self.assertNotEqual(cut, text[start:end], "the site holds no raw pointer")
                problems = scan_problems({**self.texts, name: text[:start] + cut + text[end:]})
                self.assertTrue([p for p in problems if p.startswith(name + " tells the guide")])

    def test_a_new_unpointed_instruction(self):
        for line in ("Call `generate_scaffold(language='<chosen_language>', workflow='delete')` "
                     "for the deletion code.",
                     "Generate the export program via `generate_scaffold` and save it.",
                     "Once the queue is empty (then use `generate_scaffold` for the redo code)."):
            with self.subTest(line=line):
                texts = self.mutant(M07, "### ", line + "\n\n### ")
                self.assertTrue([p for p in scan_problems(texts) if "tells the guide" in p])

    def test_a_new_unlisted_mention(self):
        texts = self.mutant(M07, "### ", "The `generate_scaffold` listing names each file.\n\n### ")
        self.assertTrue([p for p in scan_problems(texts) if "on no exemption list" in p])

    def test_an_exemption_whose_text_is_gone(self):
        texts = self.mutant(M07, "point them at `generate_scaffold` for code",
                            "point them at the scaffold tool for code")
        self.assertTrue([p for p in scan_problems(texts) if "names no paragraph" in p])

    def test_an_exempt_paragraph_that_becomes_an_instruction(self):
        texts = self.mutant(M07, "When the bootcamper asks about integration, point them at",
                            "Call `generate_scaffold` for the export code. When the bootcamper "
                            "asks about integration, point them at")
        self.assertTrue([p for p in scan_problems(texts) if "listed as no instruction" in p])

    def test_a_later_pointer_removed_from_a_module_3_step(self):
        text = self.texts[M03]
        start = text.index("### Step 3: SDK Initialization")
        end = text.index("### Step 4: Code Generation")
        cut = RAW_ROUTE_POINTER.sub("ground-rules.md`", text[start:end], count=1)
        self.assertNotEqual(cut, text[start:end])
        problems = scan_problems({**self.texts, M03: text[:start] + cut + text[end:]})
        self.assertTrue([p for p in problems if "no route pointer follows" in p])

    def test_module_2_step_8s_alternative_route_loses_its_pointer(self):
        text = self.texts[M02]
        start = text.index("Either route is fine")
        end = text.index("Step 9's connection test", start)
        cut = RAW_ROUTE_POINTER.sub("ground-rules.md` says (INV-160, INV-300)",
                                    text[start:end], count=1)
        self.assertNotEqual(cut, text[start:end], "Step 8's alternative holds no raw pointer")
        problems = scan_problems({**self.texts, M02: text[:start] + cut + text[end:]})
        self.assertTrue([p for p in problems if p.startswith(M02 + " tells the guide")])
        gone = self.mutant(M02, "Either route is fine", "Both routes work")
        self.assertTrue([p for p in scan_problems(gone) if "names no paragraph" in p])

    def test_the_rule_reads_verbs_in_imperative_position(self):
        for said in ("Use `generate_scaffold` with `workflow='query'`.",
                     "Per the routing, get counts via `reporting_guide`, or generate SDK code with "
                     "`generate_scaffold` / `find_examples`.",
                     "Call `sdk_guide` (and `generate_scaffold` if it exposes one).",
                     "2. **Generate the loader** via `generate_scaffold`."):
            with self.subTest(said=said):
                self.assertIsNotNone(instruction(said))
        for said in ("When asked, point them at `generate_scaffold` for code generation.",
                     "Entity queries use SDK code generated via `generate_scaffold`.",
                     "That fidelity is the whole reason to use `generate_scaffold`.",
                     "`generate_scaffold` returns a listing. Fetch each file."):
            with self.subTest(said=said):
                self.assertIsNone(instruction(said))


if __name__ == "__main__":
    unittest.main()
