#!/usr/bin/env python3
"""Maintainer coverage reports over `specs/` — where an audit should look next.

Two blind spots let an invariant stand unimplemented for weeks while `IMPLEMENTED.md`
recorded its spec as done (`deep-dive-audit-2026-07-29-minor-fixes`, item 4). Neither is a
test, because neither gap is a defect on its own — both are **reports**, so a real signal
is not buried under legitimate entries:

``invariants``
    Invariants no test file mentions by ID. Many are legitimately enforced by tests that
    cite them by name rather than number, so a hit is not a failure — but this is where
    INV-060 and INV-097 hid, and both would have appeared here.

    ⚠️ **This report is unreliable in BOTH directions, and the second one bites harder.**
    It keys on the ID appearing *anywhere* under ``tests/``, which under-reports as noted
    above — and **over-reports** just as easily, because an incidental mention scores an
    invariant as covered. Observed 2026-08-12: INV-183 was named by five test files, every
    one of them invoking it as *rationale* (*"a rule deliberately restated at the step it
    governs is INV-183"*), and none of them the test INV-183 names as its enforcer. The
    missing citation was therefore invisible here, and a finding that recorded it on
    2026-08-11 went unactioned with nothing failing.

    So a **miss on this report is not evidence of coverage**. For the subset of invariants
    that name their own enforcer, ``tests/test_invariant_enforcer_citations.py`` is the
    reliable check — it asserts the named file exists and cites the ID back, and it fails
    rather than reports.

``affected``
    Ledgered specs whose ``## Affected files`` predicted a path the entry's
    ``**Files changed:**`` never recorded. A prediction that did not come true is often
    correct (the change turned out not to need that file), which is exactly why this
    cannot be a gate — see ``tests/test_spec_ledger_invariants.py``, which enforces the
    same property only for entries dated on or after its cutoff.

``negatives``
    Every ``MCP-NEGATIVE:`` marker — a dated claim that some MCP tool does NOT contain
    something — oldest server version first. This is the worklist a dry run's phase 1
    re-asks. A negative cannot go stale *detectably*: the suite is offline (INV-108), so
    nothing can notice that a tool has since gained the coverage the plugin routed around.
    It has happened twice (``senz7221-now-names-its-own-remedy``,
    ``explain-error-code-now-owns-senz7426``), and the second time the stale claim was
    also written into the guards, so correcting the prose *failed* the suite.

    Scanned under ``NEGATIVE_ROOTS`` — plus the single file ``specs/DECLINED.md``, which is
    the one record with no re-verification path at all: a declined spec never reaches
    ``implement-spec`` Step 3.3, so a dated negative in a ``Revisit if:`` clause is re-read
    as authority and never re-asked. Adding that one file does not open the rest of
    ``specs/``.

``unmarked``
    The complement of ``negatives``: dated absence claims in **shipped plugin prose** that carry
    no marker. ``negatives`` can only list what is already tagged, so an unmarked negative is
    invisible to it by construction — and nothing else looks either.
    ``tests/test_dated_negatives_are_marked.py`` scans ``tests/*.py`` assertion lines, and
    INV-217 covers ``specs/DECLINED.md``; shipped prose, the largest surface, was unswept until
    2026-08-13.

    **The date is the discriminator.** A unit is reported only when it carries an MCP tool name
    *and* absence vocabulary *and* a date or server version. Prose that explains how a tool
    behaves without dating it is not a re-checkable claim — INV-192's rule contains the sentence
    "the payload of a gate is empty by design, not because the topic is undocumented", which is
    true, must never require a marker, and carries no date. Every defect found on 2026-08-13 was
    dated.

    ⚠️ **A report, not a gate, and deliberately so.** Deciding whether a hit is a live claim or
    prose about tool behavior needs judgment, which is the same reason ``invariants`` and
    ``affected`` are reports. The absence vocabulary is also a phrase list, so it is evadable by
    paraphrase: a miss is weak evidence. The marker is the durable route; this finds the ones
    nobody marked.

All four are read-only, stdlib-only, and platform-independent (INV-052/INV-108). Run from
the repo root, or pass ``--repo``:

    python3 .claude/skills/dry-run/coverage_reports.py invariants
    python3 .claude/skills/dry-run/coverage_reports.py affected
    python3 .claude/skills/dry-run/coverage_reports.py negatives
    python3 .claude/skills/dry-run/coverage_reports.py unmarked
    python3 .claude/skills/dry-run/coverage_reports.py both

Exit status is 0 whatever the findings — these inform an audit, they do not gate one.
"""
import argparse
import collections
import os
import re
import sys

INV_DEF = re.compile(r"\*\*INV-(\d{3})\*\*")
INV_REF = re.compile(r"INV-(\d{3})")
LEDGER_HEAD = re.compile(r"^## (\S+)$", re.M)
FILES_CHANGED = re.compile(r"^- \*\*Files changed:\*\*(.*)$", re.M)
PATH_IN_TICKS = re.compile(r"`([A-Za-z0-9_./{}*-]+\.(?:md|py|sh|json|yaml|yml|js|png|pdf))`")

