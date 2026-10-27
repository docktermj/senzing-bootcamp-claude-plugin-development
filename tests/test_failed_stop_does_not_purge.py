"""An unverified server stop never purges the Truth Set, and one rule says so (#673).

Enforces **INV-394**, registered by the maintainer 2026-10-20: an irreversible cleanup waits on
a confirmed stop rather than an unverified one. ⚠️ It reads the shipped prose and drives the
scripted half; it **cannot** establish that a live run actually confirmed the stop before purging.

Two shipped statements of one rule disagreed about what a *warned but unconfirmed* stop
authorizes. `phase2-close.md` Step 4 said "Do not start step 4 until the port is confirmed free
**or the bootcamper has been warned**", and step 4 is the irreversible purge; the server-lifetime
contract in `visualization-api-reference.md` said that if the port still answers after the
force-stop and the re-check, report it and "continue without the purge". A warning cannot both
authorize and forbid deleting records something may still be serving, and the contract wins: it is
the file every module's server behavior is built from (INV-090), and the purge is irreversible.

**One rule, stated once (INV-300).** The failed-stop rule lives in the contract, in an anchored
passage (`#failed-stop`) that declares itself the canonical statement and enumerates the four
outcomes a teardown can reach — a graceful stop confirmed, a force-stop confirmed, a port still
listening after the force-stop and the re-check, and no live server having run at all — saying for
each whether the irreversible step it gates may follow. Only a **confirmed** stop lets the purge
run. The close instructions point at it and state only their own action.

So the checks are:

- `rule_problems`: the canonical passage carries every clause, one entry per clause, and each of
  the four outcomes says what may follow it;
- `deferral_problems`: every close site links the anchor and cites the invariant it defers under;
- `copy_problems`: no close site carries a contract-only phrase — the second copy INV-300 forbids.
  ⚠️ The ⛔ at Step 4 item 3 ("Do not start step 4 until the port is confirmed free. A warning is
  **not** a substitute for that confirmation.") is **not** a copy and is not scanned for: it is the
  gate's own action at the site that performs it, the same exemption `#512` gives Step 4 for naming
  the items it skips. What it must not do is state the alternative, which `warned_shape_problems`
  checks;
- `warned_shape_problems`: derived by scanning every shipped Markdown file (INV-246), never from a
  list — a "confirmed free … warned" shape anywhere must sit inside a prohibition, exactly as
  `pkill` must. The contract's own quotation of the retired wording is such a prohibition;
- `record_problems`: the close records what cleanup actually did and claims nothing more — the
  `cleanup` checkpoint and its two reasons, the recap clause, and both success indicators.

**Every module that stops a server, not only the Truth Set's (#803; INV-394's dated note of
2026-10-23, applied 2026-10-26).** Module 7 stops its own
visualization server and gates no purge, so outcome 3 states two cases: where the module's teardown
gates a purge, every clause above (no purge, the records still loaded, re-run the cleanup program);
where it gates none, report the unverified stop, say the server is still running, and continue.
"A warning is not a substitute" and "This reports; it does not block" sit after both cases, so they
hold for every module. Three more checks follow from that:

- `case_problems`: outcome 3 carries both cases in order, each purge clause inside the purge case,
  the no-purge disposition inside the other, and the every-module clauses outside both;
- `scanned_site_problems`: the stop sites are found by **scanning** every shipped Markdown file
  (INV-246), never from a list. A site is every passage that stops a server by its pid ("stop it by
  the pid") and every teardown gate (👉 "Ready for me to stop the visualization server…"). A pid
  passage must link `visualization-api-reference.md#failed-stop` and cite INV-394 in the passage
  itself; a list item is its own passage, so a link on a neighboring item does not count. A gate
  is a pinned question that ends the turn and can carry no link, so its unit is the gate and its
  answers, up to the next heading. The contract's own gate lines are the gate's definition, beside
  the rule, and are not sites;
- `module7_problems`: Module 7's teardown "Yes" says, on outcome 3, that the stop is unverified and
  what was observed, never that the server stopped, and makes the "No" branch's still-running
  statement rather than a second one; Module 7 records no new outcome (no `stop_unverified`).

`copy_problems` reads Module 7's file too, since it now defers to the same rule.

Each check is a pure function over the shipped text, so each runs on a mutated copy as its negative
control and must report the clause it targets. Phrases are matched with `_wrapped_text.match_lines`
(INV-346), so a re-flow cannot turn the guard red and a wrapped regression cannot turn it green.

⛔ **The non-blocking half is asserted, not assumed.** The rule reports and never blocks: the module
still closes on an unverified stop. A guard that only forbade the purge would license a run that
stops the module instead, which is the other way to lose the Bootcamper's handoff.

**Establishes one invariant, drafted in this issue's `specs/IMPLEMENTED.md` entry as a
`DEFERRED INVARIANT` block.** INV-223 requires the pid, the port fallback and the port-free exit
condition; it does not say what happens when that exit condition is *never met*. INV-131 orders the
teardown last; it does not say the purge is skipped. This file asserts the rule that fills that gap.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issues: #673; #803 (Module 7's stop sites, outcome 3 for a module with no purge, the scan).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _corpus
from _wrapped_text import blocks, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-03b-truthset-visualization")
CONTRACT = MODULE / "visualization-api-reference.md"
PHASE2 = MODULE / "phase2-close.md"
SKILL = MODULE / "SKILL.md"
MODULE7 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
           / "module-07-query-visualize-discover" / "phase1-query-visualize.md")

ANCHOR = '<a id="failed-stop"></a>'
#: The link every close site uses to reach the canonical passage from another file.
RULE_LINK = "(visualization-api-reference.md#failed-stop)"
#: The paragraph that follows the canonical passage; the region ends there.
RULE_END = "\n**The teardown gate.**"


def read(path):
    return path.read_text(encoding="utf-8")


def has(text, pattern, flags=re.I | re.S):
    """True when ``pattern`` matches ``text`` anywhere, across a line wrap (INV-346)."""
    return bool(match_lines(text, re.compile(pattern, flags)))


def between(text, start, end=None):
    """The text from ``start`` up to ``end`` (or the end of the text); None if ``start`` is gone."""
    begin = text.find(start)
    if begin < 0:
        return None
    if end is None:
        return text[begin:]
    stop = text.find(end, begin + len(start))
    return text[begin:stop if stop >= 0 else len(text)]


# --------------------------------------------------------------------------------------------
# The canonical statement
# --------------------------------------------------------------------------------------------

#: (label, pattern) for each clause of the rule. A label is what a problem names.
RULE_CLAUSES = (
    ("owner declaration",
     r"This is the canonical statement of what each teardown outcome allows"),
    ("points here rather than restating", r"point here rather than restating it"),
    ("INV-300", r"INV-300"),
    ("only a confirmed stop", r"only a \*\*confirmed\*\* stop lets anything irreversible follow"),
    ("the invariants it rests on", r"\(INV-223, INV-131\)"),
    ("outcome 1: graceful stop confirmed", r"\*\*Graceful stop confirmed\.\*\*"),
    ("outcome 1: the poll is what confirms it",
     r"The port stops answering within the 5-second poll"),
    ("outcome 2: force-stop confirmed", r"\*\*Force-stop confirmed\.\*\*"),
    ("outcome 2: the re-check is what confirms it", r"the re-check finds nothing listening"),
    ("outcome 3: the stop is unverified",
     r"the stop is UNVERIFIED, and nothing irreversible may follow it"),
    ("outcome 3: say so plainly",
     r"When teardown cannot confirm, say so plainly and do not claim the server stopped"),
    ("outcome 3: the port and its listener are reported",
     r"the port, that something is still listening on it"),
    ("outcome 3: the purge case", r"\*\*Where the module's teardown gates a purge\*\*"),
    ("outcome 3: the no-purge case", r"\*\*Where it gates none\*\*"),
    ("outcome 3: the retained records are reported", r"the records are still loaded"),
    ("outcome 3: no purge",
     r"continue without the purge rather than purging on an unverified stop"),
    ("outcome 3: what is left to do by hand",
     r"release the listener, then re-run the module's cleanup program"),
    ("outcome 3: with no purge, the server is still running",
     r"there is no purge to withhold, so say that the server is still running"),
    ("outcome 3: with no purge, the module continues", r"then continue to the module's completion"),
    ("outcome 3: a warning is not authorization",
     r"A warning is not a substitute for the confirmation"),
    ("outcome 3: the retired alternatives are named",
     r"confirmed free \*\*or\*\* the Bootcamper has been warned"),
    ("outcome 3: a false success is worse than a failure",
     r"reports success while the port answers is worse than one that reports failure"),
    ("outcome 3: the container form that was tried",
     r"name the `<runtime> exec` form that was tried"),
    ("outcome 3: it reports and does not block", r"This reports; it does not block"),
    ("outcome 4: no live server ran", r"\*\*No live server ran at all\.\*\*"),
    ("outcome 4: nothing to verify or report",
     r"there is no stop to verify and no listener to report"),
    ("outcome 4: the purge is still owed", r"still owes whatever data purge it owes"),
    ("outcome 4: points at the no-live-server rule",
     r'`phase2-close\.md` → "No-live-server completion"'),
)

#: (label, pattern) for the disposition each outcome gives the irreversible step it gates.
#: This is the issue's coverage criterion: all four cases answered, in one place.
OUTCOME_DISPOSITIONS = (
    ("graceful stop", r"\*\*Graceful stop confirmed\.\*\*.{0,400}?may run"),
    ("force-stop success", r"\*\*Force-stop confirmed\.\*\*.{0,400}?the purge may run"),
    ("still listening", r"UNVERIFIED.{0,2000}?continue without the purge"),
    ("no live server", r"\*\*No live server ran at all\.\*\*.{0,400}?"
                       r"still owes whatever data purge it owes"),
)


def rule_region(text):
    """The canonical passage: from its anchor to the teardown gate below it."""
    return between(text, ANCHOR, RULE_END)


def rule_problems(text):
    """Problems with the canonical statement in ``text`` (all of the contract file)."""
    region = rule_region(text)
    if region is None:
        return ["the canonical passage's anchor %s is gone" % ANCHOR]
    problems = []
    above = between(text, "## Server lifetime", ANCHOR) or ""
    if "### Identifying the server process" not in above:
        problems.append("the canonical passage sits outside 'Identifying the server process'")
    for label, pattern in RULE_CLAUSES:
        if not has(region, pattern):
            problems.append("the canonical passage is missing: %s" % label)
    for label, pattern in OUTCOME_DISPOSITIONS:
        if not has(region, pattern):
            problems.append("the canonical passage does not say what follows: %s" % label)
    return problems


def flat(text):
    """``text`` with every run of whitespace made one space, so a wrapped phrase is one string."""
    return re.sub(r"\s+", " ", text)


#: The labels that open outcome 3's two cases, in the order they appear (#803).
PURGE_CASE = "**Where the module's teardown gates a purge**"
NO_PURGE_CASE = "**Where it gates none**"
#: The first clause stated for every module; both cases end where it begins.
EVERY_MODULE = "A warning is not a substitute for the confirmation"

#: (case, label, phrase): the clauses each case must carry. The purge case keeps every clause
#: #673 wrote for Module 3b; the no-purge case reports and continues.
CASE_CLAUSES = (
    ("purge", "the retained records", "the records are still loaded"),
    ("purge", "no purge on an unverified stop",
     "continue without the purge rather than purging on an unverified stop"),
    ("purge", "what is left to do by hand",
     "release the listener, then re-run the module's cleanup program"),
    ("no-purge", "the server is still running", "say that the server is still running"),
    ("no-purge", "the module continues", "then continue to the module's completion"),
)

#: Clauses that hold for every module, so neither case may own them.
EVERY_MODULE_CLAUSES = (
    "When teardown cannot confirm, say so plainly and do not claim the server stopped",
    "the pid the port lookup names where it names one",
    EVERY_MODULE,
    "This reports; it does not block",
)


def case_problems(text):
    """Problems with outcome 3's two cases in ``text`` (all of the contract file)."""
    region = rule_region(text)
    if region is None:
        return ["the canonical passage's anchor %s is gone" % ANCHOR]
    region = flat(region)
    start = region.find("the stop is UNVERIFIED")
    purge, none, every = (region.find(PURGE_CASE), region.find(NO_PURGE_CASE),
                          region.find(EVERY_MODULE))
    if not 0 <= start < purge < none < every:
        return ["outcome 3 does not state its two cases in order: the purge case, the no-purge "
                "case, then what holds for every module"]
    spans = {"purge": region[purge:none], "no-purge": region[none:every]}
    problems = []
    for case, label, phrase in CASE_CLAUSES:
        if phrase not in spans[case]:
            problems.append("outcome 3's %s case is missing: %s" % (case, label))
    for phrase in EVERY_MODULE_CLAUSES:
        at = region.find(phrase)
        if at < 0:
            problems.append("outcome 3 is missing a clause for every module: %s" % phrase)
        elif purge <= at < every:
            problems.append("outcome 3 scopes a clause for every module to one case: %s" % phrase)
    if "purge may run" in spans["no-purge"] or "cleanup program" in spans["no-purge"]:
        problems.append("outcome 3's no-purge case speaks of a purge it does not gate")
    return problems


