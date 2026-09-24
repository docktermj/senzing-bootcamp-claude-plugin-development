# Senzing Bootcamp Claude Plugin Development

## Setup

Install the development dependencies before running the test suite:

```console
python3 -m pip install -r requirements-dev.txt
```

Run everything:

```console
python3 -m unittest discover -s tests
```

`pytest -q` also works and prints a shorter summary; it is not required.

### Why the install step matters

The only dependency is `fpdf2`, and it is **not** a runtime requirement of the plugin. The
shipped PDF generators tier their renderers — `fpdf2` when importable, a stdlib fallback
otherwise — so a bootcamper without it still gets a PDF, and that fallback path ships and is
tested.

Without `fpdf2` the tests that measure the *fpdf2-rendered* output cannot exercise it. They
skip, and the suite prints one notice up front naming the cause:

```text
fpdf2 is not installed for /usr/bin/python3

The tests that measure the fpdf2-rendered PDF will be SKIPPED. They are not
failing: the stdlib fallback renderer lays out pages differently, so their
assertions do not describe it. The fallback's own tests still run.
```

⚠️ **A green run without `fpdf2` is a weaker signal than a green run with it** — the fpdf2
renderer goes unmeasured. Install it before trusting a run, and always before a release.
Set `SBCP_QUIET_FPDF2_NOTICE=1` to suppress the notice for tooling that parses test output.

CI runs the suite **both ways** on every pull request
(`.github/workflows/test-suite.yaml`, a matrix over `fpdf2: [present, absent]`), so neither
path can rot unnoticed. The `absent` job is the one that catches a new fpdf2-dependent test
landing without a `@requires_fpdf2` guard — an omission that is invisible locally to anyone
who has `fpdf2` installed.

