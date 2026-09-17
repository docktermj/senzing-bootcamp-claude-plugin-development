#!/usr/bin/env python3
"""Lead generators for the production-readiness audit. Stdlib only, read-only, exit 0.

Four scans, one per property the audit has to establish. Every one is a **lead
generator, not a verdict** — a regex cannot tell a deliberately restated rule from a
rule that drifted, nor a worked illustration from a cached authority. Read every hit
before classifying it. A run that reports this tool's counts as findings has not done
the audit; it has run a grep.

    rules          reverse direction: hard rules in shipped text that no invariant covers
    duplication    passages repeated across shipped files — where "fixed in one place" hides
    enumerations   invariants that enumerate, i.e. the ones that go stale
    size           Goldilocks measurements for the concision pass
    all            every scan

Read-only. Exits 0 whatever it finds, because a hit is usually legitimate and a report
that gates is a report nobody runs.
"""
import argparse
import collections
import pathlib
import re
import subprocess
import sys

DEFAULT_REPO = pathlib.Path(__file__).resolve().parents[3]

INV_ID = re.compile(r"INV-\d{3}")

#: ⛔ **(INV-308) The roots the `since` view diffs, defined ONCE and read by every consumer.**
#: `tests/test_new_hard_rules_are_cited_or_deferred.py` parses this view's output back into
#: file paths so it can check each reported rule at its source line. While that parser carried
#: its own idea of which roots exist it recognized the shipped corpus alone, silently dropped
#: the 112 lines this view reported under the maintainer surface, and then reported "nothing
#: added" -- green by not running. A second copy of a root list is how one end of a pipe stops
#: meaning what the other end says.
#:
#: ⚠️ Scanning a root is not the same as checking it: the consumer counts the maintainer
#: surface as explicitly out of scope. See that module's docstring for why.
SCAN_ROOTS = ("plugins/senzing-bootcamp", ".claude/commands", ".claude/skills")

# The repo's own convention for a deliberate hard rule: a ⛔ lead-in, or a bolded
# MUST/NEVER/ALWAYS. Bare prose "must" is excluded — it is ordinary instruction, and
# including it took the candidate list from 16 to 202, which no one reads.
#
# ⛔ ANCHORED is the historical pattern and is kept EXACTLY as it was, because every figure
# in the ledger's audit entries was measured with it. Changing it in place would make every
# recorded count look like a regression. Mid-line rules are a second population, reported
# separately — see MID_LINE_RULE and `classify`.
ANCHORED_RULE = re.compile(
    r"^\s*>?\s*⛔"
    r"|\*\*[^*]*\b(?:MUST|NEVER|ALWAYS)\b[^*]*\*\*"
    r"|^\s*-?\s*\*\*.*?\*\*.*\b(?:MUST|NEVER)\b"
)

# Kept as an alias: `HARD_RULE` is the name other tooling and tests reach for, and it means
# "is this line a hard rule at all" — which is now `classify(line) is not None`.
HARD_RULE = ANCHORED_RULE

CODE_SPAN = re.compile(r"`[^`]*`")

# A ⛔ that is not first on its line. Measured 2026-08-21 across shipped markdown: 191 such
# lines, against 347 the anchored pattern matched — and NONE of the 191 was caught by the
# bolded-MUST alternatives either, because a rule like `⛔ **Strip everything identifying.**`
# has no MUST inside its bold span. Three shapes recur, and two are ordinary house style: a
# numbered-list item (`2. ⛔ **...**` — the anchor admits `-` but not `1.`), a rule appended to
# a list item's prose, and a rule continuing a sentence.
#
# The discriminator is what FOLLOWS the stop sign, not where it sits: a rule leads into a
# bolded span, a capitalized word, or an imperative. Dropping the anchor without this would
# add real rules and real noise together, and a count nobody trusts is the defect `rules`
# already had.
IMPERATIVE = (r"never|always|do not|don't|use|keep|prefer|treat|stop|ask|read|write|check"
              r"|state|name|strip|report|verify|cite|record|leave|derive|scope")