# --------------------------------------------------------------------------------------------
# The sites that defer to it
# --------------------------------------------------------------------------------------------

#: The invariant each site may defer under. INV-300 is the single-statement discipline; INV-223 is
#: the pid-and-port rule the teardown steps rest on; INV-394 is the failed-stop rule the success
#: indicators summarize (#787).
DEFERRAL_INVARIANTS = ("INV-300", "INV-223", "INV-394")


def sites():
    """{label: region} for every close site that must point at the canonical passage."""
    p2, sk = read(PHASE2), read(SKILL)
    return {
        "phase2 Step 4 port confirmation":
            between(p2, "   - **Confirm the port is free**", "\n4. **Purge"),
        "phase2 Step 4 purge":
            between(p2, "4. **Purge the Truth Set data", "5. **Retain visualization artifacts"),
        "phase2 Step 4 checkpoint":
            between(p2, "**Checkpoint:** write to `config/bootcamp_progress.json`. Record what",
                    "## Step 5"),
        "phase2 success indicator": between(p2, "**Success indicator:**"),
        "SKILL success indicator": between(sk, "**Success indicator:**"),
    }


def deferral_problems(site_map=None):
    """Each site that does not link the canonical passage, or does not cite its invariant."""
    problems = []
    for label, region in (site_map or sites()).items():
        if region is None:
            problems.append("%s: the site is gone" % label)
            continue
        if RULE_LINK not in re.sub(r"\s+", "", region):
            problems.append("%s: no link to the canonical passage %s" % (label, RULE_LINK))
        if not any(has(region, inv) for inv in DEFERRAL_INVARIANTS):
            problems.append("%s: the deferral cites neither %s" % (label, " nor ".join(
                DEFERRAL_INVARIANTS)))
    return problems


