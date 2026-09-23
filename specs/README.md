# `specs/` is frozen

**Cutover: 2026-09-15.** This directory is a **read-only archive (INV-307)**. New work for
the Senzing Bootcamp Claude Plugin is tracked as **GitHub issues**, not as spec files.

The freeze itself landed 2026-09-16 (issue #52), recording the 2026-09-15 cutover date
of the move it belongs to. Those are two different dates and neither stands in for the
other.

## What is frozen

Every `*.md` file in this directory except the live records listed below. The frozen set
is pinned by name in [`FROZEN-MANIFEST.txt`](FROZEN-MANIFEST.txt) and enforced in both
directions by `tests/test_specs_are_frozen.py`:

- a manifest name whose file has gone fails the suite, so the archive cannot be silently thinned
- a `specs/*.md` that is neither in the manifest nor a live record fails the suite, so nothing new can land

No count is asserted anywhere — the set is derived and compared, because a number in prose
goes stale silently while continuing to read as authoritative.

`todo.md` is frozen with the rest. It was a future-ideas list; future ideas are issues now.

## What stays live

These are **not** frozen. They are historical record and live rules, and they are still
written to:

| File | Why it stays live |
| --- | --- |
| [`IMPLEMENTED.md`](IMPLEMENTED.md) | The completion ledger, and the **only** completion signal the repo has (INV-182). Still appended for issue-driven work. |
| [`DECLINED.md`](DECLINED.md) | The declined-work record, and the one file in the repo whose Senzing claims have no re-verification path (INV-217). |
| [`INVARIANTS.md`](INVARIANTS.md) | The canonical invariants. Machine-extended by design — `/review-invariants` appends to it after maintainer sign-off. |

**The ledger is part of the archive, not separate from it.** `INVARIANTS.md` cites its
sources by spec slug, and six of those slugs have no file here — they resolve through an
`IMPLEMENTED.md` entry instead (`tests/test_spec_ledger_invariants.py` accepts either).
Retiring the ledger would break those citations. That is why it stays.

## Commands that wrote here

These wrote new spec files into this directory. Under the freeze their output no longer has
anywhere to land, so running one that has not been reworked turns the suite red. ⛔ **One is
left**, and it is the last row:

| Command | Status |
| --- | --- |
| `/feedback-to-issues` | ✅ Renamed and reworked — it files GitHub issues now (#49) |
| `/implement-spec` | ✅ Retired in favor of `/implement-github-issue` (#50, #60) |
| `/unattended-issue-loop` | ✅ Renamed from `/unattended-spec-loop` and label-gated (#51); its blocked path now comments on the issue, and it forbids writing here outright (#69) |
| `/production-readiness-audit` | ✅ Files a GitHub issue when attended, records findings in the ledger when not (#69) |
| `/delegate-to-mcp-server` | ⛔ **Still writes specs**; needs the same rework, no issue yet |

## Triage of what remained here

**Complete (#53, 2026-09-23).** One file was in neither ledger: [`todo.md`](todo.md), a
future-ideas list. It had six top-level bullets, three already struck through or marked done.
The three live ones were decided, and ⛔ **`todo.md` itself was not edited** — it is frozen with
the rest, so this is the record.

| Item | Decision |
| --- | --- |
| Senzing web app as a curriculum option | **Let go.** The 2026-07-27 bootcamper suggestion has no detail to act on — the feedback file's *"Why it matters"* and *"Suggested fix"* both read **"Not answered"**, and it was already dispositioned `needs-clarification` on 2026-07-31. A suggestion that still matters will resurface as feedback. |
| Module 7's query-program guidance does not point at the factory-lifetime rule | **Migrated to #134.** Confirmed, and broader than `todo.md` recorded: `INV-152` is cited nowhere under `plugins/`. |
| The user-level CommonMark hook fights the defer-to-graduation rule | **Migrated to #135**, as a maintainer-documentation gap rather than a defect. ⛔ The plugin ships no `PostToolUse` hook, so no bootcamper is affected; the conflict is host configuration. |

⚠️ **No count of the archive is stated here, deliberately** — see the note above on figures in
prose going stale while continuing to read as authoritative. The original framing of #53 was
itself an instance: its *"~219 unaccounted for"* subtracted a five-week-old ledger count from a
current file count, manufacturing a gap that never existed. The true figure has never exceeded 4.

## Reading the archive

Nothing about how to *read* these files has changed. A spec records the reasoning behind a
change; `IMPLEMENTED.md` records that it landed and what it established; `INVARIANTS.md`
records the durable rule. Follow a `(Source: …)` citation from an invariant to find the
reasoning that produced it.