MID_LINE_RULE = re.compile(r"⛔\s*(?:\*\*|[A-Z]|(?:%s)\b)" % IMPERATIVE, re.IGNORECASE)

# The stop sign used as a NOUN is prose about the convention, not a rule: "a ⛔ gate", "the old
# ⛔", "Steps marked `⛔`". 32 such lines, correctly excluded.
NOUN_USE = re.compile(
    r"(?:\b(?:a|an|the|its|any|each|every|marked|old|same)\s+(?:\w+\s+)?)⛔"
    r"|⛔\s*(?:gates?|convention|marker|lead-in|sign|glyphs?)\b",
    re.IGNORECASE)


def classify(line):
    """"anchored", "mid-line", or None — the single definition every view uses.

    ⛔ No view keeps its own copy of this. Three views inheriting three copies of a pattern is
    how one of them silently stops meaning the same thing as the others.
    """
    if ANCHORED_RULE.search(line):
        return "anchored"
    if "⛔" not in line:
        return None
    # A ⛔ that survives only inside a code span is discussion of the glyph itself (21 lines),
    # and one at end-of-line has nothing after it to be the rule.
    bare = CODE_SPAN.sub("", line)
    if "⛔" not in bare or bare.rstrip().endswith("⛔"):
        return None
    if NOUN_USE.search(bare):
        return None
    return "mid-line" if MID_LINE_RULE.search(bare) else None


def paths(args):
    """Resolve the three roots every scan needs from --repo."""
    repo = pathlib.Path(getattr(args, "repo", None) or DEFAULT_REPO).resolve()
    return repo, repo / "plugins" / "senzing-bootcamp", repo / "specs" / "INVARIANTS.md"


def shipped_markdown(plugin):
    return sorted(p for p in plugin.rglob("*.md") if p.is_file())


def rel(p, repo):
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def sections(lines):
    """Map each line index to its enclosing heading block (start, end)."""
    heads = [i for i, l in enumerate(lines) if l.startswith("#")] + [len(lines)]

    def enclosing(i):
        start = max([h for h in heads if h <= i], default=0)
        end = min([h for h in heads if h > i], default=len(lines))
        return start, end

    return enclosing


def cmd_rules(args):
    """Hard rules whose enclosing section cites no invariant.

    This is the direction the forward sweep cannot see: the plugin states a durable
    rule that `INVARIANTS.md` never records, so nothing binds future work to it and
    nothing notices when a later change contradicts it. Two invariants exist only
    because this went unnoticed — INV-134 (the name is detected, never asked: shipped,
    unregistered, and INV-113 cited INV-076 as its authority, which says nothing about
    names) and INV-155 (the six-tab app was non-conformant with still-standing INV-104,
    whose text still enumerated two tabs that had been removed).

    Scoped to the enclosing section rather than a line window: a rule under a heading
    that cites the governing invariant is covered, even when the citation is 30 lines up.
    """
    repo, plugin, _ = paths(args)
    print("== hard rules whose section cites no invariant\n")
    counts = collections.Counter()
    hits = 0
    by_file = collections.OrderedDict()
    for path in shipped_markdown(plugin):
        lines = path.read_text(encoding="utf-8").splitlines()
        enclosing = sections(lines)
        for i, line in enumerate(lines):
            kind = classify(line)
            if kind is None:
                continue
            counts[kind] += 1
            start, end = enclosing(i)
            if INV_ID.search("\n".join(lines[start:end])):
                continue
            hits += 1
            by_file.setdefault(rel(path, repo), []).append((i + 1, kind, line.strip()))
    for name, rows in by_file.items():
        print("   %s" % name)
        for lineno, kind, text in rows:
            print("     :%-5d %-9s %s" % (lineno, kind, text[:100]))
    anchored, midline = counts["anchored"], counts["mid-line"]
    print("\n   %d hard-rule lines (%d line-anchored + %d mid-line), %d in a section citing no "
          "invariant, across %d file(s)"
          % (anchored + midline, anchored, midline, hits, len(by_file)))
    print("   ^ figures in ledger entries before 2026-08-21 counted the LINE-ANCHORED number")
    print("     only; compare against %d, not the total. Mid-line rules -- a stop sign that is"
          % anchored)
    print("     not first on its line -- were invisible to every view until then.")
    print("   ^ each is EITHER an unregistered rule (propose an invariant) OR a missing")
    print("     citation to one that exists. Both are findings; they need different fixes.")
    print()
    print("   \u26d4 This is NOT a count of unregistered rules, and MUST NOT be read as one.")
    print("     The unit is the SECTION. A brand-new unregistered rule does not appear here")
    print("     if it lands anywhere near an unrelated INV-nnn -- and it reads clean more")
    print("     reliably as citations get denser. Measured 2026-08-21: a run added 26 hard-rule")
    print("     lines, this count held at 1, and three of those rules were on subjects")
    print("     INVARIANTS.md covers nowhere. Use `per-rule` for the worklist and")
    print("     `since --ref <git-ref>` for what a single run actually added.")
    return 0