#: `MCP-NEGATIVE: <tool(params) asked> — <what is absent> — owner: <route that owns the fact
#:  + outcome> — server <version>, <YYYY-MM-DD>`
#: The em dash is what the plugin's prose uses; a plain `--` is accepted so the marker can
#: be written in a context where an em dash is awkward.
#:
#: ⛔ `owner:` is REQUIRED, and a marker without it deliberately does not match — it must
#: surface as a missing marker rather than as a well-formed one. Absence evidence and
#: ownership evidence are different claims, and only the second one supports a negative:
#: "`configure` returns no license variable" is a true fact about `configure` and worthless
#: as support for "no license variable exists". The route that would CARRY the fact is what
#: has to be asked (INV-194) and what a re-check must re-ask. Recording only the empty call
#: is what made a wrong-route conclusion look reviewed, twice over — see
#: `specs/mcp-negative-markers-must-name-the-owning-route.md`.
MCP_NEGATIVE = re.compile(
    r"MCP-NEGATIVE:\s*(?P<claim>.+?)\s*(?:—|--)\s*owner:\s*(?P<owner>.+?)\s*(?:—|--)\s*"
    r"server\s*(?P<version>[0-9][0-9.]*)\s*,\s*(?P<date>\d{4}-\d{2}-\d{2})"
)
#: The bare token, used to catch markers that are PRESENT but do not fully parse.
#: Making `owner:` required has a failure mode of its own: a marker missing the clause stops
#: matching `MCP_NEGATIVE`, so without this it would silently drop off the worklist instead of
#: failing — invisibility being the exact condition the marker convention exists to prevent.
#: A malformed marker is therefore worse than a missing one and is reported separately.
#: (Found by negative control: stripping the clause from one marker left the suite green and
#: quietly shrank the worklist from three to two.)
MCP_NEGATIVE_TOKEN = re.compile(r"MCP-NEGATIVE:")
#: A file that legitimately contains the marker text without making a claim (this script,
#: its test, the spec that defines the format) opts out with this line.
NEGATIVE_OPT_OUT = "MCP-NEGATIVE-SCAN: ignore-file"
#: Where a live claim can live. `specs/` and `feedback/` are records, not shipped claims — a
#: spec's Senzing facts are re-verified by `implement-spec` Step 3.3 on the way in, and an
#: `IMPLEMENTED.md` entry's `MCP re-check:` field is a point-in-time record of that check.
NEGATIVE_ROOTS = ("plugins", "tests", os.path.join(".claude", "skills"), "docs")
#: `specs/DECLINED.md` is the one exception, and it is a file rather than a root so that
#: including it does not open the rest of `specs/`. A declined spec is never implemented, so
#: Step 3.3 never runs on it — the re-verification path that justifies excluding `specs/` does
#: not exist here. That makes a negative in a `Revisit if:` clause or a dated revisit note the
#: only Senzing claim in the repo with neither a scanner nor any re-verification path, while
#: `implement-spec` positions this file as the HIGHER authority ("re-verify the condition rather
#: than trusting the spec's original citations"). A `Revisit if:` exists precisely to be
#: re-checked later, so a stale negative inside one sends that recheck to the wrong answer while
#: looking evidenced — which is what happened on 2026-08-13 (`specs/DECLINED.md`'s
#: `no-route-for-bootcampers-who-cannot-add-an-mcp-server` note).
NEGATIVE_EXTRA_FILES = (os.path.join("specs", "DECLINED.md"),)
#: Where shipped prose lives, for the `unmarked` report. Only the plugin: a spec or a test may
#: discuss an absence freely, and both have their own mechanisms (Step 3.3, INV-217, the
#: assertion-line guard).
PROSE_ROOT = os.path.join("plugins", "senzing-bootcamp")
#: The 13 MCP tools. Restated here rather than imported from a test, because this script is the
#: dependency and not the dependent — `tests/test_declined_ledger.py` imports its grammar FROM here.
MCP_TOOLS = (
    "explain_error_code", "search_docs", "sdk_guide", "get_sdk_reference", "reporting_guide",
    "generate_scaffold", "get_sample_data", "find_examples", "mapping_workflow",
    "analyze_record", "get_capabilities", "download_resource", "submit_feedback",
)
PROSE_TOOL = re.compile(r"(?i)(%s)" % "|".join(MCP_TOOLS))
#: Phrasings asserting a tool LACKS content. ⛔ Deliberately excludes a bare `never`: it matched
#: "never from training data", "never `exit 1`" and "never re-read", which is 15 false positives on
#: this corpus (measured 2026-08-13: 23 hits with it, 8 without). Only content-negatives here.
PROSE_ABSENCE = re.compile(
    r"(?i)documents? (?:neither|no\b)|returns? no\b|carr(?:y|ies) no\b|contains? no\b|has no\b|"
    r"no indexed document|appears? nowhere|nowhere in|is not documented|not documented by|"
    r"returns? only|only generic|makes no\b|never names|never documents|"
    r"does (?:\*\*)?not(?:\*\*)? (?:name|document|carry|return|list|mention|cover|answer|contain)"
)
#: What turns prose about a tool into a CLAIM that can expire.
PROSE_DATED = re.compile(r"\b20\d\d-\d\d-\d\d\b|\bserver\s+\d+\.\d+")
#: Block-level escape for prose quoting a retracted claim (same token `implement-spec` documents).
PROSE_QUOTED_HISTORY = "MCP-NEGATIVE-SCAN: quoted-history"
#: Block-level escape for an absence that is NOT about a tool's content. The vocabulary cannot tell
#: "the datastore has no default configuration" — a fact about the Bootcamper's environment — from
#: "the declared schema has no `inline` parameter", and both must stay sayable: the second needs a
#: marker and the first cannot have one, because there is no route to re-ask. Declaring it converts
#: a judgment into a greppable, reviewable decision, which is the same reason `quoted-history`
#: exists. Triaged 2026-08-13: exactly one site in the corpus (`module-02` Step 9's SENZ7221 bullet).
PROSE_NOT_A_CLAIM = "MCP-NEGATIVE-SCAN: not-a-tool-claim"
#: How far from a unit a marker may sit and still cover it. Markers are written as HTML comments
#: immediately before or after the claim, and a fenced claim's marker sits outside the fence.
PROSE_MARKER_WINDOW = 6
SKIP_DIRS = {"__pycache__", "vendor", "node_modules", ".git", ".history", ".pytest_cache"}


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _ledger_entries(repo):
    """Map spec name -> entry body, from specs/IMPLEMENTED.md."""
    txt = _read(os.path.join(repo, "specs", "IMPLEMENTED.md"))
    parts = re.split(LEDGER_HEAD, txt)
    return dict(zip(parts[1::2], parts[2::2]))


def report_invariants(repo):
    """Invariants defined in INVARIANTS.md that no test file cites by ID."""
    inv_txt = _read(os.path.join(repo, "specs", "INVARIANTS.md"))
    defined = sorted({int(n) for n in INV_DEF.findall(inv_txt)})
    tests_dir = os.path.join(repo, "tests")
    cited = set()
    for name in sorted(os.listdir(tests_dir)) if os.path.isdir(tests_dir) else []:
        if name.endswith(".py"):
            cited |= {int(n) for n in INV_REF.findall(_read(os.path.join(tests_dir, name)))}
    uncited = [n for n in defined if n not in cited]
    print("== Invariants cited by no test file ==")
    print("defined: %d   cited by a test: %d   uncited: %d"
          % (len(defined), len(defined) - len(uncited), len(uncited)))
    print("(A hit is not a defect: many invariants are enforced by tests that name them")
    print(" rather than numbering them. It is a list of where to look, not a bug list.)")
    print("(And 'cited' is a proxy for 'asserted': an ID mentioned only in a test's")
    print(" comment or docstring counts as cited here, so this UNDER-reports. A hit is")
    print(" therefore strong evidence of a gap; a miss is weak evidence of coverage.)")
    print()

    retired = fully_superseded(inv_txt)
    dropped = sorted(n for n in uncited if n in retired)
    outcome = [n for n in uncited if n <= OUTCOME_MAX and n not in retired]
    residue = [n for n in uncited if n > OUTCOME_MAX and n not in retired]

    if dropped:
        print("  filtered: %d fully superseded — a retired rule needs no test; its"
              % len(dropped))
        print("  replacement does. Sourced from the index's own \"Fully superseded\" lists,")
        print("  NOT from a grep: a partly-superseded invariant still binds and is kept.")
        print("    " + "  ".join("INV-%03d" % n for n in dropped))
        print()
    if outcome:
        # ⚠️ No literal `INV-NNN` in this heading. `test_every_reported_invariant_is_real_and
        # _genuinely_uncited` scans everything after "uncited:" for that token and treats each
        # hit as an ID the report LISTED, so a range in a label reads as two false listings.
        print("  bootcamp OUTCOME invariants (the first %d ids): %d — these are the flow's"
              % (OUTCOME_MAX, len(outcome)))
        print("  own outcomes (banners, questions, \"the SDK is installed\"). An offline suite")
        print("  cannot assert a live turn, so they are `dry-run` phase 3, not test debt.")
        _columns(outcome)
        print()
    print("  development rules with no citing test: %d" % len(residue))
    _columns(residue)
    return uncited