#: Phrases only the canonical passage may carry. A close site carrying one has started a copy.
CONTRACT_ONLY = (
    r"\*\*Graceful stop confirmed\.\*\*",
    r"\*\*Force-stop confirmed\.\*\*",
    r"\*\*No live server ran at all\.\*\*",
    r"the pid the port lookup names",
    r"release the listener, then re-run the module's cleanup program",
    r"walks away believing their machine is clean",
    r"This reports; it does not block",
)


def copy_problems(texts=None):
    """Each close file that restates a clause the canonical passage owns."""
    texts = texts if texts is not None else {p.name: read(p) for p in (PHASE2, SKILL, MODULE7)}
    return ["%s restates the rule (%s)" % (name, phrase)
            for name, text in sorted(texts.items())
            for phrase in CONTRACT_ONLY if has(text, phrase)]


# --------------------------------------------------------------------------------------------
# Every stop site, found by scanning (#803)
# --------------------------------------------------------------------------------------------

#: A passage that stops a server by its recorded pid. Case-insensitive: a sentence may open with it.
PID_STOP = re.compile(r"(?i)\bstop (?:it|the (?:visualization )?server) by the pid\b")
#: A teardown gate: the pinned question that asks to stop a visualization server.
TEARDOWN_GATE = re.compile(r"👉 \*\*Ready for me to stop the visualization server")
#: What every site must carry: the link to the rule and the invariant it applies.
SITE_LINK = "visualization-api-reference.md#failed-stop"
SITE_INVARIANT = "INV-394"
#: A line that starts a list item; each item is its own passage.
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
HEADING = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")