def rule_rows(lines):
    """Yield (index, line) for every hard-rule line, in order."""
    for i, line in enumerate(lines):
        if classify(line) is not None:
            yield i, line


def own_citations(lines, i):
    """Invariant IDs cited by the rule ITSELF or the sentence immediately adjacent.

    Deliberately narrower than `cmd_rules`' enclosing section, because the two answer
    different questions. The section scope asks "is this subject covered anywhere near
    here"; this asks "can a reader at this line name the rule that governs it", which is
    what INV-183 requires. The window is the rule's own line plus one non-blank line
    either side -- a continuation of the same bolded rule, or the sentence that explains
    it -- and no further: widening it back toward the section reintroduces the blind spot.
    """
    window = [lines[i]]
    for step in (-1, 1):
        j = i + step
        while 0 <= j < len(lines) and not lines[j].strip():
            j += step
        if 0 <= j < len(lines):
            window.append(lines[j])
    return sorted(set(INV_ID.findall("\n".join(window))))


def cmd_per_rule(args):
    """Every hard rule with the invariants cited AT it -- a worklist, not a verdict.

    \u26d4 This does NOT decide whether a rule is registered. No regex can match a rule's
    subject against 260 invariants' prose, and one that tried would produce a confident
    wrong answer -- worse than the current silence, because it would be believed. The
    output is a list to read: the rule, what it cites at the point of use, and where it is.

    The section-scoped `rules` count stays, and its history stays comparable across runs.
    This is the second question, which needs the finer unit: on 2026-08-21 the section
    count held at its baseline of 1 while a run shipped three rules on subjects
    INVARIANTS.md covers nowhere, because each landed beside an unrelated citation.
    """
    repo, plugin, _ = paths(args)
    only = getattr(args, "uncited", False)
    print("== every hard rule, with the invariants cited AT it (worklist, not a verdict)\n")
    total = bare = 0
    for path in shipped_markdown(plugin):
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = []
        for i, line in enumerate(lines):
            if classify(line) is None:
                continue
            total += 1
            own = own_citations(lines, i)
            if not own:
                bare += 1
            elif only:
                continue
            rows.append((i + 1, own, line.strip()))
        if rows:
            print("   %s" % rel(path, repo))
            for lineno, own, text in rows:
                print("     :%-5d %-24s %s"
                      % (lineno, ",".join(own) if own else "(no citation at the rule)",
                         text[:88]))
    print("\n   %d hard-rule lines, %d citing no invariant at the rule itself" % (total, bare))
    print("   ^ a worklist to READ. For each, search INVARIANTS.md for the rule's SUBJECT:")
    print("     registered but uncited -> add the citation (INV-183); not registered ->")
    print("     draft an invariant and get sign-off. Neither is decidable mechanically.")
    print()
    print("   \u26a0 Residual limitation: a hard rule written with NO stop sign and no bolded")
    print("     MUST/NEVER/ALWAYS is invisible to all three views. Bare prose \"must\" is excluded")
    print("     deliberately -- including it took the candidate list from 16 to 202 -- so this")
    print("     is a floor on what the reverse contract can see mechanically, not a ceiling.")
    return 0