def _columns(numbers, per_row=10):
    line = []
    for n in numbers:
        line.append("INV-%03d" % n)
        if len(line) == per_row:
            print("    " + "  ".join(line))
            line = []
    if line:
        print("    " + "  ".join(line))


#: INV-001..INV-050 are the bootcamp's own OUTCOMES, which `INVARIANTS.md` states are
#: deliberately not indexed ("everything below is a development rule"). They are honored by
#: the flow existing rather than by a test, so they are reported apart from test debt.
OUTCOME_MAX = 50

#: A line in the subject index listing invariants whose WHOLE text is retired.
#: ⛔ Parsed from the index rather than grepped out of each invariant's prose, because the
#: naive test is wrong: `INVARIANTS.md` draws a two-way distinction on purpose — "Fully
#: superseded: … Skip it" versus "Partly superseded … **Read it**". INV-040 is the
#: counter-example (its CORD parenthetical is superseded by INV-198 while its main clause is
#: what INV-198 strengthens), so a grep for "superseded by INV" would hide a live rule.
FULLY_SUPERSEDED_LINE = re.compile(r"\*Fully superseded[^*]*\*(?P<ids>.*)")


def fully_superseded(inv_txt):
    """{int} for invariants the index lists as fully superseded — safe to skip."""
    out = set()
    for m in FULLY_SUPERSEDED_LINE.finditer(inv_txt):
        out |= {int(n) for n in INV_REF.findall(m.group("ids"))}
    return out


#: The index group whose members bind the DEVELOPMENT environment, not the shipped plugin.
#: `specs/INVARIANTS.md` names this group as the exemption in its own text, so the rule lives
#: in the data an author already edits (rule 3 makes an index entry mandatory) rather than in
#: a list here that they would have to know to update.
DEV_GROUP = "development record itself"

#: An invariant's text NAMES a shipped artifact when it points at something under `plugins/`.
#: This is the filter that makes the report readable: a rule naming a file, module or step is
#: one INV-183 requires to be reachable AT that step, so an uncited one is a real gap. A rule
#: stating a general property with no artifact ("a value the Bootcamper was asked for MUST
#: outrank...") is honored by behavior and is not expected to be cited anywhere in
#: particular — reporting it is the noise that gets a report ignored.
#:
#: ⛔ **Repo-internal vocabulary is not enough, and getting this wrong is silent.** These
#: alternatives are all paths, `module-NN` directories and `Module N` catalog labels — the
#: spellings INV-079 and `bootcamp-preparation/SKILL.md` tell the plugin NOT to render. An
#: invariant names a module by its **display name**, so on 2026-08-14 seven of the eight newly
#: registered invariants were invisible here and only INV-226 surfaced, because its text happens
#: to say "Module 0". The better an invariant's prose, the less this filter could see it. The
#: display names are therefore composed from the shipped module table at run time
#: (`module_display_names`) rather than hand-listed a second time where they can drift.
STATIC_ARTIFACT = (
    r"plugins/|"
    r"\bmodule-\d\d|\bModule \d|"
    r"SKILL\.md|phase[0-9A-Za-z-]*\.md|ground-rules\.md|module-completion\.md|"
    r"scripts/[\w-]+\.py|hooks/[\w-]+\.py|"
    r"bootcamp_progress\.json|bootcamp_preferences\.yaml|bootcamp_recap\.md|"
    r"\bthe progress file\b|"
    r"\bgraduation\b|bootcamp[- ]onboarding|bootcamp[- ]preparation"
)

#: `| 5 | System verification | Optional — Requires … |` — the module table in
#: `bootcamp-preparation/SKILL.md`, which is what INV-079 means by a module's name.
MODULE_TABLE_ROW = re.compile(r"(?m)^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*(?:Required|Optional)")

MODULE_TABLE = os.path.join(
    "plugins", "senzing-bootcamp", "skills", "bootcamp-preparation", "SKILL.md")


def module_display_names(repo):
    """Module display names, read from the shipped module table.

    ⛔ Raises rather than returning an empty list. A silent fallback here re-creates exactly
    the blind spot this function exists to close: the report would keep printing, keep looking
    authoritative, and quietly stop seeing every display-name invariant.
    """
    names = MODULE_TABLE_ROW.findall(_read(os.path.join(repo, MODULE_TABLE)))
    if not names:
        raise RuntimeError(
            "no module rows parsed from %s — the display-name half of SHIPPED_ARTIFACT "
            "would be empty, so this report would under-report silently" % MODULE_TABLE)
    return names


def shipped_artifact_re(repo):
    """The artifact filter, with the module display names of THIS repo folded in.

    Each name also matches its hyphenated adjectival form, because an invariant writes
    "System-verification checks" as readily as "System verification".
    """
    alts = ["[ -]".join(re.escape(w) for w in name.split(" "))
            for name in module_display_names(repo)]
    return re.compile(STATIC_ARTIFACT + "|" + "|".join(alts), re.IGNORECASE)

INDEX_GROUP = re.compile(r"(?m)^- \*\*(?P<name>[^*]+)\*\* — .*?(?=^- \*\*|\Z)", re.DOTALL)

#: File kinds a citation can appear in. `plugins/` also holds PDFs and PNGs.
TEXT_SUFFIXES = frozenset(
    (".md", ".py", ".json", ".yaml", ".yml", ".sh", ".ps1", ".txt", ".js", ".html", ".css")
)


def _index_groups(inv_txt):
    """{group name: {INV ids}} from `### Index by subject`, or {} when absent."""
    start = inv_txt.find("### Index by subject")
    if start < 0:
        return {}
    section = inv_txt[start:]
    end = section.find("<!-- New invariants")
    if end > 0:
        section = section[:end]
    # INV_REF captures the DIGITS; re-attach the prefix so these compare against `INV-NNN`.
    # Getting this wrong is silent and total: the exemption set simply never matches.
    return {m.group("name").strip(): {"INV-" + n for n in INV_REF.findall(m.group(0))}
            for m in INDEX_GROUP.finditer(section)}