def passages(text):
    """(first line, flat text, is heading) for each passage of ``text``, in order.

    A passage is a Markdown block (``_wrapped_text.blocks``: blank lines, headings, fences,
    blockquote markers stripped), cut again at each list item, so a link on one answer of a gate
    does not count for the answer beside it.
    """
    out = []
    for block in blocks(text):
        current = []
        for lineno, line in block:
            if current and LIST_ITEM.match(line):
                out.append(current)
                current = []
            current.append((lineno, line))
        out.append(current)
    return [(lines[0][0], flat(" ".join(line for _, line in lines)).strip(),
             bool(HEADING.match(lines[0][1])))
            for lines in out if lines]


def scanned_sites(texts=None):
    """[(path, line, kind, region)] for every stop site in ``texts``, found by scanning."""
    texts = texts if texts is not None else shipped_markdown()
    found = []
    for path, text in sorted(texts.items(), key=lambda kv: str(kv[0])):
        ps = passages(text)
        for i, (line, body, _) in enumerate(ps):
            if PID_STOP.search(body):
                found.append((path, line, "pid stop", body))
            if TEARDOWN_GATE.search(body) and path != CONTRACT:
                end = next((j for j in range(i + 1, len(ps)) if ps[j][2]), len(ps))
                found.append((path, line, "teardown gate",
                              " ".join(b for _, b, _ in ps[i:end])))
    return found


def shown(path):
    return path.relative_to(REPO_ROOT).as_posix() if isinstance(path, Path) else str(path)


def scanned_site_problems(texts=None):
    """Each scanned stop site that does not link the failed-stop rule or cite INV-394."""
    problems = []
    for path, line, kind, region in scanned_sites(texts):
        if SITE_LINK not in region.replace(" ", ""):
            problems.append("%s:%d: the %s does not link %s" % (shown(path), line, kind, SITE_LINK))
        if SITE_INVARIANT not in region:
            problems.append("%s:%d: the %s does not cite %s"
                            % (shown(path), line, kind, SITE_INVARIANT))
    return problems


def teardown_answers(text):
    """{"yes": passage, "no": passage} for Module 7's teardown gate; a missing one is None."""
    section = between(text, "## Visualization server teardown", "\n## Module completion") or ""
    found = {"yes": None, "no": None}
    for _, body, _ in passages(section):
        if body.startswith("- **Yes:**"):
            found["yes"] = body
        elif body.startswith("- **No or not yet:**"):
            found["no"] = body
    return found


#: (label, answer, pattern) for what Module 7 says on an unverified stop.
MODULE7_CLAUSES = (
    ("the unverified stop is said plainly", "yes",
     r"On its outcome 3 the stop is unverified: say so plainly"),
    ("what was observed", "yes",
     r"what was observed \(the port, that something still answers on it"),
    ("never that the server stopped", "yes", r"never that the server stopped"),
    ("the No branch's statement is reused", "yes",
     r"make the \"No\" branch's closing statement below: that it is still running"),
    ("then the module completes", "yes", r"Then continue to module completion below"),
    ("the statement it reuses", "no", r"say plainly that it is still running and how to stop it"),
)


def module7_problems(text):
    """Problems with what Module 7's teardown says on an unverified stop, in ``text``."""
    answers = teardown_answers(text)
    problems = []
    for label, answer, pattern in MODULE7_CLAUSES:
        if answers[answer] is None:
            problems.append("Module 7's teardown %s answer is gone" % answer)
        elif not re.search(pattern, answers[answer]):
            problems.append("Module 7's teardown is missing: %s" % label)
    if "stop_unverified" in text:
        problems.append("Module 7 records a stop outcome; it says so and records nothing new")
    return problems


# --------------------------------------------------------------------------------------------
# The retired wording, wherever it reappears
# --------------------------------------------------------------------------------------------

#: The contradiction itself: a confirmed-free port offered as one of two alternatives with a
#: warning. `[^.]` keeps the match inside one sentence.
WARNED_SHAPE = re.compile(r"(?i)confirmed free[^.]{0,80}?\bwarn")


def shipped_markdown():
    """{path: text} for every shipped Markdown file, derived by scanning (INV-246)."""
    return {p: read(p) for p in _corpus.corpus_files("plugins", suffixes={".md"})}