def added_rule_lines(repo, ref, upto=None):
    """Hard-rule lines added between `ref` and `upto` (the working tree when None).

    ⛔ **One definition, read by the `since` view and by the boundary report below.** Counting
    a range with a second copy of this parse is how the three hard-rule views came to disagree
    about their corpus in the first place; a fourth copy measuring what a boundary retired would
    be the same mistake in the tool built to report it.

    Returns an ordered {path: [lines]}, or None when git could not answer.
    """
    rng = ref if upto is None else "%s..%s" % (ref, upto)
    proc = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", rng, "--", *SCAN_ROOTS],
        cwd=str(repo), capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    current = None
    added = collections.OrderedDict()
    for raw in proc.stdout.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            continue
        if raw.startswith("+++") or raw.startswith("---") or raw.startswith("+++ /dev/null"):
            continue
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        body = raw[1:]
        if current and current.endswith(".md") and classify(body) is not None:
            added.setdefault(current, []).append(body.strip())
    return added


def last_audit_ref(repo):
    """The newest audit entry with a resolvable commit, or None.

    Walks audit entries newest-first and takes the first whose `Commit:` field names a commit this
    repo has, reporting which entry it used. \u26d4 It does NOT stop at the newest entry: an audit
    writes its own ledger entry with `Commit: uncommitted` before committing, so the newest entry
    has no hash during the run that needs this most -- and failing there would make the flag
    unusable in exactly the situation it was added for. Skipping to the previous audit is still
    reading a recorded hash, not guessing a range.

    Fails loudly when NO entry has a resolvable commit. An unresolvable ref reported as "0 rules
    added" is indistinguishable from a clean range (INV-110/INV-115), and the point of this view is
    to be believed about what a run added.
    """
    ledger = repo / "specs" / "IMPLEMENTED.md"
    if not ledger.is_file():
        sys.stderr.write("no specs/IMPLEMENTED.md under %s — cannot resolve the last audit\n" % repo)
        return None
    text = ledger.read_text(encoding="utf-8")
    entries = re.findall(r"(?m)^## (production-readiness-audit\S*)\n(.*?)(?=\n## |\Z)", text, re.S)
    if not entries:
        sys.stderr.write("no audit entry found in the ledger\n")
        return None
    skipped = []
    chosen = previous = None
    for name, body in entries:
        c = re.search(r"(?m)^\s*-\s+\*\*Commit:\*\*\s*`?([0-9a-f]{7,40})`?\s*$", body)
        if not c:
            raw = re.search(r"(?m)^\s*-\s+\*\*Commit:\*\*\s*(.+)$", body)
            if chosen is None:
                skipped.append("%s (%s)"
                               % (name, raw.group(1).strip() if raw else "no Commit: field"))
            continue
        ref = c.group(1)
        ok = subprocess.run(["git", "rev-parse", "--verify", "%s^{commit}" % ref],
                            cwd=str(repo), capture_output=True, text=True)
        if ok.returncode != 0:
            if chosen is None:
                skipped.append("%s (%s — not a commit here)" % (name, ref))
            continue
        if chosen is None:
            chosen = (name, ref)
            continue
        # ⚠️ The previous resolvable record, kept only so the boundary below can measure what
        # this one retired. The scan stops here: older boundaries are older ranges' business.
        previous = (name, ref)
        break
    if chosen is None:
        sys.stderr.write("no audit entry has a resolvable commit; skipped: %s\n"
                         % "; ".join(skipped))
        return None
    name, ref = chosen
    print("   (ref %s from ledger entry %s)" % (ref, name))
    for entry in skipped:
        print("   (skipped %s)" % entry)
    start = _widen_past_a_work_commit(repo, ref, name)
    _report_retired_boundary(repo, previous, start)
    return start