def find_uncited_in_shipped(repo):
    """([(id, text)] to report, [ungrouped ids]) — invariants no shipped file cites.

    Three filters, and the second two are what make the output worth reading:

    1. Not cited by any file under `plugins/`.
    2. Not in the `INVARIANTS.md` index group that binds the development environment — those
       are *supposed* to be absent from shipped text, and flagging them trains the reader to
       skip the whole report.
    3. Its own text names a shipped artifact (a path, module, step or bundled script) — by
       repo-internal spelling **or** by the module's display name, which is how an invariant
       actually refers to a module. That is the class INV-183 governs: a rule binding a step
       must be reachable AT that step.

    An invariant in **no** group is returned separately rather than silently exempted — a
    missing index entry must not become a way to disappear from this report.
    """
    artifact_re = shipped_artifact_re(repo)
    inv_txt = _read(os.path.join(repo, "specs", "INVARIANTS.md"))
    entries = re.findall(r"(?m)^- \*\*(INV-\d{3})\*\* — (.+)$", inv_txt)
    groups = _index_groups(inv_txt)
    exempt = set()
    for name, ids in groups.items():
        if DEV_GROUP in name.lower():
            exempt |= ids
    grouped = set().union(*groups.values()) if groups else set()

    # Text only: `plugins/` also carries the certificate PDF and screenshot assets, and
    # `_read` raises UnicodeDecodeError on them. A citation can only live in text anyway.
    plugins = os.path.join(repo, "plugins")
    cited = set()
    for root, _dirs, files in os.walk(plugins):
        for name in files:
            if os.path.splitext(name)[1].lower() not in TEXT_SUFFIXES:
                continue
            # INV_REF captures the DIGITS, not the whole id — re-attach the prefix.
            cited |= {"INV-" + n
                      for n in INV_REF.findall(_read(os.path.join(root, name)))}

    hits, ungrouped = [], []
    for inv_id, text in entries:
        # INV-001–INV-050 are the bootcamp's own OUTCOMES, which `INVARIANTS.md` states are
        # deliberately not indexed ("everything below is a development rule"). They are
        # honored by the flow existing rather than by any file naming them, so scoring them
        # against shipped citations measures the wrong thing — and, being unindexed, the
        # exemption cannot classify them either way.
        if int(inv_id[4:]) <= 50:
            continue
        if inv_id not in grouped:
            ungrouped.append(inv_id)
        if inv_id in cited or inv_id in exempt:
            continue
        # ⚠️ lowercase BOTH sides. Searching for "INV" inside `text.lower()` never matches,
        # which silently let every superseded invariant through on the first run.
        if "superseded by inv" in text.lower():
            continue
        if not artifact_re.search(text):
            continue
        hits.append((inv_id, text))
    hits.sort(reverse=True)                       # newest ID first: most likely an oversight
    return hits, sorted(ungrouped)


def report_shipped(repo):
    """Invariants that bind a shipped artifact and that no shipped file cites."""
    hits, ungrouped = find_uncited_in_shipped(repo)
    print("== Invariants naming a shipped artifact that NO file under plugins/ cites ==")
    print("The mirror of the `invariants` report, which looks at tests/ only. A rule that")
    print("names a file, module or step must be reachable AT that step (INV-183); one that")
    print("is cited nowhere in shipped text is a rule the guide cannot look up.")
    print("(A hit is not a defect. An invariant can be honored by behavior without being")
    print(" named — this is where to look, not a bug list. Development-environment rules are")
    print(" exempt via the INVARIANTS.md index group that declares them; invariants stating a")
    print(" general property with no artifact are not reported at all.)")
    print()
    if ungrouped:
        print("  ⛔ %d invariant(s) are in NO index group, so the exemption could not be"
              % len(ungrouped))
        print("     applied to them. Fix the index (INVARIANTS.md rule 3) — a missing group")
        print("     entry must not become a way to vanish from this report:")
        print("     " + "  ".join(ungrouped))
        print()
    if not hits:
        print("  (none — every invariant naming a shipped artifact is cited in shipped text)")
        return hits
    print("hits: %d, newest first" % len(hits))
    print()
    for inv_id, text in hits:
        print("  %s  %s" % (inv_id, text[:104]))
    return hits


#: Gap classes, most actionable first. Only `real` can hide a missed change; the other three
#: are predictions the scan structurally cannot match, and reporting them undifferentiated is
#: what kept this report's floor high enough that nobody re-read it.
GAP_CLASS_ORDER = ("real", "moved", "bare", "glob")
GAP_CLASS_LABEL = {
    "real": "names a real current file",
    "moved": "path no longer exists (moved/renamed)",
    "bare": "bare filename — an artifact, not a repo path",
    "glob": "glob — the scan cannot match a wildcard",
}


def classify_gap(repo, path):
    """Which class a predicted-but-unrecorded path falls into."""
    if "*" in path:
        return "glob"
    if "/" not in path:
        return "bare"
    return "real" if os.path.isfile(os.path.join(repo, path)) else "moved"


def criteria_name_the_file(repo, spec_name, path):
    """True when the spec's `## Acceptance criteria` names this file.

    The discriminator the INV-097 defect actually had: a criterion *promised* a second
    consumer and only the first was built. A path appearing solely under `## Affected files`
    is a prediction, which the report already says may legitimately go unfulfilled.
    """
    txt = _read(os.path.join(repo, "specs", "%s.md" % spec_name))
    m = re.search(r"^## Acceptance criteria\s*$(.*?)(^## |\Z)", txt, re.M | re.S)
    return bool(m) and os.path.basename(path) in m.group(1)


def report_affected(repo):
    """Ledgered specs whose predicted Affected files never reached Files changed."""
    entries = _ledger_entries(repo)
    print("== Predicted-but-unrecorded files (ledgered specs) ==")
    print("A spec's `## Affected files` is a prediction; the entry's `Files changed:` is")
    print("the outcome. A gap is often legitimate — report only, never a gate.")
    print()
    gaps = {}
    for name, body in sorted(entries.items()):
        spec = os.path.join(repo, "specs", "%s.md" % name)
        if not os.path.isfile(spec):
            continue                                   # audits recorded with no spec file
        txt = _read(spec)
        m = re.search(r"^## Affected files\s*$(.*?)(^## |\Z)", txt, re.M | re.S)
        if not m:
            continue
        predicted = sorted(set(PATH_IN_TICKS.findall(m.group(1))))
        recorded = FILES_CHANGED.search(body)
        recorded = recorded.group(1) if recorded else ""
        missing = [p for p in predicted
                   if os.path.basename(p) not in recorded and os.path.basename(p) not in body]
        if missing:
            gaps[name] = missing
    print("ledgered specs examined: %d   with a gap: %d" % (len(entries), len(gaps)))
    print()

    rows = [(name, p) for name, missing in gaps.items() for p in missing]
    by_class = collections.OrderedDict((k, []) for k in GAP_CLASS_ORDER)
    for name, path in rows:
        by_class[classify_gap(repo, path)].append((name, path))

    print("  %d gap row(s), classified — only the first class can hide a real miss:"
          % len(rows))
    for cls in GAP_CLASS_ORDER:
        print("    %-46s %d" % (GAP_CLASS_LABEL[cls], len(by_class[cls])))
    print()
    for cls in GAP_CLASS_ORDER:
        if not by_class[cls]:
            continue
        print("  == %s ==" % GAP_CLASS_LABEL[cls])
        if cls == "real":
            print("  ★ = the spec's `## Acceptance criteria` NAME this file, which is what the")
            print("      INV-097 defect looked like. An `## Affected files` entry alone is only")
            print("      a prediction, and the report's own preamble says so.")
        for name, path in by_class[cls]:
            star = "★" if (cls == "real" and criteria_name_the_file(repo, name, path)) else " "
            print("  %s %-46s %s" % (star, name[:46], path))
        print()
    return gaps