def _quoted_history(text):
    """The line span of the canonical passage, which quotes the retired wording to forbid it.

    ⛔ A prohibition cannot be told from an authorization by the words around it: the retired
    instruction was itself written "⛔ Do not start step 4 until the port is confirmed free **or**
    the bootcamper has been warned", so every prohibiting word was already there. The one place the
    shape may appear is inside the rule that retires it, and that is checked by **location** —
    the same quoted-history exemption `specs/DECLINED.md` gives a retracted claim.
    """
    start = text.find(ANCHOR)
    if start < 0:
        return (0, 0)
    stop = text.find(RULE_END, start)
    return (text[:start].count("\n") + 1,
            text[:stop if stop >= 0 else len(text)].count("\n") + 1)


def warned_shape_problems(texts=None):
    """Each place the retired "confirmed free … warned" shape appears outside the rule."""
    texts = texts if texts is not None else shipped_markdown()
    problems = []
    for path, text in sorted(texts.items(), key=lambda kv: str(kv[0])):
        first, last = _quoted_history(text)
        for line in match_lines(text, WARNED_SHAPE):
            if first <= line <= last:
                continue
            shown = path.relative_to(REPO_ROOT).as_posix() if isinstance(path, Path) else path
            problems.append("%s:%d offers a warning as an alternative to a confirmed-free port"
                            % (shown, line))
    return problems


# --------------------------------------------------------------------------------------------
# What the close records and what it claims
# --------------------------------------------------------------------------------------------

#: (label, region getter, pattern) for each thing the close must record or must not claim.
RECORD_CLAUSES = (
    ("the cleanup record exists", "phase2 Step 4 checkpoint",
     r"`truthset_visualization\.checks\.cleanup`"),
    ("the complete shape", "phase2 Step 4 checkpoint", r'`\{"status": "complete"\}`'),
    ("the incomplete shape", "phase2 Step 4 checkpoint",
     r'"status": "incomplete", "reason": "stop_unverified\|purge_failed"'),
    ("the retained records are recorded", "phase2 Step 4 checkpoint",
     r'"truthset_records": "retained"'),
    ("the listening port is recorded", "phase2 Step 4 checkpoint", r'"port": <port>'),
    ("the record is not a gate", "phase2 Step 4 checkpoint",
     r"`cleanup` is a record, not a gate"),
    ("an incomplete cleanup never blocks", "phase2 Step 4 checkpoint",
     r"never blocks this module"),
    ("the recap says what cleanup did", "phase2 recap",
     r"The recap says what cleanup actually did"),
    ("the recap claims no cleanup it did not do", "phase2 recap",
     r"says the server was stopped or the data removed"),
    ("the success indicator admits the unconfirmed stop", "phase2 success indicator",
     r"where the stop could not be confirmed"),
    ("the success indicator claims no cleanup", "phase2 success indicator",
     r"instead of a cleanup being claimed"),
    ("the module's success indicator admits it", "SKILL success indicator",
     r"where the stop could not be confirmed"),
    ("the module's success indicator claims no cleanup", "SKILL success indicator",
     r"rather than a cleanup claimed"),
)


def record_regions():
    regions = sites()
    regions["phase2 recap"] = between(read(PHASE2), "2. **Append the recap section**",
                                      "3. **Present the completion line")
    return regions


def record_problems(regions=None):
    regions = regions if regions is not None else record_regions()
    problems = []
    for label, site, pattern in RECORD_CLAUSES:
        region = regions.get(site)
        if region is None:
            problems.append("%s: the site is gone" % site)
        elif not has(region, pattern):
            problems.append("%s: missing %s" % (site, label))
    return problems


def without(text, pattern):
    """``text`` with the line each match of ``pattern`` starts on removed (wrap-aware).

    A phrase wrapped across two lines is not a substring of the raw text, so ``re.sub`` would
    leave it in place and the negative control would pass by changing nothing (INV-346).
    """
    lines = text.split("\n")
    drop = {n - 1 for n in match_lines(text, re.compile(pattern, re.I | re.S))}
    return "\n".join(line for i, line in enumerate(lines) if i not in drop)


# --------------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------------


class TheContractOwnsTheFailedStopRule(unittest.TestCase):
    def test_the_canonical_statement_carries_every_clause(self):
        self.assertEqual([], rule_problems(read(CONTRACT)))

    def test_the_anchor_is_stated_once(self):
        """A second anchor would make every link ambiguous; the rule is stated once (INV-300)."""
        total = sum(read(p).count('id="failed-stop"') for p in sorted(MODULE.glob("*.md")))
        self.assertEqual(1, total, "the failed-stop anchor appears %d times" % total)

    def test_it_sits_inside_the_server_lifetime_contract(self):
        text = read(CONTRACT)
        lifetime = text.find("## Server lifetime")
        section = text.find("### Identifying the server process")
        anchor = text.find(ANCHOR)
        self.assertLess(lifetime, section, "'Server lifetime' no longer precedes the pid rule")
        self.assertLess(section, anchor,
                        "the failed-stop rule sits outside 'Identifying the server process', "
                        "which is where the teardown route it judges is stated")


