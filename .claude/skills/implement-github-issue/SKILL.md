---
name: implement-github-issue
description: Implement a GitHub issue end-to-end on a dedicated branch — assess the issue for completeness, clarify ambiguities, choose an approach (racing competing implementations when the work is complex), write and run tests, mirror the repo's CI locally, push, and open a pull request. Documents every decision on the issue. Never merges. Invoke with /implement-github-issue [issue URL or number].
disable-model-invocation: true
user-invocable: true
argument-hint: "[GitHub issue URL or number]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
---

Take a GitHub issue from "reported" to "pull request open for review".

> ⚠️ **Two copies of this skill exist, and the USER-LEVEL one resolves.** The other is at
> ``~/.claude/skills/implement-github-issue/SKILL.md``. Measured 2026-09-23 by reading the skill body Claude Code
> injected on invocation against marker strings unique to each file: with a project copy present
> and `main` up to date, **the copy under `~/.claude/skills/` is the one that loads**. ⛔ The
> earlier claim here — that the project copy governs — was false from the day it was written
> (2026-09-16), and is why #119 and #124 amended only one copy.
>
> The block marked `SHARED-RULES` below is **byte-identical in both** and is compared by
> `/check-skill-drift`. Everything outside it may legitimately differ: this repository's copy
> cites `docs/FAMILY_WORKFLOW.md` and `specs/INVARIANTS.md`, which do not exist in the repos the
> global copy serves.

This skill never auto-triggers: it posts publicly to GitHub, pushes branches, and opens PRs.
Run it only when the user explicitly invokes `/implement-github-issue`.

## Non-negotiable guardrails