def _scan_files(repo):
    """Every file a live MCP-NEGATIVE claim could sit in."""
    for root in NEGATIVE_ROOTS:
        base = os.path.join(repo, root)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith((".md", ".py")):
                    yield os.path.join(dirpath, name)
    for rel in NEGATIVE_EXTRA_FILES:                   # named files, not roots — see above
        path = os.path.join(repo, rel)
        if os.path.isfile(path):
            yield path


def find_negatives(repo):
    """[(version_key, version, date, claim, owner, relpath, lineno)] for every marker found."""
    found = []
    for path in _scan_files(repo):
        text = _read(path)
        if NEGATIVE_OPT_OUT in text:
            continue
        for lineno, line in enumerate(text.split("\n"), 1):
            m = MCP_NEGATIVE.search(line)
            if not m:
                continue
            version = m.group("version")
            key = tuple(int(p) for p in version.split(".") if p.isdigit())
            found.append((key, version, m.group("date"), m.group("claim").strip(),
                          m.group("owner").strip(), os.path.relpath(path, repo), lineno))
    found.sort(key=lambda r: (r[0], r[2]))
    return found


#: A rationale that pins a COUNT is the marker shape that cannot survive an index rebuild.
#: The claim ("tool X does not contain Y") is re-asked by phase 1; the rationale beside it is
#: not, so a census quietly stops describing the response while the claim above it stays true
#: and the date says the whole comment was checked. On 2026-08-31 two of the three drifted
#: rationales drifted for one reason in two shapes — "all four hits are …" (ten hits by then),
#: which is THIS matcher, and an exhaustive field list (a field had been added), which is NOT:
#: an enumeration carries no numeral, so nothing here can see it. That half is
#: `ENUMERATION_SHAPED` / `find_enumeration_rationales` below, added 2026-09-02 after the
#: uncovered shape drifted a second time undetected (`phase2-data-mapping.md:719` cited a
#: *Mapping identifiers* section the route no longer returns). Read the two as one report in
#: two halves. A count is never the discriminating fact:
#: "no field names a binding type" says what the census was standing in for and does not expire.
#: ⛔ A POSITIVE UNIVERSAL over the result set is a census too, and is flagged the same way.
#: "every hit is X", "each result is X", "all the hits are X" and "every one of the hits …"
#: carry no numeral, but they are falsified by the same event a count is: the index returning
#: one new thing that is not X. This comment used to exempt them — "`all`/`every` do not
#: [count]; 'every hit is V3-to-V4 material' is a property over whatever came back and survives
#: a rebuild" — and that exact marker (`module-02-sdk-setup/SKILL.md:387`) then drifted: on
#: server 1.37.13, 2026-09-24 `search_docs(query='upgrade Senzing SDK 4.3 to 4.4 procedure')`
#: returned ten hits, and hit 8 (the Python SDK's `szengine` API reference) and hit 10 (a tRPC
#: client source file) are not V3-to-V4 material, while the CLAIM beside it still held (#151).
#: A property survives new hits only when it is not quantified over them: "the corpus serves
#: V3-to-V4 migration material and no 4.x-to-4.y procedure" does; "every hit is …" does not.
#: The branch is scoped to what #151 decided, and no wider:
#:   - POSITIVE only. A negative universal ("none of the hits names …", "no hit …") is the shape
#:     of an absence CLAIM, which phase 1 re-asks, so flagging it would flag claims rather than
#:     rationales. Pinned as must-not-flag, so a later widening cannot absorb it silently.
#:   - Over a RESULT noun only. "every binding that differs" and "each tool's declared schema"
#:     quantify over something else and ship legitimately.
#:   - Ranking scope ("its top hits", "the highest-ranked hit") is a different shape, not here.
#: ⚠️ The quantifier's own number agreement picks the noun form, and that is what keeps a verb
#: out. `all …` takes the PLURAL ("all hits", "all of the documents"), so a floating
#: quantifier before a verb ("the routes all document installing only …", "all match") does
#: not read as a noun; `every` takes the singular and cannot float, so "every document is" is
#: safe; `each` CAN float ("they each document …", "each match the query"), so `document` and
#: `match` are left out after it. The fixtures on either side of each line are pinned in
#: `tests/test_mcp_negative_rationale_shape.py`, and the must-flag ones are the pre-fix text
#: that shipped, quoted with the commit it was copied from — the paraphrase that stood in for
#: it ("all six hits") is how the exemption above went unnoticed.
#: ⚠️ `both` counts on its own, as a numeral does.
#: ⚠️ `document` is dropped from the BOTH branch because it is also a verb: a shipped marker
#: reads "both document installing only …", where the subject is two routes and `document` is
#: what they do. A numeral cannot precede a verb ("four documents"), so the numbered branch
#: keeps it. Found by negative control, and pinned as a must-not-flag fixture -- the same
#: verb/noun collision that had to be corrected in two other guards this session.
_RESULT_NOUN = r"(?:hits?|results?|rows?|matches|entries|documents?|chunks?)"
_COUNTABLE_NOUN = r"(?:hits?|results?|rows?|matches|entries|chunks?)"
_ONE_RESULT = r"(?:hit|result|row|match|entry|document|chunk)"        # after `every`
_EACH_RESULT = r"(?:hit|result|row|entry|chunk)"                      # `each` floats: no verbs
_ALL_RESULTS = r"(?:hits|results|rows|matches|entries|documents|chunks)"  # after `all …`
CENSUS_SHAPED = re.compile(
    r"\b(?:(?:all|only|just)\s+)?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
    + _RESULT_NOUN + r"\b"
    r"|\bboth\s+" + _COUNTABLE_NOUN + r"\b"
    r"|\b(?:every\s+" + _ONE_RESULT
    + r"|each\s+" + _EACH_RESULT
    + r"|(?:every\s+one\s+of\s+the|all(?:\s+of)?(?:\s+the)?)\s+" + _ALL_RESULTS + r")\b",
    re.IGNORECASE,
)


def find_census_rationales(found):
    """[(relpath, lineno, phrase)] for markers whose rationale pins a count.

    A count is a numeral, `both`, or a positive universal over the result set ("every hit
    is …") — all three expire when the index returns one more thing. Reads the CLAIM and
    OWNER halves of an already-parsed marker — the two places a rationale lives. Reports
    rather than gates: a count is occasionally the fact itself ("the corpus has one entry
    for this code"), so the call is the reader's.
    """
    flagged = []
    for _key, _version, _date, claim, owner, relpath, lineno in found:
        for half in (claim, owner):
            m = CENSUS_SHAPED.search(half)
            if m:
                flagged.append((relpath, lineno, m.group(0).strip()))
                break
    return flagged


