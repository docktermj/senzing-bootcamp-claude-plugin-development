# Linters

Configuration consumed by the reusable `lint-workflows.yaml` job, which runs
[super-linter]. Super-linter reads each tool's config from this directory when
one is present and falls back to its own bundled defaults otherwise. Both files
here exist because a bundled default is wrong for this repository.

## zizmor.yaml

- `unpinned-uses` is relaxed from the default blanket hash policy to `ref-pin`.
  The org's shared workflows are consumed by tag (`@v4`) on purpose, so a fix to
  `senzing-factory/build-resources` reaches every repo without a pin bump in each
  one. Third-party actions are still SHA-pinned, and
  `tests/test_ci_workflow_guards_the_fpdf2_matrix.py` enforces that in-suite.
- `secrets-outside-env` is disabled, matching the org template.

## .jscpd.json

An empty object, which drops super-linter's bundled `threshold: 0` — a threshold
that fails the build on _any_ duplication at all. This repo ships a skill library
under `.claude/skills/`, and those skills repeat short passages by design: the
same worked example, the same reminder, the same eight-line snippet, restated
where a reader of that one skill will encounter it. Deduplicating across skills
would make each one incomplete on its own.

Set a real `threshold`, or an `ignore` list, if duplication ever needs measuring
here rather than tolerating; see the [jscpd options].

[jscpd options]: https://github.com/kucherenko/jscpd/tree/master/apps/jscpd#options
[super-linter]: https://github.com/super-linter/super-linter