def _report_retired_boundary(repo, previous, start):
    """What this range boundary RETIRED, and a refusal to say it was examined.

    ⛔ **An audit record advances the range whether or not the rules inside the previous one
    were ever looked at.** `SUSPECT-REF` above catches a *different* hazard -- a record whose
    own commit carries shipped work -- and correctly stays silent here, because a clean
    ledger-only record is exactly what it is supposed to accept. So the boundary itself went
    unreported: on 2026-09-17 a record retired 112 hard-rule lines that the gate consuming this
    view had never seen (#74), and the range moved past all of them with no line of output.

    ⛔ **The count is what was RETIRED, never what was unexamined.** Nothing in this repository
    records that any rule was read, so a tool claiming "93 unexamined" would be asserting
    something it cannot know -- the failure INV-308 is about. It reports the measurable half and
    names the unmeasurable one, which is why the wording below says where the answer is not.

    ⚠️ **Printed on every resolution, zero included.** A figure that appears only when non-zero
    makes its absence ambiguous: the reader cannot tell an empty boundary from a boundary the
    tool stopped measuring.
    """
    if previous is None:
        print("   \u26a0 BOUNDARY: no earlier audit record resolves here, so what preceded %s is"
              % start)
        print("     outside this ledger. That is a first range, not a measured zero.")
        return
    prev_name, prev_ref = previous
    retired = added_rule_lines(repo, prev_ref, start)
    if retired is None:
        print("   \u26a0 BOUNDARY: the range %s..%s could not be diffed, so what this record"
              % (prev_ref, start))
        print("     retired is UNKNOWN -- which is not the same as nothing.")
        return
    count = sum(len(rows) for rows in retired.values())
    print("   \u26a0 BOUNDARY: this record retired %s..%s, carrying %d hard-rule line(s) across"
          % (prev_ref, start, count))
    print("     %d file(s); the record before it is %s." % (len(retired), prev_name))
    print("     Whether any of them was examined is recorded NOWHERE, so this view cannot say.")
    print("     0 here means the retired range was EMPTY, never that it was checked.")



#: Paths `propagate.sh` mirrors into the public repo. An audit-record commit touches none of
#: them -- its own ledger entry says so, in the words "no shipped file modified by this audit".
_PROPAGATED = ("plugins/", ".claude-plugin/", "docs/", "README.md")


def _widen_past_a_work_commit(repo, ref, entry):
    """The recorded ref, or its parent when that commit carries shipped work.

    ⛔ **A range that starts AT the work reports zero, and zero is the answer this view
    exists to make impossible.** The resolver takes the newest audit entry's `Commit:` field,
    which is right only while an audit record is committed BEFORE the implementations that
    answer it. On 2026-09-03 a record was committed together with its two implementations
    (`ffa6a2f`), and `since --since-last-audit` reported `0 hard-rule line(s) added` while six
    had been -- indistinguishable from a run that added none, and enough to let a hard rule
    ship with no invariant and no deferral, which is the 2026-08-17 defect.

    ⚠️ **Everything downstream inherits it**: `tests/test_new_hard_rules_are_cited_or_deferred`
    SKIPS on "nothing added", so it goes green by not running, and the `unattended-issue-loop`
    set-difference script iterates an empty list.

    ⚠️ **What the probe sees is itself a measured question, not an obvious one** -- see the
    table at the call below. A merge and a root commit each come back EMPTY from one of the two
    plausible git invocations, and empty reads as "touches nothing shipped".

    So the contradiction is detected -- an audit-record commit that touches a propagated path
    contradicts its own entry -- reported loudly, and the range widened to the parent. The
    widening is announced rather than silent: a resolver that re-points a range without saying
    so is how a wrong baseline becomes invisible a second time.
    (Source: `since-last-audit-reports-zero-when-the-audit-record-shares-the-work-commit`.)
    """
    # ⛔ **`git show --name-only` cannot answer this for every commit shape, and its wrong
    # answer is silence.** Measured 2026-09-03 in a throwaway repo, all three shapes:
    #
    #   probe                                  root commit   normal   merge
    #   git show --name-only --format=         lists         lists    EMPTY
    #   diff-tree --name-only -r -m            EMPTY         lists    lists
    #   diff-tree --name-only -r -m --root     lists         lists    lists
    #
    # So `git show` passes a merge silently, and the obvious replacement without `--root`
    # would only trade that for a root-commit blind spot. `--root` covers all three; `-m` is
    # what makes a merge report each parent's diff; `-r` recurses into trees, without which a
    # change deep in a directory reports the top-level tree name and no `plugins/...` path
    # would ever match. Both blind spots are negative-controlled in
    # `tests/test_since_last_audit_widens_past_a_work_commit.py`.
    # (Source: `the-work-commit-detector-sees-nothing-on-a-merge`, 2026-09-03.)
    touched = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", "--root", ref],
        cwd=str(repo), capture_output=True, text=True)
    if touched.returncode != 0:
        return ref
    shipped = sorted({f for f in touched.stdout.split()
                      if any(f.startswith(pre) for pre in _PROPAGATED)})
    if not shipped:
        return ref
    parent = subprocess.run(["git", "rev-parse", "--verify", "--short", "%s^{commit}" % (ref + "^")],
                            cwd=str(repo), capture_output=True, text=True)
    print("   ⛔ SUSPECT-REF: %s is an audit record committed WITH shipped work" % ref)
    print("     entry %s records it, and such an entry claims no shipped file was modified;" % entry)
    print("     it touches %d propagated file(s): %s" % (len(shipped), ", ".join(shipped[:6])))
    if parent.returncode != 0:
        print("     it has no parent, so the range is left AT %s -- pass --ref explicitly" % ref)
        return ref
    widened = parent.stdout.strip()
    print("     the range is WIDENED to its parent %s so the work it carries is in view." % widened)
    print("     Commit an audit record on its own, BEFORE the implementations that answer it.")
    return widened