#: An ENUMERATED NAME-LIST expires for the same reason a count does, and carries no numeral,
#: so `CENSUS_SHAPED` above is structurally blind to it. A rationale saying the route "returned
#: the *A* and *B* sections" is falsified by the server renaming, dropping or adding one —
#: silently, because phase 1 re-asks the CLAIM and never the rationale, and the marker's date
#: then certifies a comment nobody re-read. This is not hypothetical twice over: the shape was
#: named as an observed drift cause in the comment above on 2026-08-31 and left unimplemented,
#: and on 2026-09-02 `phase2-data-mapping.md:719` was found citing a *Mapping identifiers*
#: section that `search_docs` over the Entity Specification does not return at all (server
#: 1.36.0, 2026-09-02). Nothing flagged it; a human read the returned titles against the
#: rationale's and noticed.
#:
#: ⛔ **Three conditions, all required — the third is what makes this readable rather than noise.**
#: A reporting verb, then two or more COORDINATED named elements after it, plus a governing
#: element noun anywhere in the clause. Dropping any one of them flags correct prose:
#:   - Coordination, not mere co-occurrence. `search_docs` is itself snake_case and appears in
#:     nearly every `owner:` clause, so "2+ names anywhere" would flag almost every marker via
#:     its own owning route's name. A joined run (`A, B` / `A and B`) is what an enumeration is.
#:   - The element noun is the whole reason "every hit is V3-to-V4 material (sz_dbupgrade,
#:     sz_configupgrade, …)" — the pre-fix text of `module-02-sdk-setup/SKILL.md:387` — is NOT
#:     flagged HERE: it has the verb and the coordinated snake_case run, but the run is
#:     examples under `material`, and `hit`/`material` name no response element. It is not an
#:     enumeration. It IS a census, and `CENSUS_SHAPED` above now claims it: "every hit is X"
#:     was falsified on 2026-09-24 by one new hit that was not X, exactly as a count would be
#:     (#151). So the two reporters divide that shape explicitly — census yes, enumeration no.
#: ⚠️ The parsed `claim` half INCLUDES the tool invocation, so `search_docs(query='…',
#: category='data_mapping')` hands every marker two snake_case tokens and a `section` noun for
#: free. `_strip_tool_calls` removes them first: a call's own parameters are not an enumeration
#: of what the response contained. Found while designing this, not by a later negative control,
#: and it would have made the report useless on its first run.
_ELEMENT_NOUN = (
    r"(?:sections?|fields?|flags?|keys?|commands?|parameters?|entry|entries)"
)
_REPORT_VERB = (
    r"(?:returned|returns|carries|carry|carried|holds|hold|held"
    r"|lists|list|listed|are|is|were|was)"
)
#: A named element: emphasized (`*…*`, `` `…` ``) or a bare ALL-CAPS / snake_case identifier.
#: Emphasis is the strongest signal — a rationale quoting a response's own section title
#: almost always marks it — and the bare forms catch field lists like `snippets[]`'s.
_EMPHASIZED = r"(?:\*[^*\n]{2,60}\*|`[^`\n]{2,60}`)"
_IDENTIFIER = (
    r"(?:[A-Z][A-Z0-9_]{2,}(?:\[\])?(?:\.[A-Z][A-Z0-9_]*)*"
    r"|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)"
)
_NAMED = r"(?:" + _EMPHASIZED + r"|" + _IDENTIFIER + r")"
#: ALL-CAPS prose is not a response element. Without this, a rationale writing MUST or NEVER
#: beside another capital contributes a spurious coordinated pair.
_CAPS_STOPWORDS = frozenset("""
    MUST NEVER NOT AND THE ITS IS ARE ALL ONE TWO ONLY JUST YES NO DUE OK ERR
    SDK MCP JSON HTTP HTTPS URL URI API CLI PII SQL CSV JSONL UTC README TODO
    """.split())
_COORDINATED = re.compile(
    _NAMED + r"(?:\s*(?:,|,?\s*and|,?\s*or)\s*(?:the\s+)?" + _NAMED + r")+"
)
_ELEMENT_NOUN_RE = re.compile(r"\b" + _ELEMENT_NOUN + r"\b", re.IGNORECASE)
#: ⚠️ No space before `(`, and the arguments must carry an `=` or a quote. Without both,
#: this ate the prose parenthetical in "*Payload attributes (optional)*" and reported the
#: name as `*Payload  *` — a stripper that removes real response-element names would
#: suppress the very hits this reporter exists to find.
_TOOL_CALL = re.compile(r"\b[a-z][a-z0-9_]*\([^()]*[='\"][^()]*\)")


def _strip_tool_calls(text):
    """Remove `tool(param='value', …)` invocations — their parameters enumerate nothing.

    The marker's claim half opens with the call that was asked, so without this every
    rationale inherits the call's own snake_case tokens as if they were response elements.
    """
    return _TOOL_CALL.sub(" ", text)


def _clauses(text):
    """Split on `;` and em dash only.

    ⚠️ Deliberately NOT on `--`: a shipped marker enumerates `install --cask` and
    `uninstall --cask`, and splitting there would cut a clause in half mid-name.
    """
    return [c for c in re.split(r"[;—]", text) if c.strip()]


def _named_run(clause):
    """The longest coordinated run of named elements in `clause`, or None.

    Filters ALL-CAPS prose words out of a run and requires two survivors, so
    "MUST and NEVER" does not read as an enumeration of two response elements.
    """
    for m in _COORDINATED.finditer(clause):
        names = [n for n in re.findall(_NAMED, m.group(0))
                 if n.upper().strip("*`[]().") not in _CAPS_STOPWORDS]
        if len(names) >= 2:
            return m.group(0).strip()
    return None


#: The gap between the enumeration and its element noun may not cross a coordinator. This is
#: the condition that separates a GOVERNING noun from one that merely shares the clause, and it
#: is what keeps the criterion-2 case out: in the pre-fix text of `module-02-sdk-setup/SKILL.md:387`
#: (historical — the text as of commit bc4be70, before #151 rewrote it) the noun sits
#: in a different conjunct — "every hit is V3-to-V4 migration material (sz_dbupgrade,
#: sz_configupgrade, …) **and the topic list carries no upgrade entry**" — where `entry` governs
#: `upgrade`, not the parenthesised run, and the run itself is examples under the property word
#: `material`. Presence-in-clause alone flagged it, which is a false positive on the exact
#: fixture the spec names as must-not-flag for THIS detector (the census detector does flag it).
_COORDINATOR = re.compile(r"\b(?:and|or|but)\b|[;,]", re.IGNORECASE)
_GOVERNING_GAP = 40


def _governing_noun(clause, run_start, run_end):
    """The element noun governing the run at [run_start, run_end), or None.

    Adjacent means: within `_GOVERNING_GAP` characters on either side, with no coordinator
    between noun and run. Both directions are real phrasings — "returned the *A* and *B*
    sections" puts it after, "carries the fields `a` and `b`" puts it before.
    """
    for m in _ELEMENT_NOUN_RE.finditer(clause):
        if m.end() <= run_start:
            gap = clause[m.end():run_start]
        elif m.start() >= run_end:
            gap = clause[run_end:m.start()]
        else:
            continue                      # the noun is inside the run; it is a name, not a noun
        if len(gap) <= _GOVERNING_GAP and not _COORDINATOR.search(gap):
            return m.group(0)
    return None


