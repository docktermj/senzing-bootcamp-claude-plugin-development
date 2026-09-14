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

## Claude development skills

### Create specifications

1. `/feedback-to-specs` - Extract spec/ files from SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md files.

### Development loop

1. `/implement-spec` - Implement specifications in the `spec/` directory.
1. `/review-invariants` - Decide the deferred invariants awaiting sign-off.
1. `/delegate-to-mcp-server` - Determine if there are instructions that are in the MCP server
1. `/compact-dev-environment` - Try to compact the plugin.
1. `/production-readiness-audit` - Do a thorough static review.
1. `/dry-run` - Do a thorough runtime review.
1. `/unattended-spec-loop` - Work the specs/ backlog unattended, alternating implement and audit.

### Publish

1. `/auto-test` - Probe the live MCP server for drift; optionally walk the bootcamp.
1. `/retrofit-from-public` - Bring public-repo edits back into development.
1. `/propagate-to-public` - Mirror the shippable plugin into the public access repo.