class EveryTeardownOutcomeSaysWhatMayFollow(unittest.TestCase):
    """The issue's coverage criterion: four outcomes, each with its disposition."""

    def setUp(self):
        self.region = rule_region(read(CONTRACT))

    def test_a_confirmed_stop_lets_the_purge_run(self):
        for label, pattern in OUTCOME_DISPOSITIONS[:2]:
            with self.subTest(outcome=label):
                self.assertTrue(has(self.region, pattern),
                                "%s does not say the purge may follow it" % label)

    def test_an_unverified_stop_does_not_purge(self):
        self.assertTrue(
            has(self.region, OUTCOME_DISPOSITIONS[2][1]),
            "the still-listening outcome no longer forbids the purge — the contradiction #673 "
            "closed is back")

    def test_no_live_server_still_owes_its_purge(self):
        self.assertTrue(
            has(self.region, OUTCOME_DISPOSITIONS[3][1]),
            "the no-live-server case is not answered, so a module that never started a server "
            "reads as a failed teardown and keeps records it was supposed to remove")

    def test_the_rule_reports_and_never_blocks(self):
        self.assertTrue(
            has(self.region, r"The module still closes and the handoff is unchanged"),
            "nothing says the unverified stop is non-blocking, so a reader may stop the module "
            "instead — losing the handoff the other way")


class TheCloseDefersRatherThanRestates(unittest.TestCase):
    def test_every_site_links_the_rule_and_cites_it(self):
        self.assertEqual([], deferral_problems())

    def test_no_site_carries_a_second_copy(self):
        self.assertEqual([], copy_problems())

    def test_the_gate_at_step_4_states_its_own_action(self):
        """⛔ Not a copy: this is the gate the close itself performs (the #512 exemption)."""
        region = sites()["phase2 Step 4 port confirmation"]
        self.assertTrue(
            has(region, r"Do not start step 4 until the port is confirmed free"),
            "the gate that keeps the irreversible purge behind a confirmed-free port is gone")
        self.assertTrue(
            has(region, r"A warning is \*\*not\*\* a substitute for that confirmation"),
            "the gate no longer says a warning does not stand in for the confirmation, which is "
            "the exact substitution #673 removed")

    def test_the_purge_item_runs_only_after_a_confirmed_stop(self):
        region = sites()["phase2 Step 4 purge"]
        self.assertTrue(
            has(region, r"only after a confirmed stop, or where no server ran at all"),
            "the purge item no longer names the condition it waits on")
        self.assertTrue(
            has(region, r"On an unverified stop this item does not run"),
            "the purge item does not say it is skipped on an unverified stop")


class OutcomeThreeReadsForEveryModule(unittest.TestCase):
    """#803: the purge case keeps Module 3b's clauses; the no-purge case reports and continues."""

    def test_both_cases_are_stated(self):
        self.assertEqual([], case_problems(read(CONTRACT)))


class EveryStopSiteIsFoundAndDefers(unittest.TestCase):
    """#803: the sites come from a scan of shipped Markdown, never from a list of files."""

    def test_every_scanned_site_links_the_rule_and_cites_inv_394(self):
        self.assertEqual([], scanned_site_problems())

    def test_the_scan_finds_the_known_sites(self):
        """⛔ INV-265: the floor. A scan that finds nothing passes by inspecting nothing."""
        found = [(path, kind, region) for path, _, kind, region in scanned_sites()]
        expected = (
            (MODULE7, "pid stop", "captured when it was started, never by a command-line pattern"),
            (MODULE7, "pid stop", "Yes:** stop it by the pid recorded in the `m7_visualizations`"),
            (MODULE7, "teardown gate", "Ready for me to stop the visualization server?**"),
            (PHASE2, "teardown gate", "and clean up the Truth Set data?**"),
        )
        for path, kind, quote in expected:
            with self.subTest(site=quote):
                self.assertTrue(any(p == path and k == kind and quote in r for p, k, r in found),
                                "the scan no longer finds %s's %s" % (path.name, kind))

    def test_the_contracts_own_gate_lines_are_not_sites(self):
        self.assertFalse([s for s in scanned_sites({CONTRACT: read(CONTRACT)})
                          if s[2] == "teardown gate"])

    def test_module7_says_so_and_never_that_it_stopped(self):
        self.assertEqual([], module7_problems(read(MODULE7)))


class NoSiteOffersAWarningAsAnAlternative(unittest.TestCase):
    def test_the_retired_wording_is_gone_or_quoted_as_forbidden(self):
        self.assertEqual([], warned_shape_problems())

    def test_the_scan_found_the_corpus(self):
        """⛔ INV-265: a scan over an empty corpus passes by inspecting nothing."""
        texts = shipped_markdown()
        self.assertGreaterEqual(len(texts), 20,
                                "only %d shipped Markdown files found" % len(texts))
        self.assertIn(CONTRACT, texts, "the contract is not among the scanned files")
        self.assertIn(PHASE2, texts, "the close is not among the scanned files")

    def test_the_close_no_longer_carries_the_contradiction(self):
        self.assertFalse(
            has(read(PHASE2), r"confirmed free or the bootcamper has been warned"),
            "Step 4 still authorizes the irreversible purge on a warning alone")


class TheCloseRecordsWhatCleanupDid(unittest.TestCase):
    def test_every_record_clause_is_present(self):
        self.assertEqual([], record_problems())

    def test_the_cleanup_record_is_not_a_gate(self):
        """Non-blocking handoff: the record informs the close; it never stops the module."""
        region = sites()["phase2 Step 4 checkpoint"]
        self.assertTrue(has(region, r"reads `web_service` and `web_page` only"),
                        "the checkpoint does not say the pre-advancement gate ignores `cleanup`, "
                        "so a reader may treat an incomplete cleanup as a blocker")