def find_enumeration_rationales(found):
    """[(relpath, lineno, phrase)] for markers whose rationale enumerates named elements.

    The sibling of `find_census_rationales` for the shape a numeral cannot express. Reports
    rather than gates, and for a stronger reason than the count case: three of the four
    enumerations in the corpus on 2026-09-02 were legitimate — an exhaustive list IS the
    discriminating fact of an absence claim ("no `brew upgrade` anywhere; what it does carry
    is …"). What makes an enumeration a liability is not its shape but whether the claim
    beside it would survive the list changing, and no regex can read that. So the reader
    judges, exactly as the preamble says.

    ⚠️ **What this does NOT cover, stated so the gap is loud rather than assumed.** The
    element noun must GOVERN the run (see `_governing_noun`), so an enumeration whose noun
    trails in a separate conjunct is missed — `phase1-verification.md:251`'s
    "carry file_path, source_url, … with no content **field** at all" is the shipped example,
    and it is the same "exhaustive field list" the comment above names as a 2026-08-31 drift
    cause. That is a deliberate trade: presence-in-clause also flagged the property-shaped
    fixture the spec forbids flagging, and a report that cries wolf is one nobody opens. If a
    second enumeration drifts in that phrasing, widen `_governing_noun` — do not drop the
    coordinator test, which is the half doing the discriminating.
    """
    flagged = []
    for _key, _version, _date, claim, owner, relpath, lineno in found:
        hit = None
        for half in (claim, owner):
            for clause in _clauses(_strip_tool_calls(half)):
                vm = re.search(_REPORT_VERB + r"\b", clause, re.IGNORECASE)
                if not vm:
                    continue
                tail = clause[vm.end():]
                run = _named_run(tail)
                if not run:
                    continue
                start = vm.end() + tail.index(run)
                if _governing_noun(clause, start, start + len(run)):
                    hit = run
                    break
            if hit:
                break
        if hit:
            flagged.append((relpath, lineno, hit))
    return flagged


def find_malformed_negatives(repo):
    """[(relpath, lineno, line)] for every `MCP-NEGATIVE:` that does not fully parse.

    Two causes, and they need different fixes: a missing `owner:` clause, or a marker
    **wrapped across lines** — `MCP_NEGATIVE` is not `re.DOTALL`, so it cannot match past a
    newline and a wrapped marker fails identically to a clauseless one. `tests/
    test_dated_negatives_are_marked.py` diagnoses which per row; do not guess one for both.

    A marker that is present but malformed — whatever the cause, missing its required `owner:`
    clause — is worse than a missing marker: the claim is still shipped and still shapes
    the plugin's routing, but it no longer appears on the re-check worklist. Report it
    loudly rather than letting the count quietly shrink.
    """
    bad = []
    for path in _scan_files(repo):
        text = _read(path)
        if NEGATIVE_OPT_OUT in text:
            continue
        for lineno, line in enumerate(text.split("\n"), 1):
            if MCP_NEGATIVE_TOKEN.search(line) and not MCP_NEGATIVE.search(line):
                bad.append((os.path.relpath(path, repo), lineno, line.strip()))
    return bad


def _prose_units(text):
    """[(first_lineno, unit_text)] — one unit per fenced block, per bullet, per paragraph.

    Granularity is the whole game here. A contiguous bullet list read as ONE unit produced a false
    positive on `ground-rules.md`'s tool-routing list: a tool name in one bullet, "returns no" in
    another and a date in a third co-occurred without ever being a single claim. Same lesson as
    `tests/test_declined_ledger.py`, which had to go per-bullet rather than per-entry.

    A fenced block stays whole, because a claim there is routinely split across two comment lines —
    the tool on one, the date on the next.
    """
    units, cur, start, fence = [], [], None, False

    def flush():
        if cur:
            units.append((start, "\n".join(cur)))

    for lineno, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            if fence:                                   # closing
                cur.append(line)
                flush()
                cur, start, fence = [], None, False
            else:                                       # opening
                flush()
                cur, start, fence = [line], lineno, True
            continue
        if fence:
            cur.append(line)
            continue
        if not line.strip():                            # blank line ends a unit
            flush()
            cur, start = [], None
        elif re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):  # a bullet starts its own unit
            flush()
            cur, start = [line], lineno
        elif cur:
            cur.append(line)                            # continuation
        else:
            cur, start = [line], lineno
    flush()
    return units


def find_unmarked_negatives(repo):
    """[(date, relpath, lineno, phrase, excerpt)] for dated tool-absence prose with no marker."""
    base = os.path.join(repo, PROSE_ROOT)
    found = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            text = _read(path)
            if NEGATIVE_OPT_OUT in text:
                continue
            lines = text.split("\n")
            for start, unit in _prose_units(text):
                phrase = PROSE_ABSENCE.search(unit)
                dated = PROSE_DATED.search(unit)
                if not (phrase and dated and PROSE_TOOL.search(unit)):
                    continue
                # A marker or an escape covers the claim when it sits NEAR it, not only inside
                # the same unit: both are written as HTML comments immediately before or after,
                # which puts them in a different unit whenever the claim is a bullet or a fence.
                lo = max(0, start - 1 - PROSE_MARKER_WINDOW)
                hi = min(len(lines), start - 1 + len(unit.split("\n")) + PROSE_MARKER_WINDOW)
                near = "\n".join(lines[lo:hi])
                if PROSE_QUOTED_HISTORY in near or PROSE_NOT_A_CLAIM in near:
                    continue                            # declared not-a-claim / quoted history
                if MCP_NEGATIVE.search(near):
                    continue                            # a marker already covers it
                found.append((dated.group(0), os.path.relpath(path, repo), start,
                              phrase.group(0), " ".join(unit.split())[:150]))
    found.sort()                                        # oldest stamp first, like `negatives`
    return found


def report_unmarked(repo):
    """Dated tool-absence prose carrying no marker — the complement of `negatives`."""
    found = find_unmarked_negatives(repo)
    print("== Dated tool-absence claims in shipped prose with NO marker ==")
    print("`negatives` lists what is already tagged, so it cannot see these. Each is a claim")
    print("that expires with no way to notice: the suite is offline (INV-108), and nothing")
    print("re-asks an unmarked negative. Give each one a marker with its `owner:` clause — after")
    print("re-asking the owning route, never by stamping today's date on an unverified claim.")
    print()
    print("⚠️ Judgment required, which is why this is a report. A hit may be prose ABOUT tool")
    print("behavior rather than a live claim. The date is what separates the two: undated prose")
    print("is not re-checkable, so it is not reported. Vocabulary is a phrase list and evadable")
    print("by paraphrase — a miss is weak evidence, a hit is worth reading.")
    print()
    if not found:
        print("  (none — every dated tool-absence claim in shipped prose carries a marker)")
        return found
    print("unmarked: %d" % len(found))
    print()
    for stamp, relpath, lineno, phrase, excerpt in found:
        print("  %-12s %s:%d   [%s]" % (stamp, relpath, lineno, phrase))
        print("      %s" % excerpt)
    return found


def version_tuple(version):
    """(major, minor, patch) from a marker's recorded server version, or None if unparseable."""
    parts = re.findall(r"\d+", version or "")
    if not parts:
        return None
    return tuple(int(x) for x in (parts + ["0", "0", "0"])[:3])


