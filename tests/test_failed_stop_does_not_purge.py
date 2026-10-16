"""An unverified server stop never purges the Truth Set, and one rule says so (#673).

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

Source issue: #673.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _corpus
from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-03b-truthset-visualization")
CONTRACT = MODULE / "visualization-api-reference.md"
PHASE2 = MODULE / "phase2-close.md"
SKILL = MODULE / "SKILL.md"

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
    ("outcome 3: the retained records are reported", r"the records are still loaded"),
    ("outcome 3: no purge",
     r"continue without the purge rather than purging on an unverified stop"),
    ("outcome 3: what is left to do by hand",
     r"release the listener, then re-run the module's cleanup program"),
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


# --------------------------------------------------------------------------------------------
# The sites that defer to it
# --------------------------------------------------------------------------------------------

#: The invariant each site may defer under. INV-300 is the single-statement discipline; INV-223 is
#: the rule the success indicators summarize.
DEFERRAL_INVARIANTS = ("INV-300", "INV-223")


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
    texts = texts if texts is not None else {p.name: read(p) for p in (PHASE2, SKILL)}
    return ["%s restates the rule (%s)" % (name, phrase)
            for name, text in sorted(texts.items())
            for phrase in CONTRACT_ONLY if has(text, phrase)]


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
        self.assertIn("%s: the deferral cites neither INV-300 nor INV-223" % label,
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

    def test_each_record_clause_removed_is_reported(self):
        regions = record_regions()
        for label, site, pattern in RECORD_CLAUSES:
            with self.subTest(clause=label):
                broken = dict(regions)
                broken[site] = without(regions[site], pattern)
                self.assertIn("%s: missing %s" % (site, label), record_problems(broken))


if __name__ == "__main__":
    unittest.main()