- **Never merge the pull request.** Never run `gh pr merge`, and never fast-forward `main`.
- **Never commit to `main`**, never force-push, never push anything before Gate 2.
- **Never delete or rewrite an existing branch** other than the one this run created.
- If the issue turns out to be invalid, a duplicate, or already fixed, **stop and say so**
  (Phase 9's escape hatch). Do not manufacture a change to justify the run.

## Approval gates

The run pauses at exactly two points. Everything between them proceeds unattended.

- **Gate 1 — Plan.** After the readiness assessment, clarifications, and approach selection.
  The user confirms the interpretation and the chosen approach before any code is written.
- **Gate 2 — Pre-push.** After implementation, tests, and the local CI mirror all pass.
  The user confirms before anything leaves the machine (push + PR + PR-link comment).

Stop and wait at each gate. Do not proceed on silence.

---

## Phase 0 — Resolve the target

Accept any of these in `$ARGUMENTS`:

- Full URL: `https://github.com/<owner>/<repo>/issues/<n>`
- Shorthand: `<owner>/<repo>#<n>`
- Bare number: `<n>` — resolves against the current repo

<!-- SHARED-RULES:BEGIN — byte-identical in both copies of this skill. Verified by
     `.claude/skills/check-skill-drift/skill_drift.py` (#128). Edit here and carry across. -->
If `$ARGUMENTS` is empty, **review the open issues for dependencies first.** Report, in this
order: the dependencies you found, a suggested implementation order where one follows, and which
issues are independent. Then **name the issue you suggest** and stop.

⛔ **Never begin work on an issue the maintainer has not approved.** You may analyze, you may
rank, you may name one; you may not start. That is the whole of this rule — not a qualifier on
it.

- **End by naming one issue**, so the maintainer's next act is approval rather than selection.
  You have just read the entire backlog and are the thing best placed to propose a target.
- ⚠️ Where the open set is empty, or where no issue is a defensible suggestion, **say so** rather
  than naming one to satisfy the form.
- **Every ordering claim carries its evidence** — the sentence, file or acceptance criterion the
  maintainer can check. An ordering with no citable evidence is a **preference**; label it as one
  rather than presenting it as a dependency.
- ⛔ **Never read a reference that asserts NON-dependence as a dependency.** An issue naming
  others to support an absence claim — *"none of which touch …"*, an `owner-checked:` line — is
  saying they are **unrelated**. Reading those as edges inverts the clearest signal available.
- ⛔ **Shared-file coupling is merge risk, not order.** A file touched by most of the backlog is
  a hub and establishes no sequence. Report it separately or not at all.
- Where the issues are independent, **say so and imply no order.** An invented sequence over an
  independent set is worse than no report.

The real relations are found by **reading the issues**, not by counting references or
intersecting paths — both mechanical methods have produced wrong answers on a real backlog, and
the only true relation was visible to neither.
<!-- SHARED-RULES:END -->

⚠️ **In this repository specifically**, the family-wide statement of the rules above is
[`docs/FAMILY_WORKFLOW.md`](../../../docs/FAMILY_WORKFLOW.md) **R8**, and §10 records that R8 has
been narrowed three times — approval before action is the clause that is left. The measurements
behind the two reading rules were taken 2026-09-22 over seven open issues, where
`specs/INVARIANTS.md` was the hub that made five of seven look ordered. ⛔ **None of that belongs
in the shared block**: the global copy serves repositories that have neither file.

Preflight — abort with a clear message if any fails:

```bash
gh auth status                    # authenticated?
git rev-parse --show-toplevel     # inside a git repo?
git status --porcelain            # working tree clean? (abort if dirty)
gh repo view --json nameWithOwner --jq .nameWithOwner
```

If the URL names a different repo than the current working directory, stop and tell the user
which repo they need to be in — do not clone or `cd` elsewhere.

Fetch the issue and its existing comments:

```bash
gh issue view <n> --json number,title,body,labels,state,author,url,comments
```

If the issue is closed, ask whether to continue before doing anything else.

## Phase 0.5 — Resume check

State file: `<repo-root>/.claude/skills/implement-github-issue/state/<issue-number>.json`

```json
{
  "issue": 42,
  "branch": "42-jdoe-1",
  "phase": "implement",
  "approach": "…one-line summary of the chosen approach…",
  "gate1_approved": true,
  "comments_posted": ["started", "clarifications"]
}
```

If the file exists and its branch still exists, tell the user what phase the previous run
reached and offer to resume from there rather than starting over. Write the file after every
phase transition and after every issue comment posted, so an interrupted session is always
recoverable.

## Phase 1 — Branch

Invoke the `git-branch` skill with the issue number. It creates and checks out
`<issue-number>-<github-username>-<n>`. Do not reimplement its naming logic.

Post **issue comment 1 of 4** (see Issue log below): work started, on which branch.

## Phase 2 — Readiness assessment

Score the issue against this rubric. For each, record `yes` / `no` / `partial` plus one line
of evidence quoted from the issue:

| Dimension | Question |
|---|---|
| Goal | Is the desired end state stated, not just the symptom? |
| Acceptance | Is there a testable definition of done? |
| Scope | Is it clear what is explicitly *not* included? |
| Locus | Can the affected components be identified from the issue plus the codebase? |
| Testability | Can a test strategy be inferred? |
| Compatibility | Is breaking-change status known (API, schema, config, CLI surface)? |

Before scoring, actually look: search the codebase for the components the issue names, and
read the surrounding code. Most "ambiguity" dissolves once you have read the code.

Verdict:

- **READY** — proceed to Phase 4.
- **NEEDS-CLARIFICATION** — proceed to Phase 3.
- **BLOCKED** — the issue does not describe an actionable change at all. Post the assessment
  to the issue, tell the user, and stop.

## Phase 3 — Clarify

Ask **only** about ambiguities that would change the implementation. If two readings produce
the same code, pick one, note the assumption, and move on. Do not interrogate the reporter
over trivia.

1. Ask the user directly, in chat, batched as a single set of questions.
2. Take their answers as authoritative.
3. Post **issue comment 2 of 4**: one consolidated Q&A block — every question with its
   answer, plus any assumptions taken without asking. This is the public record.

Never fabricate an answer, and never attribute an answer to the issue's author when it came
from the user.

## Phase 4 — Choose the approach

Run the complexity test. Race competing implementations if **any** of these hold:

- The change spans more than one module or package
- It changes a public API, wire format, schema, config, or CLI surface
- There is no existing pattern in the repo to copy
- It is concurrency-, performance-, or migration-sensitive
- The issue itself proposes more than one option

Otherwise implement directly (Phase 5a).

### Gate 1

Present to the user: the readiness verdict, the clarifications taken, the intended approach
(or the fact that approaches will be raced and on what criteria), and the files expected to
change. **Wait for approval.** Record `gate1_approved` in the state file.

## Phase 5a — Direct implementation

Implement the change on the branch. Match the surrounding code's conventions, naming, and
comment density. Change only what the issue calls for.

## Phase 5b — Competing approaches

1. **Write the judging rubric first**, before launching anything, and show it to the user.
   Default criteria, in priority order:
   1. Correctness against the acceptance criteria
   2. Fit with existing repo patterns
   3. Blast radius (files touched, surfaces changed)
   4. Test surface (how testable the result is)
   5. Reversibility

2. Launch **2–3** agents in a single message so they run concurrently, each with
   `isolation: "worktree"` so they cannot stomp each other. Give each a distinct strategy
   (not "do your best" three times) and identical context: issue body, clarifications,
   acceptance criteria, relevant file paths.

3. Each agent must, in its worktree: implement the change, add tests, run the repo's test
   command, then write two files to the shared scratchpad directory:
   - `approach-<key>.patch` — `git diff` of its full change
   - `approach-<key>.md` — strategy, files touched, test results, known trade-offs

4. Judge the returned patches against the rubric as written in step 1. Do not revise the
   rubric after seeing the results.

5. Apply the winner to the real branch deliberately: `git apply` the patch, then read the
   result and adapt it to the branch's actual state. Never merge a scratch worktree in blind.

6. Post **issue comment 3 of 4**: a comparison table of the approaches, the rubric, the
   winner, and *why* — including what the losing approaches did better.

## Phase 6 — Tests

Mirror the repo; never introduce a new test framework or test dependency.

1. Detect the existing convention: `*_test.go` (table-driven), `pytest`, `vitest`/`jest`,
   JUnit, etc. Read a neighboring test file and match its structure and naming.
2. Write tests covering the acceptance criteria, the edge cases surfaced in Phase 3, and
   any regression the issue describes.
3. Run them locally with the repo's own command (`make test`, `go test ./...`, `pytest`, …).
4. Iterate until green. If a test cannot pass, say so plainly with the output — do not
   weaken the test to make it pass.

Commit tests **together with** the implementation via the `commit` skill (Conventional
Commits, with the `issue: #<n>` trailer). Tests are not a separate trailing commit.

## Phase 7 — Local CI mirror

Read `.github/workflows/*.yml` and extract the commands the pipeline actually runs — lint,
vet, build, test, format checks. If a `Makefile` fronts them, prefer its targets
(`make lint`, `make test`). Run each locally and report the results as a checklist.

Everything must pass before Gate 2. If something fails, fix it and re-run. If a step cannot
run locally (needs a secret, a service, a runner-only tool), say which step and why, and
carry it to Gate 2 as a known gap rather than silently skipping it.

## Phase 8 — Gate 2, then push and PR

Present: the diff summary, test results, CI-mirror checklist, and any known gaps.
**Wait for approval to push.**

On approval:

```bash
git push -u origin <branch-name>
gh pr create --base main --head <branch-name> \
  --title "<type>(<scope>): <summary>" --body-file <file>
```

PR body must contain:

- `Closes #<issue-number>` (so merging auto-closes the issue)
- What changed and why, in a short paragraph
- The chosen approach, and the rejected alternatives if Phase 5b ran
- Test coverage added and the local CI-mirror results
- Any known gaps from Phase 7

The PR title follows the same Conventional Commits shape as commit messages (see the `commit`
skill). Never pass `--fill` blindly. Never run `gh pr merge`.

## Phase 9 — Close the loop

Post **issue comment 4 of 4**: the PR link, a one-paragraph summary of what was implemented,
and the test/CI results. Update the state file to `phase: "pr-open"`.

Report to the user: branch name, PR URL, tests added, what still needs human review.

### Escape hatch

If at any phase the work reveals the issue is invalid, a duplicate, or already fixed: stop,
post a comment on the issue explaining what you found with the evidence, delete nothing, and
tell the user. An unnecessary PR is worse than no PR.

---

## Issue log

Exactly four comments across a full run, so the issue reads as a clean log rather than a
chat stream:

1. **Started** — branch name, brief restatement of what will be implemented
2. **Clarifications** — consolidated Q&A plus assumptions taken
3. **Approach** — comparison table and rationale (skipped when Phase 5a ran; instead fold a
   one-line "implemented directly, straightforward change" note into comment 4)
4. **Result** — PR link, summary, test and CI results

Mechanics: write each body to a file in the scratchpad directory, show the user the exact
text, then post with `gh issue comment <n> --body-file <file>`. Record which comments have
been posted in the state file so a resumed run never double-posts.

For any ad-hoc post outside these four moments, use the `write-git-comment` skill.
