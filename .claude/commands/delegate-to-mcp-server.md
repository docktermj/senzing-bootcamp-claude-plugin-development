---
description: Find Senzing facts the plugin still holds that the MCP server now serves itself, and file issues to delegate them (maintainer tool).
argument-hint: "[area or category to bound this run to] (omit to take the full re-check list)"
---

Maintainer request: sync the Senzing Bootcamp plugin with the live Senzing MCP server.

Invoke the `delegate-to-mcp-server` skill and follow it end to end.

Run bounded to: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, build the re-check list from all four of Step 2's sources and
  bound the inventory at Step 3. ⛔ **Do not attempt the whole surface in one pass** — the skill
  says to bound it, and a run that sprawls finishes nothing and records nothing.
- If `$ARGUMENTS` **names an area or category**, take that as the bound and say so in the
  report, so the next run knows what was left.

**Step 1 first, and it is not optional.** Record both of the server's versions — the server
version *and* the docs index — before looking at anything. Every ledger comparison is against
those two axes, and a run that skips them cannot tell an expired decision from a current one.

⛔ **Re-ask the server this session, for every fact (INV-080).** Never carry a Senzing fact
from the plugin, from a spec, from the ledger, or from training data into a recommendation.
**The ledger records what was true at a version; it is not a source.** This is the rule the
whole skill rests on, and it is the one a fast run drops first.

⛔ **Ask the tool that OWNS the fact**, not `search_docs` for everything. An absence found
through the wrong route is not evidence of absence (INV-194) — it is a true statement about the
wrong tool, and one has already become an invariant plus a guard enforcing it.

⛔ **"The server can answer it" is not by itself a reason to delete anything.** It is the entry
ticket to Step 6, where delegation has to earn its place. **A large fraction of legitimate
findings end in `keep` — record those too**, or the next run re-litigates them from scratch.

⛔ **Delegation done badly is worse than duplication.** A paragraph replaced by "ask the MCP
server", with no tool, no parameters and no statement of what to extract, is a regression
dressed as a cleanup. Every `delegate` issue names the call.

**Sweep `specs/INVARIANTS.md` for invariants asserting a server limitation** — every run.
It is the highest-risk category in the repo and the easiest to skip, precisely because it is
not under `plugins/`. An invariant saying the server *cannot* do something is pinned by tests,
cited by specs and shapes future work, so when the server gains the ability the false premise
is load-bearing in a way ordinary stale prose never is.

⛔ **Write nothing under `specs/`** — the archive is frozen (INV-307). This command's only
writes are **GitHub issues** and its own ledger, `specs/mcp-coverage.jsonl`, which is a
**named live exception** to the freeze, recorded as such in INV-307 and in
`docs/FAMILY_WORKFLOW.md` §8. ⚠️ **It is NOT exempt because it is `.jsonl`.** That was the
reason given here until #142, and it is the reasoning `invariant_manifest.py` rejects by name
for its own artifact — the freeze guard globs `specs/*.md`, so a non-Markdown file there is
legal only because the glob does not reach it, *a scope-narrowing that happens to produce
correct behavior, which INV-308 says must not be relied on*. A permission that rests on a
guard's blind spot disappears the moment the guard is widened, and nobody widening it would
know they were revoking one. Never modify plugin code,
hooks, scripts or skills — filing the issues is the deliverable, and implementing them is
`/implement-github-issue`'s job. ⛔ **Never propose deleting or renumbering an invariant**;
`specs/INVARIANTS.md` is append-only, and a superseded one is *marked* superseded.

⛔ **(INV-314) Show the maintainer every issue title and body and get an explicit yes before filing**,
and ⛔ **never pass `--repo`.** Filing is outward-facing and immediate: an issue cannot be
un-filed and its notifications have already gone out. This is the parent repository, where
parent-to-child change travels by parity from a tagged release — so the parent never files
into a child at all.

**Step 8 is part of the job, not an afterthought** — the `keep-server-lacks-it` rows are
collectively a list of things the server could serve and does not, and reporting them is the
only thing that shrinks this plugin's maintenance surface for good. ⛔ **Show the maintainer
the exact message and get an explicit yes before sending (INV-314)**, strip everything identifying
(data shape, never data; no paths, hostnames, employer or dataset contents), and ⛔ never send
under `category='license_request'` (INV-135).

Finish by recording **every** verdict in the ledger — keeps included — and reporting what was
bounded out, which server version and docs index the run ran against, and any site whose owning
tool could not be reached. A gap disclosed is a finding; a gap skipped silently is a false
clean bill of health.