def cmd_since(args):
    """Hard-rule lines a git ref introduced -- the unit an unattended run needs.

    A corpus-wide count answers "how many rules exist", and what a run needs to know is
    "which rules did I just add". Those differ by exactly the amount that makes the
    section-scoped count useless for the job `implement-spec` Step 5 gives it: on
    2026-08-21 the count did not move at all while 26 hard-rule lines were added.
    """
    repo, plugin, _ = paths(args)
    ref = args.ref
    if getattr(args, "since_last_audit", False):
        ref = last_audit_ref(repo)
        if ref is None:
            return 2
    if not ref:
        sys.stderr.write("since needs --ref <git-ref> or --since-last-audit\n")
        return 2
    # ⛔ The maintainer surface is included HERE and in no other view, deliberately.
    # `.claude/` carries ~165 hard-rule lines against the shipped corpus's ~672, nearly
    # all deliberate restatements of rules that already live in the skills -- so widening
    # `rules`/`per-rule` would add that many permanent false leads to a worklist whose own
    # skill warns these are leads, not verdicts. This view asks a different question --
    # "what appeared SINCE the last audit?" -- where a restatement that has been there all
    # along does not show up at all, and a NEW guarantee does. Four such guarantees shipped
    # under `.claude/` between 2026-09-03 and 2026-09-14 and this view reported 0.
    # (Source: `the-github-issue-path-ships-guarantees-with-no-invariant`, 2026-09-14.)
    print("== hard-rule lines added since %s (shipped markdown + the .claude/ maintainer surface)\n" % ref)
    added = added_rule_lines(repo, ref)
    if added is None:
        sys.stderr.write("git diff against %r failed\n" % ref)
        return 2
    count = sum(len(rows) for rows in added.values())
    for name, rows in added.items():
        print("   %s" % name)
        for text in rows:
            print("     + %s" % text[:110])
    print("\n   %d hard-rule line(s) added since %s, across %d file(s)"
          % (count, ref, len(added)))
    print("   ^ read every one. This is the set a run is answerable for; the corpus-wide")
    print("     `rules` count cannot see them (it did not move for the 26 added 2026-08-21).")
    print("   \u26a0 Line-level: a rule MOVED between files shows as added here. That is the")
    print("     right default for review -- a relocated rule still needs its citation to")
    print("     travel with it -- but it is not the same as a NEW guarantee.")
    return 0


