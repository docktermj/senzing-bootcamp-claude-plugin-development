# Processed bootcamp feedback (archive)

Every `SENZING_BOOTCAMP_PLUGIN_FEEDBACK*.md` that `feedback-to-issues` has triaged is moved
here as `SENZING_BOOTCAMP_PLUGIN_FEEDBACK_<unixtime>.md`, and every entry it processed is
recorded in `PROCESSED.jsonl`.

**Why this exists.** Feedback files arrive from multiple bootcampers at multiple times, and
the working copy at the repo root is gitignored and transient — one has already been lost to
an overwrite before it was archived. Committing the processed file here makes the raw report
durable, and the ledger makes re-processing detectable.

**Why the ledger is per entry, not per file.** The realistic collision is a file that
*overlaps* a previous one: a bootcamper's project accumulates entries during a run, so a
later copy carries the earlier entries plus new ones. Whole-file comparison gets that wrong
in both directions — a byte-compare calls it new and re-specs everything, and a whole-file
duplicate verdict would discard the genuinely new entries. So an entry's identity is
`sha256` of its **normalized** text (BOM stripped, newlines normalized, lines right-stripped,
blank runs collapsed), which also means a file re-saved on Windows with a BOM or CRLF endings
is still recognized as the same content.

`PROCESSED.jsonl` — append-only, one object per processed entry:

| Field | Meaning |
|---|---|
| `entry_id` | first 16 hex chars of `sha256` of the entry's normalized text |
| `title` | the entry's `## ` heading, as parsed |
| `archive` | the file in this directory that carries it |
| `archive_unixtime` | that file's timestamp, which a `_DUPLICATE` rename points back at |
| `processed` | the date it was triaged |
| `disposition` | the spec it produced, or `already-tracked` / `needs-clarification` |

`disposition` is what makes the ledger worth keeping: it is the only record linking an entry
to the spec it became, and it stops an entry that legitimately produced no spec from being
re-triaged forever.

## Rules

- **Never edit an archived file or a ledger line.** Both are the record of what was
  processed. A correction is a new spec, not rewritten history.
- **Never treat a file in this directory as input.** `feedback-to-issues` resolves candidates
  from the repo root or a bootcamper project, never from here.
- **This directory is committed but never propagated.** It carries bootcamper text —
  usernames, workstation details, dataset names — so `feedback/**` is on
  `propagate-to-public`'s excluded list. Do not relax either half of that.

Tooling: `.claude/skills/feedback-to-issues/feedback_ledger.py` (`check` and `commit`).