class TheChecksSeeSomething(unittest.TestCase):
    """⛔ INV-265: a guard over an empty site list passes by inspecting nothing."""

    def test_every_site_is_found(self):
        found = {label: region for label, region in record_regions().items() if region}
        self.assertEqual(6, len(found),
                         "sites not found: %s" % sorted(set(record_regions()) - set(found)))

    def test_the_rule_clauses_are_numerous(self):
        self.assertGreaterEqual(len(RULE_CLAUSES), 20)
        self.assertEqual(4, len(OUTCOME_DISPOSITIONS))


class TheChecksCatchARegression(unittest.TestCase):
    """Each removal must be reported by the clause it removed, not merely by some problem."""

    def setUp(self):
        self.contract = read(CONTRACT)
        self.phase2 = read(PHASE2)
        self.skill = read(SKILL)

    def test_the_anchor_removed(self):
        self.assertEqual(["the canonical passage's anchor %s is gone" % ANCHOR],
                         rule_problems(self.contract.replace(ANCHOR, "")))

    def test_each_clause_removed_is_reported_by_name(self):
        region = rule_region(self.contract)
        for label, pattern in RULE_CLAUSES:
            if label == "INV-300":
                continue  # cited more than once in the passage; covered by the pointer checks
            with self.subTest(clause=label):
                broken = self.contract.replace(region, without(region, pattern))
                self.assertIn("the canonical passage is missing: %s" % label,
                              rule_problems(broken))

    def test_the_still_listening_outcome_softened_to_a_purge(self):
        """The defect itself: outcome 3 made to allow the purge after a warning."""
        broken = self.contract.replace(
            "continue without the purge rather than purging on an unverified stop",
            "warn the Bootcamper, then purge")
        self.assertIn("the canonical passage does not say what follows: still listening",
                      rule_problems(broken))

    def test_a_site_that_drops_the_link(self):
        region = sites()["phase2 Step 4 purge"]
        broken = dict(sites())
        broken["phase2 Step 4 purge"] = region.replace(RULE_LINK, "(nowhere.md)")
        self.assertIn("phase2 Step 4 purge: no link to the canonical passage %s" % RULE_LINK,
                      deferral_problems(broken))

    def test_a_site_that_drops_its_citation(self):
        broken = dict(sites())
        label = "phase2 success indicator"
        broken[label] = re.sub(r"INV-\d+", "the rule", broken[label])
        self.assertIn("%s: the deferral cites neither INV-300 nor INV-223 nor INV-394" % label,
                      deferral_problems(broken))

    def test_a_close_site_that_starts_a_second_copy(self):
        broken = {"phase2-close.md": self.phase2 + "\n**Graceful stop confirmed.** …\n"}
        self.assertIn("phase2-close.md restates the rule (%s)" % CONTRACT_ONLY[0],
                      copy_problems(broken))

    def test_the_retired_alternative_put_back(self):
        """⛔ The retired wording was itself a ⛔ "Do not" sentence, so it is caught by place,
        not by tone: outside the rule that retires it, the shape is an offense however phrased."""
        broken = {PHASE2: self.phase2.replace(
            "Do not start step 4 until the port is confirmed free.**",
            "Do not start step 4 until the port is confirmed free or the bootcamper has been "
            "warned.**")}
        self.assertEqual(
            ["plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/phase2-close.md"
             ":%d offers a warning as an alternative to a confirmed-free port"
             % match_lines(broken[PHASE2], WARNED_SHAPE)[0]],
            warned_shape_problems(broken))

    def test_the_contracts_own_quotation_is_not_an_offense(self):
        """The rule quotes the retired wording to forbid it; that must stay legal."""
        self.assertEqual([], warned_shape_problems({CONTRACT: self.contract}))

    # ---- #803: outcome 3's two cases -----------------------------------------------------

    def test_a_purge_clause_moved_into_the_no_purge_case(self):
        moved = self.contract.replace(
            "say too that the records are still loaded, then", "then").replace(
            "there is no\n   purge to withhold,", "the records are still loaded; there is no\n   "
            "purge to withhold,")
        self.assertIn("outcome 3's purge case is missing: the retained records",
                      case_problems(moved))

    def test_the_no_purge_case_removed(self):
        region = rule_region(self.contract)
        broken = self.contract.replace(region, without(region, re.escape(NO_PURGE_CASE)))
        self.assertIn("outcome 3 does not state its two cases in order: the purge case, the "
                      "no-purge case, then what holds for every module", case_problems(broken))

    def test_an_every_module_clause_scoped_to_one_case(self):
        broken = self.contract.replace(
            "release the listener, then re-run the module's cleanup program.",
            "release the listener, then re-run the module's cleanup program. This reports; it "
            "does not block.").replace("⚠️ **This reports; it does not block.**", "⚠️")
        self.assertIn("outcome 3 scopes a clause for every module to one case: "
                      "This reports; it does not block", case_problems(broken))

    # ---- #803: the scanned sites ----------------------------------------------------------

    def mutate_module7(self, old, new):
        text = read(MODULE7)
        self.assertEqual(1, text.count(old), "the mutation no longer applies: %r" % old)
        return {MODULE7: text.replace(old, new)}

    STEP_3C_LINK = ("[failed-stop rule](../module-03b-truthset-visualization/"
                    "visualization-api-reference.md#failed-stop),\nstated once there")
    YES_LINK = ("  [failed-stop rule](../module-03b-truthset-visualization/"
                "visualization-api-reference.md#failed-stop)\n  (INV-394, INV-300); this teardown")

    def test_step_3c_drops_the_link(self):
        broken = self.mutate_module7(self.STEP_3C_LINK, "the failed-stop rule,\nstated once there")
        problems = scanned_site_problems(broken)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("the pid stop does not link %s" % SITE_LINK, problems[0])

    def test_the_teardown_yes_drops_the_link(self):
        broken = self.mutate_module7(self.YES_LINK, "  the failed-stop rule\n  (INV-394, INV-300); "
                                                    "this teardown")
        problems = scanned_site_problems(broken)
        self.assertTrue(any("the pid stop does not link" in p for p in problems), problems)
        self.assertTrue(any("the teardown gate does not link" in p for p in problems), problems)

    def test_the_teardown_yes_drops_inv_394(self):
        broken = self.mutate_module7("(INV-394, INV-300); this teardown", "(INV-300); this teardown")
        self.assertTrue(any("the pid stop does not cite INV-394" in p
                            for p in scanned_site_problems(broken)))

    def test_a_link_on_the_neighboring_answer_does_not_count(self):
        """A list item is its own passage: the link moved to "No" leaves "Yes" unlinked."""
        broken = self.mutate_module7(self.YES_LINK, "  the failed-stop rule\n  (INV-394, INV-300); "
                                                    "this teardown")
        text = broken[MODULE7].replace(
            "- **No or not yet:** leave it running,",
            "- **No or not yet:** ([failed-stop rule](../module-03b-truthset-visualization/"
            "visualization-api-reference.md#failed-stop)) leave it running,")
        problems = scanned_site_problems({MODULE7: text})
        self.assertTrue(any("the pid stop does not link" in p for p in problems), problems)
        self.assertFalse(any("the teardown gate" in p for p in problems), problems)

    def test_a_new_unlinked_pid_stop_anywhere(self):
        path = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                / "module-06-data-processing" / "new-server.md")
        text = ("# A new server\n\nOn teardown, stop it\nby the pid recorded at launch and confirm "
                "the port is free (INV-223).\n")
        self.assertEqual(["plugins/senzing-bootcamp/skills/module-06-data-processing/new-server.md"
                          ":3: the pid stop does not link %s" % SITE_LINK,
                          "plugins/senzing-bootcamp/skills/module-06-data-processing/new-server.md"
                          ":3: the pid stop does not cite INV-394"],
                         scanned_site_problems({path: text}))

    def test_a_new_unlinked_teardown_gate_anywhere(self):
        path = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                / "module-06-data-processing" / "new-gate.md")
        text = ("## Teardown\n\n> 👉 **Ready for me to stop the visualization server?**\n\n"
                "- **Yes:** stop the process and continue.\n\n## Next\n\nSee "
                "[the rule](visualization-api-reference.md#failed-stop) (INV-394).\n")
        problems = scanned_site_problems({path: text})
        self.assertEqual(2, len(problems), problems)
        self.assertTrue(all(":3: the teardown gate does not" in p for p in problems), problems)

    def test_module7_claims_the_stop(self):
        broken = self.mutate_module7("never that the\n  server stopped.",
                                     "then say the\n  server stopped.")
        self.assertIn("Module 7's teardown is missing: never that the server stopped",
                      module7_problems(broken[MODULE7]))

    def test_each_module7_clause_removed_is_reported(self):
        text = read(MODULE7)
        answers = teardown_answers(text)
        for label, answer, pattern in MODULE7_CLAUSES:
            with self.subTest(clause=label):
                lines = [n for n in match_lines(text, re.compile(pattern))]
                self.assertEqual(1, len(lines), "%s is not matched exactly once" % label)
                broken = without(text, pattern)
                self.assertIn("Module 7's teardown is missing: %s" % label,
                              module7_problems(broken))
        self.assertIsNotNone(answers["yes"])

    def test_module7_adds_a_checkpoint_field(self):
        broken = read(MODULE7).replace(
            "Then continue to module completion below.",
            'Record `"stop_unverified"` in `m7_visualizations`. Then continue to module completion '
            "below.")
        self.assertIn("Module 7 records a stop outcome; it says so and records nothing new",
                      module7_problems(broken))

    def test_module7_restating_the_rule_is_a_copy(self):
        broken = {"phase1-query-visualize.md": read(MODULE7) + "\nThis reports; it does not block.\n"}
        self.assertIn("phase1-query-visualize.md restates the rule (This reports; it does not "
                      "block)", copy_problems(broken))

    def test_each_record_clause_removed_is_reported(self):
        regions = record_regions()
        for label, site, pattern in RECORD_CLAUSES:
            with self.subTest(clause=label):
                broken = dict(regions)
                broken[site] = without(regions[site], pattern)
                self.assertIn("%s: missing %s" % (site, label), record_problems(broken))


if __name__ == "__main__":
    unittest.main()