Before this was wired up (#30), those tests did not skip — they ran against the fallback and
failed as 41 assertions about certificate names, grid alignment and label wrapping, only 6 of
which named the missing package anywhere in their traceback. The suite read as 41 product
defects when the only defect was an unstated prerequisite.

## Conventions

### Spelling: US English, not British English

**US English is the preferred spelling throughout this repository** — shipped
plugin prose, specs, invariants, tests, code comments, and identifiers alike.
Prefer `-ize`/`-yze` over `-ise`/`-yse`, `-or` over `-our`, `-er` over `-re`,
`license` over `licence`, and a single `l` before a suffix (`labeled`,
`modeled`, `traveled`).

| British (avoid) | US (use)     | British (avoid) | US (use)     |
| --------------- | ------------ | --------------- | ------------ |
| analysed        | analyzed     | judgement       | judgment     |
| artefact        | artifact     | labelled        | labeled      |
| behaviour       | behavior     | licence         | license      |
| catalogue       | catalog      | millimetre      | millimeter   |
| centre          | center       | normalise       | normalize    |
| colour          | color        | organisation    | organization |
| defence         | defense      | recognise       | recognize    |
| favour          | favor        | sanitise        | sanitize     |
| honoured        | honored      | summarise       | summarize    |

Two deliberate exceptions, both verified rather than assumed:

- `plugins/senzing-bootcamp/scripts/vendor/d3.v7.min.js` — a vendored
  third-party bundle whose `grey` is a CSS color-name key, not prose.
- `D:\Programme` in `tests/test_windows_browser_discovery.py` (and where
  `specs/IMPLEMENTED.md` records it) — a *German* localized `%ProgramFiles%`
  fixture proving environment expansion. It is not English.

`SCOPE_VERBS` in `.claude/skills/compact-dev-environment/widened_scope.py`
deliberately carries both `"generalis"` and `"generaliz"` so the scanner stays
tolerant of either spelling in text it reads.

This is **INV-253**, enforced by `tests/test_us_english_spelling.py`, which scans
the whole tree and matches whole words after splitting identifiers on both `_`
and CamelCase boundaries — so `test_the_..._limit` and `NoStep...Changed` are
caught as readily as prose.

⚠️ **A clean run does not mean the corpus is US English.** The guard's word list
is hardcoded and cannot be otherwise: the corpus is the thing being judged, so
there is nothing to derive the vocabulary from. A clean run means no *listed*
form is present. Two consequences worth knowing before you rely on it:

- `analyses` is deliberately absent, because it is both the British verb and the
  correct US plural of `analysis`. Those seven occurrences were converted by
  hand and would not be caught coming back.
- Stem matching is rejected: `organism`, `mechanism`, `parallelism`,
  `characteristic`, `equally`, `totally`, `radialLine` and
  `LabelLayoutAssertions` are all correct and all contain British-looking stems.

A file that must carry a British form is waived by **path plus the exact word and
count**, never as a whole file, so every other British form in it still fails and
a waiver whose word has gone fails as stale. There is no marker you can add to a
line to silence the guard — that is deliberate, or it becomes the way every
future British spelling gets waved through.

## What downstream ports may rely on

The Kiro and Codex ports (and those that follow) read this repository as their parent. ⛔ **They
must never copy or renumber an `INV-NNN`** — the ids are authoritative here and a child that
renumbers cannot be checked against anything.

What the parent undertakes to provide:

- **`invariant-manifest.json` at the repository root** — every invariant with its `id`,
  `index_group`, `section`, `status`, `statement`, and a `summary` where one could be derived.
  ⛔ **(INV-311)** Generated from `specs/INVARIANTS.md`, which stays the source of truth, and
  checked in CI so it cannot drift (`tests/test_invariant_manifest_matches_the_prose.py`). Regenerate with
  `python3 .claude/skills/review-invariants/invariant_manifest.py`; `--check` exits 1 when stale.
- **A diffable shape.** Sorted keys, one entry per id, so two releases' manifests can be compared
  to see what was added, edited or superseded — which is what a child's dual-evaluation needs.
- ⚠️ **Honest nulls.** `summary` is `null` where no one-line statement could be extracted, and
  ⛔ **that means *not derivable*, never *no rule***. `statement` always carries the full text.
  A child treating null as absence will under-count its register. ⚠️ **No count is stated here
  deliberately** — a figure in prose goes stale silently while reading authoritative; read the
  live number off `invariant-manifest.json`.
- ⛔ **(INV-313) `status` is `active` or `superseded`. There is no third value (#112).** It is decided by
  a bullet — `- **Superseded by:** INV-nnn — <what changed>` — and by **nothing else**: prose
  mentioning supersession is not evidence. The earlier `unclear` value is gone, and so is the
  caveat that went with it.
- ⚠️ **A `Partly superseded by:` bullet leaves the entry `active`.** Six invariants had only a
  *clause* replaced and still bind in full; reporting them `superseded` would tell a child the
  whole rule is obsolete. Read the bullet when one is present.
- **`/review-invariants` keeps it current**: registering an invariant regenerates the manifest.

⚠️ **Not undertaken:** that a `summary` exists for every id, or that `status` is decidable for
every id. Both are properties of the prose, and the manifest reports them rather than repairing
them (#88).

## How the pieces fit together

⛔ **The normative description lives in [`FAMILY_WORKFLOW.md`](FAMILY_WORKFLOW.md), not here.**
That page is the family-wide reference the Kiro, ChatGPT, Copilot and Gemini ports all cite by
rule number, and it carries the repository topology, the four-phase per-change flow, the
maintenance track and the issue-ownership decision. ⚠️ **This page must not restate any of
it** — a rule with two homes is a rule that will disagree with itself (INV-300), and the two
already did: until #111 the topology drawn here said *"one of three"* children while the family
had grown to four.

What stays here is repository-local: the command index below, and the rule governing how this
repository's own maintainer pages name commands.

⛔ **A command named on a maintainer page either ships here or is marked as not shipping.**
A command that ships has a file in `.claude/commands/`. One that does not carries its reason at
the point of use: *(children only)* for `/parity-check` *(children only)* and
`/escalate-to-parent` *(children only)*, or a statement of retirement, as
`/implement-spec` *(retired)* is below. ⚠️ **Three dispositions, not two** — the page legitimately discusses
a command it used to ship, and forcing that into *ships* or *child's* is how a guard starts
reporting a false phantom.
`tests/test_canonical_operations_resolve.py` holds this both ways round — a name that neither
ships nor carries the marker fails the suite, and so does a marker placed on a command that
*does* ship.

⚠️ **INV-302's guard cannot see either page's diagrams.** It parses the numbered ``1. `/name` ``
list shape only, so a phantom command inside a fenced block was invisible to it until this
guard landed (#55), and `FAMILY_WORKFLOW.md` names its operations without a leading slash at
all — deliberately, since the canonical name is the invariant and the invocation mechanism is
the host's business (R4).

## Claude development skills

⛔ **(INV-302) This list and `.claude/commands/` must agree in both directions, and every
skill must be fronted by a command.** A documented command that does not ship tells you to
run something that does not exist; one that ships undocumented is undiscoverable. Every
entry carries a description. Do not state how many there are — the set is derived and
compared, and a count in prose goes stale silently while reading authoritative.

⛔ **(INV-307) `specs/` is frozen as of the 2026-09-15 cutover; new work is tracked as
GitHub issues.** See [`specs/README.md`](../specs/README.md). ✅ **Every command that used to
write there has now been reworked**, and none is blocked: `/feedback-to-issues` files GitHub
issues (#49), `/implement-spec` was retired (#50, #60), `/unattended-issue-loop` is renamed and
label-gated and now forbids writing into the archive outright (#51, #69),
`/production-readiness-audit` files issues when attended and records findings in the ledger when
not (#69), and `/delegate-to-mcp-server` files issues and writes nothing under `specs/` (#114).
⚠️ **Its ledger, `specs/mcp-coverage.jsonl`, is not an exception to the freeze** — the guard
globs `*.md`, so a `.jsonl` file is outside it by construction rather than by exemption.
`IMPLEMENTED.md`, `DECLINED.md`, `INVARIANTS.md` and `README.md` are **not** frozen and are
still written to.

### Triage feedback

1. `/feedback-to-issues` - File GitHub issues from SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md files.

### Development loop

1. `/implement-github-issue` - Take a GitHub issue to pull-request-open on its own branch.
1. `/review-invariants` - Decide the deferred invariants awaiting sign-off.
1. `/delegate-to-mcp-server` - Determine if there are instructions that are in the MCP server
1. `/compact-dev-environment` - Try to compact the plugin.
1. `/production-readiness-audit` - Do a thorough static review.
1. `/dry-run` - Do a thorough runtime review.
1. `/unattended-issue-loop` - Work the `unattended-ok` issues unattended, alternating implement and audit.
1. `/check-skill-drift` - Compare this repo's skills against their user-level twins and report drift.

### Publish

1. `/auto-test` - Probe the live MCP server for drift; optionally walk the bootcamp.
1. `/retrofit-from-public` - Bring public-repo edits back into development.
1. `/release` - Bump the version, write the CHANGELOG entry and create the git tag as one unit.
1. `/propagate-to-public` - Mirror the shippable plugin into the public access repo.