def _normalize(line):
    """Collapse a line to comparable words: code, emphasis and INV ids are noise here."""
    s = re.sub(r"`[^`]*`", " CODE ", line)
    s = re.sub(r"\*\*|\*|_", "", s)
    s = INV_ID.sub("INV", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def cmd_duplication(args):
    """Passages repeated across shipped files.

    This targets the audit's single most common finding: one rule stated in several
    places, corrected in some. INV-161's document-relative image path was fixed in
    `graduation/SKILL.md` and left wrong in three other files that *produce* the path,
    so every Bootcamper's recap silently lost every screenshot. INV-146's "2-3
    screenshots" survived in three places after the rule changed.

    Repetition is not automatically a defect — a rule required *at* the step it governs
    is INV-183's requirement, not a redundancy. The finding is repetition that has
    **drifted**: compare the hits and see whether they still say the same thing.
    """
    repo, plugin, _ = paths(args)
    n = args.words
    index = collections.defaultdict(set)
    for path in shipped_markdown(plugin):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            words = _normalize(line).split()
            if len(words) < n:
                continue
            for i in range(len(words) - n + 1):
                index[" ".join(words[i:i + n])].add((rel(path, repo), lineno))

    shared = {s: locs for s, locs in index.items() if len({f for f, _ in locs}) > 1}
    pairs = collections.Counter()
    for locs in shared.values():
        files = sorted({f for f, _ in locs})
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pairs[(files[i], files[j])] += 1

    print("== passages of %d+ words appearing in more than one shipped file\n" % n)
    for (a, b), count in pairs.most_common(args.top):
        print("   %4d shared" % count)
        print("        %s" % a)
        print("        %s" % b)
    print("\n   %d repeated passages across %d file pair(s)" % (len(shared), len(pairs)))
    print("   ^ repetition required AT a step is INV-183, not redundancy. The finding is")
    print("     repetition that has DRIFTED — read both sites and compare.")
    return 0


def cmd_enumerations(args):
    """Invariants that enumerate, because enumerations are what go stale.

    An invariant stating a property survives change; an invariant *listing* members
    breaks the moment a member is added or removed, and it breaks silently — the list
    still reads authoritative. INV-104 enumerated two visualization tabs after both had
    been removed; INV-050's layout tree omitted three always-produced deliverables and
    misattributed a file to the wrong module.
    """
    _, _, invariants = paths(args)
    text = invariants.read_text(encoding="utf-8")
    entries = re.findall(r"^\s*- \*\*(INV-\d{3})\*\*\s*—\s*(.+?)(?=\n\s*- \*\*INV-|\n##|\Z)",
                         text, re.M | re.S)
    signals = (
        ("exact count", re.compile(r"\bexactly (?:one|two|three|four|five|six|seven|"
                                   r"eight|nine|ten|\d+)\b", re.I)),
        ("closed list", re.compile(r"\bis (?:exactly|precisely)\b|\bthe following\b"
                                   r"|\bconsists of\b|\bno other\b|\bonly these\b", re.I)),
        # Three or more backticked literals in a row. The separator must allow
        # "`A`, `B` and `C`" as well as "`A`, `B`, `C`" — real invariants use both, and
        # a comma-only pattern silently misses every Oxford-comma-less series.
        ("comma series", re.compile(
            r"`[^`]+`(?:(?:\s*,\s*|\s*,?\s*(?:and|or)\s+)`[^`]+`){2,}")),
    )
    print("== invariants that enumerate (stale-risk surface)\n")
    found = 0
    for ident, body in entries:
        body = " ".join(body.split())
        why = [label for label, pat in signals if pat.search(body)]
        if not why:
            continue
        found += 1
        print("   %s  [%s]" % (ident, ", ".join(why)))
        print("       %s" % body[:150])
    print("\n   %d of %d invariants enumerate something" % (found, len(entries)))
    print("   ^ for each, check the enumeration against what the plugin ships TODAY.")
    print("     A stale enumeration is a false premise that reads as authoritative.")
    return 0


def cmd_size(args):
    """Goldilocks measurements: where the definition is heaviest.

    Size is not a defect and this scan names no target. It exists so the concision pass
    starts from where the words actually are rather than from an impression, and so a
    later run can tell growth from churn.

    ⛔ Never cut rationale to move these numbers. Every "observed:" clause in this repo
    names a real defect, and it is what stops the rule being re-argued or re-broken.
    """
    repo, plugin, _ = paths(args)
    md = shipped_markdown(plugin)
    rows = []
    for path in md:
        body = path.read_text(encoding="utf-8")
        rows.append((len(body.split()), len(body.splitlines()), rel(path, repo)))
    rows.sort(reverse=True)
    total_words = sum(r[0] for r in rows)
    print("== shipped markdown: %d files, %s words\n" % (len(md), format(total_words, ",")))
    print("   heaviest files:")
    for words, lines, name in rows[:12]:
        print("     %7s words  %5d lines  %s" % (format(words, ","), lines, name))
    scripts = sorted((plugin / "scripts").glob("*.py")) if (plugin / "scripts").is_dir() else []
    if scripts:
        print("\n   bundled scripts: %d files, %d lines"
              % (len(scripts),
                 sum(len(p.read_text(encoding="utf-8").splitlines()) for p in scripts)))
    print("\n   ^ a number, not a target. Cutting rationale to shrink it is forbidden;")
    print("     the win is merging duplicated statements, never deleting the reason.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None,
                        help="repository root (default: the one this script ships in)")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("rules", help="hard rules no invariant covers (reverse direction)")

    per = sub.add_parser("per-rule",
                         help="every hard rule + the invariants cited AT it (worklist)")
    per.add_argument("--uncited", action="store_true",
                     help="show only rules citing no invariant at the rule itself")

    since = sub.add_parser("since", help="hard-rule lines added since a git ref")
    since.add_argument("--ref", default=None, help="git ref to diff against")
    since.add_argument("--since-last-audit", action="store_true",
                       help="resolve the ref from the newest audit entry's Commit: field")

    dup = sub.add_parser("duplication", help="passages repeated across shipped files")
    dup.add_argument("--words", type=int, default=14, help="shingle length (default 14)")
    dup.add_argument("--top", type=int, default=12, help="file pairs to show (default 12)")

    sub.add_parser("enumerations", help="invariants that enumerate, i.e. go stale")
    sub.add_parser("size", help="Goldilocks measurements")
    sub.add_parser("all", help="every scan")

    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0

    # Fail loudly on a wrong --repo rather than reporting an empty, clean-looking sweep:
    # "0 findings" and "0 files read" are indistinguishable in the output (INV-110/INV-115).
    repo, plugin, invariants = paths(args)
    if not plugin.is_dir():
        sys.stderr.write("no plugins/senzing-bootcamp under %s — wrong --repo?\n" % repo)
        return 2
    if args.cmd in ("enumerations", "all") and not invariants.is_file():
        sys.stderr.write("no specs/INVARIANTS.md under %s — wrong --repo?\n" % repo)
        return 2

    if args.cmd == "all":
        # ⛔ Every subcommand with no required argument runs here. `rules` and `per-rule` are
        # adjacent on purpose: the two counts differ, and the difference is the finding. An
        # earlier `all` ran `rules` alone while Step 1.3 called it "every lead generator", so a
        # run that followed Step 1 got only the view documented as unable to see the class.
        args.uncited = True
        for fn in (cmd_rules, cmd_per_rule, cmd_enumerations, cmd_size):
            fn(args)
            print()
        args.words, args.top = 14, 12
        cmd_duplication(args)
        print()
        print("== not run by `all`: since")
        print("   `since` needs a range, and guessing one would report the wrong answer silently.")
        print("   Run it separately — the ref is computable from the ledger:")
        print("     conformance.py since --since-last-audit")
        return 0

    return {
        "rules": cmd_rules,
        "per-rule": cmd_per_rule,
        "since": cmd_since,
        "duplication": cmd_duplication,
        "enumerations": cmd_enumerations,
        "size": cmd_size,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