def negatives_due(found, current):
    """Split markers into (due, current_ones) against a CURRENT server version.

    ⚠️ `current` is supplied by the caller, never guessed. This scan is offline (INV-108) and
    MUST NOT pretend to know what the live server is running — a version it inferred would be
    the same silent-staleness defect one level down. With no `--server` argument the split is
    not attempted and every marker is reported unlabeled, as before.

    Why this exists: on 2026-08-21 three audit runs in one day each read this report as CLEAN
    while 21 of 23 markers were dated `server 1.32.9` against a live 1.33.0, none re-asked.
    The report answered "is every marker well-formed?" and was read as "has any expired?" —
    so an eight-day-stale marker was indistinguishable from one re-asked that morning. One of
    the four sampled was already false.
    """
    ref = version_tuple(current)
    if ref is None:
        return [], list(found)
    due, ok = [], []
    for row in found:
        v = version_tuple(row[1])
        (due if v is None or v < ref else ok).append(row)
    return due, ok


def report_negatives(repo, current_server=None):
    """Dated 'this tool does not contain X' claims, oldest server version first."""
    found = find_negatives(repo)
    print("== Dated MCP negatives, oldest server version first ==")
    print("A negative about a tool's content cannot go stale detectably: the suite is")
    print("offline (INV-108), so nothing notices when the server gains the coverage the")
    print("plugin routed around. Re-ask for each of these; the oldest is the most likely")
    print("to have moved. When one no longer holds, correct the claim AND invert or")
    print("rescope the guard that pins it — do not delete the guard.")
    print()
    print("⛔ Re-ask the OWNER, not just the route that came back empty. An empty result")
    print("from a tool that never carried the fact is a true statement about that tool and")
    print("no evidence at all for the negative — which is how a wrong-route conclusion")
    print("reaches an invariant looking reviewed (INV-194). The `owner:` line below is the")
    print("route the claim actually rests on; if it is where the fact lives, the negative")
    print("is about ROUTING and the reader should be sent there instead.")
    print()
    malformed = find_malformed_negatives(repo)
    if malformed:
        print("⛔ MALFORMED markers: %d — shipped claims that fell OFF the worklist. A"
              % len(malformed))
        print("   malformed marker is worse than a missing one: the claim still routes the")
        print("   plugin, but nothing re-asks it. Either a missing `owner:` clause or a")
        print("   marker WRAPPED across lines — it must be on ONE line (regex is not DOTALL).")
        for relpath, lineno, line in malformed:
            print("     %s:%d" % (relpath, lineno))
            print("       %s" % line[:150])
        print()
    census = find_census_rationales(found)
    if census:
        print("⚠️ CENSUS-SHAPED rationales: %d — re-describe rather than re-date." % len(census))
        print("   These pin a COUNT — a numeral, `both`, or a claim about EVERY result (\"every")
        print("   hit is …\"), which one new hit falsifies just as it falsifies a numeral.")
        print("   Phase 1 re-asks the CLAIM, never the rationale beside it,")
        print("   so a census stops describing the response while the claim stays true and the")
        print("   date certifies the whole comment. Replace it with the discriminating property")
        print("   the count was standing in for — that is the half a later reader acts on.")
        for relpath, lineno, phrase in census:
            print("     %s:%d  — %r" % (relpath, lineno, phrase))
        print("   ⚠️ A hit needs judgment: a count is occasionally the fact itself.")
        print()
    enumerated = find_enumeration_rationales(found)
    if enumerated:
        print("⚠️ ENUMERATION-SHAPED rationales: %d — re-ask before re-dating."
              % len(enumerated))
        print("   These pin a LIST OF NAMED ELEMENTS presented as what the route returned.")
        print("   It expires exactly as a count does and for the same reason — a rename, a")
        print("   drop or an addition falsifies it server-side — but carries no numeral, so")
        print("   the census matcher above is structurally blind to it. On 2026-09-02 this")
        print("   shape had drifted undetected: a rationale cited a *Mapping identifiers*")
        print("   section the route does not return.")
        for relpath, lineno, phrase in enumerated:
            print("     %s:%d  — %r" % (relpath, lineno, phrase))
        print("   ⚠️ A hit needs judgment, and MORE often than above: an exhaustive list is")
        print("     frequently the discriminating fact of an absence claim, which is the")
        print("     legitimate use. Ask whether the claim survives the list changing.")
        print()
    if not found:
        print("  (none found — if that is a surprise, the markers are missing, not the claims)")
        print("  A marker with no `owner:` clause does NOT parse, by design: it is reported")
        print("  above as malformed rather than silently accepted.")
        return found
    due, ok = negatives_due(found, current_server)
    if current_server:
        print("markers: %d — %d DUE (recorded below server %s), %d current"
              % (len(found), len(due), current_server, len(ok)))
        print("   ⛔ DUE means the marker was recorded against an OLDER server than the one")
        print("     supplied, so its claim has not been re-asked since. It does NOT mean the")
        print("     claim is wrong — three of four sampled on 2026-08-21 still held. It means")
        print("     nothing knows either way, which is the state this label exists to end.")
        print("   ⛔ Re-ask each one INDIVIDUALLY. Re-dating in bulk makes every marker look")
        print("     reviewed at the cost of reviewing none.")
    else:
        print("markers: %d" % len(found))
        print("   ⚠️ No --server given, so no staleness split was attempted: this listing says")
        print("     every marker is well-formed and nothing about whether any has expired.")
        print("     Pass --server <version> (from get_capabilities) to get the DUE count.")
    print()
    for label, rows in (("DUE", due), ("current", ok)):
        if not rows or not current_server:
            continue
        print("  --- %s (%d) ---" % (label, len(rows)))
        for _key, version, date, claim, owner, relpath, lineno in rows:
            print("  %-7s server %-8s %s  %s:%d" % (label, version, date, relpath, lineno))
            print("      %s" % claim)
            print("      owner: %s" % owner)
        print()
    if not current_server:
        for _key, version, date, claim, owner, relpath, lineno in found:
            print("  server %-8s %s  %s:%d" % (version, date, relpath, lineno))
            print("      %s" % claim)
            print("      owner: %s" % owner)
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report",
                    choices=("invariants", "shipped", "affected", "negatives", "unmarked",
                             "both"))
    ap.add_argument("--server", default=None,
                    help="current MCP server version (from get_capabilities); enables the "
                         "DUE/current split on the negatives report. Never inferred — an "
                         "offline scan must not guess what the live server runs.")
    ap.add_argument("--repo", default=os.getcwd(),
                    help="repo root (default: current directory)")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, "specs")):
        sys.stderr.write("no specs/ under %s — pass --repo\n" % repo)
        return 2
    if args.report in ("invariants", "both"):
        report_invariants(repo)
    if args.report == "both":
        print()
    if args.report in ("shipped", "both"):
        report_shipped(repo)
    if args.report == "both":
        print()
    if args.report in ("affected", "both"):
        report_affected(repo)
    if args.report == "both":
        print()
    if args.report in ("negatives", "both"):
        report_negatives(repo, args.server)
    if args.report == "both":
        print()
    if args.report in ("unmarked", "both"):
        report_unmarked(repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
