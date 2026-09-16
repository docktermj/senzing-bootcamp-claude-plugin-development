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

These wrote new spec files into this directory. Under the freeze their output no longer
has anywhere to land, and running them before their rework lands will turn the suite red:

| Command | Status |
| --- | --- |
| `/feedback-to-specs` | Rename to `/feedback-to-issues` — issue #49 |
| `/implement-spec` | Retire in favor of `/implement-github-issue` — issue #50 |
| `/unattended-spec-loop` | Rename to `/unattended-issue-loop`, label-gated — issue #51 |
| `/delegate-to-mcp-server` | Still writes specs; needs the same rework, no issue yet |

Triage of what remains here is issue #53.

## Reading the archive

Nothing about how to *read* these files has changed. A spec records the reasoning behind a
change; `IMPLEMENTED.md` records that it landed and what it established; `INVARIANTS.md`
records the durable rule. Follow a `(Source: …)` citation from an invariant to find the
reasoning that produced it.
