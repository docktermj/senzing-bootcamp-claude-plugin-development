# Blueprint: docktermj/senzing-bootcamp-claude-plugin-development
<!-- blueprint: sha=542f8135b9e5b07ef49d041543bfdd494df57e6d date=2026-10-04 -->

## 1. Purpose

This repository develops the Senzing Bootcamp plugin for Claude Code (the SBCP).
Installed from its own marketplace, the plugin turns Claude Code into a guide
("the guide") that walks a learner ("the Bootcamper") from a first
entity-resolution demo to a production-shaped Senzing project: business problem,
SDK install, verification, a Truth Set visualization, data collection, quality
assessment and mapping, loading, querying and visualizing results, and a
graduation package with a recap PDF, an optional narrated video and a
certificate.

The product is mostly Markdown: skills under `plugins/senzing-bootcamp/skills/`
that the guide follows step by step, five slash commands, lifecycle hooks, and
an HTTP connection to the Senzing MCP server (<https://mcp.senzing.com/mcp>),
which the skills call for every Senzing fact rather than relying on model
memory. Python scripts bundled with the plugin render the recap PDF and video,
serve the visualizations, capture screenshots, package the project, and
implement the hooks.

The rest of the repository is the development apparatus: a stdlib `unittest`
suite of about 6,100 tests that guards the skill text and the scripts,
maintainer skills under `.claude/skills/` (audits, dry runs, releases, invariant
review, propagation to the public repository), a frozen spec archive and live
ledgers under `specs/` (the invariant register, the implementation ledger,
declined items), and archived Bootcamper feedback. A separate public repository
receives the shippable plugin through `/propagate-to-public`.

## 2. Repository layout

- `.claude-plugin/marketplace.json`: the `senzing-bootcamp-dev` marketplace
  this repository serves; lists the one plugin (section 6.3).
- `.claude/memory/`: project memory notes loaded by Claude Code sessions in this
  repository.
- `.claude/skill-overlays/`: repo overlays: obligations this repository adds to
  user-level skills (implement-github-issue, order-github-issues,
  unattended-issue-loop).
- `.claude/skills/auto-test/`: maintainer skill `/auto-test`: sandboxed MCP
  drift probe, simulated walk and transcript lint, with its baseline snapshot.
- `.claude/skills/compact-dev-environment/`: maintainer skill
  `/compact-dev-environment` and its citation scanner `citations.py`.
- `.claude/skills/delegate-to-mcp-server/`: maintainer skill
  `/delegate-to-mcp-server`, its MCP coverage ledger script and issue template.
- `.claude/skills/dry-run/`: maintainer skill `/dry-run`: its three phase guides
  and helper scripts.
- `.claude/skills/feedback-to-issues/`: maintainer skill `/feedback-to-issues`,
  its feedback ledger script and issue template.
- `.claude/skills/production-readiness-audit/`: maintainer skill
  `/production-readiness-audit` and its `conformance.py`.
- `.claude/skills/propagate-to-public/`: maintainer skill `/propagate-to-public`
  and `propagate.sh`.
- `.claude/skills/release/`: maintainer skill `/release` and `release.py`.
- `.claude/skills/retrofit-from-public/`: maintainer skill
  `/retrofit-from-public` and `retrofit.sh`.
- `.claude/skills/review-invariants/`: maintainer skill `/review-invariants`,
  `pending_invariants.py` and `invariant_manifest.py`.
- `.github/linters/`: configuration for the linters the reusable lint-workflows
  workflow runs.
- `.github/workflows/lint-workflows.yaml`: CI: lints GitHub workflow files on
  pull requests (section 4.1).
- `.github/workflows/test-suite.yaml`: CI: runs the unittest suite with fpdf2
  present and absent (section 4.2).
- `.gitignore`: ignores bytecode, the pytest cache and the transient root
  feedback file.
- `.sync-state.json`: records the Kiro Power commit the plugin was first
  scaffolded from.
- `CHANGELOG.md`: release notes, one entry per version, written by `/release`
  (section 9).
- `MIGRATION.md`: migration notes from the Kiro Power predecessor to this Claude
  Code plugin.
- `README.md`: repository README for maintainers.
- `docs/.nojekyll`: empty marker that makes GitHub Pages serve `docs/` as-is,
  without Jekyll (section 5.56).
- `docs/FAMILY_WORKFLOW.md`: the operations shared across the plugin family and
  which skill owns each.
- `docs/README.md`: user-facing install, update and uninstall guide (mirrored to
  the public repository).
- `docs/development.md`: developer guide: layout, tests, release,
  propagation and installing the development plugin.
- `docs/images/apple-touch-icon.png`: Pages site touch icon (section 9).
- `docs/images/favicon-32.png`: Pages site favicon (section 9).
- `docs/images/senzing-logo.png`: Pages site logo (section 9).
- `docs/index.css`: stylesheet of the GitHub Pages quick-start site.
- `docs/index.html`: the GitHub Pages quick-start site (section 5.56).
- `feedback/`: archived Bootcamper feedback reports and the processed-feedback
  log.
- `invariant-manifest.json`: generated machine-readable copy of the invariant
  register (section 9).
- `plugins/senzing-bootcamp/.claude-plugin/plugin.json`: the plugin manifest:
  name, version, license (section 3).
- `plugins/senzing-bootcamp/.mcp.json`: connects the plugin to the Senzing MCP
  server over HTTP (section 6.3).
- `plugins/senzing-bootcamp/commands/`: the plugin's five slash commands
  (section 5).
- `plugins/senzing-bootcamp/docs/examples/`: example recap and visualization
  screenshots shown to Bootcampers (section 9).
- `plugins/senzing-bootcamp/docs/model-selection.md`: per-stage model and effort
  recommendations the skills surface.
- `plugins/senzing-bootcamp/hooks/README.md`: documents each hook and the script
  it runs.
- `plugins/senzing-bootcamp/hooks/hooks.json`: registers the plugin's lifecycle
  hooks (section 6.3).
- `plugins/senzing-bootcamp/scripts/brand_tokens.py`: shared Senzing brand
  palette and font constants for the renderers.
- `plugins/senzing-bootcamp/scripts/capture_screenshots.py`:
  captures each tab of a running visualization app as PNGs.
- `plugins/senzing-bootcamp/scripts/checkpoint-tick.py`: UserPromptSubmit hook:
  counts turns toward the next recap checkpoint.
- `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`: names, inspects and
  tears down the Bootcamper's containers, and picks a free host port.
- `plugins/senzing-bootcamp/scripts/feedback-capture.py`: UserPromptSubmit hook:
  captures feedback typed in the prompt.
- `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`:
  renders the Module 7 discoveries PDF.
- `plugins/senzing-bootcamp/scripts/generate_document_pdf.py`:
  renders a project Markdown document to PDF.
- `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`: renders and checks
  the graduation recap PDF (fpdf2 or stdlib fallback).
- `plugins/senzing-bootcamp/scripts/generate_recap_video.py`:
  renders the optional narrated graduation video from a storyboard.
- `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`:
  normalizes the Bootcamper's generated Markdown documents.
- `plugins/senzing-bootcamp/scripts/package_bootcamp.py`: packages the finished
  project into a portable archive with OPEN_ME_FIRST.md.
- `plugins/senzing-bootcamp/scripts/precompact-recap.py`: PreCompact hook:
  preserves recap state before context compaction.
- `plugins/senzing-bootcamp/scripts/recap_checkpoint.py`: shared logic for recap
  checkpoints used by the hooks.
- `plugins/senzing-bootcamp/scripts/secret_patterns.py`: shared secret-detection
  patterns used by the write gate and packager.
- `plugins/senzing-bootcamp/scripts/senzing_logo_light.png`:
  Senzing logo used in rendered documents (section 9).
- `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`: local HTTP server
  for the Truth Set and results visualizations.
- `plugins/senzing-bootcamp/scripts/session-end.py`: SessionEnd hook.
- `plugins/senzing-bootcamp/scripts/session-start.py`: SessionStart hook:
  resumes or starts the bootcamp context.
- `plugins/senzing-bootcamp/scripts/stop-nudge.py`: Stop hook: nudges the guide
  when a turn ends without its pinned question.
- `plugins/senzing-bootcamp/scripts/vendor/`: vendored D3 v7.9.0 used offline by
  the visualizations (section 9).
- `plugins/senzing-bootcamp/scripts/write-gate.py`: PreToolUse Write/Edit hook:
  blocks secrets and files outside allowed locations.
- `plugins/senzing-bootcamp/skills/bootcamp-onboarding/`: the
  `bootcamp-onboarding` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/bootcamp-preparation/`: the
  `bootcamp-preparation` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/graduation/`: the `graduation` skill and its
  phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-00-entity-resolution-concepts/`:
  the `module-00-entity-resolution-concepts` skill and its phase files (section
  5).
- `plugins/senzing-bootcamp/skills/module-01-business-problem/`:
  the `module-01-business-problem` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-02-sdk-setup/`: the
  `module-02-sdk-setup` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-03-system-verification/`:
  the `module-03-system-verification` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/`:
  the `module-03b-truthset-visualization` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-04-data-collection/`:
  the `module-04-data-collection` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/`:
  the `module-05-data-quality-mapping` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-06-data-processing/`:
  the `module-06-data-processing` skill and its phase files (section 5).
- `plugins/senzing-bootcamp/skills/module-07-query-visualize-discover/`:
  the `module-07-query-visualize-discover` skill and its phase files (section
  5).
- `requirements-dev.txt`: development-only dependencies for running the full
  test suite (section 3).
- `resources/2026-sz-light.png`: Senzing brand artwork (section 9).
- `resources/certificate-of-completion.pdf`: certificate template referenced by
  graduation (section 9).
- `resources/senzing-style-reference.pdf`: Senzing brand style reference
  (section 9).
- `scripts/sync-check.sh`: maintainer check of the sync state against the Kiro
  Power source.
- `specs/DECLINED.md`: live record: items the maintainer declined, with reason
  and revisit condition.
- `specs/FROZEN-MANIFEST.txt`: pins the frozen spec set by name (INV-307).
- `specs/IMPLEMENTED.md`: live ledger: one dated entry per implemented spec or
  issue, newest first (section 9).
- `specs/INVARIANTS.md`: live, append-only invariant register with its subject
  index (section 9).
- `specs/PreToolUseWriteError.md`: frozen spec (INV-307).
- `specs/README.md`: explains the frozen archive and which records stay live.
- `specs/a-check-that-matches-nothing-must-not-report-agreement.md`:
  frozen spec (INV-307).
- `specs/a-check-whose-scope-is-wider-than-its-claim-passes-without-establishing-it.md`:
  frozen spec (INV-307).
- `specs/a-composite-flag-is-a-set-in-java-and-cannot-be-listed-among-enum-constants.md`:
  frozen spec (INV-307).
- `specs/a-guard-must-not-pin-the-wording-of-a-claim-about-an-mcp-tool.md`:
  frozen spec (INV-307).
- `specs/a-malformed-ledger-entry-is-invisible-to-every-guard.md`:
  frozen spec (INV-307).
- `specs/a-non-utf8-recap-crashes-three-hooks-and-the-obvious-fix-destroys-it.md`:
  frozen spec (INV-307).
- `specs/a-project-local-visualization-server-has-no-vendored-d3-beside-it.md`:
  frozen spec (INV-307).
- `specs/a-question-with-no-origin-in-a-skill-file-reached-the-bootcamper.md`:
  frozen spec (INV-307).
- `specs/a-renderer-warning-exemption-must-be-scoped-to-a-passage.md`:
  frozen spec (INV-307).
- `specs/a-shared-feature-group-is-read-as-a-shared-attribute-when-predicting-joins.md`:
  frozen spec (INV-307).
- `specs/a-spec-asserting-server-absence-must-name-the-owning-route.md`:
  frozen spec (INV-307).
- `specs/a-step-names-what-to-select-without-naming-the-route.md`:
  frozen spec (INV-307).
- `specs/a-stray-fence-marker-silently-deletes-finalized-recap-modules.md`:
  frozen spec (INV-307).
- `specs/a-syntax-error-on-a-just-written-file-across-a-bind-mount-must-be-retried-before-it-is-believed.md`:
  frozen spec (INV-307).
- `specs/a-targeted-re-capture-truncates-the-tab-manifest.md`:
  frozen spec (INV-307).
- `specs/advanced-modules-8-11-scope.md`: frozen spec (INV-307).
- `specs/agent-rule-citations-are-positional-and-cross-a-module-boundary.md`:
  frozen spec (INV-307).
- `specs/align-invariants-cord-and-optin.md`: frozen spec (INV-307).
- `specs/always-pass-language-to-reporting-guide.md`: frozen spec (INV-307).
- `specs/always-produce-data-discoveries-document.md`: frozen spec (INV-307).
- `specs/an-unsourced-inference-about-the-bootcamper-steered-a-consent-gate.md`:
  frozen spec (INV-307).
- `specs/analyzer-legacy-sublist-format-false-errors.md`: frozen spec (INV-307).
- `specs/anti-rationalization-clause-lives-in-four-modules-and-no-contract.md`:
  frozen spec (INV-307).
- `specs/any-language-contract-guard-checks-a-hardcoded-requirement-set.md`:
  frozen spec (INV-307).
- `specs/applicability-and-attribute-catalog-are-authored-by-hand-and-fail-silently.md`:
  frozen spec (INV-307).
- `specs/apply-senzing-style-guide-to-deliverables.md`: frozen spec (INV-307).
- `specs/artifact-level-verification-for-deliverables.md`: frozen spec
  (INV-307).
- `specs/audit-polish-cleanup.md`: frozen spec (INV-307).
- `specs/audit3-minor-fixes.md`: frozen spec (INV-307).
- `specs/auto-detect-platform.md`: frozen spec (INV-307).
- `specs/auto-initialize-git-without-prompt.md`: frozen spec (INV-307).
- `specs/bootcamp-notes-capture-and-recap-section.md`: frozen spec (INV-307).
- `specs/bootcamp-prep-name-never-asked.md`: frozen spec (INV-307).
- `specs/bootcamp-preparation-end-of-module-recap.md`: frozen spec (INV-307).
- `specs/bundled-file-reads-resolve-like-bundled-script-runs.md`:
  frozen spec (INV-307).
- `specs/business-problem-keeps-only-the-refined-wording-so-the-gate-cannot-catch-drift.md`:
  frozen spec (INV-307).
- `specs/bytecode-caching-hides-a-latent-syntax-error-from-the-suite.md`:
  frozen spec (INV-307).
- `specs/capture-entity-resolution-concepts-in-recap.md`: frozen spec (INV-307).
- `specs/capture-reversed-decisions-during-the-run.md`: frozen spec (INV-307).
- `specs/capture-screenshots-aborts-where-inv-122-says-skip.md`:
  frozen spec (INV-307).
- `specs/capture-screenshots-cannot-tell-whether-the-tab-actually-changed.md`:
  frozen spec (INV-307).
- `specs/capture-screenshots-captures-tabs-the-app-suppressed.md`:
  frozen spec (INV-307).
- `specs/capture-steps-pass-the-flags-without-naming-the-capture-script.md`:
  frozen spec (INV-307).
- `specs/capture-visualization-screenshots-for-recap.md`: frozen spec (INV-307).
- `specs/census-detector-misses-enumerated-name-lists.md`: frozen spec
  (INV-307).
- `specs/certificate-name-fallback-at-graduation.md`: frozen spec (INV-307).
- `specs/certificate-name-must-reach-the-generator.md`: frozen spec (INV-307).
- `specs/certificate-of-completion-from-template.md`: frozen spec (INV-307).
- `specs/completeness-denominator-has-two-readings-on-a-raw-source.md`:
  frozen spec (INV-307).
- `specs/concepts-module-verified-qa-and-quiz.md`: frozen spec (INV-307).
- `specs/concepts-questions-before-quiz.md`: frozen spec (INV-307).
- `specs/confirm-json-data-and-network-link-response-paths.md`:
  frozen spec (INV-307).
- `specs/confirmations-has-a-third-state-present-and-empty-and-the-teaching-step-has-no-branch-for-it.md`:
  frozen spec (INV-307).
- `specs/conformance-rules-cannot-see-a-new-rule-beside-an-old-citation.md`:
  frozen spec (INV-307).
- `specs/consolidate-merge-statistics-and-results-dashboard-tabs.md`:
  frozen spec (INV-307).
- `specs/consolidate-module7-visualizations-as-truthset-app-tabs.md`:
  frozen spec (INV-307).
- `specs/consolidate-recap-per-module-summary.md`: frozen spec (INV-307).
- `specs/consolidate-results-dashboard-offer-in-module7.md`:
  frozen spec (INV-307).
- `specs/consolidate-truthset-viz-merges-and-network-tabs.md`:
  frozen spec (INV-307).
- `specs/container-lifecycle-hooks-assume-docker.md`: frozen spec (INV-307).
- `specs/cord-download-rate-limit-is-saved-as-data.md`: frozen spec (INV-307).
- `specs/cord-fastpath-load-readiness.md`: frozen spec (INV-307).
- `specs/cord-is-described-as-real-world-like-but-the-server-says-it-is-real.md`:
  frozen spec (INV-307).
- `specs/cord-source-download-url-403s-the-python-stdlib-client.md`:
  frozen spec (INV-307).
- `specs/core-path-enumerates-every-module.md`: frozen spec (INV-307).
- `specs/count-mismatch-rule-files-a-mapping-explained-delta-as-a-failed-load.md`:
  frozen spec (INV-307).
- `specs/counting-the-writers-of-license-record-limit-is-the-wrong-invariant.md`:
  frozen spec (INV-307).
- `specs/coverage-reports-count-known-non-defects-as-hits.md`:
  frozen spec (INV-307).
- `specs/cross-platform-hook-execution.md`: frozen spec (INV-307).
- `specs/cross-source-visualization-offer-module6-vs-module7.md`:
  frozen spec (INV-307).
- `specs/customizable-module-selection.md`: frozen spec (INV-307).
- `specs/data-collection-does-not-recognize-a-synthesized-scenario.md`:
  frozen spec (INV-307).
- `specs/data-collection-generated-path-is-non-yielding-and-unmarked.md`:
  frozen spec (INV-307).
- `specs/data-collection-records-mapping-claims-before-the-entity-specification-is-read.md`:
  frozen spec (INV-307).
- `specs/datastore-goes-in-the-project-directory-which-on-wsl2-is-the-slow-one.md`:
  frozen spec (INV-307).
- `specs/declined-ledger-negatives-are-invisible-to-the-scanner.md`:
  frozen spec (INV-307).
- `specs/declined-revisit-note-asserts-an-absence-from-two-surfaces.md`:
  frozen spec (INV-307).
- `specs/deep-dive-audit-2026-07-29-minor-fixes.md`: frozen spec (INV-307).
- `specs/default-tab-capture-without-injection.md`: frozen spec (INV-307).
- `specs/defer-commonmark-to-graduation.md`: frozen spec (INV-307).
- `specs/desired-outcome-question-is-single-select-for-a-multi-valued-answer.md`:
  frozen spec (INV-307).
- `specs/detect-dynamic-key-document-shaped-sources.md`: frozen spec (INV-307).
- `specs/discoveries-pdf-offpage-blocks-and-list-spacing.md`:
  frozen spec (INV-307).
- `specs/discoveries-pdf-real-tables-and-paragraph-spacing.md`:
  frozen spec (INV-307).
- `specs/doc-consistency-audit.md`: frozen spec (INV-307).
- `specs/docker-container-lifecycle-teardown-and-resume.md`:
  frozen spec (INV-307).
- `specs/download-resource-returns-a-url-not-the-specification.md`:
  frozen spec (INV-307).
- `specs/drop-checklist-and-summary-gates.md`: frozen spec (INV-307).
- `specs/drop-deliverable-generation-gates.md`: frozen spec (INV-307).
- `specs/drop-trophy-wording.md`: frozen spec (INV-307).
- `specs/dry-run-phase2-says-six-hooks-when-seven-scripts-must-run.md`:
  frozen spec (INV-307).
- `specs/dry-run-phase3-interaction-prose-defects.md`: frozen spec (INV-307).
- `specs/dry-run-scaffold-uses-a-verification-filename-the-plugin-never-writes.md`:
  frozen spec (INV-307).
- `specs/effort-above-every-recommendation-triggers-a-step-down-question-every-module.md`:
  frozen spec (INV-307).
- `specs/effort-only-switch-question-says-keep-your-current-model.md`:
  frozen spec (INV-307).
- `specs/embed-every-captured-tab-in-tab-order.md`: frozen spec (INV-307).
- `specs/embedded-image-count-needs-an-external-denominator.md`:
  frozen spec (INV-307).
- `specs/embedded-master-check-belongs-at-plan-time-not-only-as-a-back-recovery.md`:
  frozen spec (INV-307).
- `specs/embedded-master-legacy-payload-example-is-not-runnable.md`:
  frozen spec (INV-307).
- `specs/embedded-of-referenced-count-needs-external-denominator-crossref.md`:
  frozen spec (INV-307).
- `specs/empty-progress-file-makes-resume-unsatisfiable.md`:
  frozen spec (INV-307).
- `specs/encourage-own-business-case.md`: frozen spec (INV-307).
- `specs/end-of-bootcamp-banner.md`: frozen spec (INV-307).
- `specs/end-of-module-summary-blocks-guaranteed.md`: frozen spec (INV-307).
- `specs/enforce-screenshot-embed-and-backfill.md`: frozen spec (INV-307).
- `specs/engine-config-returned-by-sdk-guide-is-not-valid-json.md`:
  frozen spec (INV-307).
- `specs/enrich-feedback-context.md`: frozen spec (INV-307).
- `specs/entity-graph-legend-labels-participation-counts-as-single-source.md`:
  frozen spec (INV-307).
- `specs/entity-graph-node-occludes-a-neighbors-label-at-small-n.md`:
  frozen spec (INV-307).
- `specs/entity-resolution-module-zero.md`: frozen spec (INV-307).
- `specs/env-script-must-be-shell-portable.md`: frozen spec (INV-307).
- `specs/env-script-template-names-every-export-but-pythonpath.md`:
  frozen spec (INV-307).
- `specs/escape-viz-snapshot-script-payload.md`: frozen spec (INV-307).
- `specs/every-module5-gate-checks-shape-and-none-checks-what-a-value-IS.md`:
  frozen spec (INV-307).
- `specs/example-recap-reference.md`: frozen spec (INV-307).
- `specs/explain-error-code-now-owns-senz7426.md`: frozen spec (INV-307).
- `specs/export-flags-are-not-documented-against-the-export-method.md`:
  frozen spec (INV-307).
- `specs/export-related-entities-is-flag-conditional.md`: frozen spec (INV-307).
- `specs/factory-must-outlive-every-engine-it-creates.md`: frozen spec
  (INV-307).
- `specs/feedback-capture-misses-natural-phrasings.md`: frozen spec (INV-307).
- `specs/feedback-file-durability.md`: frozen spec (INV-307).
- `specs/feedback-flow-boundary-banner.md`: frozen spec (INV-307).
- `specs/feedback-routing-has-no-verdict-for-a-defect-neither-component-owns.md`:
  frozen spec (INV-307).
- `specs/feedback-step-2-mishandles-a-partial-feedback-report.md`:
  frozen spec (INV-307).
- `specs/feedback-trigger-is-never-taught-to-the-bootcamper.md`:
  frozen spec (INV-307).
- `specs/fifth-response-schemas-stops-short-site-survives.md`:
  frozen spec (INV-307).
- `specs/final-review-doc-coherence.md`: frozen spec (INV-307).
- `specs/find-examples-coverage-disagreement-was-fixed-upstream.md`:
  frozen spec (INV-307).
- `specs/find-examples-elision-is-by-design-not-a-failed-retrieval.md`:
  frozen spec (INV-307).
- `specs/find-examples-file-retrieval-returns-empty-content.md`:
  frozen spec (INV-307).
- `specs/find-examples-self-describes-two-different-coverages.md`:
  frozen spec (INV-307).
- `specs/find-path-and-find-network-links-diverge.md`: frozen spec (INV-307).
- `specs/fix-truthset-snapshot-empty.md`: frozen spec (INV-307).
- `specs/flag-gated-fields-are-unannotated-in-both-reference-topics.md`:
  frozen spec (INV-307).
- `specs/generalized-invariants-leave-no-pointer-on-the-narrower-rule.md`:
  frozen spec (INV-307).
- `specs/generate-diagrams-for-generated-scenarios.md`: frozen spec (INV-307).
- `specs/generated-dataset-is-sized-before-anything-measures-the-license.md`:
  frozen spec (INV-307).
- `specs/generated-scenario-marker-is-dropped-from-the-keepsake-pdf.md`:
  frozen spec (INV-307).
- `specs/generators-warn-on-dropped-unencodable-characters.md`:
  frozen spec (INV-307).
- `specs/generic-concept-label-collides-with-the-mcp-first-checklist.md`:
  frozen spec (INV-307).
- `specs/globalization-retrieval-names-a-query-that-returns-homonyms.md`:
  frozen spec (INV-307).
- `specs/graduation-assistant-retrospective-feedback.md`: frozen spec (INV-307).
- `specs/graduation-full-module-preface.md`: frozen spec (INV-307).
- `specs/graduation-prechecks-read-the-keys-that-are-written.md`:
  frozen spec (INV-307).
- `specs/graduation-reads-integration-and-deployment-answers.md`:
  frozen spec (INV-307).
- `specs/graduation-revisit-resume-bundle.md`: frozen spec (INV-307).
- `specs/graduation-upstream-offer-collides-with-the-dry-run-no-send-rule.md`:
  frozen spec (INV-307).
- `specs/graph-capture-budget-does-not-converge-at-truth-set-density.md`:
  frozen spec (INV-307).
- `specs/graph-nodes-are-colored-by-their-first-data-source.md`:
  frozen spec (INV-307).
- `specs/ground-rules-names-a-reporting-guide-field-the-server-no-longer-returns.md`:
  frozen spec (INV-307).
- `specs/guarantee-quiz-offer-is-presented.md`: frozen spec (INV-307).
- `specs/guards-enforce-class-scoped-rules-from-hardcoded-site-sets.md`:
  frozen spec (INV-307).
- `specs/guards-pinning-a-dated-negative-outlive-it.md`: frozen spec (INV-307).
- `specs/harden-write-gate.md`: frozen spec (INV-307).
- `specs/hook-to-message-convention.md`: frozen spec (INV-307).
- `specs/host-control-handling-clause-can-be-read-as-two-questions-in-one-turn.md`:
  frozen spec (INV-307).
- `specs/host-rendered-control-prompt-interrupts-a-pending-question.md`:
  frozen spec (INV-307).
- `specs/how-analysis-step-does-not-name-the-confusable-virtual-entity-keys.md`:
  frozen spec (INV-307).
- `specs/how-heard-is-fixed-by-context-and-should-not-cost-a-turn.md`:
  frozen spec (INV-307).
- `specs/how-side-flag-instruction-contradicts-its-own-confirmations-observation.md`:
  frozen spec (INV-307).
- `specs/icij-free-data-samples-do-not-join.md`: frozen spec (INV-307).
- `specs/inert-screenshot-omission-conflicts-with-embed-every-tab.md`:
  frozen spec (INV-307).
- `specs/install-verification-has-no-invariant-so-inv129-is-borrowed.md`:
  frozen spec (INV-307).
- `specs/interaction-or-questions.md`: frozen spec (INV-307).
- `specs/internal-connection-string-breaks-the-viz-server.md`:
  frozen spec (INV-307).
- `specs/inv-124-is-cited-as-the-any-language-rule-it-is-not.md`:
  frozen spec (INV-307).
- `specs/inv-179-is-cited-as-a-state-it-once-rule-it-does-not-contain.md`:
  frozen spec (INV-307).
- `specs/inv-244-still-carries-the-writer-count-its-own-guard-rejects.md`:
  frozen spec (INV-307).
- `specs/inv-300-is-drafted-from-the-pointer-side-and-cited-at-owner-side-declarations.md`:
  frozen spec (INV-307).
- `specs/inv-300s-notes-put-three-file-line-refs-in-an-append-only-file.md`:
  frozen spec (INV-307).
- `specs/inv017-root-readme-exception-missing.md`: frozen spec (INV-307).
- `specs/inv050-layout-tree-names-three-artifacts-nothing-produces.md`:
  frozen spec (INV-307).
- `specs/inv050-tree-has-no-reachability-guard.md`: frozen spec (INV-307).
- `specs/inv077-supersession-dropped-the-visualization-verification-guarantee.md`:
  frozen spec (INV-307).
- `specs/inv121-cursor-discipline-is-guarded-in-one-generator.md`:
  frozen spec (INV-307).
- `specs/inv174-per-record-applicability-is-unverified.md`: frozen spec
  (INV-307).
- `specs/inv200-overstates-what-the-write-gate-blocks.md`: frozen spec
  (INV-307).
- `specs/inv205-covers-whether-to-ask-but-not-how.md`: frozen spec (INV-307).
- `specs/inv243-reconciliation-binds-more-sites-than-it-reaches.md`:
  frozen spec (INV-307).
- `specs/inv244-absent-license-branch-exists-in-module-4-too.md`:
  frozen spec (INV-307).
- `specs/inv247-guard-is-narrower-than-the-invariant-it-enforces.md`:
  frozen spec (INV-307).
- `specs/inv251-relabel-missed-six-sites-its-own-guard-cannot-see.md`:
  frozen spec (INV-307).
- `specs/invariants-index-flattens-partial-supersession.md`:
  frozen spec (INV-307).
- `specs/java-classpath-guidance-is-macos-sourced-and-unusable-on-linux.md`:
  frozen spec (INV-307).
- `specs/java-filenames-force-a-class-naming-choice-the-plugin-never-names.md`:
  frozen spec (INV-307).
- `specs/java-initialize-scaffold-snippet-references-the-wrong-class.md`:
  frozen spec (INV-307).
- `specs/java-scaffold-json-dependency-gap.md`: frozen spec (INV-307).
- `specs/landscape-certificate-of-completion.md`: frozen spec (INV-307).
- `specs/language-agnostic-scope-excludes-plugin-apparatus.md`:
  frozen spec (INV-307).
- `specs/language-gate-does-not-say-where-its-options-render.md`:
  frozen spec (INV-307).
- `specs/language-gate-names-the-container-not-its-cost-and-omits-wsl2.md`:
  frozen spec (INV-307).
- `specs/layout-tree-reconciliation.md`: frozen spec (INV-307).
- `specs/ld-library-path-relayed-as-conditional-on-a-stock-linux-apt-install.md`:
  frozen spec (INV-307).
- `specs/license-cap-branch-offers-no-way-to-apply-the-license-that-may-have-arrived.md`:
  frozen spec (INV-307).
- `specs/license-limit-assumed-when-it-could-be-measured.md`:
  frozen spec (INV-307).
- `specs/license-record-limit-has-a-detected-only-contract-nothing-enforces.md`:
  frozen spec (INV-307).
- `specs/license-request-omits-a-required-field-the-server-demands.md`:
  frozen spec (INV-307).
- `specs/license-request-option.md`: frozen spec (INV-307).
- `specs/load-time-warning-ignores-the-license-cap-decided-one-step-earlier.md`:
  frozen spec (INV-307).
- `specs/lookup-sdk-response-schemas-before-parsing.md`: frozen spec (INV-307).
- `specs/macos-jvm-launch-environment-guidance.md`: frozen spec (INV-307).
- `specs/macos-protected-launchers-strip-dyld-from-a-backgrounded-server.md`:
  frozen spec (INV-307).
- `specs/mapping-step3-rejects-disjoint-name-declarations.md`:
  frozen spec (INV-307).
- `specs/mapping-workflow-step1-prose-contradicts-its-own-advance-schema.md`:
  frozen spec (INV-307).
- `specs/mapping-workflow-step1-script-defects.md`: frozen spec (INV-307).
- `specs/mapping-workflow-tells-the-guide-not-to-ask-and-the-plugin-never-reconciles-it.md`:
  frozen spec (INV-307).
- `specs/mapping-workflow-terminates-after-five-grammar-violations.md`:
  frozen spec (INV-307).
- `specs/mapping-workflow-truncated-validation-errors.md`: frozen spec
  (INV-307).
- `specs/match-key-audit-cannot-read-related-entities-from-export.md`:
  frozen spec (INV-307).
- `specs/match-key-audit-pools-per-record-and-relationship-suppressors.md`:
  frozen spec (INV-307).
- `specs/match-key-details-does-list-the-export-methods.md`:
  frozen spec (INV-307).
- `specs/mcp-coverage.jsonl`: log of MCP coverage checks used by
  delegate-to-mcp-server (section 9).
- `specs/mcp-freshness-contract-says-this-turn-and-this-session.md`:
  frozen spec (INV-307).
- `specs/mcp-grounding-in-every-skill.md`: frozen spec (INV-307).
- `specs/mcp-negative-markers-carry-rationale-nothing-reverifies.md`:
  frozen spec (INV-307).
- `specs/mcp-negative-markers-must-name-the-owning-route.md`:
  frozen spec (INV-307).
- `specs/mcp-tools-disagree-on-eval-license-duration.md`: frozen spec (INV-307).
- `specs/merge-histogram-y-axis-shows-fractional-entity-counts.md`:
  frozen spec (INV-307).
- `specs/method-default-flags-omit-record-data.md`: frozen spec (INV-307).
- `specs/migrate-kiro-power.md`: frozen spec (INV-307).
- `specs/minimal-verbosity-scope-against-structured-output.md`:
  frozen spec (INV-307).
- `specs/mirror-comment-names-the-wrong-guarding-test.md`: frozen spec
  (INV-307).
- `specs/model-effort-change-prompt.md`: frozen spec (INV-307).
- `specs/model-effort-guidance-advisory-not-gate.md`: frozen spec (INV-307).
- `specs/model-effort-switch-done-confirmation.md`: frozen spec (INV-307).
- `specs/model-effort-table-name-based.md`: frozen spec (INV-307).
- `specs/model-selection-per-skill-table-omits-bootcamp-preparation.md`:
  frozen spec (INV-307).
- `specs/model-switch-single-turn-continuation.md`: frozen spec (INV-307).
- `specs/module-0-suggested-query-for-ambiguous-matches-misses-its-topic.md`:
  frozen spec (INV-307).
- `specs/module-03b-hardcodes-the-port-its-own-text-says-may-differ.md`:
  frozen spec (INV-307).
- `specs/module-05-shared-workspace-transient-filename-collision.md`:
  frozen spec (INV-307).
- `specs/module-05-step16-high-quality-branch-missing-pinned-question.md`:
  frozen spec (INV-307).
- `specs/module-3b-skill-states-the-per-record-build-with-no-scope.md`:
  frozen spec (INV-307).
- `specs/module-completion-reads-every-capture-failure-as-exit-2.md`:
  frozen spec (INV-307).
- `specs/module-preface-time-estimate.md`: frozen spec (INV-307).
- `specs/module-references-by-name-not-number.md`: frozen spec (INV-307).
- `specs/module-start-model-nudge.md`: frozen spec (INV-307).
- `specs/module-step-overview.md`: frozen spec (INV-307).
- `specs/module-visualization-mapping-can-drift-from-the-token-registry.md`:
  frozen spec (INV-307).
- `specs/module02-dated-negatives-about-sdk-guide-carry-no-marker.md`:
  frozen spec (INV-307).
- `specs/module02-postgres-credentials-hardening.md`: frozen spec (INV-307).
- `specs/module1-license-flow-parity.md`: frozen spec (INV-307).
- `specs/module1-threshold-check-says-the-mcp-server-where-module2-names-the-route.md`:
  frozen spec (INV-307).
- `specs/module2-license-clarity.md`: frozen spec (INV-307).
- `specs/module2-transition-staleness.md`: frozen spec (INV-307).
- `specs/module3-connectivity-probe-still-uses-the-deprecated-search-docs-call.md`:
  frozen spec (INV-307).
- `specs/module3-register-truthset-data-sources.md`: frozen spec (INV-307).
- `specs/module3-synthetic-verification-data.md`: frozen spec (INV-307).
- `specs/module4-example-gap-rates-cannot-reach-the-band-they-illustrate.md`:
  frozen spec (INV-307).
- `specs/module5-cannot-honor-an-embedded-entity-discovered-at-step-3.md`:
  frozen spec (INV-307).
- `specs/module5-ending-and-transition.md`: frozen spec (INV-307).
- `specs/module5-fastpath-cord-only-vs-senzing-ready.md`: frozen spec (INV-307).
- `specs/module5-quality-gate-demands-a-question-its-best-branch-lacks.md`:
  frozen spec (INV-307).
- `specs/module5-quality-pages-are-branded-visual-deliverables.md`:
  frozen spec (INV-307).
- `specs/module5-quality-score-has-bands-but-no-formula.md`:
  frozen spec (INV-307).
- `specs/module5-step2-asks-for-data-module4-already-collected.md`:
  frozen spec (INV-307).
- `specs/module6-register-data-sources-before-load.md`: frozen spec (INV-307).
- `specs/module6-validation-routing-not-reports-sql.md`: frozen spec (INV-307).
- `specs/name-the-claude-interface.md`: frozen spec (INV-307).
- `specs/network-link-fields-and-uncovered-response-schemas.md`:
  frozen spec (INV-307).
- `specs/never-modify-global-shell-config-is-unregistered.md`:
  frozen spec (INV-307).
- `specs/newly-minted-invariants-carry-no-shipped-citation.md`:
  frozen spec (INV-307).
- `specs/no-license-path-environment-variable.md`: frozen spec (INV-307).
- `specs/no-report-for-invariants-the-shipped-plugin-never-cites.md`:
  frozen spec (INV-307).
- `specs/no-route-for-bootcampers-who-cannot-add-an-mcp-server.md`:
  frozen spec (INV-307).
- `specs/non-yielding-pointers-name-no-governing-invariant.md`:
  frozen spec (INV-307).
- `specs/normalize-production-markdown-at-graduation.md`: frozen spec (INV-307).
- `specs/nothing-owns-creating-the-recap-header.md`: frozen spec (INV-307).
- `specs/nothing-writes-the-recap-checkpoint.md`: frozen spec (INV-307).
- `specs/offer-generate-data-in-data-collection-menu.md`: frozen spec (INV-307).
- `specs/offer-to-update-an-existing-senzing-install.md`: frozen spec (INV-307).
- `specs/omit-empty-recap-takeaway.md`: frozen spec (INV-307).
- `specs/onboarding-explore-gate-wording.md`: frozen spec (INV-307).
- `specs/onboarding-preface-copy-trim.md`: frozen spec (INV-307).
- `specs/orchestrator-per-source-stats-vs-static-scaffold-counters.md`:
  frozen spec (INV-307).
- `specs/organization-search-requires-name-org.md`: frozen spec (INV-307).
- `specs/overlap-preserving-sampling-at-the-license-gate.md`:
  frozen spec (INV-307).
- `specs/overview-bullet-count-is-stale-after-the-note-bullet.md`:
  frozen spec (INV-307).
- `specs/packaging-claims-natural-language-triggers-nothing-routes.md`:
  frozen spec (INV-307).
- `specs/paths-and-links-in-one-network-response-use-different-endpoint-keys.md`:
  frozen spec (INV-307).
- `specs/pattern-gallery-asks-for-more-than-mcp-can-supply.md`:
  frozen spec (INV-307).
- `specs/pattern-gallery-sector-list-misdescribes-the-cost-table.md`:
  frozen spec (INV-307).
- `specs/pdf-layout-verification-without-poppler.md`: frozen spec (INV-307).
- `specs/per-module-outcome-invariants-omit-the-apparatus-exempt-carve-out.md`:
  frozen spec (INV-307).
- `specs/per-tab-screenshot-capture-and-grounded-captions.md`:
  frozen spec (INV-307).
- `specs/phase-a-preload-test-load-precedes-its-prerequisites.md`:
  frozen spec (INV-307).
- `specs/phasec-fires-two-self-answered-confirmations-back-to-back.md`:
  frozen spec (INV-307).
- `specs/pin-iterate-proceed-decision-gate.md`: frozen spec (INV-307).
- `specs/pin-remaining-interaction-questions.md`: frozen spec (INV-307).
- `specs/pin-visual-explanations-question.md`: frozen spec (INV-307).
- `specs/pin-visualization-offer-questions.md`: frozen spec (INV-307).
- `specs/plugin-prose-negatives-are-unswept-by-any-guard.md`:
  frozen spec (INV-307).
- `specs/plugin-version-resolves-to-the-running-plugin-root.md`:
  frozen spec (INV-307).
- `specs/poor-band-offers-the-remap-loop-before-anything-establishes-a-mapping-cause.md`:
  frozen spec (INV-307).
- `specs/poppler-is-not-standard-on-macos.md`: frozen spec (INV-307).
- `specs/post-load-match-key-semantic-audit.md`: frozen spec (INV-307).
- `specs/post-yes-switch-statement-ignores-what-the-bootcamper-already-set.md`:
  frozen spec (INV-307).
- `specs/postgres-in-docker-database-option.md`: frozen spec (INV-307).
- `specs/pr4-review-minor-fixes.md`: frozen spec (INV-307).
- `specs/pr7-review-minor-fixes.md`: frozen spec (INV-307).
- `specs/prefer-the-package-manager-version-is-wrong-for-an-unmanaged-install.md`:
  frozen spec (INV-307).
- `specs/preparation-recap-template-contradicts-its-own-rules.md`:
  frozen spec (INV-307).
- `specs/preparation-summarizes-the-model-nudge-trigger-as-the-forbidden-comparison.md`:
  frozen spec (INV-307).
- `specs/proceed-on-sqlite-keeps-the-tier-s-thread-count.md`:
  frozen spec (INV-307).
- `specs/production-volume-question-clarity-and-threading-cutover.md`:
  frozen spec (INV-307).
- `specs/profile-report-filename-is-conditional-on-file-count.md`:
  frozen spec (INV-307).
- `specs/project-readme-is-updated-but-never-created.md`: frozen spec (INV-307).
- `specs/provenance-aware-phasec-load-questions.md`: frozen spec (INV-307).
- `specs/proving-an-id-is-unused-by-writing-it-cites-it.md`:
  frozen spec (INV-307).
- `specs/python3-compile-and-example-recap-mechanism.md`: frozen spec (INV-307).
- `specs/quality-score-per-record-type.md`: frozen spec (INV-307).
- `specs/quality-scoring-presence-test.md`: frozen spec (INV-307).
- `specs/query-programs-dedupe-source-rows-by-record-key.md`:
  frozen spec (INV-307).
- `specs/readiness-gate-acts-on-structure-while-naming-semantics.md`:
  frozen spec (INV-307).
- `specs/readme-claims-two-interfaces-while-inv098-handles-four.md`:
  frozen spec (INV-307).
- `specs/reassess-per-module-model-effort-assignments.md`: frozen spec
  (INV-307).
- `specs/reassurance-must-precede-its-pinned-question.md`: frozen spec
  (INV-307).
- `specs/rebuild-viz-snapshot-after-customization.md`: frozen spec (INV-307).
- `specs/recap-always-created-vs-refusing-a-non-recap.md`: frozen spec
  (INV-307).
- `specs/recap-checkpoint-block-is-parsed-as-modules-instead-of-being-lifted.md`:
  frozen spec (INV-307).
- `specs/recap-durability.md`: frozen spec (INV-307).
- `specs/recap-new-line-labels-regression-tests.md`: frozen spec (INV-307).
- `specs/recap-pdf-certificate-version-and-list-spacing.md`:
  frozen spec (INV-307).
- `specs/recap-pdf-generator-fail-loudly-on-content-loss.md`:
  frozen spec (INV-307).
- `specs/recap-pdf-images-resolve-against-recap-directory.md`:
  frozen spec (INV-307).
- `specs/recap-pdf-professional-design.md`: frozen spec (INV-307).
- `specs/recap-screenshots-in-bullets-never-reach-the-pdf.md`:
  frozen spec (INV-307).
- `specs/recap-sections-name-based-and-complete.md`: frozen spec (INV-307).
- `specs/recap-subsection-heading-drift-is-caught-only-at-graduation.md`:
  frozen spec (INV-307).
- `specs/recap-summary-blocks-authored-as-bullets.md`: frozen spec (INV-307).
- `specs/reconcile-action-taken-wording.md`: frozen spec (INV-307).
- `specs/reconcile-sdk-guide-license-note-with-detected-limit.md`:
  frozen spec (INV-307).
- `specs/record-declined-specs-so-they-are-not-re-offered.md`:
  frozen spec (INV-307).
- `specs/record-preview-requires-registered-source.md`: frozen spec (INV-307).
- `specs/record-truthset-visualization-completion.md`: frozen spec (INV-307).
- `specs/recorded-server-pid-is-the-subshell-not-the-server.md`:
  frozen spec (INV-307).
- `specs/redo-batch-drain-must-terminate.md`: frozen spec (INV-307).
- `specs/reframe-the-quiz-as-a-knowledge-check.md`: frozen spec (INV-307).
- `specs/refresh-example-recap-to-the-consolidated-app.md`: frozen spec
  (INV-307).
- `specs/refresh-example-recap.md`: frozen spec (INV-307).
- `specs/refresh-model-guidance-to-current-top-tier-model.md`:
  frozen spec (INV-307).
- `specs/refresh-reverified-provenance-stamps.md`: frozen spec (INV-307).
- `specs/refresh-the-initialize-workflow-snippet-count-in-step4.md`:
  frozen spec (INV-307).
- `specs/register-data-sources-sample-tuple-is-stated-per-language-as-universal.md`:
  frozen spec (INV-307).
- `specs/registration-code-rests-on-two-configure-behaviors-the-server-does-not-have.md`:
  frozen spec (INV-307).
- `specs/registration-edits-damaged-the-text-they-landed-in.md`:
  frozen spec (INV-307).
- `specs/rel-key-attributes-fail-the-verbatim-gate-too-whenever-record-id-is-a-hash.md`:
  frozen spec (INV-307).
- `specs/relationship-network-edge-color-and-legend-filter.md`:
  frozen spec (INV-307).
- `specs/relay-the-default-flags-production-caution.md`: frozen spec (INV-307).
- `specs/releasing-is-manual-and-the-steps-can-drift-apart.md`:
  frozen spec (INV-307).
- `specs/relocate-git-init-to-onboarding.md`: frozen spec (INV-307).
- `specs/relocate-integration-deployment-questions-to-module1.md`:
  frozen spec (INV-307).
- `specs/relocate-setup-questions-to-bootcamp-preparation.md`:
  frozen spec (INV-307).
- `specs/remove-orphaned-first-visualization-guarantee.md`: frozen spec
  (INV-307).
- `specs/remove-sample-recap-pdf-mention-from-welcome.md`: frozen spec
  (INV-307).
- `specs/rename-data-quality-mapping-display-name.md`: frozen spec (INV-307).
- `specs/rename-transformed-to-senzing-ready.md`: frozen spec (INV-307).
- `specs/render-any-bootcamp-document-as-a-styled-pdf.md`: frozen spec
  (INV-307).
- `specs/reporting-guide-topics-gate-on-language.md`: frozen spec (INV-307).
- `specs/required-params-guard-covers-two-of-nine-tools.md`:
  frozen spec (INV-307).
- `specs/response-schemas-now-documents-match-info-depth.md`:
  frozen spec (INV-307).
- `specs/restamp-27-mcp-negatives-to-server-1-36-0.md`: frozen spec (INV-307).
- `specs/restructure-module7-visualization-offers.md`: frozen spec (INV-307).
- `specs/results-presentation-turns-end-with-zero-questions.md`:
  frozen spec (INV-307).
- `specs/reverify-the-three-verbatim-check-limitations.md`: frozen spec
  (INV-307).
- `specs/robust-fpdf2-install.md`: frozen spec (INV-307).
- `specs/routing-a-registered-feature-attribute-to-payload-is-silently-a-no-op.md`:
  frozen spec (INV-307).
- `specs/routing-report-flags-every-payload-field-as-dropped.md`:
  frozen spec (INV-307).
- `specs/scaffold-banner-ignores-fresh-and-seeded-modes.md`:
  frozen spec (INV-307).
- `specs/scaffold-engine-config-never-reaches-the-sdk-path.md`:
  frozen spec (INV-307).
- `specs/scaffold-snippet-count-and-group-list-are-stale.md`:
  frozen spec (INV-307).
- `specs/scenario-generation-has-no-size-cap-or-load-time-warning.md`:
  frozen spec (INV-307).
- `specs/screenshot-embed-rule-requires-a-turn-the-recap-section-does-not-exist-in.md`:
  frozen spec (INV-307).
- `specs/sdk-guide-configure-now-leads-with-seeding.md`: frozen spec (INV-307).
- `specs/sdk-guide-configure-unseeded-datastore.md`: frozen spec (INV-307).
- `specs/sdk-reference-carries-signatures-under-every-topic.md`:
  frozen spec (INV-307).
- `specs/sdk-setup-step-4-requires-an-engine-before-the-datastore-exists.md`:
  frozen spec (INV-307).
- `specs/sdk-setup-step5a-reads-absence-as-the-built-in-license.md`:
  frozen spec (INV-307).
- `specs/sdk-setups-license-reconciliation-does-not-say-whether-to-persist.md`:
  frozen spec (INV-307).
- `specs/search-attribute-fallback-survives-a-failed-attempt.md`:
  frozen spec (INV-307).
- `specs/search-docs-instructions-omit-the-required-query-parameter.md`:
  frozen spec (INV-307).
- `specs/selecting-from-an-mcp-listing-by-shape-is-unregistered.md`:
  frozen spec (INV-307).
- `specs/senz7221-now-names-its-own-remedy.md`: frozen spec (INV-307).
- `specs/senzing-python-sdk-must-not-be-pip-installed.md`: frozen spec
  (INV-307).
- `specs/separate-server-owned-commands-from-plugin-owned-update-checks.md`:
  frozen spec (INV-307).
- `specs/settle-whether-the-install-vs-update-gap-was-reported-upstream.md`:
  frozen spec (INV-307).
- `specs/seven-deferred-invariants-each-claim-the-same-next-free-id.md`:
  frozen spec (INV-307).
- `specs/seven-hard-rules-shipped-in-one-run-with-no-invariant.md`:
  frozen spec (INV-307).
- `specs/shipped-citation-report-cannot-see-a-module-display-name.md`:
  frozen spec (INV-307).
- `specs/show-plugin-version-and-record-environment.md`: frozen spec (INV-307).
- `specs/since-last-audit-reports-zero-when-the-audit-record-shares-the-work-commit.md`:
  frozen spec (INV-307).
- `specs/single-license-gate-at-data-processing.md`: frozen spec (INV-307).
- `specs/single-page-capture-crops-to-the-viewport-and-calls-it-full-page.md`:
  frozen spec (INV-307).
- `specs/single-page-capture-instruction-produces-zero-images.md`:
  frozen spec (INV-307).
- `specs/six-rules-become-visible-when-the-detector-is-fixed.md`:
  frozen spec (INV-307).
- `specs/skill-model-selection.md`: frozen spec (INV-307).
- `specs/skip-business-user-uat-for-generated-scenario.md`: frozen spec
  (INV-307).
- `specs/skip-model-guidance-question.md`: frozen spec (INV-307).
- `specs/skipping-step-3-on-an-existing-install-skips-the-env-script.md`:
  frozen spec (INV-307).
- `specs/snapshot-port-and-dataset-wording.md`: frozen spec (INV-307).
- `specs/snapshot-static-search-results.md`: frozen spec (INV-307).
- `specs/source-colors-from-discovered-data-sources.md`: frozen spec (INV-307).
- `specs/source-encoding-collides-past-twenty-four-sources.md`:
  frozen spec (INV-307).
- `specs/space-every-recap-bullet-list-by-default.md`: frozen spec (INV-307).
- `specs/split-truthset-visualization-into-standalone-module.md`:
  frozen spec (INV-307).
- `specs/sqlite-branch-says-no-additional-setup-but-the-schema-is-required.md`:
  frozen spec (INV-307).
- `specs/statement-only-step-cannot-satisfy-one-question-per-turn.md`:
  frozen spec (INV-307).
- `specs/stdlib-pdf-writer-substitutes-question-marks.md`: frozen spec
  (INV-307).
- `specs/step-1-says-skip-step-3-entirely-then-says-not-entirely.md`:
  frozen spec (INV-307).
- `specs/step-15s-both-versions-gate-is-unsatisfiable-on-a-generated-scenario.md`:
  frozen spec (INV-307).
- `specs/step-1s-does-not-work-claim-about-the-object-shape-is-stale.md`:
  frozen spec (INV-307).
- `specs/step-2-prose-prescribes-a-record-type-its-own-schema-rejects.md`:
  frozen spec (INV-307).
- `specs/step-5a-coverage-check-partitions-root-keys-only.md`:
  frozen spec (INV-307).
- `specs/step-5a-measures-the-license-before-the-engine-config-exists.md`:
  frozen spec (INV-307).
- `specs/step1-filesystem-fallback-is-linux-only.md`: frozen spec (INV-307).
- `specs/step1-license-framing-ignores-the-measured-record-limit.md`:
  frozen spec (INV-307).
- `specs/step14-value-proposition-query-is-bm25-hostile-with-no-fallback.md`:
  frozen spec (INV-307).
- `specs/step3-field-count-warning-no-longer-fires.md`: frozen spec (INV-307).
- `specs/step3-makes-the-73kb-spec-authoritative-while-the-workflow-forbids-reading-it.md`:
  frozen spec (INV-307).
- `specs/step3b-quality-lookup-misroutes-and-omits-the-evidence-requirement.md`:
  frozen spec (INV-307).
- `specs/step5b-keepsake-pdfs-are-never-announced.md`: frozen spec (INV-307).
- `specs/step8-lacks-the-platform-mandatory-rule-that-agent-behavior-carries.md`:
  frozen spec (INV-307).
- `specs/stop-hook-false-positive.md`: frozen spec (INV-307).
- `specs/stop-hook-issue.md`: frozen spec (INV-307).
- `specs/stop-hook-ran-bare-python3-and-executed-its-own-payload.md`:
  frozen spec (INV-307).
- `specs/stop-nudge-partial-flush.md`: frozen spec (INV-307).
- `specs/supportpath-failure-code-and-szproduct-masking.md`:
  frozen spec (INV-307).
- `specs/supportpath-trap-is-not-windows-only.md`: frozen spec (INV-307).
- `specs/suppress-admin-write-noise.md`: frozen spec (INV-307).
- `specs/surface-aware-model-effort-instructions.md`: frozen spec (INV-307).
- `specs/synthesized-scenarios-make-the-quality-gate-unreachable.md`:
  frozen spec (INV-307).
- `specs/system-verification-banner-no-action-needed.md`: frozen spec (INV-307).
- `specs/system-verification-java-loading-scaffold-hits-the-json-p-gap-too.md`:
  frozen spec (INV-307).
- `specs/szbuildversion-windows-path-is-now-mcp-sourced.md`:
  frozen spec (INV-307).
- `specs/tab-coverage-has-no-denominator-for-a-visualization-that-wrote-no-manifest.md`:
  frozen spec (INV-307).
- `specs/the-2026-08-21-run-shipped-three-unregistered-guarantees.md`:
  frozen spec (INV-307).
- `specs/the-absence-branch-guard-reaches-three-of-four-sites.md`:
  frozen spec (INV-307).
- `specs/the-acknowledge-rule-does-not-reach-across-the-module-transition.md`:
  frozen spec (INV-307).
- `specs/the-audit-skill-reads-its-own-ledger-backwards.md`:
  frozen spec (INV-307).
- `specs/the-audit-skills-baselines-and-required-reading-are-stale.md`:
  frozen spec (INV-307).
- `specs/the-bootcamp-asks-where-the-output-is-going-and-never-gets-it-there.md`:
  frozen spec (INV-307).
- `specs/the-bootcamp-cannot-leave-the-machine-it-was-built-on.md`:
  frozen spec (INV-307).
- `specs/the-cjk-drop-remedy-assumes-the-non-latin-text-is-a-label-not-the-finding.md`:
  frozen spec (INV-307).
- `specs/the-cord-disclosure-rule-cites-inv-012-where-inv-247-governs.md`:
  frozen spec (INV-307).
- `specs/the-deep-linking-preflight-refuses-a-tabless-page-it-should-capture-whole.md`:
  frozen spec (INV-307).
- `specs/the-dev-command-list-has-drifted-from-the-shipped-set.md`:
  frozen spec (INV-307).
- `specs/the-documented-command-set-has-drifted-from-the-shipped-one.md`:
  frozen spec (INV-307).
- `specs/the-download-url-preference-is-a-rule-no-invariant-and-no-deferral-covers.md`:
  frozen spec (INV-307).
- `specs/the-eval-license-duration-tools-now-agree-so-retire-the-note-and-its-guard.md`:
  frozen spec (INV-307).
- `specs/the-export-flag-set-is-coupled-to-absorb-with-nothing-connecting-them.md`:
  frozen spec (INV-307).
- `specs/the-export-stream-build-is-unreachable-in-the-shipped-server.md`:
  frozen spec (INV-307).
- `specs/the-field-count-miscounts-type-discriminator-half-is-confirmed-not-un-re-run.md`:
  frozen spec (INV-307).
- `specs/the-forbidden-question-is-the-most-prominent-text-in-the-step-that-forbids-it.md`:
  frozen spec (INV-307).
- `specs/the-github-issue-path-ships-guarantees-with-no-invariant.md`:
  frozen spec (INV-307).
- `specs/the-hard-rule-detector-misses-every-rule-not-first-on-its-line.md`:
  frozen spec (INV-307).
- `specs/the-improve-path-repoints-the-registry-without-updating-record-count.md`:
  frozen spec (INV-307).
- `specs/the-inv-300-guard-checks-one-of-the-invariants-three-obligations.md`:
  frozen spec (INV-307).
- `specs/the-invariant-to-enforcing-test-link-is-asserted-nowhere.md`:
  frozen spec (INV-307).
- `specs/the-negatives-backlog-was-never-re-asked-and-one-claim-is-now-false.md`:
  frozen spec (INV-307).
- `specs/the-new-conformance-views-are-not-reachable-from-the-paths-that-prescribe-them.md`:
  frozen spec (INV-307).
- `specs/the-no-fork-discipline-is-registered-only-inside-inv-183s-artifact-scope.md`:
  frozen spec (INV-307).
- `specs/the-one-question-per-turn-rule-is-registered-nowhere.md`:
  frozen spec (INV-307).
- `specs/the-owner-side-detector-reads-a-pointer-as-an-owner.md`:
  frozen spec (INV-307).
- `specs/the-packager-secret-scan-skips-the-files-most-likely-to-be-secrets.md`:
  frozen spec (INV-307).
- `specs/the-packaging-consent-gate-is-an-unregistered-guarantee.md`:
  frozen spec (INV-307).
- `specs/the-phase2-fixture-cannot-exercise-the-cover-chip-clip.md`:
  frozen spec (INV-307).
- `specs/the-quality-gates-improve-option-has-no-procedure-and-is-incoherent-on-a-generated-scenario.md`:
  frozen spec (INV-307).
- `specs/the-single-page-capture-never-requests-the-settled-render.md`:
  frozen spec (INV-307).
- `specs/the-source-set-coloring-rule-is-stated-three-times-and-verified-nowhere.md`:
  frozen spec (INV-307).
- `specs/the-teardown-contract-assumes-a-host-shell-and-the-container-has-neither-tool.md`:
  frozen spec (INV-307).
- `specs/the-truth-set-does-exercise-the-encoding-self-check.md`:
  frozen spec (INV-307).
- `specs/the-upstream-outcome-vocabulary-is-an-unbound-closed-set.md`:
  frozen spec (INV-307).
- `specs/the-viz-contract-never-states-the-bind-host-so-a-port-conflict-can-succeed.md`:
  frozen spec (INV-307).
- `specs/the-viz-server-header-describes-only-one-of-its-two-build-paths.md`:
  frozen spec (INV-307).
- `specs/the-work-commit-detector-sees-nothing-on-a-merge.md`:
  frozen spec (INV-307).
- `specs/the-writer-count-matcher-enumerates-phrasings-not-the-concept.md`:
  frozen spec (INV-307).
- `specs/three-hard-rules-from-the-2026-08-28-loop-carry-no-citation-at-the-line.md`:
  frozen spec (INV-307).
- `specs/three-numbered-questions-render-their-options-inline.md`:
  frozen spec (INV-307).
- `specs/todo.md`: frozen spec (INV-307).
- `specs/topical-index-for-the-invariants.md`: frozen spec (INV-307).
- `specs/triage-the-twelve-uncited-hard-rules.md`: frozen spec (INV-307).
- `specs/truth-set-is-spelled-two-ways-in-shipped-prose.md`:
  frozen spec (INV-307).
- `specs/truthset-cannot-satisfy-the-generated-scenario-invariants.md`:
  frozen spec (INV-307).
- `specs/truthset-step-saves-a-five-record-preview-not-the-truth-set.md`:
  frozen spec (INV-307).
- `specs/truthset-visualization-full-apparatus.md`: frozen spec (INV-307).
- `specs/truthset-viz-entity-actions-and-aggregate-drilldowns.md`:
  frozen spec (INV-307).
- `specs/truthset-viz-graph-label-toggles-and-scale-aware-defaults.md`:
  frozen spec (INV-307).
- `specs/truthset-viz-readable-why-how-and-modal-polish.md`:
  frozen spec (INV-307).
- `specs/us-english-spelling-is-unregistered-and-unguarded.md`:
  frozen spec (INV-307).
- `specs/vendor-d3-offline-visualization.md`: frozen spec (INV-307).
- `specs/verbatim-check-cannot-see-field-name-derived-values.md`:
  frozen spec (INV-307).
- `specs/verbatim-check-numeric-source-values.md`: frozen spec (INV-307).
- `specs/verbatim-check-rejects-extract-and-relationship-scaffolding.md`:
  frozen spec (INV-307).
- `specs/verbose-mapping-requires-a-plan-gate-that-does-not-exist.md`:
  frozen spec (INV-307).
- `specs/verbosity-minimal-preset.md`: frozen spec (INV-307).
- `specs/verification-grades-the-engine-against-the-guides-own-prediction.md`:
  frozen spec (INV-307).
- `specs/verification-report-cannot-express-an-expectation-mismatch.md`:
  frozen spec (INV-307).
- `specs/verify-and-mark-the-six-unmarked-prose-negatives.md`:
  frozen spec (INV-307).
- `specs/verify-sdk-parameter-shapes-and-flag-families.md`: frozen spec
  (INV-307).
- `specs/visible-mcp-source-attribution.md`: frozen spec (INV-307).
- `specs/visualization-contract-and-reference-server-disagree-on-record-fields.md`:
  frozen spec (INV-307).
- `specs/visualization-legibility-at-production-scale.md`: frozen spec
  (INV-307).
- `specs/visualization-model-build-does-one-get-entity-per-record.md`:
  frozen spec (INV-307).
- `specs/visualization-server-in-chosen-language.md`: frozen spec (INV-307).
- `specs/visualization-server-lifetime-and-teardown-gate.md`:
  frozen spec (INV-307).
- `specs/visualization-server-teardown-does-not-record-a-pid.md`:
  frozen spec (INV-307).
- `specs/visualization-why-how-and-clickable-histogram.md`: frozen spec
  (INV-307).
- `specs/viz-reference-help-text-names-removed-tabs.md`: frozen spec (INV-307).
- `specs/viz-server-settings-precedence-and-validation.md`: frozen spec
  (INV-307).
- `specs/why-entities-default-flags-has-no-composite-members.md`:
  frozen spec (INV-307).
- `specs/why-key-details-is-documented-now-so-the-no-flag-claim-is-stale.md`:
  frozen spec (INV-307).
- `specs/why-key-details-needs-the-flag-the-plugin-forbids.md`:
  frozen spec (INV-307).
- `specs/why-match-info-scalars-are-why-key-and-why-errule-code.md`:
  frozen spec (INV-307).
- `specs/why-response-carries-why-key-details-not-match-key-details.md`:
  frozen spec (INV-307).
- `specs/windows-headless-browser-discovery-for-screenshots.md`:
  frozen spec (INV-307).
- `specs/windows-powershell-encoding-and-syntax.md`: frozen spec (INV-307).
- `specs/windows-scoop-facts-the-server-now-owns.md`: frozen spec (INV-307).
- `specs/write-gate-location-logic-is-unregistered.md`: frozen spec (INV-307).
- `specs/write-gate-tests.md`: frozen spec (INV-307).
- `tests/`: the stdlib unittest suite, its helper modules and fixtures (section
  8).

## 3. Toolchain and build

### Toolchain

Python 3 only; no compiled code. CI pins the interpreter version with
`actions/setup-python`:

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "3.12"
```

<!-- markdownlint-enable MD013 -->

Runtime scripts use only the standard library, with optional extras: `fpdf2`
(recap PDF renderer; a stdlib fallback ships), `Pillow` and `ffmpeg` or
`imageio-ffmpeg` (recap video), and a browser driver for screenshot capture.
Tests are stdlib only (INV-108). Claude Code loads the plugin; no build step
exists.

### Manifests

<!-- markdownlint-disable MD013 -->

From `requirements-dev.txt`:

```text
# Development-only dependencies for running the test suite in full.
#
# NOT a runtime requirement of the plugin. The shipped PDF generators
# (plugins/senzing-bootcamp/scripts/generate_recap_pdf.py and
# generate_discoveries_pdf.py) tier their renderers: fpdf2 when it is importable,
# a stdlib fallback otherwise. A bootcamper without fpdf2 still gets a PDF, and
# that fallback path ships and is tested. Nothing here is installed on their machine.
#
# What this file is for: without fpdf2, the tests that measure the fpdf2-rendered
# output cannot exercise it and are skipped (tests/_fpdf2_support.py). The suite
# stays green, but the fpdf2 renderer goes unmeasured -- so install this before
# trusting a run, and always before a release.
#
# The tests themselves remain standard-library only, per INV-108: availability is
# probed with importlib.util.find_spec, never by importing fpdf2 in a test.
#
#   python3 -m pip install -r requirements-dev.txt
#
# Source issue: #30

fpdf2

# The recap-video renderer (plugins/senzing-bootcamp/scripts/generate_recap_video.py) draws
# its frames with Pillow and encodes them with ffmpeg, found on PATH first and then from the
# imageio-ffmpeg package. Neither is a runtime requirement: graduation offers the video and
# skips it when they are missing. Without them tests/test_recap_video.py skips its drawing
# and end-to-end tests, with a reason, and still runs its validation tests. Pillow also
# arrives with fpdf2; it is named here because the video tests exercise it directly.
#
# Source issue: #299

Pillow
imageio-ffmpeg

# Optional. The suite's documented runner is stdlib unittest:
#     python3 -m unittest discover -s tests
# pytest also works and gives a shorter summary; it is not required.
# pytest
```

<!-- markdownlint-enable MD013 -->

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/.claude-plugin/plugin.json`:

```json
{
  "name": "senzing-bootcamp",
  "version": "0.6.1",
  "description": "Guided bootcamp for learning Senzing entity resolution with Claude Code, from first demo to production deployment.",
  "author": {
    "name": "Senzing"
  },
  "homepage": "https://github.com/docktermj/senzing-bootcamp-claude-plugin-development",
  "repository": "https://github.com/docktermj/senzing-bootcamp-claude-plugin-development",
  "license": "Apache-2.0"
}
```

<!-- markdownlint-enable MD013 -->

<!-- markdownlint-disable MD013 -->

From `.claude-plugin/marketplace.json`:

```json
{
  "name": "senzing-bootcamp-dev",
  "owner": {
    "name": "docktermj"
  },
  "description": "Senzing bootcamp plugin for Claude Code.",
  "plugins": [
    {
      "name": "senzing-bootcamp",
      "source": "./plugins/senzing-bootcamp",
      "description": "Guided bootcamp for learning Senzing entity resolution with Claude Code, from first demo to production deployment.",
      "keywords": ["senzing", "bootcamp", "entity-resolution", "tutorial", "guided-learning"]
    }
  ]
}
```

<!-- markdownlint-enable MD013 -->

### Build commands

There is nothing to build. From the repository root, install the development
extras, then run the suite (the command `tests/README.md` and CI use):

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests
```

CI runs the suite twice, with fpdf2 installed and absent (section 4.2). Locally,
run both legs with `HOME` set to an empty directory outside `/tmp`, the present
leg with `PYTHONUSERBASE` pointing at the real user site so fpdf2 stays
importable, and the absent leg from a `python3 -m venv --without-pip`
interpreter. Also run, from the repository root:

```sh
python3 .claude/skills/compact-dev-environment/citations.py verify
python3 .claude/skills/review-invariants/invariant_manifest.py --check
```

Install the plugin into Claude Code (from `docs/README.md`):

<!-- markdownlint-disable MD013 -->

From `docs/README.md`:

```sh
    claude plugin marketplace add docktermj/senzing-bootcamp-claude-plugin-development
    claude plugin install senzing-bootcamp@senzing-bootcamp-dev
```

<!-- markdownlint-enable MD013 -->

## 4. CI

### 4.1 `.github/workflows/lint-workflows.yaml`

Name `Lint workflows`. Trigger:

<!-- markdownlint-disable MD013 -->

From `.github/workflows/lint-workflows.yaml`:

```yaml
on:
  pull_request:
    branches: [main]
```

<!-- markdownlint-enable MD013 -->

Top-level `permissions: {}` and a concurrency group per workflow and head ref,
canceling in progress.

#### 4.1.1 `lint-workflows`

A reusable-workflow call with no runner, steps, `needs`, matrix or `env` of its
own. It grants `contents: read`, `packages: read`, `pull-requests: write` and
`statuses: write`, and calls:

<!-- markdownlint-disable MD013 -->

From `.github/workflows/lint-workflows.yaml`:

```yaml
      statuses: write
```

<!-- markdownlint-enable MD013 -->

The called workflow skips itself when no workflow file changed, through its own
`changes` job.

### 4.2 `.github/workflows/test-suite.yaml`

Name `Test suite`. Trigger:

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

<!-- markdownlint-enable MD013 -->

Top-level `permissions: {}` and a concurrency group per workflow and head ref,
canceling in progress.

#### 4.2.1 `test-suite`

Display name `tests (fpdf2 ${{ matrix.fpdf2 }})`, `runs-on: ubuntu-latest`,
`permissions: contents: read`, `timeout-minutes: 15`, no `needs` and no `env`.
Matrix, with `fail-fast: false`:

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
        fpdf2: [present, absent]
```

<!-- markdownlint-enable MD013 -->

Steps, in order:

- `Checkout repository`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Checkout repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
```

<!-- markdownlint-enable MD013 -->

- `Set up Python`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "3.12"
```

<!-- markdownlint-enable MD013 -->

- `Install fpdf2`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Install fpdf2
        if: matrix.fpdf2 == 'present'
        run: |
          python -m pip install --upgrade pip
          python -m pip install --requirement requirements-dev.txt
```

<!-- markdownlint-enable MD013 -->

- `Confirm fpdf2 really is absent`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Confirm fpdf2 really is absent
        if: matrix.fpdf2 == 'absent'
        run: |
          if python -c "import fpdf" 2>/dev/null; then
            echo "::error::fpdf2 is importable in the 'absent' job, so this job is no longer" \
              "testing the stdlib fallback. Something installed it transitively."
            exit 1
          fi
```

<!-- markdownlint-enable MD013 -->

- `Run the test suite`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: Run the test suite
        shell: bash
        run: |
          python -m unittest discover -s tests 2>&1 | tee suite.log
```

<!-- markdownlint-enable MD013 -->

- `The absent job must skip, and say why`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: The absent job must skip, and say why
        if: matrix.fpdf2 == 'absent'
        shell: bash
        run: |
          if ! grep -q "fpdf2 is not installed" suite.log; then
            echo "::error::The suite ran without fpdf2 but printed no notice naming it." \
              "That notice is the user-facing half of #30: without it, a contributor sees" \
              "skips with no stated cause."
            exit 1
          fi
          # A run reporting zero skips here means the guards have stopped being applied,
          # which is the #30 regression arriving quietly rather than as a failure.
          if ! grep -Eq "OK \(skipped=[1-9][0-9]*\)" suite.log; then
            echo "::error::Expected the run to be OK with a non-zero skip count." \
              "Without fpdf2 the fpdf2-dependent tests must SKIP, not vanish and not fail."
            exit 1
          fi
```

<!-- markdownlint-enable MD013 -->

- `The present job must not print the absence notice`

<!-- markdownlint-disable MD013 -->

From `.github/workflows/test-suite.yaml`:

```yaml
      - name: The present job must not print the absence notice
        if: matrix.fpdf2 == 'present'
        shell: bash
        run: |
          if grep -q "fpdf2 is not installed" suite.log; then
            echo "::error::fpdf2 was installed, but the suite reported it missing." \
              "The detection in tests/_fpdf2_support.py disagrees with the environment."
            exit 1
          fi
```

<!-- markdownlint-enable MD013 -->

## 5. Components

### 5.1 `.claude-plugin/marketplace.json`

The marketplace catalog at the repository root. It names the marketplace
`senzing-bootcamp-dev`, owned by `docktermj`, described as the Senzing bootcamp
plugin for Claude Code. It lists exactly one plugin, also named
`senzing-bootcamp`, whose source is the relative directory
`./plugins/senzing-bootcamp`, with a one-sentence description (guided bootcamp
for learning Senzing entity resolution with Claude Code, from first demo to
production deployment) and the keywords `senzing`, `bootcamp`,
`entity-resolution`, `tutorial` and `guided-learning`. Adding the repository as
a marketplace and installing `senzing-bootcamp` from it is how a user gets the
plugin. The `-dev` suffix lets it be registered beside the published
`senzing-bootcamp` marketplace, which Claude Code would otherwise refuse as one
name with two sources; `propagate.sh` rewrites it back on publish (#449).

### 5.2 `plugins/senzing-bootcamp/.claude-plugin/plugin.json`

The plugin manifest. It declares the name `senzing-bootcamp`, the version
`0.5.3` (the single version every other version assertion must match), the
same description as the marketplace entry, author `Senzing`, homepage and
repository both set to the development repository on GitHub, and license
`Apache-2.0`. It declares no components explicitly: Claude Code discovers the
plugin's `skills/`, `commands/`, `hooks/hooks.json` and `.mcp.json` from their
conventional locations under the plugin root.

### 5.3 `plugins/senzing-bootcamp/.mcp.json`

Registers one MCP server named `senzing`, of type `http`, at
<https://mcp.senzing.com/mcp>. It needs no credentials and no environment
variables. Every Senzing fact, SDK snippet, mapping, sample dataset and error
explanation the skills use comes from this server's tools (for example
`get_capabilities`, `search_docs`, `sdk_guide`, `generate_scaffold`,
`find_examples`, `mapping_workflow`, `analyze_record`, `get_sample_data`,
`get_sdk_reference`, `explain_error_code`, `reporting_guide`,
`download_resource` and `submit_feedback`); the skills treat it as the only
source of truth for Senzing and never answer Senzing questions from training
data.

### 5.4 `plugins/senzing-bootcamp/hooks/hooks.json`

Registers seven `command`-type hooks. Each `command` string is
`python3` followed by the quoted path
`"${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py"`; the quoting keeps a plugin root
containing a space working. No hook has a timeout or other options.

- `SessionStart` (no matcher) runs `session-start.py`.
- `UserPromptSubmit` (no matcher) runs `feedback-capture.py`, then
  `checkpoint-tick.py`, as two hooks of one entry.
- `PreToolUse` with matcher `Write|Edit` runs `write-gate.py`.
- `Stop` (no matcher) runs `stop-nudge.py`.
- `PreCompact` (no matcher) runs `precompact-recap.py`.
- `SessionEnd` (no matcher) runs `session-end.py`.

Every script is gated on an active bootcamp: it does nothing unless
`config/bootcamp_progress.json` exists in the project directory, so the plugin
never changes unrelated sessions. Only `write-gate.py` (exit 2) and
`stop-nudge.py` (a `decision: block` reply, at most once per stop chain) can
block; `feedback-capture.py`, `checkpoint-tick.py` and `session-start.py`
inject context; the others emit nothing. The sibling `hooks/README.md`
documents each hook's purpose phrased from the Bootcamper's view beginning with
"to" (the INV-016 convention), the `python3`-on-`PATH` prerequisite on Linux,
macOS and Windows, the recap-checkpoint durability design shared by
`PreCompact`, `SessionEnd` and `SessionStart`, the two Stop-nudge opt-outs
(the `SENZING_BOOTCAMP_DISABLE_STOP_NUDGE` environment variable and the
top-level `disable_stop_nudge: true` key in
`config/bootcamp_preferences.yaml`), and why administrative `Write`/`Edit`
noise is minimized by batching writes rather than hidden.

### 5.5 `plugins/senzing-bootcamp/skills/bootcamp-onboarding/`

Entry skill ("start/resume the bootcamp"). The guide reads `ground-rules.md`,
then decides fresh vs resume from the CONTENT of
`config/bootcamp_progress.json`: missing, empty, malformed, non-object or a
blank `current_module` is a silent fresh start; a recorded `current_module`
offers resume at `current_module`/`current_step`, after re-offering any
feedback entry still marked `offer pending`. It never announces a resume it
cannot perform (`recap_checkpoint.bootcamp_active()` applies the same rule).

`onboarding-flow.md` (fresh start):

- Step 0: read the plugin `version` from
  `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (variable non-empty),
  else `<skill-dir>/../../.claude-plugin/plugin.json`, else "Unknown"; never
  by filesystem search. Feedback, recap header and recap provenance resolve
  it the same way.
- Step 0b: one `get_capabilities` probe (about 10 s). Failure shows a
  blocking "server unreachable" message with troubleshooting and waits for
  "retry".
- Step 1 (silent): create `src/`, `data/`, `docs/`, `config/`, `database/`,
  empty progress and preferences files, and `README.md` with `## Overview`
  and `## Business Problem` placeholders (filled by Module 1 Step 12).
- Step 2: light check of shell, Python 3 and network (a missing SDK does not
  block).
- Step 3: WELCOME banner, `Senzing Bootcamp vX.Y.Z` line, then an overview:
  guided discovery, recap PDF keepsake, the named module sequence, Core vs
  Customized, licensing, module-sized timing with resumable progress, and the
  "bootcamp feedback:" and "make a note" controls (stated, never asked). A
  pre-existing `minimal` preset shows only the module list and timing.
- Step 4: "any questions?" (not a hard gate; never invent a total duration).
- Step 5: invoke `bootcamp-preparation`. The preface writes no preferences.

Ground rules (`ground-rules.md`, every turn):

- One bold `👉` question ends each yielding turn; no "and/or" joins (only a
  trailing "(respond yes or no)" hint). Question-free steps are non-yielding
  and run inside the turn that ends on the next asking step. Informing text
  precedes the 👉; options sit directly beneath it. Every question traces to
  a shipped skill step; host controls (auto mode, plan mode, `/compact`) are
  never asked. Never fabricate answers; `🛑`/`⛔` markers are internal.
  Acknowledge each answer briefly and specifically, before any skill load.
- ⛔ gates and numbered steps are never skipped.
- MCP-first: every Senzing fact (and claim about Senzing the company) comes
  from an MCP call this turn, a skill file, or a local measurement, else is
  labeled inference or omitted; a local measurement beats generic MCP
  guidance. Routing: `mapping_workflow`, `generate_scaffold`/`sdk_guide`,
  `get_sdk_reference` (`parameters`, `flags`, `response_schemas`),
  `explain_error_code`, `search_docs`, `find_examples`, `get_sample_data`,
  `reporting_guide` (always with `language`; a `needs_input` reply is a gate
  to satisfy and re-call), `get_capabilities`. Elided example content is
  fetched via `raw_url` then `git clone`, never `inline` (only
  `download_resource` declares `inline`, chunked by `offset`). Retry a failed
  call once, then stop. Blank parsed fields suggest a wrong name or missing
  `*_MATCHING_INFO` flag; the SDK factory must outlive its engines.
  Attribution is light and suppressed under `minimal`.
- No SQL against `database/G2C.db`.
- Files stay in the project (no `/tmp`, no shell-profile edits). Layout:
  `src/`, `src/scripts/`, `docs/` (all `.md` but `README.md`), `data/`,
  `data/temp/`, `data/mapping/`, `src/resources/`, `config/`,
  `database/G2C.db`. Root whitelist: `.gitignore`, `.env`, `.env.example`,
  `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`,
  `package.json`. Never `internal://` as the datastore.
- Platform notes: Java standalone files use a package-private class;
  PowerShell 5.1 syntax and encodings; sourced env scripts work under zsh and
  never `exit`; on Docker a fresh parse error is retried once.
- Visual deliverables use `brand_tokens.py`, render offline, escape data.
- State: write rarely and batched, once per turn at step boundaries:
  `current_step` and `step_history[<module>]` (`last_completed_step`,
  `updated_at`). Keep `docs/progress/recap_checkpoint.md` filled between
  `RECAP-CHECKPOINT:START/END` markers.
- Reversed decisions (an audit changes a mapping, a score is corrected, a
  change is abandoned) are filed via `feedback.md`'s silent append.
- Verbosity presets `minimal`/`concise`/`standard`/`detailed`; required
  output is never suppressed, only merged with a semicolon and a space.
- Any-time controls (never the turn's 👉): feedback, make a note (feedback
  wins), change verbosity, repeat the question; an unanswered pending
  question is re-presented verbatim after any interruption.
- Module start (not for preparation or concepts): never show module numbers;
  `🚀🚀🚀  MODULE: <NAME>  🚀🚀🚀` banner, journey map of
  `selected_modules` (✅ done, 🔄 current, ⬜ upcoming), before/after,
  step overview, range time estimate, then the model/effort nudge. The nudge
  compares the stage's recommendation per dial with the live setting; a
  mismatch either way asks one pinned switch question (CLI `/model` and
  `/effort`, or interface-named controls) naming only the differing dial; a
  match or a setting above the table is one statement. A yes with the dial
  unchanged gates on "Are you done modifying the model and effort?".
  Recommendations: Sonnet 5.5/medium for the conversational stages and Data
  collection, Sonnet 5.5/high for System verification, Opus 5.5/high for SDK
  setup, Truth Set visualization and Data Quality onward.

Module completion (`module-completion.md`, before the transition question):

- Step 1, one write: add the name token to `modules_completed`, advance
  `current_module`, null `current_step`, final `step_history`.
- Step 2a: create `docs/bootcamp_recap.md`'s header if missing (name,
  started, programming language, path, plugin version).
- Step 2b: append `## {Name} — {timestamp}` with H3 Information Shared,
  Questions & Responses, Actions Taken, End-of-Module Summary (labeled What
  you accomplished and Files produced lists, Why it matters, optional
  takeaway). Embed every captured screenshot on its own line as
  `visualizations/<name>-<tab>.png` in tab order, captioned from the image.
- Step 2c: re-read, repair, run `generate_recap_pdf.py --check` silently,
  print `Recap updated: {Name}.`
- Step 2d: strip checkpoint blocks and clear the checkpoint.
- Step 2e: upsert `docs/video/broll.json[<token>]` (`module`, `images`,
  `facts`, `highlight`, `captured_at`); no raw record values; non-blocking.
- Capture uses `capture_screenshots.py` (`--single` for one-page HTML); exit
  1 means fix the tabs, exit 2 means skip.
- Step 3: `✅ Module complete: {Name}` summary with What's next.
- Step 4: "Are you ready to move on to the next module: {name}?"; after Query,
  Visualize and Discover, "Would you like to graduate now…?", then
  `graduation`.

Any-time flows:

- Feedback (`feedback.md`; phrases, hook or `/bootcamp-feedback`): capture
  context silently; create `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`
  if absent; 📝 banner; ask only unanswered parts of subject, what happened,
  why, fix, priority (High/Medium/Low); triage to `plugin`, `mcp-server`,
  `both`, `host` or `unclear`; append `## Improvement:` (Source, Routing,
  Upstream, context) and re-read. For `mcp-server`/`both`, ask to send an
  anonymized report via `submit_feedback`; `Upstream:` records the outcome.
  Exit banner, then the pending question. A silent append
  (`self-observed (assistant retrospective)`) serves reversed decisions.
- Notes (`notes.md`; phrases, hook or `/bootcamp-note`): 📌 banner; take the
  note from the message or ask; classify silently; recite with options save,
  add context, elaborate, reword; append to `docs/bootcamp_notes.md` with
  separate `**Context:**`/`**Elaboration:**` labels; re-read; exit banner.
  Never sent anywhere.
- Packaging (`packaging.md`; `/package-bootcamp`): dry-run
  `package_bootcamp.py` for `share` and `transfer` sizes; ask results,
  everything, or cancel; for transfer ensure `backups/revisit/` via
  `../graduation/database-backup.md`; run it and report path, size, digest.

### 5.6 `plugins/senzing-bootcamp/skills/bootcamp-preparation/`

First, mandatory module. Shows the `BOOTCAMP PREPARATION` banner; no journey
map, nudge or recap section; never in `modules_completed`. Its module table
fixes the state tokens: `bootcamp_preparation`, `entity_resolution_concepts`
(optional), `business_problem`, `sdk_setup`, `system_verification`
(optional, needs SDK setup), `truthset_visualization` (optional, needs
System verification), `data_collection`, `data_quality_mapping`,
`data_processing`, `query_visualize_discover`, `graduation`.

- Step 0: read `config/bootcamp_preferences.yaml`; a valid saved `path`,
  `verbosity` or `programming_language` suppresses its question and is never
  overwritten.
- Step 1 (⛔): 1 Core (recommended, all eleven tokens) or 2 Customized.
- Step 2 (Customized): pick from Entity Resolution Concepts, System
  verification, Truth Set visualization, or "none"; Truth Set without System
  verification adds it.
- Step 3: detail level 1 minimal, 2 concise, 3 standard (recommended),
  4 detailed, stored as `verbosity` `preset` plus five `categories`
  (`explanations`, `code_walkthroughs`, `step_recaps`, `technical_details`,
  `code_execution_framing`) at 0-3. No `model_guidance` question.
- Step 4: detect OS/arch (pinned fallback question if detection fails) and
  `name` from `git config user.name`; get languages from `get_capabilities`;
  ask the programming language, annotating options per Module 2 routing
  (Python needs Docker on macOS, Docker or WSL2 on Windows).
- Step 5: `git rev-parse` gives `git_init` `existing`; else `git init` and
  `true`; no git, `unavailable`.
- Step 6: one write of `path`, `selected_modules`, `verbosity`,
  `programming_language`, `name`, `os`, `arch`, `git_init`; one write of
  `selected_modules` and `current_module` to the progress file.
- Step 7: a "Bootcamp preparation complete" recap (modules separated by
  "; ", honored values marked "from your saved preferences", one line under
  `minimal`), then invoke `module-00-entity-resolution-concepts` if selected,
  else `module-01-business-problem`.

### 5.7 `plugins/senzing-bootcamp/skills/module-00-entity-resolution-concepts/`

Optional primer (state token `entity_resolution_concepts`). `SKILL.md` holds
the flow and close; `concepts.md` the banner, content, measured
`search_docs` queries and pinned questions. It runs only when Bootcamp
preparation selected it, so it asks no skip question, and as a preamble it
has no module-start apparatus or bootcamper-facing summary.

- Shows the ENTITY RESOLUTION CONCEPTS banner.
- Teaches from `search_docs`, each substantive claim checked by a second
  MCP call: what entity resolution is; false negatives and positives
  (ambiguous matches as invisible false positives); the pipeline
  (standardization, blocking, scoring, classification, clustering);
  disclosed versus discovered relationships; entities plus relationships as
  output (never "golden record"); Senzing's principle-based approach. A miss
  is re-queried in the documentation's own wording.
- Pinned "any questions about entity resolution", then a pinned "any other
  questions" variant after each answer.
- Mandatory pinned offer of an optional knowledge check (never called a
  quiz): 3 to 5 numbered multiple-choice MCP-sourced questions, one per
  turn; a wrong answer is named and re-taught; exit anytime; no score.
- Readiness gate "ready to move on to the next module: Discover the
  Business Problem?"; questions are answered and the gate re-presented.

Close, in one write to `config/bootcamp_progress.json`: append
`entity_resolution_concepts` to `modules_completed`, set `current_module` to
the next `selected_modules` entry and `current_step` to null, and record
`module_0_concepts.quiz_offered` / `quiz_taken` (presenting the offer first
if it was missed). It then runs module-completion Step 2 in full, including
2a (creates the recap header, being first on Core), the
`## Entity Resolution Concepts — {timestamp}` section, 2d and 2e (B-roll,
empty allowed), and invokes `module-01-business-problem`.

### 5.8 `plugins/senzing-bootcamp/skills/module-01-business-problem/`

"Discover the Business Problem" (`business_problem`). `SKILL.md` resumes
from `current_step` and routes SENZ codes to `explain_error_code`;
`phase1-discovery.md` holds steps 1 to 6, `phase2-document-confirm.md`
steps 9 to 17. Every step checkpoints to `config/bootcamp_progress.json`.

- 1: privacy reminder sharing step 2's turn. 2: offer a design-pattern
  gallery.
- 3: gallery entries (problem, goal, typical sources, value) from
  `search_docs` that turn, via measured routes (the mismatched-identity
  cost table, use-case sections, USCIS case study, MDM and
  non-person-entity FAQs with `category='faq'`); unreached categories are
  named, not invented; MCP attribution line; asks whether one fits.
- 4: three paths: a real case, the chosen pattern, or a generated scenario.
- 4a, generated: one category of Customer 360, Fraud Detection, Data
  Migration, Compliance, Marketing, Healthcare, Supply Chain, KYC,
  Insurance, Vendor MDM; at least two sources; cross-source mapping
  divergence; quality variation; about 10,000 records unless asked.
- 4b: `get_sample_data` decides CORD backing (`las-vegas`, `london`,
  `moscow` when the domain fits, provenance `cord`, stated as real data;
  never `truthset`) or `synthesized`.
- 5: infer record types, sources, category, criteria, outcome and
  integration. 5a compares the record total with a measured
  `license_record_limit`, else the built-in capacity from
  `sdk_guide(topic='load', record_count=<above limit>)`; over it, set
  `license_guidance_deferred: true` in `config/bootcamp_preferences.yaml`.
  A stated entitlement goes to `license_stated_limit`; no license prompt.
- 6a confirms a summary; 6b to 6d fill gaps one per turn: record types,
  source count, desired outcome (multi-select, every choice kept).
- 9: generated scenario writes Mermaid diagrams to
  `docs/data_architecture.md`; otherwise it asks for diagrams.
- 10a: integration question (and systems), then deployment target (cloud,
  container, local, not sure); one write of `integration_targets`,
  `deployment_target`, `cloud_provider` to preferences.
- 11: `docs/business_problem.md` from a fixed template, with verbatim
  bootcamper quote lines on prose sections only. Generated scenarios add
  the `> 🤖 Bootcamp-generated business case` marker, the diagram link and
  one `config/data_sources.yaml` entry per source.
- 12 fills `## Overview` and `## Business Problem` in `README.md`. 13
  proposes the approach; 14 restates value from
  `search_docs(query='entity resolution business value')`.
- 15: pinned confirmation, quotes shown beside the rendering (generated
  path: against the 6a summary). 16 writes
  `docs/stakeholder_summary_module1.md`. 17 runs module completion and the
  transition question; `current_step` becomes null.

### 5.9 `plugins/senzing-bootcamp/skills/module-02-sdk-setup/`

One file, `SKILL.md` ("SDK setup"): installs, configures and verifies the
Senzing SDK natively in the chosen language. It reads
`config/bootcamp_progress.json` (resuming at `current_step`), shows the
ground-rules module opening, and checkpoints each step number there. Senzing
facts come from MCP tools; SENZ codes go to `explain_error_code`, then
`search_docs`.

- Step 1, existing install: a language version check from
  `sdk_guide(topic='install', platform, language)`, else a probe for the
  platform's native library (`libSz.so`, `libSz.dylib` under `brew --prefix`,
  `Sz.dll` under `SENZING_DIR`); an unchecked platform is "unknown", never
  "not installed". V4.0+ takes the existing-install path: skip Step 2 and
  Step 3's EULA and package phases, still run its bindings phase and env
  script, then Steps 4 to 9. Below V4.0 upgrades; absent goes to Step 2.
- Step 1b, update offer (V4.0+, non-blocking): installed and available versions
  from package-manager queries (`dpkg-query`/`apt-cache`,
  `rpm`/`yum check-update`, `brew info`, `scoop info`; docker: the image tag);
  update commands from `sdk_guide` (apt/yum) or `search_docs` tap/bucket
  READMEs. Separators are normalized (`4.3.3-26191` vs `szBuildVersion.json`'s
  `4.3.3.26191`); a real mismatch means the file wins. The target's release
  notes (`search_docs(category='release_notes')`) are relayed, then one
  question: update, keep, or name a version (apt only, sha256-checked). An
  update asks the EULA first; a decline is never re-offered. After updating,
  re-verify and probe the artifact. The outcome (`up-to-date`,
  `update-declined`, `updated-to-<v>`, `check-skipped-<reason>`) is recorded
  under step 1.
- Step 2, platform: detected from `os`/`arch` in
  `config/bootcamp_preferences.yaml` or the system; a numbered question only
  as fallback. Routing: Python on macOS/Windows goes to docker (or WSL2 as
  `linux_apt` on Windows); Intel Mac to docker; Apple Silicon to `macos_arm`;
  Windows with Scoop to `windows`, else docker; Linux to `linux_apt` or
  `linux_yum`. Tap and bucket are flagged as unsupported previews.
- Step 3, install: `search_docs(category='anti_patterns')` first. Phase 1 asks
  the EULA before anything installs; a decline on a fresh install stops with no
  checkpoint. Phase 2 sets the platform's EULA variable (`SENZING_ACCEPT_EULA`,
  or `HOMEBREW_SENZING_ACCEPT_EULA` with a lowercase value) and installs. Docker
  path: a plain Debian container running the `linux_apt` steps, project
  bind-mounted, each container appended to `docker_containers` (`name`,
  `runtime`, optional `image`, `purpose`); `session-start.py` reports them and
  `session-end.py` stops them. An anchored rule (`#container-naming`) names
  every container the bootcamp creates with `docker_lifecycle.py
  container-name <base>` (project-derived; `-2` … `-9` past another project's
  container; stop and ask on a non-zero exit), and never removes, stops,
  starts or reuses a container `docker_containers` does not record. Phase 3 binds by the MCP-named route only: Python
  installs nothing (`pip install senzing` forbidden; shadowing detected via
  `senzing.__file__`); Java the product `sz-sdk.jar`; C# a local `Senzing.Sdk`
  NuGet source; Rust a git dependency; TypeScript from GitHub, with a
  build-from-source recovery branch (name the cause, offer fix, retry or
  fallback language).
- Step 3, env script (every path): `src/scripts/senzing-env.sh`, sourced
  (Windows `src\scripts\senzing-env.ps1`, dot-sourced); global shell profiles
  are never edited. It resolves its own path under bash and zsh, fails
  loudly naming the root if `config/bootcamp_progress.json` is missing
  (`return`, not `exit`), exports `SENZING_PROJECT_ROOT`,
  `SENZING_ENGINE_CONFIGURATION_JSON` from `config/engine_config.json`
  (unset with a notice while absent, refused if empty), and the platform and
  language variables from `sdk_guide` `env_vars` plus language `gotchas[]`.
- Step 4, verify the binding (no engine): fetch the
  `generate_scaffold(workflow='information')` snippets by `raw_url` (never
  `inline=true`); print the version and the resolved binding path; write
  `sdk_version` and `sdk_version_measured_at`. `SENZ7426`/`SENZ7220` are
  expected here.
- Step 5, license (no prompt; the key gate is Module 4): `get_license()`,
  saved to `config/license.json`; `recordLimit` (0 is unlimited) goes to
  `license_record_limit` with `license_record_limit_measured_at` marked
  provisional. If unmeasurable, write nothing and state the evaluation limit
  from `sdk_guide(topic='load', record_count=1000)` as an assumption.
- Step 6: creates `src/`, `src/scripts/`, `src/resources/`, `data/`,
  `data/mapping/`, `data/temp/`, `database/`, `docs/`, `config/`,
  `licenses/`.
- Step 7, database question (SQLite or PostgreSQL): writes `database_type`
  (`sqlite`/`postgresql`) to `config/bootcamp_preferences.yaml`; checkpoint
  only after setup. SQLite: on a mounted host filesystem (WSL2 `/mnt/`, bind
  mount) report `check_repository_performance`, never relocating; apply the
  `sdk_guide` schema via Python `sqlite3` to `database/G2C.db`, with an
  absolute connection string, never `/tmp`. PostgreSQL asks how: Docker
  (recommended; name from `container-name bootcamp-postgres`, localhost port
  from `free-port 5432` recorded as `host_port` and used in `SQL.CONNECTION`,
  absent meaning 5432; a busy port on resume is reported and asked about;
  generated password, volume `database/postgres`, `pg_isready`, schema DDL,
  `docker_containers` entry), local, existing server, or switch to SQLite.
- Step 8, engine config: `sdk_guide(topic='configure', platform, language)`,
  built from `environment.default_paths` (not the brace-doubled
  `engine_config`), `SQL.CONNECTION` repointed, saved to
  `config/engine_config.json`. `SUPPORTPATH` must hold data (Windows falls
  back to sibling `..\data`; macOS needs `*TransRules.sz`). Re-source the
  env script.
- Step 8a, seed: `sdk_guide(topic='configure')` without `data_sources` gives
  `init_default_config`, with them `register_data_sources` (chosen by
  `source_path`); confirm a default config id. 8a.1 re-measures the license
  as authoritative, saying any change aloud.
- Step 9: from `generate_scaffold(workflow='initialize')`, run the snippet
  that calls an engine method (chosen by shape, not count or name).

Completion runs `bootcamp-onboarding/module-completion.md` (Module 2 recap
in `docs/bootcamp_recap.md`), asks the transition question naming the next
selected module, and sets `current_step` to null.

### 5.10 `plugins/senzing-bootcamp/skills/module-03-system-verification/`

System verification (`system_verification`) proves the Module 2 install end
to end on synthetic records. Files: `SKILL.md` (start apparatus, error
routing, resume from `current_step`), `phase1-verification.md` (steps 1-8),
`phase2-report-close.md` (steps 9-11). Code is in `programming_language`
from `config/bootcamp_preferences.yaml`; artifacts go in
`src/system_verification/`; no SQL against `database/G2C.db`. Every step is
non-yielding: the only 👉 is the closing transition, so progress is written
once per turn. Each check lands in `module_3_verification.checks`.

- Opt-out ("skip verification"): write `module_3_verification` status
  `skipped`, reason `bootcamper_opted_out`; warn; gate 3→4 `skipped`.
- 1 `mcp_connectivity`: `get_capabilities` (10 s, never `search_docs`), one
  retry, then troubleshooting; block until "retry" passes.
- 1a `engine_initialization`: init and release an engine from the
  `generate_scaffold(workflow='initialize')` code; stop on failure. No SENZ
  code means an unsourced env script; `SENZ2027`/`SENZ7426` point to Module
  2 Step 8's SUPPORTPATH check.
- 2: write 4 or more `VERIFY` records to `verification_data.jsonl`: a 2-3
  record merge cluster (identical names, DOB, address and feature set; only
  formatting varies) plus a singleton distractor. Records `synthetic_data`
  (`expected_entities`, `expected_merge_record_count`).
- 3 `sdk_initialization`: fetch the scaffold's `raw_url` (`git clone`
  fallback, never `inline=true`), save `verify_init.<ext>`, run (30 s).
- 4 `code_generation`: from `full_pipeline` pick the loader that reads an
  input file, repoint it, save `verify_pipeline.<ext>`. A missing JSON
  library (Java `javax.json`) is swapped, SDK calls untouched, noted in the
  header.
- 5 `build_compilation`: per-language build (120 s).
- 5a `data_source_registration`: `sdk_guide(topic='configure')` code
  `register_data_sources.<ext>` registers the codes present and sets the
  default config, re-runnable (60 s); codes go to `config/data_sources.yaml`.
- 6 `data_loading`: run the pipeline (120 s); counts must match.
- 7 `results_validation`: entity count, cluster merged, distractor alone.
  On mismatch ask `why_records`/`why_entities`: explained gives
  `expectation_mismatch` plus `engine_explanation`, else `failed`.
- 8 `database_operations`: write count, read by id, attribute search (30 s).
- 9: module `status` and banner use the eight install checks only; results
  validation is reported on its own line and never as a failure. Persists
  `timestamp`, `status`, `checks`, `fix_instructions`; failure means re-run.
- 10: purge `VERIFY` records via SDK code; keep the files.
- 11: add `system_verification` to `modules_completed`, gate 3→4
  `completed`, append `## System verification — {timestamp}` to
  `docs/bootcamp_recap.md`, B-roll, 👉 transition to `truthset_visualization`
  if selected, else Data collection.

Timeouts kill the process, record a fail and continue; SENZ codes go to
`explain_error_code`.

### 5.11 `plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/`

Truth Set visualization (`truthset_visualization`) runs after System
verification when selected (always in Core) and serves the Senzing Truth Set
as an interactive D3 app. Files: `SKILL.md`, `phase1-visualization.md`
(steps 1-2), `phase2-close.md` (steps 3-5), `visualization-api-reference.md`
(the server contract for any language).

- Start: set `current_module`; standard module-start apparatus.
- 1.1: `get_sample_data(dataset='list')`, then `dataset='truthset'`,
  `source='list'` for codes and counts. Per-source calls are previews, so
  download `citation.download_url` (fallback `source_download_url`; on 403
  switch back), back off on 429, stop on a count mismatch. Writes
  `src/system_verification/truthset_data.jsonl` (`mcp_primary`). Fallback
  `senzing_truthset_demo` in `config/fallback_sources.yaml`
  (`github_fallback`); else a 👉 offer of CORD (`cord_substitute`).
- 1.2: register the codes present, then load with generated code.
- 2.1: Python runs `scripts/senzing_viz_server.py`; other languages
  generate a server in `src/server/` and never run the reference.
- 2.2: snapshot first: `--records`, `--title`, `--dataset`, `--snapshot`
  set to `docs/visualizations/truthset_verification.html`, `--no-serve`.
  Run the encoding self-check (legend combination rows must equal
  `encoding_check.combination_keys`; fix before capture; report
  `not_exercised` as such, a warning sign here). Screenshots: run
  `scripts/capture_screenshots.py` with `--url` pointing at the bound
  localhost port, `--name truthset_verification`, `--tabs all`, `--query`.
  Non-blocking, skipped only on its exit code.
- 2.3: source the env on its own line, background with plain `&` (no
  `nohup`), port 8080 or a free one; record pid and port.
- 2.4: probe every endpoint (10 s); zero entities fails. 2.4b: any change
  means rebuilding the snapshot. 2.5: URL, snapshot path, tour, then 👉
  "ready to continue?", which never authorizes teardown. Writes
  `truthset_visualization.checks` `web_service` (port, pid) and `web_page`
  (url, snapshot).
- Gate: both checks passed, snapshot non-empty, its `id="tab-<name>"` set
  matches the live app (zero counts are a broken check); else redo 1-2.
- 4: after stating consequences, ask 👉 "Ready for me to stop the
  visualization server and clean up the Truth Set data?" On yes: rebuild a
  stale snapshot, capture missing screenshots, kill by pid (never
  `pkill -f`; port lookup fallback; in Docker `sh -c 'kill'` and a
  `python3` probe), confirm the port free in 5 s, then purge last.
- 5: record after `system_verification`, recap section with
  `visualizations/…` images, B-roll, 👉 transition.

Contract:

- Endpoints `/api/stats` (counts, `histogram`, `bucket_entities`,
  `sample_entities`, nonce), `/api/graph` (`total`, `capped`,
  `related_total`, `encoding_check`; `relationship_type` one of
  `possibly_same`, `possibly_related`, `disclosed`, `ambiguous`),
  `/api/merges`, `/api/records`, `/api/search` (`NAME_FULL` then
  `NAME_ORG`, `attributes_tried`; top 10 get `match_keys`,
  `feature_scores`, `resolution_rules`, `enrichment_error`), `/api/why`
  and `/api/how` (raw SDK JSON; errors as HTTP 200), `/api/overlap`
  (`cell_entities`), `/api/matchkeys` (`match_key_entities`),
  `/api/features` (40-entity `why_records` sample); no `/api/dashboard`.
- Six tabs in order `graph`, `stats`, `matchkeys`, `features`, `overlap`,
  `probe`; idempotent `activate()`, `?tab=`/`?q=`, `?capture=1`,
  `data-graph-settled`.
- Records/Why?/How? everywhere; drill-downs; source-set colors; labels off
  above about 150 nodes; relationship mode default above 400 entities;
  inlined D3 or refuse; escaping; `127.0.0.1` bind; snapshot lacks
  why/how/search.

### 5.12 `plugins/senzing-bootcamp/skills/module-04-data-collection/`

`SKILL.md` ("Data collection") collects each source into `data/raw/`,
registers it in `config/data_sources.yaml`, and holds the single
license-key gate. It starts from `config/bootcamp_progress.json` with the
standard banner set. A `collection_return` instead runs only Step 2's
receiving branch.

- **License framing.** Every capacity decision, including how many records
  to generate, reads `license_record_limit` and
  `license_record_limit_measured_at`.
  - A provisional, unmarked or absent value is re-measured by Step 8a
    sub-step 7. Absent means "never measured", not "no custom license".
  - `0` means there is no cap.
  - Only a failed measurement falls back to the evaluation license, whose
    size comes from MCP and is stated as an assumption.
  - Oversize is a choice between expanding capacity and sampling.
  - With two or more sources, samples keep whole cross-source overlap
    groups first. Never take a random slice.
- **Step 2 guard.** The `🤖 Bootcamp-generated business case` marker in
  `docs/business_problem.md` means nothing is asked.
  - `cord` sources are fetched.
  - `synthesized` sources are generated from the recorded scenario. They
    carry the promised shape differences and describe shape only. Quality
    gaps: one source in the 70-79 band (30-43% of slots empty), off-pattern
    values in each source, one source at 80 or above. Keys are never
    gapped, and identifiers are unique per entity unless listed in
    `quality_intent.shared_features`.
  - The generated data is self-scored with Module 5's formula and
    regenerated on a band miss or an identifier collision. The result goes
    to `quality_intent` (`target_band`, `gaps`, `shared_features`,
    `measured_score`).
- **No provenance.** A pinned five-option question: upload, URL or path,
  database, API, or generate. Generate recommends CORD
  (`get_sample_data(dataset='list')`) and states that it is real data, then
  falls back to the free-data repo, then synthesized data. Inputs are saved
  as `data/raw/<name>.<ext>` or `_sample` files and documented without
  secrets.
- **CORD fetch integrity.**
  - Prefer `download_url` (capped) over `source_download_url`.
  - Check the HTTP status: retry a 429 with backoff, switch URLs on a 403.
  - Match the counted records to `record_count`, or to the cap for a capped
    fetch; the cap is read from `download_url_max_records`, never stated.
  - A source listed with `truncated: true` has a capped `record_count`: an
    uncapped fetch must hold at least that many, a capped one exactly
    `min(record_count, download_url_max_records)`. One anchored rule
    (`#truncated-cord-source`) states this; every reader of
    `expected_record_count` links it.
  - Stage in `data/temp/`, then move to `data/raw/`.
- **Registry fields.** `name`, `file_path`, `format`, `record_count`
  (measured), `expected_record_count`, `truncated` (only for a truncated
  CORD source), `file_size_bytes`, `quality_score`,
  `mapping_status: pending`, `load_status: not_loaded`,
  `validation_status`, `validation_checks`, `provenance`
  (`cord|own|free_data|synthesized|unknown`), `added_at` and `updated_at`.
  The optional `sample: {file_path, record_count, strategy, reason}` never
  touches the top-level counts. A CORD snapshot goes to
  `config/cord_metadata.yaml`.
- **Steps 3-8.** Verify the files. Write `docs/data_collection_checklist.md`
  and `docs/data_source_locations.md`. Give a privacy note, make
  `.gitignore` cover `data/raw/*`, and write `docs/security_compliance.md`.
  Sample on request into `data/samples/`, then require
  `validation_status: passed`.
- **Step 8a license gate.** Skipped when `license: custom` is set
  (`config/bootcamp_preferences.yaml`) or the total fits the limit.
  Otherwise `get_capabilities` chooses between a pinned four-option form
  and a three-option form; the fourth option is an in-flow request through
  `submit_feedback`.
  - A key is written to `licenses/g2.lic` and added as
    `PIPELINE.LICENSEFILE`, with `license: custom` recorded.
  - An in-flow request asks for first name, work email and `how_heard`, one
    per turn, then asks a pinned consent question. Only a send writes
    `license_key_requested {channel, date}`. Otherwise
    `license: evaluation`.
  - The limit is measured with a scaffold calling `SzProduct` get-license
    and saved to `config/license.json`, writing `license_record_limit` and
    its marker.
  - Afterwards, clear `license_guidance_deferred`.
- **Step 8b SQLite heads-up.**
  `loadable = min(collected, effective_limit)`. Warn only for
  `database_type: sqlite` above the MCP threshold from Module 6 Phase A
  item 3, with timing from
  `search_docs(query='hardware sizing capacity planning')`. The pinned
  question offers load, sample (dropped if the license already caps) or
  switch database. The answer is written to `sqlite_load_time_prompt` with
  `decided`, `choice`, `loadable`, `collected_total` and `effective_limit`.
- **Close.** Each step writes `current_step`; steps with no question share
  one write at the end of the turn. Step 9 runs Module Completion and asks
  the pinned transition question, but not on a return. A return
  regenerates a `synthesized` source to `>=80` as
  `<source>-regenerated.<ext>`, keeping its `RECORD_ID`s, or asks the
  provision question for `own` or `unknown`.

### 5.13 `plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/`

"Data Quality, Mapping, and Transformation". `SKILL.md` routes to
`phase1-quality-assessment.md` (steps 1-7), `phase2-data-mapping.md`
(8-20) and the optional `phase3-test-load.md` (21-25). Non-Latin guidance
uses `search_docs(..., category='globalization')`. A `quality_iteration`
skips the banner and goes straight to Phase 2. A legacy `current_step` 26
means the module is complete: only the transition question is asked.

- **Steps 1-5.** Take the sources from the registry. Verify files and
  counts, asking only if one is missing.
  - `download_resource` for `senzing_entity_specification.md` returns a URL
    listing. Fetch it into `docs/reference/` and check `size_bytes`. The
    fallback is `inline=true` chunks, checked against `total_chars` (in
    bytes). Look up attributes as needed rather than reading the whole
    file.
  - Compare the fields with the spec, then sort each source as compliant,
    needs mapping or needs enrichment.
- **Step 5a (CORD only).**
  - Loadable means a `FEATURES` array or legacy flat attributes, checked on
    up to 100 records.
  - Root keys, and the keys inside root arrays, are sorted into structural,
    spec attributes (label prefixes allowed) and unrecognized.
  - The pinned fast-path offer appears only with zero unrecognized keys and
    zero type/name candidates. Accepting sets `fast_pathed: true` and
    `mapping_status: complete` and writes a lineage entry to
    `docs/mapping/data_lineage.yaml`.
  - The registry gets `senzing_loadable`, `fully_mapped` and
    `unmapped_fields`.
  - If every source fast-paths, a pinned question offers a raw source to
    practice mapping on.
- **Step 6 score.** 0.70 times completeness, plus 0.25 times
  format consistency, plus 0.05 times (100 minus the duplicate rate).
  - Completeness is per record over fields applicable to its
    `RECORD_TYPE`: fields with a spec counterpart or a disposition, plus
    keys. An empty denominator is undefined (needs enrichment).
  - `false` and `0` count as present; empty containers and blank strings do
    not.
  - Duplicates are counted on (`DATA_SOURCE`, `RECORD_ID`).
  - A 100%/0% per-type split blocks the score.
  - Bands are 80+, 70-79 and below 70. The score is written to
    `quality_score`.
  - Cross-source pairs are labeled `measured` or "candidate, overlap
    unmeasured".
- **Type/name check.** A PERSON record whose name ends in an organization
  suffix (LLP, LP, PLC, LIMITED, LTD, LLC, INC, CORP, CORPORATION, GMBH) is
  a candidate. The pinned retype-or-keep answer goes to
  `## Record Type Check` in `docs/mapping/{source}_mapper.md`.
- **Step 7 and the gate.** Step 7 writes `docs/data_source_evaluation.md`.
  The optional visual is a branded, offline page captured with
  `--single`.
  - 80+ asks nothing. 70-79 and below 70 ask a pinned improve-or-continue
    question, with a disclosure first for `synthesized` data.
  - 7a improves format and duplicates only, writing
    `data/raw/<source>-improved.<ext>`, re-counting, re-scoring and asking
    again.
  - 7b applies when nothing is fixable. `cord` and `free_data` get a
    statement only. Other sources get a pinned "Return to Data collection"
    option, which writes `current_step` `"7b"` and `collection_return`
    (`source`, `provenance`, `from_band`, `resume_step`, `started_at`),
    and resumes at step 6 (`synthesized`) or step 4.
- **Phase 2 setup.**
  - A `quality_iteration` with stage `remap` writes
    `data/mapping/{source}_loaded_record_ids.txt`, reruns steps 8-18 per
    named source, then sets stage `reload` and hands to Module 6.
  - Fast-pathed sources are skipped.
  - A pinned question sets `mapping_verbosity` (verbose or concise).
  - `config/mapping_state_<ds>.json` keeps state, decisions and
    `validation_rejections`, and is deleted when the source is done.
- **`mapping_workflow` contract.**
  - `start` needs `file_paths` and `data.workspace_dir='data/mapping'`.
  - The actions are `start`, `advance`, `back`, `status` and `reset`.
  - `state` is echoed back verbatim.
  - Five bad advances in a row end the run.
  - Advances: step 9 `profile_summary` (array), step 10 `master_schemas`
    and `support_schemas`, step 11 `schema_mappings`, step 15 `verdict`.
  - Bootcamp question rules override the tool's "do not ask" directives.
- **Steps 9-11.**
  - Step 9 flags more than 100 fields as dynamic keys.
  - Step 10 sends the predominant `record_type`, never `MIXED`. It declares
    an `embedded_master` via the legacy `entity_plan` (`embedded_in`,
    `RECORD_HASH`); `back` recovers a missed one. Verbose mode asks a
    pinned plan question.
  - Step 11 dispositions are feature, payload, ignore, derived and extract.
    One name field maps to `NAME_FULL`; a retype becomes a derived
    `RECORD_TYPE`.
  - Pinned questions cover a payload key that collides with a feature name
    (rename to `{KEY}_PAYLOAD`) and non-exempt cross-source feature pairs.
  - Validation: `sz_json_analyzer.py` is primary. The verbatim and routing
    checks are best-effort, and their known limitations are recorded as
    exemptions. After two unactionable rejections, a pinned three-option
    fallback question is asked.
- **Steps 12-20.**
  - Step 13 writes `src/transform/transform_<name>.<ext>`.
  - Step 14 writes `{source}_sample.jsonl` and checks it with
    `analyze_record(workspace_dir='data/mapping')`.
  - Step 15 writes `{source}_quality.jsonl`, advances with the verdict and
    offers a visual.
  - Step 16 asks a pinned next-source or loading question per band.
  - Step 17 sets `mapping_status: complete`.
  - Step 18 writes `data/senzing-ready/<name>.jsonl` (now `file_path`) and
    `transformation_lineage_<name>.md`.
  - Step 18a answers `detect_environment` with `skip` or `test_load`.
  - Step 19 moves the reports to `docs/mapping/` under source-qualified
    names and requires a mapper doc for every ready file.
  - Step 20 is the only Module Completion.
- **Phase 3.** Register the data source, then run workflow steps 6-8. ER
  stats go to `config/er_current_<ds>.json`; the first run becomes
  `er_baseline_<ds>.json`, and later runs ask a pinned accept-or-iterate
  question. Step 25 asks yes or no: yes goes to step 19, no to step 17.
  The registry gets `test_load_status` and `test_entity_count`.

### 5.14 `plugins/senzing-bootcamp/skills/module-06-data-processing/`

Module 6 builds a production-quality loader, loads every mapped source, drains
redo and validates resolution. `SKILL.md` holds the module rules and routes to
four phase files by `current_step`. A `quality_iteration` with `stage: reload`
(from Module 7 step 3b) skips the banner and all Module 6 checkpoints and runs
only Phase B's receiving branch. Rules: SENZ errors go to `explain_error_code`;
loader, redo and query code comes only from `generate_scaffold` (`add_records`,
`redo`, `query`) and `sdk_guide`; paths under `/tmp/` or `ExampleEnvironment`
become `database/G2C.db`; back up before each load; no SQL against the database;
statistics come from `reporting_guide` `evaluation` or `export`, never
`reports`.

Phase A (`phaseA-build-loading.md`, steps 1-4a):

- Pre-load: `test_load_status` per source in `config/data_sources.yaml`
  (`complete` skips the test load; otherwise one is owed at step 5).
- Step 1 asks one pinned question, production volume as four ranges mapped to
  tiers `demo` (500 or fewer), `small`, `medium`, `large`. Writes
  `production_volume` (`tier`, `raw_value`; `null` for an option reply) to
  `config/bootcamp_preferences.yaml` and echoes the chosen architecture. Free
  text stores the parsed number; unparseable text gets one follow-up, then
  defaults to `demo`. License framing appears only when the measured
  `license_record_limit` (progress file) is positive and below the dataset size;
  an absent or provisional value is measured via Module 4 Step 8a sub-step 7.
- Step 2 sets `load_status: loading`. Step 3 writes
  `src/load/load_<source>.<ext>` from `sdk_guide` with `topic='load'` and
  `record_count=<raw_value>` (threaded above 500 or when omitted); SQLite
  (`database_type`, absent treated as SQLite) serializes writes, and a header
  comment records tier and concurrency. Non-stdlib scaffold imports are fixed
  before compiling by swapping only the JSON library. The loader logs failures
  to `logs/loading_errors.json` and reports throughput.
- Step 4a registers each `DATA_SOURCE` code in the data via
  `sdk_guide(topic='configure', data_sources=[...])`, codes substituted by hand,
  as a re-runnable `src/load/register_data_sources.<ext>`, run before any load;
  the codes are recorded in the registry.
- SQLite heads-up: when the loadable total exceeds the MCP-sourced threshold and
  no `sqlite_volume_prompt` or Module 4 `sqlite_load_time_prompt` marker covers
  the load, ask proceed or migrate to PostgreSQL and record
  `sqlite_volume_prompt` `{decided, choice, loadable, tier, raw_value}`. On
  SQLite a `medium` or `large` tier also gets a one-line PostgreSQL
  recommendation.

Phase B (`phaseB-load-first-source.md`, steps 5-11):

- With 2+ sources the first is chosen by step 14's heuristics, stated and
  recorded in `docs/loading_strategy.md`. Step 5 runs an owed 10-100 record test
  load and sets `test_load_status: complete`. Step 6 explains that engine `ERR:`
  console lines are not record failures.
- Step 7 loads the source. A binding license limit asks one question: an
  overlap-preserving subset, apply a license (Module 4 Step 8a sub-step 5, then
  re-measure) or first N. Subsets write `license_cap_prompt` to preferences and
  a `load_subset:` block (`strategy`, `limit` or `file_path` and measured
  `record_count`, `reason`) to the source, files under `data/subsets/`; the
  remaining cap is measured through the SDK. An unasked SQLite case may suggest
  the first 1,000 records (`choice: "subset"`).
- Two-stage reconciliation: stage 1 compares loaded with the load input and
  alone can set `load_status: failed`; stage 2 compares the input with the
  collected `record_count` through cited `sample:`, mapping and `load_subset:`
  records, writing `validation_checks.load_count_matches_source` as `pass`,
  `expected_delta` (plus `load_reconciliation`) or `unexplained_delta` (plus
  `issues`). Baseline counts are never overwritten.
- Step 9 drains redo until fetch returns nothing (never polling the count). Step
  10 records the incremental strategy in `docs/loading_strategy.md`; step 11
  marks the source loaded; 2+ sources with `mapping_status: complete` go to
  Phase C, else Phase D.
- Receiving a `quality_iteration`: per named source, rerun Phase A only if its
  path changed, delete records missing from
  `{source_name}_loaded_record_ids.txt` via `sdk_guide(topic='delete')`, reload,
  add to `completed`; drain redo once, return to Module 7 step 3b. No Phase D,
  no completion, no checkpoint.

Phase C (`phaseC-multi-source.md`, steps 12-20, 2+ sources): inventory;
dependencies (generated sources get one yes/no for "none, Sequential"; real
sources are asked, then choose Sequential, Parallel or Hybrid); load order
(reference first, quality, density, volume); checklist;
`src/load/orchestrator.<ext>` with a per-source budget table, per-source
counters, backoff retry and error isolation; sample test; every `load_subset:`
block written before the run, not-loaded sources skipped with `load_status`
unchanged; one redo drain.

Phase D (`phaseD-validation.md`, steps 21-28):

- Spot-check entities, UAT in `docs/uat_results.md`; with 2+ sources,
  cross-source and quality checks, UAT (self-directed for a generated business
  case, else asks about business users), and `docs/results_validation.md`.
  Module 6 offers no visualization.
- Match-key audit on a `SZ_EXPORT_DEFAULT_FLAGS` export: `-` suppressors in
  single-source, cross-source and relationship buckets, reported as finding, no
  finding or could not measure, each bucket against its own denominator; a
  changed mapping is filed silently as feedback.
- How-state audit: `how_entity` on every multi-record entity, flagging
  `NEED_REEVALUATION` or several virtual entities, "checked N of M", appended as
  `## How-state audit`.
- Gate on per-record results (never the relationship bucket): 90% or better
  proceeds, below 80% recommends Module 5, 80-89% asks iterate or move on.
  `docs/stakeholder_summary_module6.md` is always written. Failed loads: restore
  the backup or resume; multi-source failures offer skip, retry or
  restore-and-restart.
- Completion runs `module-completion.md`, asks the transition question, sets
  `current_step: null` and starts Module 7.

### 5.15 `plugins/senzing-bootcamp/skills/module-07-query-visualize-discover/`

Module 7 is the last content module, required on every path and always followed
by graduation. No SQL: entity operations are generated SDK code from
`get_sdk_reference`, `sdk_guide` and `reporting_guide`. On start a
`quality_iteration` routes by `stage` to Module 5 (`remap`) or Module 6
(`reload`). Resume uses `current_step` (integer or `"3b"`-style strings) and
`module_7_query.steps`.

Phase 1 (`phase1-query-visualize.md`):

- Step 1 derives 1-10 query requirements from `docs/business_problem.md` and
  asks for adjustments, or asks what the data must answer.
- Step 2 writes programs in `src/query/` from
  `generate_scaffold(workflow='query')`, with flags and response paths looked up
  in `get_sdk_reference` (`flags`, `response_schemas`, `parameters`). Programs
  iterate over loaded record IDs via `get_entity_by_record_id` and fold on
  `(data_source, record_id)` before counting. Examples: `find_duplicates`,
  `search_entities`, `customer_360`, `query_results`.
- Step 3 runs them; 3a presents results and why output (`WHY_KEY`,
  `WHY_KEY_DETAILS`).
- Step 3b uses `reporting_guide` `quality` and `evaluation`, shows sampled
  entities as evidence, grades Acceptable (possible matches under 5%), Marginal
  (5-15%) or Poor; only a mapping-actionable Poor asks whether to go back to
  Module 5. Accepting writes `quality_iteration` (`sources`, `from_verdict`,
  `stage`, `completed`, `started_at`) and appends to
  `module_7_query.quality_iterations`; after remap and reload, 3b reruns and
  records `after`.
- Step 3c asks once for an interactive app. Accepted, it builds a server in
  `src/server/` modeled on `senzing_viz_server.py`: six tabs (Entity Graph,
  Merge Statistics, Match Keys, Feature Scores, Cross-Source, Search / Probe),
  colored by whole source set with the encoding self-check, `NAME_ORG` search
  fallback, built from the export stream, D3 copied into the project, loopback
  bind with an identity check, a snapshot
  `docs/visualizations/results_visualization.html` naming the Bootcamper's own
  sources, and screenshots (skipped only on its exit code) from
  `capture_screenshots.py --name results_visualization`. The server stays up;
  `m7_visualizations` records `offered`, `accepted`, `artifact`, `port` and
  `pid`.
- On every path it writes `docs/bootcamp_data_discoveries.md` (six named
  sections, Headline numbers through What was not found, with `**Measurement:**`
  and near-miss labels, Latin-script text) and its PDF via
  `generate_discoveries_pdf.py`, whose extracted text is checked; failure is
  reported, never blocking.
- Query Completeness Gate, then (only if a server started) a separate stop
  question that stops by recorded pid. Completion runs `module-completion.md`,
  recaps every quality iteration and offers graduation, invoking the
  `graduation` skill on yes.

Phase 2a (`phase2-discover.md`): an opt-in, separate from 3c, sets
`discover_phase` to `skipped` or `in_progress`; declining never skips the
discoveries file. 4a finds multi-record, cross-source and related entities
(`steps.4a.patterns_found`); 4b demonstrates `why_records` with
`SZ_INCLUDE_MATCH_KEY_DETAILS` plus a relations flag, 4c narrates
`how_entity` (both fall back to `FEATURE_SCORES`, both checkpoint
`entity_demonstrated`), each ending with continue-or-finish. Phase 2b
(`phase2b-discover.md`, 4d) shows `find_network` and `find_path` (hub method for
a 2+ degree pair, up to three hubs; links from `ENTITY_NETWORK_LINKS[]` or
`ENTITY_PATH_LINKS[]` with `MIN_ENTITY_ID`/`MAX_ENTITY_ID`; Python takes a list
of ints), or records `skipped`/`no_relationships`, then sets
`discover_phase` to `"completed"` and returns to the gate.

### 5.16 `plugins/senzing-bootcamp/skills/graduation/`

Terminal module (`graduation`). `database-backup.md` is the one backup
procedure, shared with `bootcamp-onboarding/packaging.md`. Every step warns
and continues; the recap PDF is guaranteed.

- Opens with the BOOTCAMP GRADUATION banner, a terminal preface and the
  model/effort nudge.
- Pre-checks read `name`, `programming_language`, `database_type`, `path`,
  `selected_modules`, `integration_targets`, `deployment_target`,
  `cloud_provider` and `modules_completed`. A missing file means asking
  language and database; a missing key is noted silently. A name unfit for
  the certificate (system account, handle, email, non-Latin-1) triggers a
  pinned question; the answer goes to `name` and the recap's
  `**Bootcamper:**` line.
- Step 0 appends self-observed `## Improvement:` entries
  (`Source: self-observed (assistant retrospective)`, `Routing:`,
  `Upstream:`) to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`, with
  one batched `submit_feedback` offer, and re-reads to verify.
- Step 1a reconciles `docs/bootcamp_recap.md`: a section per
  `modules_completed` entry, the three summary blocks, `**Completed:**`, a
  PII-free run-environment block (`sdk_version` for the SDK), any
  `docs/progress/recap_checkpoint.md` narrative, orphaned screenshots in
  tab order, capture-shortfall warnings from `<name>-tabs.json`, notes
  between `BOOTCAMP-NOTES:START/END`, then `normalize_docs_markdown.py`.
- Step 1b offers `fpdf2` in `data/temp/recap-venv/`, runs
  `generate_recap_pdf.py` and `--check --expect-modules` (semicolons),
  trusts only `PDF generated:`, falls back inline, and reports any
  verification skipped for a missing tool.
- Step 1c, optional video: on yes, `docs/video/storyboard.json` (Intro,
  preparation, modules from `docs/video/broll.json` or the recap,
  certificate, "Resolved: [Name], Senzing graduate."), per-module shares of
  120 s rescaled over modules taken, aggregates and only the
  `match-keys`/`feature-scores`/`cross-source` screenshots. It offers Piper,
  runs `generate_recap_video.py --check` and the render, handling exit 1
  (fix), 2 (offer `imageio-ffmpeg`/Pillow), 3 (skip, keep storyboard), and
  checks 2:00 plus or minus 10 s.
- Step 2 builds `production/` (asks overwrite, merge or abort): copies
  `src/transform`, `src/load`, `src/query`, `src/utils`,
  `data/senzing-ready/` and the dependency manifest; writes
  `production/config/data_sources.yaml` keeping only `version` and each
  source's `name`, `file_path`, `format`; never copies progress,
  preferences, recap, notes, `data/raw`, `data/samples`, `data/subsets`,
  `logs`, `backups`, `docs/feedback`.
- Step 3: `.env.example` (`SENZING_ENGINE_CONFIGURATION_JSON`,
  `SENZING_LICENSE_FILE`, `DATABASE_URL`, `LOG_LEVEL`),
  `docker-compose.yml` by `database_type`, `.gitignore`. Step 4:
  `production/README.md` and `production/MIGRATION_CHECKLIST.md` (six
  sections; DEFAULT-flags item with its export exception). Step 5:
  `production/GRADUATION_REPORT.md`; 5a normalizes with
  `--docs-dir production`; 5b renders `docs/business_problem.pdf` and
  `docs/data_source_evaluation.pdf` via `generate_document_pdf.py` with
  `--subtitle` and `--require-sections`.
- Step 6 writes `backups/revisit/`: the database backup (SQLite copy or
  `pg_dump -Fc -f`, never redirection), state snapshot, `RESUME_STATE.json`
  and `docs/REVISIT_BOOTCAMP.md`.
- Close: confirm the PDF, announce only existing artifacts plus a
  `/package-bootcamp` statement, ask "anything else you would like to
  explore?"; on decline set `bootcamp_complete: true` and show the END OF
  SENZING BOOTCAMP banner once.

### 5.17 `plugins/senzing-bootcamp/commands/bootcamp-feedback.md`

The `/bootcamp-feedback` command (description: give feedback about the
bootcamp, saved locally to `docs/feedback/`). It directs the guide to the
`bootcamp-onboarding` skill's `feedback.md` workflow: capture context silently,
gather the feedback one 👉 question at a time, triage whether the problem lies
in the plugin or in the Senzing MCP server, and append (never overwrite) a
formatted entry to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`,
creating it with its header when absent. Every entry is recorded locally
whatever the triage says. When the problem is in the MCP server the guide also
offers, once and after showing the exact message, to forward it with the
server's `submit_feedback` tool; nothing is sent without that yes. Afterwards
the Bootcamper is returned to where they left off.

### 5.18 `plugins/senzing-bootcamp/commands/bootcamp-note.md`

The `/bootcamp-note` command (description: jot down an idea, question,
reminder or to-do, saved locally to `docs/bootcamp_notes.md`). A note concerns
the Bootcamper's own work, not the bootcamp. The guide follows the
`bootcamp-onboarding` skill's `notes.md`: capture time, module and pending
question silently, classify the note without asking, recite it for approval,
append (never overwrite) it to `docs/bootcamp_notes.md` (creating the file with
its header when absent), and verify the entry is on disk before saying it was
saved. Elaboration or context is stored under its own label, never merged into
the Bootcamper's words. When the command carries an argument, that text is the
note and the guide does not ask for it; it asks only when invoked bare. A note
is never routed, triaged or sent anywhere; it is folded into the recap at
graduation. The Bootcamper is then returned to exactly where they left off.

### 5.19 `plugins/senzing-bootcamp/commands/graduate.md`

The `/graduate` command. It invokes the `graduation` skill: the GRADUATION
banner, the graduation preface (journey map, before/after, step overview,
estimated time), finalizing `docs/bootcamp_recap.md` and rendering
`docs/bootcamp_recap.pdf`, the optional video `docs/bootcamp_recap.mp4`, the
`production/` project, the revisit/resume bundle, the guaranteed-recap
announcement and the single closing 👉 question asking whether there is
anything else to explore. Only after the Bootcamper declines further
exploration is the terminal `END OF SENZING BOOTCAMP` banner rendered, exactly
once, as the final output (INV-057); never while exploration continues, and
graduation never ends on the closing question once the Bootcamper says they are
done. It tells the skill to pass
`${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_pdf.py` as the PDF generator.
When `config/bootcamp_progress.json` is missing it says there is no bootcamp to
graduate and offers `/start-bootcamp`.

### 5.20 `plugins/senzing-bootcamp/commands/package-bootcamp.md`

The `/package-bootcamp` command (description: package the bootcamp into one
transferable zip under `backups/packages/`; nothing is sent anywhere). The
guide follows the `bootcamp-onboarding` skill's `packaging.md`: run
`package_bootcamp.py` as a dry run first so the question quotes a measured
size, ask the one pinned numbered 👉 question about what should travel, then
run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/package_bootcamp.py"` with
`--profile share` or `--profile transfer`. `share` carries the results (recap
PDF, keepsake documents, visualizations, `production/`) with no database, no
source data and no credentials; `transfer` adds the revisit bundle, config and
mappings so the bootcamp can be resumed elsewhere. A profile given as the
command's argument does not skip the dry run or the question, because the size
and exclusions are what the Bootcamper consents to. The archive stays inside
the project; the guide reports the path, size and digest from the script's own
output, names anything excluded they might expect, and returns them to where
they left off.

### 5.21 `plugins/senzing-bootcamp/commands/start-bootcamp.md`

The `/start-bootcamp` command. It invokes the `bootcamp-onboarding` skill.
Whether it is a resume depends on what `config/bootcamp_progress.json`
contains, not whether it exists:

- No file: start onboarding from the beginning.
- A file recording no module (empty, `{}`, malformed, or `current_module` null
  or blank): also start from the beginning, silently, because this is the
  normal state between the preface's project setup and Bootcamp preparation's
  final write, not a corruption to report.
- A file with a `current_module`: resume from that module.

### 5.22 `plugins/senzing-bootcamp/scripts/brand_tokens.py`

Library module (no CLI) holding the Senzing "Obsidian & Ember" brand tokens:
palettes, ember accents, `SIGNAL_GREEN` (reserved for live/resolved states,
never a data-source color), text colors, `FONT_STACK`, `CODE_FONT_STACK` and
`PDF_FONT` (`Helvetica`; no web font is imported). `senzing_viz_server.py`,
`generate_recap_pdf.py` and `generate_discoveries_pdf.py` import it and keep
inlined fallback copies that tests pin equal.

- `color_for_sources` sorts and de-duplicates the source codes present and
  returns, per code, `fill`, `stroke`, `stroke_width` (None when no stroke
  is drawn) and `cycle`. Codes in `SOURCE_COLORS` keep their preferred fill;
  others take unclaimed `FALLBACK_COLORS`, then widen by stroke state and
  then by a `shade_fill` lightness shade, up to `SOURCE_ENCODING_CAPACITY`.
  Beyond capacity it issues a warning and repeats appearances.
- `hex_to_rgb` converts `#RRGGBB` to an integer triple for fpdf2.

### 5.23 `plugins/senzing-bootcamp/scripts/capture_screenshots.py`

Best-effort, dependency-optional helper that renders a local visualization
to one PNG per tab for the graduation recap. It never touches the network:
targets must be local files or `localhost`, `127.0.0.1` or `::1` URLs
(`_is_local_target`).

- CLI: exactly one of `--html <file>` or `--url <url>`; `--out-dir`
  (default `docs/visualizations`); `--name` (default `visualization`);
  `--tabs` (list or `all`; omitted means `DEFAULT_TABS`); `--single` (whole
  page as one image, `{name}.png`); `--query` (Search / Probe text, needs
  `--url`).
- Tabs come from `TABS`; `RESERVED_TABS` are accepted with a stderr note
  for old snapshots. Files are named by `_out_path`. For `--url`,
  `_tab_url` adds `tab`, `capture=1` and (probe only) `q`; for `--html`,
  `_snapshot_copy` injects an `activate(<id>)` call (falling back to
  clicking `#navbtn-<id>`) into a temp sibling that is always deleted.
  Other paths use `_with_capture`.
- Pre-flights on the page source (unreadable source passes every check):
  `_tabs_present` skips tabs with no `tab-<id>` section; `_tabs_applicable`
  with `_page_stats` and `_APPLICABILITY` skips tabs the app suppresses; a
  page with no tab controls (`_has_tab_controls`) falls back to single-page
  capture; for `--url`, `_supports_deep_linking` must pass.
- Backends in `_BACKENDS` order (Playwright, Selenium, Chrome/Chromium/Edge
  CLI found by `_chrome_exe`, `wkhtmltoimage`); the first that works is
  reused for later tabs, and if none works on the first tab capture stops.
  Animated tabs wait for `data-graph-settled="1"` and record `settled`,
  `unsettled`, `unknown` or `n/a`; unsettled and unknown are reported.
  Single-page height is measured (`_measure_chrome_cli` for the CLI),
  clamped at `_MAX_FULL_PAGE_PX`, and labeled by `_single_page_label`.
- Byte-identical captures (`_identical_groups`) are all deleted and
  reported.
- `write_manifest` writes `<name>-tabs.json` (`MANIFEST_SCHEMA`) listing
  requested, captured, not-present, not-applicable and failed tabs, merged
  per tab into a valid prior manifest (`_merge_manifest`); a bad prior is
  overwritten and a write failure only warns.
- Stdout: one `<png path>` TAB `<label>` line per image; a partial run
  adds `Captured N/M tabs` on stderr.

Exit codes:

- 0: at least one PNG written, no duplicates.
- 1: bad arguments (`--single` with `--tabs`, unknown tab, empty tab list,
  `--query` without `--url`, non-local target, missing HTML file), a live
  server without `?tab=` deep-linking (all tabs recorded as failed), or
  duplicates deleted.
- 2: nothing to capture (all requested tabs absent or inapplicable;
  manifest still written) or no backend wrote an image; the message says
  whether no browser was found (listing paths searched) or one was found
  but failed. Callers treat 2 as "keep the HTML link".

### 5.24 `plugins/senzing-bootcamp/scripts/checkpoint-tick.py`

`UserPromptSubmit` hook. Reads and discards stdin; exits 0 silently unless
`recap_checkpoint.bootcamp_active`. It then calls `ensure_checkpoint`, and
only on the turn that creates the file prints a `hookSpecificOutput` JSON
object whose `additionalContext` tells the guide to keep
`docs/progress/recap_checkpoint.md` current between its markers at each step
boundary, to clear it at module completion, and not to mention it. Always
exits 0.

### 5.25 `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`

Library module for `session-start.py` and `session-end.py`, and the command
line Module 2 runs before it creates a container (#461). Importing it runs
nothing. Containers the bootcamp starts are listed in `config/bootcamp_progress.json`
under `docker_containers`; an entry has a `name` and a `runtime`, and a bare
string or missing `runtime` means `docker`.

- `tracked_containers` returns normalized entries, or an empty list when the
  file or key is absent, unreadable or not a list.
- `runtime_cli` returns a CLI path only for a runtime in `KNOWN_RUNTIMES`
  (docker, podman, Apple `container`) whose CLI is on `PATH`, else None.
- `stop_started_containers` runs `<cli> stop <name>` (never remove) per
  entry with an available CLI, via `_run` (30-second timeout, never raises),
  and returns the names stopped.
- `resume_summary` returns one paragraph per runtime listing each container
  with its state (`running`, `stopped`, `missing`, or `unknown` when not in
  `STATE_PROBE_RUNTIMES` or the probe fails) or noting the CLI is missing,
  and asks the guide to offer restart or regeneration; empty string when
  nothing is recorded.
- `derived_container_name` returns `<base>-<slug>-<hash6>` for the working
  directory or `project_dir`. `project_slug` is the real path's basename,
  lowercased, each run outside `[a-z0-9_.-]` made `-`, `-_.` stripped from both
  ends, then cut to `SLUG_MAX` (32), or `project` when empty. `project_hash6`
  is the first 6 hex characters of SHA-256 over the normcased real path. A
  base outside `NAME_CHARSET` raises `ValueError`.
- `container_name` walks the derived name, then `-2` … `-9`, and returns
  `(name, how)`: a name `docker_containers` records is `recorded`; otherwise
  `_container_state` decides, `missing` giving `free`, `unknown` giving
  `unprobed`, and `running` or `stopped` moving on. All taken returns
  `(None, "exhausted")`. Its only container command is the `ps` probe.
- `free_port` returns the preferred port, or the first of the next
  `PORT_SPAN` (99) that `_can_bind` binds on `127.0.0.1` without
  `SO_REUSEADDR`, else None.
- `main` runs `container-name` and `free-port`, printing the name or port.
  Exit 0 when printed (an unprobed name adds a note on stderr); 1 when every
  candidate or port is taken, with a message on stderr; 2 for a base outside
  the charset or no subcommand (argparse usage errors also exit 2).

### 5.26 `plugins/senzing-bootcamp/scripts/feedback-capture.py`

`UserPromptSubmit` hook. Reads the stdin JSON's `prompt` (the raw payload if
not JSON), lower-cased. Exits 0 silently unless
`config/bootcamp_progress.json` exists. The first matching regex of
`FEEDBACK`, `NOTE`, `VERBOSITY` decides the `additionalContext` it prints in a
`hookSpecificOutput` object; no match prints nothing. Always exits 0.

- `FEEDBACK` matches requests to give feedback, or fault words only when
  they name the bootcamp, plugin, tutorial or a module; a bare "I found a
  bug" does not match. The context directs the `feedback.md` workflow
  (banners, silent context capture including the version from
  `plugin_version`, which reads the hook's own `.claude-plugin/plugin.json`
  or yields `Unknown`; append to
  `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` and verify; routing
  verdict; offer `submit_feedback` once only for an MCP-server verdict).
- `NOTE` matches only an imperative to record (make a note, remind me,
  remember to ...), never a bare "remember" or "note that". The context
  directs the `notes.md` workflow: append to `docs/bootcamp_notes.md`,
  verify, never send anywhere, re-present the pending question.
- `VERBOSITY` matches requests for more or less detail; the context says to
  update `config/bootcamp_preferences.yaml`, confirm in one sentence and
  continue.

### 5.27 `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`

CLI rendering a Markdown document as a house-style PDF, by default
`DEFAULT_INPUT` to `DEFAULT_OUTPUT`. It imports the PDF plumbing (such as
`_write_pdf`, `_safe`, `dropped_character_warning`) from
`generate_recap_pdf.py` beside it, and the palette from `brand_tokens.py`,
falling back to `_FALLBACK_RGB` with a stderr note.

- Options: `--input`, `--output`, `--check` (audit only),
  `--require-sections` (semicolon-separated, replacing `REQUIRED_SECTIONS`),
  `--no-section-check`, `--subtitle` (default `COVER_SUBTITLE`). `main`
  accepts a `description` for the alias's help text.
- `parse_discoveries` reads the H1 title, preamble `**Key:** value` meta,
  H2/H3, two levels of bullets, `**Label:**` paragraphs, verbatim code,
  pipe tables (one block per table) and paragraphs.
- `audit_discoveries` is fatal when there are no blocks, no headings, none
  of a non-empty required list among the H2/H3 headings (matched via
  `_normalize`), or retention below `MIN_CONTENT_RETENTION` (0.60); missing
  only some sections is a warning.
- Renders with fpdf2 (cover, ember headings, real table grids with the
  header repeated on page breaks, `_NEW_LINE_LABELS` on their own line,
  gaps per `_needs_item_gap`), falling back to a stdlib writer with
  monospace tables when fpdf2 is absent or fails.
- Exit codes: 0 after printing `PDF generated:` with renderer and retention
  (dropped-character warning first, on stderr), or an `OK:` line with
  `--check`. 1 when `--require-sections` names nothing, the input is missing
  or not UTF-8, the audit is fatal (no PDF written), or both renderers
  fail. 2 when the shared helpers cannot be imported.

### 5.28 `plugins/senzing-bootcamp/scripts/generate_document_pdf.py`

Alias for `generate_discoveries_pdf.py` (a general renderer, not renamed
because skills, specs and tests name it). It imports that `main` and calls
it with this file's first docstring line as the help description. Callers
should pass `--subtitle` and `--require-sections`. Exit codes are those of
the wrapped `main`, plus 2 when the import fails.

### 5.29 `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`

Renders `DEFAULT_INPUT` (`docs/bootcamp_recap.md`) into `DEFAULT_OUTPUT`
(`docs/bootcamp_recap.pdf`). Flags: `--input`, `--output`, `--preferences`
(default `config/bootcamp_preferences.yaml`), `--check`, `--expect-modules`
(semicolon-separated), `--progress` (default
`config/bootcamp_progress.json`), `--expect-visualizations`
(comma-separated, overrides `--progress`). Optional imports: `fpdf2` (with
Pillow) and `brand_tokens`.

- `parse_recap` lifts the BOOTCAMP-NOTES fence into a `NotesSection` and
  drops `DISCARDED_FENCES`, unless that would leave no `##` heading. A
  stray START is skipped, never paired (`_fence_spans`). An unterminated
  notes fence runs to end of text; an unterminated checkpoint fence stays.
  Each `##` becomes a `ModuleSection` (`_split_title_date` splits off a
  timestamp or `in progress`). Body text survives only under `###`
  headings.
- `audit_recap` builds on `verify_recap`: `REQUIRED_SECTIONS`,
  `END_SUMMARY_BLOCKS` (via `_summary_block_label`; legacy `Journal` is
  exempt), duplicate modules and `--expect-modules` gaps. Fatal: no `##`
  sections, no recognized sub-section anywhere, or retention below
  `MIN_CONTENT_RETENTION`. Warnings: incomplete sections, leftover
  checkpoint markers, stray fences.
- Images (`IMAGE_LINE_RE`) resolve against the recap's directory, then the
  cwd; a bullet marker before one is allowed. URLs are never fetched.
  Each non-embedded image is reported once on stderr.
- Tab coverage reads the `*-tabs.json` manifests next to the images
  (`find_tab_manifests`; an unreadable one is reported and skipped):
  - `tab_coverage_problems`: captured tabs the recap never references.
  - `manifest_undercount_problems`: a manifest listing fewer captures than
    the `<name>-*.png` files beside it.
  - `missing_visualization_reports`: a visualization that
    `MODULE_VISUALIZATIONS` says a module in `modules_completed` owes, but
    which has no manifest.
- `render_with_fpdf2` renders twice for exact contents page numbers: a
  cover (`senzing_logo_light.png`, else a drawn ring), contents, one page
  per module (four sub-sections, then any extras), notes, and a landscape
  certificate (`_CERT_*` geometry). A missing summary block prints
  "(not recorded)", and tables become grids (aligned monospace as a last
  resort). Bullets are spaced apart before each top-level bullet. If fpdf2
  is missing or fails, it falls back to the stdlib renderer.
- `_cert_fields` picks the name: preferences `name:` first, then the
  recap's, else `CERTIFICATE_NAME_PLACEHOLDER`. It prefers the completed
  date. `_cert_citation` states the module count. The module list is fit
  to `_CERT_MODULE_LINES`. A plugin-version colophon appears only when one
  is recorded (`_cert_attribution`).
- Fallback `render_with_stdlib`: a hand-written PDF with the same content
  and certificate, no images, tables as monospace columns.
- `_safe` maps `_UNICODE_MAP`, then `_fold_to_latin1`; anything else is
  dropped, never `?`. `dropped_character_warning` reports the drops, except
  `_EXPECTED_DROP_PASSAGE`.
- Palette from `brand_tokens`, else `_FALLBACK_RGB`; stderr names the
  failure.

Stderr also notes when fpdf2 is unusable, when the preferences name
differs from the recap's, and when the certificate name is missing or
unprintable. Exit codes:

- 0: `--check` passed (`Recap complete: ...`; a visualization with no
  manifest is `SKIPPED:` and withholds the coverage figure), or the PDF was
  written, printing a `PDF generated:` line with the path, renderer,
  retention, embedded image count and tab coverage.
- 1: input missing or not UTF-8; `--check` problems (`INCOMPLETE:`
  lines); a fatal audit (`ERROR: refusing to render`, no PDF); or both
  renderers failed.

### 5.30 `plugins/senzing-bootcamp/scripts/generate_recap_video.py`

Renders `DEFAULT_STORYBOARD` (`docs/video/storyboard.json`) into
`DEFAULT_OUTPUT` (`docs/bootcamp_recap.mp4`): H.264/AAC mp4, `yuv420p`,
1920x1080 at 30 fps. Flags: `--storyboard`, `--output`, `--project-root`
(default `.`), `--voice-model`, `--no-voice`, `--check`, `--schema`. Fully
offline (`NETWORK_MODULES` are never imported).

- `SCENE_TYPES` is the one table that drives both validation and drawing.
  Scene types are `title_card`, `image`, `counter`, `mapping`, `loading`,
  `entity_merge`, `certificate` and `tag_line`; fields are `FieldSpec`
  objects, plus `VIDEO_FIELDS` and `COMMON_FIELDS`. `validate_storyboard`
  names each problem's field path. Keys starting with `_` are ignored;
  other unknown keys are errors. Durations must be at most
  `MAX_SCENE_SECONDS`, `counter`/`mapping` take at most 8 items, and
  `entities` may not exceed `records`. `project_relative_problem` rejects URLs,
  absolute paths and paths outside the project.
- Voice: `find_piper_voice` (Piper run as a subprocess; the model defaults
  to `DEFAULT_VOICE_MODEL`, and its `.onnx.json` is required).
  `voice_with_piper` voices all scenes (`spell_numbers`) or none; otherwise
  `find_speech_engine` tries `say`, Windows SAPI, then
  `espeak-ng`/`espeak`. If Piper fails on any scene, the platform engine
  re-voices every scene, so two voices are never mixed. A scene the
  platform engine fails on is silent.
- `plan_timeline`: a missing or unreadable image becomes a title card. A
  scene lasts max(planned, narration plus lead and tail); without a voice,
  narration time is estimated at `WORDS_PER_MINUTE`. Each extension prints
  `OVERRUN:`. Captions (the narration by default) are always burned in,
  two lines per screen, paced by word count.
- `certificate_fields` reuses `generate_recap_pdf`'s parser and `_cert_*`
  helpers, so its name, date and modules match the PDF's. With no readable
  recap it uses the storyboard's name, date and `modules`, and says so.
- Audio: narration WAV and the `synthesize_music_bed` bed (unless
  `video.music` is false), mixed by `audio_filter_graph`: `LEVELER` on the
  voice, then `DUCKING`, then `LOUDNORM`. Fonts come from
  `_FONT_CANDIDATES`, else Pillow's built-in font; the palette comes from
  `brand_tokens`, else `_FALLBACK_RGB`.
- Frames go through ffmpeg's stdin (`encode_command`). `find_ffmpeg` uses
  `PATH` when it has libx264, aac, `sidechaincompress` and `loudnorm`,
  else `imageio-ffmpeg`. Output goes to a `.partial` file that
  replaces the target only on success. Each fallback is printed once on
  stderr as `FALLBACK:`.

Exit codes (nothing is written unless 0):

- 0 `EXIT_RENDERED`: `--schema` JSON printed, `--check` valid, or the
  video rendered (`Video generated:`, `Duration:`, `Voice:`, `Music:`).
- 1 `EXIT_INVALID_STORYBOARD`: missing, non-UTF-8, invalid JSON or failed
  validation (`INVALID:` lines).
- 2 `EXIT_MISSING_CAPABILITY`: no usable Pillow or ffmpeg.
- 3 `EXIT_RENDER_FAILED`: ffmpeg failed, the pipe broke, or the render
  raised.

### 5.31 `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`

CLI run at graduation before the recap PDF. Options: `--docs-dir` (default
`docs`; only top-level `*.md`, so `docs/feedback/` is never touched) and
`--dry-run`.

- `normalize_text` applies, outside fences: blank lines around headings,
  fences and whole lists or tables, a `DEFAULT_FENCE_LANG` info string on
  bare opening fences, `**Label:**` colon spacing, trailing-space removal,
  collapsed blank runs and one final newline.
- Guard: if `_signatures_compatible` finds any change in `_signature` other
  than a fence gaining an info string, the original is kept and reported on
  stderr ("skipped").
- `mojibake_lines` warns on stderr, never repairs, about lines that
  round-trip from Windows-1252 to different valid UTF-8.
- Unreadable or unwritable files are reported and left untouched. Prints a
  summary of the files (to be) normalized.
- Exit codes: 0 when finished, even with skipped or failed files; 1 when
  the docs directory does not exist.

### 5.32 `plugins/senzing-bootcamp/scripts/package_bootcamp.py`

CLI packaging the project into one zip; it never transmits it. Options:
`--profile` (`share` or `transfer`, required), `--project-root` (default
`.`), `--date` (YYYYMMDD, default today UTC), `--dry-run`, `--output`
(default `backups/packages/senzing-bootcamp-<profile>-<date>.zip`).

- Roots: `SHARE_INCLUDE` (`docs`, `production`), plus `TRANSFER_EXTRA`
  (`backups/revisit`, `config`, `src`) for `transfer`. Missing roots are
  recorded as excluded.
- `is_excluded` matches path segments against `ALWAYS_EXCLUDE` (credentials,
  licenses, raw and temp data, logs, `.git`, caches, virtualenvs,
  `backups/packages`) and, for `share`, `SHARE_EXCLUDE` and
  `DATABASE_SUFFIXES`.
- Files resolving outside the project are excluded. Every other file is
  scanned by `_scan` with `find_secret` (in overlapping blocks, any
  extension); a match excludes it with the class named, and an unreadable
  file (`UNEXAMINED`) is excluded too. If `secret_patterns` cannot be
  imported, every file counts as a secret.
- `build_manifest` records profile, date, `plugin_version`,
  `modules_completed`, root directory (`ROOT_PREFIX`), each file's size and
  SHA-256, total size, rules applied and every exclusion with its reason.
  `open_me_first` writes `OPEN_ME_FIRST.md` built only from the manifest's
  included list.
- `--dry-run` prints the manifest on stdout and a size summary on stderr
  (warning above `SIZE_WARN_BYTES`) and writes nothing.
- Otherwise it writes the manifest, `OPEN_ME_FIRST.md` and members under
  one top-level directory, re-opens the zip with `testzip`, checks the
  single top-level directory, writes a `.sha256` sidecar and prints a
  summary.
- Exit codes: 0 on success or dry run; 1 when the project root is not a
  directory, nothing qualifies, `testzip` fails or the archive has several
  top-level directories (the last two delete the archive).

### 5.33 `plugins/senzing-bootcamp/scripts/precompact-recap.py`

`PreCompact` hook. When `recap_checkpoint.bootcamp_active` it calls
`fold_checkpoint` and prints a plain-text reminder to keep the checkpoint
current. Otherwise silent. Always exits 0.

### 5.34 `plugins/senzing-bootcamp/scripts/recap_checkpoint.py`

Library module (no CLI) for four hooks. Paths are relative to the working
directory: `CHECKPOINT`, `RECAP`, `PROGRESS`; markers `START`, `END` and
`SCAFFOLD`. Status lines go to stderr (prefix `recap-checkpoint:`), never
stdout.

- `bootcamp_active` is true only when `current_module` finds a non-empty
  `current_module` in the progress file, so the empty file written during
  onboarding is not active. Neither raises.
- `checkpoint_state` returns `missing`, `unreadable` (not UTF-8, via
  `UNREADABLE`), `scaffold` or `filled`.
- `ensure_checkpoint` creates the scaffold file when absent and returns
  True only then; a failure is reported, not raised.
- `fold_checkpoint` refuses (False, nothing written) when the checkpoint is
  missing, a scaffold, or not UTF-8, or when the recap is not UTF-8.
  Otherwise it strips guidance comments, fences the block, removes any
  earlier marker block from the recap, appends the new one (creating files
  as needed) and returns True. Folds never duplicate and never rewrite
  completed sections; a write failure returns False.

### 5.35 `plugins/senzing-bootcamp/scripts/secret_patterns.py`

Library module defining secrets once. `SECRET_PATTERN` matches a PEM
private-key armor line, an AWS access-key ID (`AKIA` plus 16 characters) and
a Senzing license payload (`AQAAAD` plus at least 16 base64 characters).
`find_secret` returns the matching class from `SECRET_PATTERN_NAMES`, never
the matched text, or None. Used by `package_bootcamp.py`; `write-gate.py`
keeps an inline copy that a test pins equal.

### 5.36 `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`

Python reference of the visualization app, run directly only when the
Bootcamper's language is Python; other languages build to the contract in
`module-03b-truthset-visualization/visualization-api-reference.md`. It
needs the Senzing Python SDK (`senzing`, `senzing_core`).

- CLI: `--settings` (default `config/engine_config.json`); `--records`
  (JSONL files or globs, optional); `--port` (default 8080); `--title`
  (default "Senzing Entity Resolution"); `--dataset` (snapshot wording,
  default "the loaded data"); `--snapshot <path>`; `--no-serve`.
- Settings (`resolve_settings`): the file wins when its `PIPELINE` has
  all `REQUIRED_PIPELINE_KEYS`, else a complete
  `SENZING_ENGINE_CONFIGURATION_JSON`; the winner is stated when both
  exist. If neither is usable it names the source and missing keys.
- Model (`build_model`, `Model`): with `--records`, one
  `get_entity_by_record_id` per record key (`SZ_ENTITY_DEFAULT_FLAGS`);
  without, one export pass (`SZ_EXPORT_INCLUDE_ALL_ENTITIES` plus
  `SZ_ENTITY_DEFAULT_FLAGS`, handle always closed). Rows fold through
  `_absorb`. `compute_feature_dist` then samples up to 40 multi-record
  entities via `why_records`; its failure is non-fatal.
- Routes (`make_handler`, GET; unknown path 404, exception 500, both JSON
  with `error`): `/` and `/index.html` (page); `/api/stats` (totals,
  histogram, bucket lists, `data_sources_total`, `server_nonce`);
  `/api/graph` (capped at `GRAPH_NODE_CAP`, with `encoding_check` from
  `_encoding_check`); `/api/merges`; `/api/overlap`; `/api/matchkeys`
  (top 20); `/api/features`; `/api/records?entity_id=`;
  `/api/search?q=` (`NAME_FULL`, then `NAME_ORG`, up to 10 results);
  `/api/why?entity_id=` (`why_records` or `why_record_in_entity`);
  `/api/how?entity_id=` (`how_entity_by_entity_id`).
- Page: summary banner and six tabs (Entity Graph, Merge Statistics, Match
  Keys, Feature Scores, Cross-Source, Search / Probe) with ids `tab-<id>`
  and `navbtn-<id>`, each shown only when its data exists. Entities offer
  Records, Why? and How? actions. Nodes are colored by their whole source
  set (`SOURCE_KEY_SEP`, `color_keys`). `?tab=` and `?q=` deep-link;
  `?capture=1` settles and fits the graph and sets `data-graph-settled`.
- Assets: `vendor/d3.v7.min.js` is inlined (`_d3_script`), with no network
  fallback; brand colors come from `brand_tokens` or the `_FALLBACK_*`
  copies.
- Snapshot (`write_snapshot`): embeds the data via `_script_json` with a
  `fetch` shim (search empty, Why/How point to the live server); Search /
  Probe becomes `_snapshot_probe_html` (note, merged-entity browse, up to
  five verified example cards).
- Serving binds `BIND_HOST` and prints the URL only after
  `confirm_server_identity` sees this process's `SERVER_NONCE`.

Exit codes:

- 0: built (and snapshot written) with `--no-serve`, or served and
  stopped.
- 1: vendored D3 missing (checked first, so no snapshot), model build
  failed, port bind failed, or another process answers the port.
- 2: no usable engine settings.

### 5.37 `plugins/senzing-bootcamp/scripts/session-end.py`

`SessionEnd` hook. When a bootcamp is active it calls `fold_checkpoint` and
`docker_lifecycle.stop_started_containers`. Prints nothing; always exits 0.

### 5.38 `plugins/senzing-bootcamp/scripts/session-start.py`

`SessionStart` hook. When a bootcamp is active it folds the checkpoint,
calls `ensure_checkpoint`, and prints one message: offer to resume from the
module in `config/bootcamp_progress.json`; whether a checkpoint was folded;
and any `resume_summary`. Silent otherwise; always exits 0.

### 5.39 `plugins/senzing-bootcamp/scripts/stop-nudge.py`

`Stop` hook, a safety net for the single closing `POINTER` question. Reads
the stdin JSON (invalid means empty). It exits 0 with no output when any
gate holds, in order:

- `stop_hook_active` is true (so it blocks at most once).
- `config/bootcamp_progress.json` is absent.
- `nudge_disabled`: `SENZING_BOOTCAMP_DISABLE_STOP_NUDGE` is truthy, or
  `pref_flag` finds `disable_stop_nudge` set in
  `config/bootcamp_preferences.yaml` (line scan, no YAML library).
- `bootcamp_complete`: the `bootcamp_complete` preference is set.
- `transcript_path` is absent or unreadable.
- `settled_final_text` over `current_turn_records` returns None: the turn
  ends in a tool call or tool result, or has no assistant text.
- The final text contains the pointer, or is empty.

Otherwise it prints `decision: block` with a reason telling the model to
check its last message, never repeat a question, and add exactly one bolded
closing question only if none exists. Always exits 0.

### 5.40 `plugins/senzing-bootcamp/scripts/write-gate.py`

`PreToolUse` hook for `Write` and `Edit`. Exits 0 unless
`config/bootcamp_progress.json` exists. A block writes a message to stderr
and exits 2; otherwise exit 0.

- The target is `tool_input.file_path` (regex fallback for non-JSON); an
  empty target passes the location check. `~` is expanded; `%TEMP%` or
  `%TMP%` blocks at once.
- Relative paths join the working directory; `norm` resolves `..` without
  touching the filesystem. A target inside the working directory
  (case-insensitive) is allowed; one matching `TEMP_PREFIXES`,
  `TEMP_SUBSTRINGS` or the `TMPDIR`, `TEMP`, `TMP` directories gets the
  temp/Downloads message; anything else outside gets the outside-project
  message.
- Whatever the path, the whole raw payload is searched with the inline
  secret pattern; a match blocks with a message to use environment
  variables.

### 5.41 `plugins/senzing-bootcamp/docs/`

Reference material shipped inside the plugin; nothing here is executed.

- `model-selection.md` is a maintainer note, not Bootcamper-facing. It records
  that a skill's `model:`/`effort:` frontmatter is turn-scoped, so for this
  multi-turn plugin the session model and effort are the real lever; which
  component kinds can carry an override; a dated (last verified 2026-10-01)
  model-tier snapshot (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 4.5) whose
  superseded names may appear only in that one dated note; a per-skill
  best-value evaluation; and the module-start nudge rules (INV-137 to INV-140,
  INV-098, INV-158, INV-236): one 👉 switch question naming only the dial that
  differs from what the Bootcamper currently runs, asked symmetrically for
  step-ups and step-downs (a step-down flagged as a cost saving); a one-line
  statement when it matches or when the dial sits above every row (effort
  `xhigh`/`max` or model Fable 5.1); a per-dial proxy comparison with the
  previous stage's row only while the dial truly cannot be read (an `/effort`
  result in the transcript makes it readable); the retired `model_guidance`
  preference is ignored. Its per-stage table is derived from the
  authoritative copy in `bootcamp-onboarding/ground-rules.md` and must match
  it row for row: Sonnet 5.5 with medium effort for Onboarding, Bootcamp
  preparation, Entity Resolution Concepts, Discover the Business Problem and
  Data collection; Sonnet 5.5 with high effort for System verification; Opus
  5.5 with high effort for SDK setup, Truth Set visualization, Data Quality,
  Mapping, and Transformation, Data processing, Query, Visualize and
  Discover, and Bootcamp graduation. CLI equivalents are `/model sonnet` or
  `/model opus` plus `/effort medium` or `/effort high`; other interfaces use
  their own model and effort controls. The recommended session setup is
  Sonnet 5.5 switched up to Opus 5.5 for the heavy stretches, or Opus 5.5 with
  high effort throughout.
- `examples/bootcamp_recap.example.md` is a sanitized finished recap (INV-065)
  from a Python, Core-path, SQLite run on plugin version 0.5.3: the header
  fields (Bootcamper, Started, Completed, Programming language, Path, Plugin
  version, Operating system, Python version, Language runtime, Senzing SDK,
  Database), one `## {Module name} — {timestamp}` section per completed module
  in experienced order, each with Information Shared, Questions & Responses,
  Actions Taken and an End-of-Module Summary carrying the three labeled
  blocks, and a `## Notes, Ideas and Questions` section fenced by
  `BOOTCAMP-NOTES:START`/`END` comments. Its images are referenced relative to
  the document as `visualizations/<name>.png`. Graduation points the
  Bootcamper at it and copies its block shapes; SDK setup cites it as
  evidence of the PyPI-shadowing failure.
- `examples/bootcamp_recap.example.pdf` is that Markdown rendered by
  `generate_recap_pdf.py`; it must stay regenerable from the `.md` and match
  its text.
- `examples/visualizations/` holds the screenshots the example embeds: the six
  Truth Set visualization tabs (`truthset_verification-` followed by
  `entity-graph`, `merge-statistics`, `match-keys`, `feature-scores`,
  `cross-source`, `search-probe`), the same six for the results app
  (`results_visualization-` prefix), and `data_quality_assessment.png`.
- `examples/bootcamp_recap.example.truthset.png` is an older single Truth Set
  screenshot kept beside the example.

### 5.42 `.claude/skills/auto-test`

Maintainer skill (never part of a bootcamp) for an unattended, sandboxed test
of the plugin; the cheap counterpart of `dry-run`. `SKILL.md` frontmatter takes
`[walk] [persona: terse|verbose|confused|impatient|offscript] [turns]`.

Procedure. With no argument it asks whether to run the MCP probe alone (zero
tokens) or the probe plus a simulated walk (INV-333: never inferred from
silence); a walk argument runs both, with optional persona and turns
(defaults `terse`, 12). The probe runs first. Findings are reported BREAKING,
WATCH, INFO; a clean run is "no regression detected", never "the bootcamp
works". Findings are recorded before any fix (INV-317) in the run's dated
`specs/IMPLEMENTED.md` entry or as an approved issue (INV-314), never a new
`specs/` file (INV-307), then `dry-run`'s fix steps apply; a scheduled
report is raw output. Server-side findings are never sent upstream from an
automated run. `submit_feedback` and `download_resource` are blocked by flag;
process A is never told it is tested; the sandbox is never under `/tmp`;
`baseline/mcp-snapshot.json` stays committed
(`tests/test_auto_test_harness.py`).

`autotest.py` runs one test in `~/senzing-autotest/runs/<stamp>-<persona>/`
(`SANDBOX_ROOT`): a detached worktree `plugin-src` at `--ref` (default
`HEAD`, SHA kept as `plugin_sha`; on failure the live tree, null SHA and a
coverage limit), a per-run `mcp.json` naming only `MCP_URL`, then
`mcp_probe.py check --json` (exit 2 or unparseable output adds a coverage
limit; findings tagged `source: mcp`). With `--walk` it scaffolds a project
via `dry-run`'s `scaffold_project.py` (`--seed fresh|seeded`; bare dirs on
failure), runs `walk.py` (passing `--model`, `--isolate-config`), lints a
non-empty transcript with `transcript_lint.py --phase <phase> --json`
(`source: transcript`), and lists project files as `artifacts`; coverage
limits always state what a walk could not show or that none ran. The report
(`run`, `sandbox`, `persona`, `plugin_sha`, `findings`, `coverage_limits`,
`report_path`, `transcript_path`, `artifacts`) goes outside the sandbox to
`~/senzing-autotest/reports/<stamp>-<persona>.json` with the transcript
copied beside it and a `latest.json` copy; `--json` prints it, else a
BREAKING/WATCH summary. The worktree and (unless `--keep`) the sandbox are
removed in `finally`. Exit 1 if any finding is BREAKING, else 0.

`mcp_probe.py` talks JSON-RPC (stdlib `urllib`, no Claude process) to
`DEFAULT_URL`. Replies may be plain JSON or SSE `data:` frames; an RPC `error`
raises. A snapshot sends `initialize` (protocol `2024-11-05`, client
`sbcp-auto-test`) and `tools/list`, and records server info, protocol, the
instructions text and a 16-hex SHA-256 digest of it, and per tool its sorted
`required` and property names, any JSON-Schema `enums`, the `prose_values`
parsed from its description by the `PROSE_VALUES` regexes (quoted items win,
else comma/semicolon lists with em-dash glosses removed), description and
schema digests. Schemas are order-normalized first. It snapshots the
`get_capabilities` response text (`CONTENT_PROBES`; failure is recorded, never
fatal) unless `--no-content`. `probe_values` sends `PROBE_SENTINEL` once per
`PROBE_MATRIX` entry and classifies the reply as `enumerated` (the rejection
named valid values, harvested permissively from backticks or prose, minus
gloss words), `opaque`, `silently-accepted` (no error) or `probe-error`.
Tools in `NEVER_CALL` (`submit_feedback`, `download_resource`) are never
called. `accepted_values` prefers probed values, else prose values, unioned
with `verified_values`. Subcommands (default `check`):

- `snapshot` prints the normalized snapshot.
- `update` runs `record_verified_extras` (every plugin literal outside the
  accepted set is sent to the server by `verify_literal`; accepted ones are
  stored under `verified_values`), then writes `baseline/mcp-snapshot.json`
  (sorted keys, indent 2, trailing newline).
- `check` collects five finding families: `diff_baseline` (codes
  `baseline-missing`, `server-version`, `protocol`, `instructions`,
  `tool-removed`, `tool-added`, `required-added`, `required-dropped`,
  `param-removed`, `param-added`, `prose-unextractable`, `doc-value-removed`,
  `doc-value-added`, `probe-mode-changed`, `value-removed`, `value-added`,
  `enums-appeared`, `description`, `content`); `conformance` over every `*.md`
  under the plugin's `skills/` and `commands/` (a one-line
  `tool(param='value')` literal outside the accepted set is first verified
  live: accepted gives INFO `undocumented-value`, rejected gives BREAKING
  `invalid-value`; placeholders `<...>` and `FREE_TEXT_PARAMS` are skipped;
  BREAKING `unknown-tool` for an `mcp__senzing__X` that does not exist;
  BREAKING `missing-required` when no calling file names a required
  parameter; WATCH `confabulation` for a `CONFABULATIONS` wrong form on a line
  without a `NEGATION_CUES` word; INFO `sensitive-call-site` for each
  `NEVER_CALL` call site); `server_quality` (WATCH `silent-accept`, INFO
  `opaque-rejection`, WATCH `doc-incomplete` for accepted-but-undocumented
  values after `ALIASES` canonicalization, BREAKING `doc-wrong` when a
  documented value is rejected live); `cross_tool` (WATCH `cross-tool-mismatch`
  when `sdk_guide` and `generate_scaffold` disagree on `language`); and
  `audit_static_contract` over `tests/test_mcp_call_contracts.py` (WATCH
  `contract-stale` when `CONTRACT_VERIFIED_ON` is older than
  `CONTRACT_STALE_DAYS`, BREAKING `static-contract-wrong` when
  `VALID_WORKFLOW_ACTIONS` differs from live or a `REQUIRED_PARAMS` tool is
  gone, WATCH `static-contract-drift` for a pinned required parameter that the
  live schema neither requires nor mentions).

Output is text sorted by severity then code, or `--json`. Exit codes: 2 when
the snapshot fails (URL, OS, value or RPC error: a network blip is never a
finding); 0 for `snapshot` and `update`; for `check`, 1 if any finding is
BREAKING, else 0.

`walk.py` drives a walk with two OS processes. Process A runs `claude -p` with
`--plugin-dir` the plugin, the per-run MCP config with `--strict-mcp-config`,
`--disallowedTools` for `FORBIDDEN_TOOLS`, `--permission-mode
bypassPermissions`, `stream-json` output, `--add-dir` the project, a fresh
UUID `--session-id` on turn 1 and `--resume` after. The opening message is
`--opening` (default `/senzing-bootcamp:start-bootcamp`, since the bare command
is unknown). Process B answers as the Bootcamper: a text-only `claude -p` with
no tools, run from `$HOME`, the `BOOTCAMPER_BRIEF` (an insurance-company
Bootcamper on Linux who knows SQL and Python, replies only what they would
type) plus one of five `PERSONAS`, on `--bootcamper-model` (default a Haiku
model). Each turn appends A's JSON events and a `bootcamper` event to the
transcript. The loop stops when A exits non-zero (a `walk_error` event), when a
turn shows no 👉, or when B returns nothing. If turn 1 shows "Unknown command"
or under 200 characters, it writes the transcript and exits via `SystemExit`
with a message (a silent non-start must not read as a clean run).
`--isolate-config` sets `CLAUDE_CONFIG_DIR` to `<project>/.claude-config`
(needs `ANTHROPIC_API_KEY`). Exit codes: 2 if `--project` is not a directory,
1 from the non-start `SystemExit`, else 0.

`transcript_lint.py` lints a stream-json transcript offline: it keeps the text
blocks of each `assistant` event as one turn and runs `CHECKS`. BREAKING
`INV-251-multi-question` for two or more 👉 in a turn; WATCH
`INV-005-not-turn-final` when over 120 characters of prose follow the single 👉
question (option rows, a `(respond ...)` parenthetical and quote/code/rule
lines are ignored); BREAKING `INV-079-module-number` for `Module <n>`; WATCH
`INV-051-or-joined` for `X or Y?` on a question line (the
`(respond yes or no)` form excepted); BREAKING `internal-marker-leaked` for ⛔,
🛑 or `(Internal:`; WATCH `INV-006-re-asked` when a 👉 line's normalized first
12 words (at least 20 characters) repeat. With `--phase` it adds the
`APPARATUS` check: in `preparation` or `module0` any journey map,
before/after, step overview, time estimate or model nudge is BREAKING
`INV-075-apparatus-in-exempt-phase`; in `content` each missing one is WATCH
`INV-028-apparatus-missing`. `--selftest` is a negative control: each check
must fire on built-to-break input and stay silent on good input, including a
well-formed numbered-options question. Exit codes: selftest 0 or 1; missing
transcript argument is an argparse usage error (2); 2 when no assistant turns
are found; otherwise 1 if any BREAKING finding, else 0. `--json` prints the
findings list.

`baseline/mcp-snapshot.json` is the committed `update` output (keys `content`,
`instructions`, `instructions_sha`, `protocol`, `server`, `tools`, `url`); the
offline suite reads it.

### 5.43 `.claude/skills/compact-dev-environment`

Maintainer skill that reduces what development carries across four asset
classes (invariants, specs, tests, feedback) without losing rationale.
Argument: one class to assess (`invariants`, `specs`, `tests`, `feedback`);
the full census is taken regardless and the argument scopes only the
assessment and plan. Guiding rule: never break an address. An invariant ID is
an address (thousands of citations, many in immutable commit messages), so the
default is consolidation without renumbering; a spec is a frozen record
(INV-307); a test is a guarantee; a feedback archive is a record addressed by
`entry_id` in `feedback/PROCESSED.jsonl`. Every figure in the skill text is a
dated illustration to re-measure, never to quote.

Procedure (report first; each destructive step confirmed per class). Step
1 runs `citations.py census`, `citations.py verify` and
`coverage_reports.py invariants`. Step 2 sorts invariants into
`load-bearing`, `mergeable`, `superseded`, `unenforced`, `not-an-invariant`;
the skill never edits `INVARIANTS.md` or mints an ID (INV-309): after a yes
it appends one dated ledger entry with a `DEFERRED INVARIANT` block per merged
rule (`INV-NNN`) and a `PROPOSED AMENDMENT` per superseded, merged or demoted
original, checks `pending_invariants.py list`, and hands off to
`/review-invariants`. Step 3 censuses specs read-only (verdict "leave").
Step 4 never consolidates tests for speed and combines traversals, never
assertions (one `subTest` per check); it hunts stale premises, deleted
subjects, duplicates and vacuous scans, confirmed by reading. Step 5 reads
the feedback ledger last-wins, fixes dispositions with `feedback_ledger.py
annotate`, never prunes `PROCESSED.jsonl`, and prunes archives only when
fully dispositioned. Step 6 reports before/after numbers and a plan: other
semantic changes become approved issues (INV-314); mechanical ones run here,
each followed by `verify` and the suite; never batch a delete with a move.
Renumbering, only if authorized, is last, all at once, with a root
`RENUMBERING.md` map and mechanical rewrites.

`citations.py` (`--repo`, default cwd). It scans `.md`, `.py`, `.json`,
`.jsonl` and `.sh` files under `AREAS` (plugin, specs, tests, skills) for
`INV-NNN`, excluding `specs/INVARIANTS.md` itself, caches, and any file
containing `IGNORE_MARKER`. Defined invariants are the `- **INV-NNN**` entry
lines of `INVARIANTS.md`; spec names are `specs/*.md` stems minus
`META_SPECS` (plus `specs/archive/*.md` if present); ledger headings are the
`##` lines of `IMPLEMENTED.md` (minus the `<spec-name>` template) and of
`DECLINED.md`. `feedback_state` collapses `PROCESSED.jsonl` last-wins by
`entry_id` and counts raw lines.

- `census [--area invariants|specs|feedback] [--verbose]` prints the defined
  count, live citations by area, the invariants cited nowhere, the
  unprotected-commit-message reminder; spec files versus headings (headings
  without a file, files not in the ledger, declined, genuinely
  unimplemented); feedback archives, collapsed entries and superseded lines,
  entries with no or `unrecorded` disposition, archive size with a "no
  action" note under 512 KB. Exit 0.
- `verify` reports undefined cited IDs, invariant `Source:` names that are
  neither a spec file nor a ledger heading, duplicate definitions, and
  archived feedback files no ledger entry names in `archive`. Exit 2 with the
  problem list, 0 when clean.

A missing subcommand or bad option is an argparse usage error (exit 2).

`widened_scope.py [--repo] [--all-verbs]` parses `INVARIANTS.md` entries and
reports candidate one-way links: a later invariant whose sentence uses a
`SCOPE_VERBS` verb (supersede, generalize, amends, restates, replaces,
reverses, retires, widens; `--all-verbs` adds `EXTRA_VERBS`) and names an
earlier invariant that never names it back. Output is a shortlist with the
sentence (cut at 200 characters) and a warning that most hits are false
positives and plain-prose widenings are missed. Exit 0 always, including when
no invariants parse.

### 5.44 `.claude/skills/delegate-to-mcp-server`

Maintainer skill that finds Senzing facts the plugin still holds that the live
MCP server now serves (INV-080), and files GitHub issues proposing a runtime
call instead. Goal: a smaller maintenance surface, not a smaller plugin.
Argument: an area or category bounding the run (stated in the report).
Distinct from `dry-run` phase 1 (do the calls work), `auto-test` (has the
server drifted) and `feedback-to-issues` (what did a Bootcamper hit). It never
edits the plugin and writes nothing under `specs/` except its ledger
`specs/mcp-coverage.jsonl`, a named live exception to the freeze (INV-307).

Procedure. Step 1 records both server axes, `server_version`
(`get_capabilities`) and `metadata.index_built` (`search_docs`), with the
coverage manifest and `common_confabulations`, and runs `summary`; if neither
axis moved only never-examined sites are covered. Step 2 builds the re-check
list (`stale --server --index` rows, gaps first; new coverage areas; plugin
files changed since the last run; the un-ledgered surface). Step 3 runs
`inventory`, including invariants that assert a server limitation. Step 4
asks the owning tool, this session, whether it answers and agrees, quoting
replies. Step 5 assigns exactly one of six `VERDICTS`: `delegate`,
`contradicted` (urgent; apply INV-169 first), `retire-workaround` (never
delete or renumber the invariant; name pinning tests; prove the fix),
`keep-server-lacks-it`, `keep-by-design` (reason required),
`not-a-senzing-fact`. Step 6 permits `delegate` only if the call can be made
there, the answer is usable, the plugin is not narrower on purpose
(INV-150), no invariant requires local text (INV-183), a fallback keeps
quality gates (INV-125), and no Bootcamper turn is wasted (INV-012). Step 7
files one approved issue per coherent change (INV-314; never `--repo`,
INV-319; deduped against open and closed issues), naming the replacing call
and carrying `owner-checked:` on absence claims (INV-213). Step 8 sends gaps
upstream per `feedback-to-issues` Step 8 (usually `feature`, anonymized,
approved, never `license_request`, INV-135). Step 9 records every verdict.
Step 10 reports both stamps, `contradicted` first, issues filed, new and
remaining coverage, and sweep coverage, then offers `/implement-github-issue`.

`issue-template.md` gives the issue body: no title heading (the body starts at
`## Problem`; the title states the fact, not the file), then `## Problem`
(plugin text with file:line and the server reply, quoted, with tool,
parameters, version, date), `## Root cause`, `## Proposed change` (the
replacing call, what to extract, what stays, the fallback), `## Acceptance
criteria` (checkboxes including a re-verification clause and the
cross-platform line), `## Affected files`, `## Source` (sweep date and ledger
key, verdict, MCP evidence, priority, upstream state from the
`feedback-to-issues` Step 8.1 set, related issues, invariants). A section
requires `owner-checked:` naming the route that would carry an absent fact,
exempting `n/a (no Senzing fact)`; enforced by
`tests/test_spec_absence_claims_name_their_owner.py`.

`coverage_ledger.py` (`--repo`, default cwd) manages `LEDGER`
(`specs/mcp-coverage.jsonl`), one JSON row per verdict, append-only and read
last-wins by `key` (a stable slug, never a path); blank, `#` and malformed
lines are skipped. Rows hold `key`, `verdict`, `server_version`, `checked`,
and optionally `index_built`, `where`, `claim`, `reason`, `tool`, `upstream`,
`issue`; legacy rows carry `spec` instead of `issue` and are read by
`produced_by`, never rewritten.

- `inventory [--category] [--verbose]` greps plugin Markdown (excluding
  `examples/` and caches) and `specs/INVARIANTS.md` with `PATTERNS`
  (attributes, flags, error-codes, sdk-shapes, install-config, dated-claims;
  first match per line wins) and, for unmatched invariant entry lines,
  `LIMITATION_PATTERN` (category `server-limitation`). It prints leads per
  category and file with the owning tool. Exit 1 if there are no leads,
  else 0.
- `stale --server <v> [--index <built>]` lists rows whose `expiry_reason` is
  non-empty: a different server version, or (when `--index` is given) a
  missing or different `index_built`. Sorted gaps first. Without `--index` it
  prints a caveat that the index axis was not checked. Exit 3 when the ledger
  is empty or nothing expired, 0 when rows are listed.
- `record --key --verdict --server [...]` appends one row (sorted keys,
  `checked` defaulting to today) and reports any superseded verdict; it warns
  when no `--index` was given. Exit 1 when `keep-by-design` lacks `--reason`;
  0 otherwise. An unknown verdict is an argparse error.
- `summary` prints counts by verdict (unknown ones flagged), server versions
  and index builds represented, and open `keep-server-lacks-it` gaps with
  their upstream state. Exit 0, including for an empty ledger.

Argparse usage errors (missing subcommand, required option or bad choice)
exit 2.

### 5.45 `.claude/skills/dry-run`

Maintainer test-gate skill that finds defects reading the plugin cannot: where
the plugin disagrees with the live MCP server, a real filesystem, or a human.
Argument: `[phases: 1, 2, 3 or all] [module phase 3's analysis starts at]`.

Procedure (`SKILL.md`). Ask which phases to run when not given (INV-333);
for phase 3 also ask the start module, marking the environment's reachable
ceiling. Work in `$HOME/senzing-bootcamp-dryrun` (never the repo or `/tmp`),
record environment limits (`senzing`, `libSz.so`, `fpdf2`, `docker`, a
browser), and run `coverage_reports.py both`. Host Markdown-lint hooks are
excluded for top-level `docs/*.md`, never fixed in the plugin. Only two
outward acts, each approved out of character per record (INV-314): an issue
or comment here, and `submit_feedback` for a re-verified `mcp-server` finding
(INV-194, INV-213, INV-321; never `license_request`). Never fabricate a
Bootcamper answer; commit or copy aside before mutating; clear `__pycache__`
after same-size reverts; bracket `pgrep -f` patterns. Findings are drafted on
sight into a `## dry-run-<YYYY-MM-DD>` **Not a spec** ledger entry (INV-317,
INV-307) in the issue-template shape; then fix the class, add a stdlib test
(INV-108), negative-control it, record the outcome and invariant answer.
Filing happens after a phase or walk pause, never mid-walk, after searching
open and closed issues and per-issue approval; never `--repo` (INV-319) or
`unattended-ok` (INV-318); no maintainer, nothing filed. The report names
where each finding lives, states coverage limits and the run's own mistakes.

`phase1-mcp-contracts.md`: check every MCP call literal in plugin skills
against the live schemas (tool exists, required parameters named, values
accepted), probe claims empirically, and re-ask each dated negative from
`coverage_reports.py negatives` (claim false: fix prose and invert or rescope
its guard; claim true: restamp, rewriting a rationale that no longer
reproduces); cross-check `common_confabulations`; beware rejections caused by
the plugin's own malformed call.

`phase2-hooks-and-scripts.md`: run every hook entry in `hooks.json` (counted
from the manifest) first outside a bootcamp (must exit 0 silently), then with
real stdin on a scaffolded project (write-gate, feedback-capture, stop-nudge
silence and opt-outs, fold idempotency over three runs, INV-059); drive each
bundled script and inspect the artifact (INV-129), including the viz
server's distinct exit 2 (config pre-flight) and exit 1 (SDK gate).

`phase3-conversational.md`: the maintainer answers; never self-played. Before
the chosen module is a no-analysis fast-forward; scaffold `--fresh` plus a
short `--seeded` walk when analysis starts at preparation (INV-133), else
`--seeded`. Bootcamp output and a collapsed test-notes block stay separate.
Watch list: INV-251/225, INV-133, INV-006, INV-058, apparatus exemptions
(INV-075/078 vs INV-028–031/096), INV-079, INV-051, INV-112, pinned wording
(INV-056). Graduation's upstream offer is presented, never sent, and
recorded `submission blocked: dry run ...` (INV-281).

`scaffold_project.py <directory> [--fresh|--seeded] [--explain]` builds a
project (removing any existing directory): the `DIRS` tree, always
`config/engine_config_incomplete.json` (empty `PIPELINE`) and a feedback file
holding a precious entry. Mid mode (default) adds `engine_config.json` with
the complete `PIPELINE_DEFAULTS` and a SQLite connection, a mid-module
`PROGRESS` (current `data_quality_mapping`, an absent docker container), saved
`PREFERENCES`, a recap with one completed section, an unfinalized
`RECAP-CHECKPOINT` block in `docs/progress/recap_checkpoint.md`, messy
Markdown in `docs/loading_strategy.md`, and four synthetic `VERIFY` records.
`--fresh` writes `{}` progress and empty preferences; `--seeded` (which wins)
writes `{}` progress and `SEEDED_PREFERENCES`. It then prints the mode's
`FIXTURE_MAP` rows, the fixtures that mode omits, and reminders. `--explain`
prints the map for the implied mode without writing (exit 0). Exit codes: 2
when the target is inside the repo or under `/tmp/` or `/var/tmp/`; argparse
error (2) when no directory and no `--explain`; 0 otherwise.

`coverage_reports.py <report> [--server <v>] [--repo]`, read-only, reports
only:

- `invariants`: invariants no `tests/*.py` cites, split into filtered
  fully-superseded (from the index's `*Fully superseded` lines), outcome
  invariants up to `OUTCOME_MAX` (phase 3's business) and development rules.
- `shipped`: invariants above 50 that no text file under `plugins/` cites,
  are not in the `DEV_GROUP` index group, are not "superseded by", and name a
  shipped artifact (`STATIC_ARTIFACT` plus module display names read from the
  `bootcamp-preparation/SKILL.md` table, raising `RuntimeError` if none
  parse); ungrouped invariants are listed separately; newest first.
- `affected`: ledgered specs whose `## Affected files` paths never appear in
  the entry, classified `real`, `moved`, `bare`, `glob`; ★ marks real rows
  the spec's acceptance criteria name.
- `negatives`: every one-line `MCP-NEGATIVE:` marker (claim, required
  `owner:`, server version, date) under `NEGATIVE_ROOTS` plus
  `specs/DECLINED.md`, oldest first, skipping files with `NEGATIVE_OPT_OUT`;
  it also lists malformed markers, census-shaped rationales
  (`CENSUS_SHAPED`) and enumeration-shaped rationales; with `--server` it
  splits markers into DUE (older version) and current.
- `unmarked`: plugin Markdown units (paragraph, bullet or fence) holding an
  MCP tool name, absence vocabulary and a date or server version with no
  marker or escape token within `PROSE_MARKER_WINDOW` lines.
- `both` runs all five.

Exit 2 when `<repo>/specs` is missing; argparse errors exit 2; an unparsable
module table surfaces as an uncaught exception (exit 1); otherwise 0.

`measure_label_occlusion.py <png> [--fill hex,...] [--fail-under px]
[--min-marker-px n]` is a phase-2 helper needing Pillow and numpy (exit 2 if
absent). It finds node-marker blobs of each fill color by connected-component
labeling, takes each node's label band at `cy + r + 11`, and reports the
minimum distance from any other marker to that label's ink. Exit 2 when no
marker/label pair is found, 1 when below `--fail-under`, else 0.

### 5.46 `.claude/skills/feedback-to-issues`

Maintainer skill that turns a bootcamp feedback file into deduplicated GitHub
issues in this repository only (never `--repo`, INV-319; never into children,
which receive change by parity), after re-verifying every Senzing fact against
the live MCP server, and reports confirmed server defects upstream. Argument:
a feedback file path. It writes only under `feedback/`, never into `specs/`
(INV-307), never edits a feedback file's content, and never implements.

Procedure. Step 1 resolves the file: the given path, else root
`SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`, else
`docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`, never anything under
`feedback/` or a `*_DUPLICATE.md`. Step 2 parses `## Improvement:` blocks
(title, symptom, impact, fix, priority, module, date, `Source:`
`bootcamper-reported` or `self-observed (assistant retrospective)`). Step 3
runs `feedback_ledger.py check` (NEW, PARTIAL: new entries only, DUPLICATE:
stop and `commit` to rename). Step 4 reads `INVARIANTS.md`, open and closed
issues, and `specs/` as history. Step 5 re-asks the owning MCP tool for every
Senzing fact, quoting it with server version (still reproduces, fixed
upstream, or now contradicts the plugin; INV-169, INV-080/149; unreachable
means "unverified"). Step 6 classifies, confirms the root cause at file:line,
routes (`plugin`, `mcp-server`, `both`, `host`, `unclear`; `host` never goes
upstream), dedupes and groups. Step 7 files approved issues (INV-314) with
`gh issue create --body-file`, absence claims carrying `owner-checked:`
(INV-213). Step 8 sends a confirmed server defect upstream: it maps the
entry's `Upstream:` value through the canonical two-table vocabulary
(INV-281, INV-300; entry values `not applicable`, `submitted YYYY-MM-DD`,
`offered, declined`, `offer pending`, `submission blocked: <reason>`,
`submission failed: <reason>`; issue values `not applicable`, `already sent
<date> (per the entry)`, `declined by the bootcamper (per the entry)`, `sent
<date> via submit_feedback (<category>, anonymous)`, `declined by the
maintainer`, `submission failed: <reason>`, `submission blocked: <reason>`,
`not yet sent — needs maintainer approval`, the last three still owing a
report; parsed by `tests/test_blocked_submission_has_a_vocabulary_value.py`),
drafts an anonymized report (INV-321), and sends `bug` or `feature` only on
an explicit yes, never `license_request` (INV-135). Step 9, after filing,
runs `commit` with a `--disposition` per entry. Step 10 reports a per-item
table with the server version, skipped entries, archive path, issues and
upstream outcomes.

`issue-template.md`: body starts at `## Problem` (no title heading), then
`## Root cause` (with the live-server quote and conditions), `## Proposed
change`, `## Acceptance criteria` (with the cross-platform line), `## Affected
files`, `## Source` (feedback file, entry, date, module, `Source:`; priority;
`MCP re-check` outcome with `owner-checked:` for absence claims; `Upstream`
value; related issues; invariants).

`feedback_ledger.py` (`--repo`, default cwd) splits a feedback file into
entries at each `##` heading after `normalize` (strip BOM, LF line endings,
right-strip lines, collapse blank runs, trim), dropping scaffold titles and
empty headings; `entry_id` is the first 16 hex characters of SHA-256 of the
normalized entry. The ledger `feedback/PROCESSED.jsonl` is read last-wins by
`entry_id` (blank, `#` and malformed lines skipped).

- `check <candidate>` prints JSON (`candidate`, `file_id`, `entries_total`,
  `new`, `known`) and a NEW/PARTIAL/DUPLICATE verdict on stderr. Exit 1 when
  the file is missing or has no entries, 3 when every entry is known, else 0.
  Writes nothing.
- `commit <candidate> [--disposition TITLE=VALUE ...]`: for a full duplicate
  it renames the candidate in place to
  `SENZING_BOOTCAMP_PLUGIN_FEEDBACK_<earliest archive unixtime>_DUPLICATE.md`
  (suffix `-2`, `-3` on collision), appends nothing, exit 3. Otherwise it
  appends one sorted-key line per new entry (`entry_id`, `title`, `archive`,
  `archive_unixtime`, `processed` UTC date, `disposition`, matched by exact
  title or `entry_id`, split on the last `=`, default `unrecorded` with a
  warning) and moves the file to
  `feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK_<now unixtime>.md`; exit 0.
  Exit 1 when the file is missing or has no entries.
- `annotate <entry_id> <disposition>` appends a copy of the current record
  with the new disposition and an `annotated` date; exit 1 if the id is
  unknown, else 0.

Argparse usage errors exit 2.

### 5.47 `.claude/skills/production-readiness-audit`

Maintainer skill: the last static gate before `dry-run`. It establishes four
properties of the whole plugin that no test can hold (INV-003 consistent,
coherent, complete; INV-004 production-ready; plus concision, audited on
request and not an invariant) and checks `specs/INVARIANTS.md` in both
directions: forward (every site an invariant binds honors it; one wrong site
means sweep the class) and reverse (every durable hard rule the plugin states
is registered and cited at its line, INV-183). Argument: an area to sweep
first. Conversational invariants (INV-251, INV-006, INV-014, INV-005/008/009,
gate ordering) are out of scope and must be reported as untested and routed
to `dry-run` phase 3.

Procedure. Step 1: confirm the suite is green, read the newest audit
entries (`grep` of `## production-readiness-audit`/`## deep-dive-audit`
headings with `head`, the ledger being newest-first), run `conformance.py
all`, `since --since-last-audit`, `coverage_reports.py both` and
`citations.py verify` (leads, not verdicts), and record unreachable tools.
Step 2: a scoped, disclosed forward sweep (generator hits, `enumerations`,
what changed since the last audit, a rotation of outcome blocks). Step 3:
each reverse hit is an unregistered rule (draft, sign-off, next ID), a
missing citation, or not a durable rule; also hunt wrong citations. Steps 4
to 6: consistency and coherence, completeness (three platforms, every
language, deliverables verified, INV-129), concision (`size`,
`duplication`; never cut rationale). Step 7 ranks defect classes: partial
application, cwd- or runtime-relative strings, guards narrower than their
invariant, stale enumerations, wrong citations, phantom tests, diverging
inlined constants, stale behavior claims. Step 8 records before fixing
(INV-317): attended, an approved issue (INV-314); unattended, a ledger line
marked not filed; never `unattended-ok` (INV-318); then fix, test,
negative-control, and write a `## production-readiness-audit-<date>` **Not a
spec** entry, committed before the work that answers it. Step 9 reports per
property, coverage limits and own mistakes, and offers `dry-run`.

`conformance.py [--repo] <view>` (stdlib, read-only). A hard-rule line is
classified by `classify`: `anchored` (`ANCHORED_RULE`: a leading ⛔ or a
bolded MUST/NEVER/ALWAYS) or `mid-line` (a ⛔ outside code spans followed by
bold, a capital or an `IMPERATIVE` word, excluding `NOUN_USE`). Views over
`plugins/senzing-bootcamp/**/*.md` unless noted:

- `rules`: hard rules whose enclosing heading section cites no `INV-NNN`,
  with line-anchored and mid-line totals and a warning that the count is not
  a count of unregistered rules.
- `per-rule [--uncited]`: every hard rule with the IDs cited on its line or
  the adjacent non-blank lines (`own_citations`).
- `since --ref <ref> | --since-last-audit`: hard-rule lines added in `git
  diff --unified=0` over `SCAN_ROOTS` (plugin, `.claude/skills`,
  `.claude/skill-overlays`) plus `RETIRED_ROOTS`, `.md` only, printed `+`;
  then the corpus statement and hard-rule lines added outside it (in
  `UNCOUNTED_RULE_HOMES` or non-`.md` files under the roots), printed `!`.
  `last_audit_ref` takes the newest `production-readiness-audit*` entry whose
  `Commit:` resolves (skipping uncommitted ones), prints which, widens to the
  parent with `SUSPECT-REF` when that commit touched a propagated path
  (`git diff-tree -r -m --root`), and prints a `BOUNDARY` line with the
  hard-rule lines the previous record's range retired.
- `reverse-check --ref | --since-last-audit`: the INV-282 check; added lines
  in the plugin corpus are TESTED (cited or UNCITED at the line), others are
  UNTESTED (with a citation rate and a caveat), unlocatable ones UNRESOLVED;
  `VERDICT: clean` only when all were tested and cited, else `NOT CLEAN`.
- `duplication [--words 14] [--top 12]`: normalized word shingles shared by
  more than one file, top file pairs.
- `enumerations`: invariants whose text has an exact count, closed-list
  wording, or a series of three or more backticked literals.
- `size`: shipped Markdown file and word counts, the 12 heaviest files, and
  bundled script line totals.
- `all`: `rules`, `per-rule --uncited`, `enumerations`, `size`,
  `duplication`, then a note that `since` and `reverse-check` need a range.

Exit codes: 0 with no subcommand (prints help) and for every completed view;
2 when the plugin directory is missing, when `INVARIANTS.md` is missing for
`enumerations`/`all`, when `since`/`reverse-check` get no ref or the
last-audit ref cannot be resolved, or when `git diff` fails.

### 5.48 `.claude/skills/propagate-to-public`

Maintainer release-path skill that mirrors the shippable subset of this repo
into the public access repo `Senzing/senzing-bootcamp-claude-plugin` (default
checkout `~/senzing.git/senzing-bootcamp-claude-plugin`; argument overrides
the path) and stops at the working tree: no commit, push or PR unless asked
(then Conventional Commits with an `issue: #<n>` trailer). Manifest:
propagated are `plugins/senzing-bootcamp/**`, `.claude-plugin/`, `README.md`
and `docs/` (with the Pages site, #452) except `docs/development.md` and
`docs/FAMILY_WORKFLOW.md`;
excluded are `.claude/**`, `specs/**`, `feedback/**` (bootcamper text),
`MIGRATION.md`, top-level `scripts/`, `.sync-state.json`, `resources/`, caches
and the dev `.gitignore`; preserved (never touched) are the public repo's
`.github/**`, `LICENSE`, `.claude/settings.json`, `.vscode/cspell.json`,
`.gitignore`. The skill reports the script's summary and `git status --short`,
points at `git diff` in the public repo, and never guesses a destination.
Manifest changes update `SKILL.md` and `propagate.sh` together.

`propagate.sh [dest]` (bash, `set -euo pipefail`) resolves the dev root three
levels up. It exits 1 when the source lacks `plugins/senzing-bootcamp`, when
`<dest>/.git` is missing, when the destination's `origin` URL does not contain
`Senzing/senzing-bootcamp-claude-plugin`, when source and destination are the
same directory, or when `rsync` is absent; any failing command also aborts
non-zero. It prints source, destination, origin and branch, then runs `rsync
-a --delete` for `plugins/` (excluding `__pycache__/`, `*.pyc`,
`.pytest_cache/`), `.claude-plugin/`, and `docs/` (excluding root-anchored
`/development.md` and `/FAMILY_WORKFLOW.md`, kept on one line because
`tests/test_maintainer_tooling_stays_out_of_public.py` parses it), and copies
`README.md`. An embedded Python pass rewrites `SLUG_OLD`
(`docktermj/senzing-bootcamp-claude-plugin-development`, the suffixed form
deliberately) to `SLUG_NEW` in every `.md`, `.json`, `.html` and `.css` file
(`REWRITTEN_SUFFIXES`; the last two since #452, for the Pages site) under the
mirrored roots plus `README.md`, never opening a binary, and
`"name": "docktermj"` to `"name": "Senzing"` in
`marketplace.json`. The same pass rewrites the marketplace name
`"name": "senzing-bootcamp-dev"` to `"name": "senzing-bootcamp"` in
`marketplace.json`, and `senzing-bootcamp-dev` to `senzing-bootcamp` in every
rewritten file wherever no `[A-Za-z0-9_-]` follows it (#449), so the published
plugin ID stays `senzing-bootcamp@senzing-bootcamp`. It prints each rewritten
file and a count, then ends with `git status --short` of the destination and a
review reminder; exit 0.

### 5.49 `.claude/skills/release`

Maintainer skill that cuts a release as one operation: bump every version
site, write the `CHANGELOG.md` entry, commit those files, and tag that commit
(INV-301), so a version can never exist untagged (the kiro-power defect: a
changelog entry with no tag, invisible to downstream ports that target tagged
releases). Argument: `major|minor|patch` or an explicit `X.Y.Z`; with none,
run the dry run, show the current version and newest tag, and ask (INV-333).
Always show the dry run and get approval before `--apply`. It never pushes
and never invokes `/propagate-to-public`; afterwards it names the next steps
(run the suite, propagate, push the branch and the tag). Never hand-edit a
version site or changelog heading. A signing `tag.gpgsign` setting may prompt;
the script does not override it. A new file asserting the version is added to
`VERSION_SITES` (`tests/test_release_covers_every_version_site.py` fails
otherwise).

`release.py [version] [--major|--minor|--patch] [--apply|--dry-run] [--repo]
[--allow-branch] [--allow-divergent-base] [--message]`. Dry run is the
default. Preconditions, each a `Refusal`: the manifest
`plugins/senzing-bootcamp/.claude-plugin/plugin.json` exists; the repo is a
git repo; the working tree is clean (no override); the branch is
`RELEASE_BRANCH` (`main`) unless `--allow-branch`. The target is the explicit
version or the bumped manifest version (exactly one selector; none, both, or
a non-semver version refuse). `check_target` refuses a target not newer than
the manifest, an existing tag, a target not newer than the newest semver tag
(sorted numerically), and a manifest that differs from the newest tag (unless
`--allow-divergent-base`, which downgrades only that refusal to a warning).
`rewrite_sites` plans every `VERSION_SITES` edit in memory (the manifest's
`"version"` line, the example recap's `**Plugin version:**` row, and the
manifest's verbatim copy in `BLUEPRINT.md` section 3), refusing
a missing file, a pattern that no longer matches, a site already stating a
different version, or a no-op rewrite. `plan_changelog` builds an entry
`## [X.Y.Z] - <today>` listing non-merge commit subjects since the newest tag;
if `CHANGELOG.md` is absent it is created from `CHANGELOG_HEADER`, a
`SEED_NOTE` naming the newest seeded version, and one reconstructed entry per
existing tag (newest first, dated by the tagged commit, the earliest not
itemized); the new entry is prepended before the first `##`. Output: repo,
branch, version change, newest tag, changelog action, mode, unified diffs of
the sites (capped at `DIFF_LINE_BUDGET` lines), the entry, and the three git
commands. With `--apply` it writes the files, `git add` of exactly those
files, commits with the subject (default `chore(release): <version>`) and
creates an annotated tag; on any git failure it deletes the tag, hard-resets
to the recorded HEAD and refuses. Exit codes: 2 when `--apply` and
`--dry-run` are both given or argparse rejects the arguments; 1 on any
refusal (including rollback); 0 after a dry run or a release.

### 5.50 `.claude/skills/retrofit-from-public`

Maintainer skill, the return path of `propagate-to-public`: it reports what
changed in the public access repo since the last propagation and files GitHub
issues in this repository describing each coherent change. It writes nothing
into the dev tree (INV-312) and never deletes, adds or pulls the public
governance layer. Argument: the public repo path (default
`~/senzing.git/senzing-bootcamp-claude-plugin`). Compared paths: `plugins/`
(minus caches), `.claude-plugin/`, `docs/`, `README.md`. After the script:
report its summary, group divergence into decisions (a dependency bump, a
workflow, a prose fix), search open and closed issues by the public commit
subject or SHA, show each title and body and get a yes (INV-314), file with
`gh issue create` in this repository only. Each issue carries the public
commit, the affected paths and, as work still owed, the narrow inverse
rewrite (`Senzing/senzing-bootcamp-claude-plugin` back to
`docktermj/senzing-bootcamp-claude-plugin-development`, and
`marketplace.json`'s owner name, and the marketplace name `senzing-bootcamp`
back to `senzing-bootcamp-dev` where it names the marketplace; never
`plugin.json`'s author or plugin name, or product mentions). It stopped
copying (#54) because copied prose desynced dev-only tests.

`retrofit.sh [--base <dev-tag>] [path]` (bash, `set -euo pipefail`). Exit 2
for a usage error (`--base` without a value, an unknown option, too many
arguments); `-h`/`--help` prints usage, exit 0. Guards exit 1: dev root lacks
`plugins/senzing-bootcamp`, source lacks `.git`, source `origin` lacks the
public slug, source equals the dev root. Baseline selection (#202): the dev
tag named by `--base`, else the tag of the same name as public's newest tag
(`git describe --tags --abbrev=0`); exit 1 with a `--base` suggestion when
public has no tag, the dev repo lacks that tag, the tag lacks
`.claude/skills/propagate-to-public/propagate.sh`, extraction fails, the
throwaway destination cannot be created, or the tag's `propagate.sh` fails.
The baseline is built in a `mktemp -d` directory (removed by an EXIT trap;
INT exits 130, TERM 143): `git archive` of the tag, a fresh git repo whose
origin names the public slug, and the tag's own `propagate.sh` run into it,
so paths, exclusions and the slug rewrite match what that release published.
It prints source, origin, branch, dev root and baseline, then per path
`same`, `DIFFERS` (with up to 40 `diff -rq` lines), `(absent in public)` or
`ERROR` (diff exit 2 or more); the public commits since public's newest tag;
a count line ending "NOTHING WAS WRITTEN"; and every baseline file absent
from public (not deleted). Exit 1 when any path could not be compared, else
0.

### 5.51 `.claude/skills/review-invariants`

Maintainer skill that walks the maintainer through every pending
`DEFERRED INVARIANT` (a rule already shipping and test-guarded with no ID)
and `PROPOSED AMENDMENT` (a dated correction to a registered invariant) block
in `specs/IMPLEMENTED.md`, one at a time, asks for a verdict and performs the
mechanical work for approved ones. It never signs off an invariant itself.
Argument: the block number to start from. Verdicts, all three offered every
time: register (mint an ID, permanent), hold (record reason and a checkable
revisit condition), amend (change the wording, show it, get a second yes,
then register; includes splitting a two-subject draft). At the first block
it explains that declining does not remove the rule, only whether the ruleset
knows it.

Procedure. Step 1 runs `list` and `check`, reading every count (unresolved
means unverified; zero checked is an empty check, INV-308); held blocks are
never re-offered unless their revisit condition is met. Step 2 shows one
block (`show`, `sites`): source, shipping rules verbatim, full wording, the
citation sites and scan scope, rejected citations, and what holding means;
then asks once. Register: re-read `next-id`; add the index entry and
invariant in one edit with `(Source: ...)`; cite `(INV-NNN)` at every site,
derived from `sites` plus a repository grep (INV-246); back-cite from the
enforcer and re-derive `EXPECTED_PAIRS` in
`tests/test_invariant_enforcer_citations.py`; mark the block `resolved
INV-NNN, registered by the maintainer <date>` (amendments `applied <date>`);
verify (`citations.py verify`, `coverage_reports.py shipped`, the suite);
regenerate the manifest; then stop at the working tree, no commit or push
(INV-310), listing touched files. Hold: a `**HELD <date>:**` paragraph inside
the block. Amend: change the wording, get a second yes, register. At the end
write a `## invariant-review-<date>` **Not a spec** ledger entry.

`pending_invariants.py <subcommand>` (read-only, exit 0 always, including
for unknown subcommands, which print the docstring; no argument or
`-h`/`--help`/`help` prints it too). `blocks` scans the ledger for bullets
starting `-` that contain `DEFERRED INVARIANT` (not `resolved INV-`) or
`PROPOSED AMENDMENT`, running to the next `##` or top-level `- **`, and
keeps a block only when its body carries a marker (`AWAITING`,
`HELD_IN_BLOCK` or `AMENDMENT_AWAITING`). `parse` extracts rule bullets
(indented items with ⛔) as `described` (`DESCRIBED`, path first, never
verified) or `quoted` (`QUOTE` with an optional `— in <path>` location), or
records them as unparsed; the drafted wording after `**INV-NNN**` or
`**INV-nnn**`; the amended ID; the enforcer from `Enforced by` (named, none,
or unreadable when the clause opens but cannot be read); and the hold reason
from `**HELD <date>:**` (preferring a `Revisit ...` sentence) or the in-block
approval string. `resolve` finds a location under `RESOLUTION_ROOTS` (plugin
skills, scripts, plugin, repository) or maps a retired
`.claude/commands/<name>.md` to `.claude/skills/<name>/SKILL.md`.

- `list`: pending and held counts, next free ID (highest `**INV-nnn**` plus
  one), each pending block with rule count, kind (`new invariant` or `AMENDS
  INV-nnn — already registered`), ledger line and enforcer; held blocks with
  reasons.
- `show <n>`: ledger line, amended ID, spec, enforcer, the ID it would get,
  each rule with its location and `[quoted]` or `[described, NOT quoted —
  unverified]`, unparsed bullets raw, and the wrapped drafted wording.
- `sites <n>`: named sites; paths named in the block's prose that resolve
  (excluding the ledgers and the enforcer); candidate plugin lines carrying ⛔,
  no citation, and two or more rare wording terms; then the scan scope
  (scanned plugin files, unscanned counts by top directory, frozen files
  excluded via `specs/FROZEN-MANIFEST.txt`).
- `next-id`: prints `INV-nnn`.
- `check`: each quoted rule must appear (citations stripped, whitespace
  flattened) in its resolved file; prints MISMATCH, UNRESOLVED and UNPARSED
  lines, then counts checked, mismatched, unresolved, no-prose-site,
  described-not-quoted and unparsed, the amendment share, and warnings.

`show` or `sites` without a numeric argument prints usage; an out-of-range
number prints a message; both exit 0.

`invariant_manifest.py [--check]` derives `invariant-manifest.json` at the
repository root from `specs/INVARIANTS.md` (INV-311: the prose stays
authoritative). Each entry `- **INV-NNN** — ...` becomes `id`, `index_group`
(first `Index by subject` group listing it), `section` (nearest `#`/`##`
heading), `status` (`superseded` only with a `- **Superseded by:** INV-nnn`
bullet, else `active`; INV-313), `superseded_by`, `partly_superseded_by`
(from a `Partly superseded by:` bullet; the entry stays active), `summary`
(first sentence if at most `SUMMARY_MAX` characters, else null) and the
flattened `statement`; sorted by ID, wrapped with `source`, `generator`,
`note` and `count`, rendered as sorted-key JSON with indent 2 and a trailing
newline. It prints counts by status, null summaries, entries without a
group and without a heading. Without `--check` it writes the file, exit 0;
with `--check` it exits 1 (stderr regeneration hint) if the file differs,
else prints the report and exits 0.

### 5.52 `.claude/skill-overlays`

Repo overlays for three user-level skills (INV-337: the governing copy is
`~/.claude/skills/<name>/SKILL.md`, which CI cannot see; INV-308). Each file
states only what this repository adds.

- `implement-github-issue.md`: invoking `/implement-github-issue <n>` assents
  to five comments on issue `<n>` (Started, Clarifications, Approach, Result,
  and the escape-hatch comment) and nothing else (INV-314, #216). The local CI
  mirror reads `.github/workflows/*.yaml`: run `test-suite.yaml`'s two legs
  with `HOME` set to an empty directory outside `/tmp` (present leg with
  `PYTHONUSERBASE` set and `import fpdf` confirmed; absent leg in a `venv
  --without-pip` ending `OK (skipped=N)`, N > 0); `lint-workflows.yaml` is a
  known local gap; `citations.py verify` is required. An issue may not close
  until it registers an invariant, writes a `DEFERRED INVARIANT` block with
  `INV-NNN`, or states it establishes none (INV-309); the command cannot mint
  IDs. Re-verify Senzing facts and record an `MCP re-check` line (INV-080),
  with `owner-checked:` for absence claims (INV-213). Phase 6 writes the
  `specs/IMPLEMENTED.md` entry in the same commit as the change; `citations.py
  verify` runs after the entry exists and again after any later ledger edit
  (INV-207); read the runner's verdict line, not its count. Declining is the
  maintainer's alone (INV-332); a decline appends a `## <issue-slug>` entry to
  `specs/DECLINED.md` with `Declined`, `Decided by`, `Reason`, `Revisit if`,
  and absence claims there carry an `MCP-NEGATIVE` marker (INV-217). The
  child-only `PARENT_VERSION` clause is deliberately unimplemented here.
- `order-github-issues.md`: adds no obligations; exists so the command
  resolves to a checkable file (INV-316); the governing copy has no overlay
  hook.
- `unattended-issue-loop.md`: merge policy and label gate live in
  `docs/FAMILY_WORKFLOW.md` §2 (INV-300). Every worker brief includes the
  implement overlay (INV-309). An unattended run creates only, on the issue it
  works: the four log comments, one blocked comment plus removing
  `unattended-ok`, the branch push and PR, and the merge and branch deletion
  unless `--no-merge` (INV-314). It never signs off an invariant (but ships
  the rule with a `DEFERRED INVARIANT` block), never calls `submit_feedback`
  (drafts with `Upstream: not yet sent — needs maintainer approval`), never
  declines (INV-332), and writes under `specs/` only its own ledger entry
  (INV-307). The handoff leads with what needs a yes.

### 5.53 `.claude/memory`

Project memory files with YAML frontmatter (`name`, `description`,
`metadata.type: feedback`) and an index `MEMORY.md` (one line per memory).

- `commit-message-format.md`: every commit uses a Conventional Commits
  subject with an `issue: #<n>` trailer (never in the subject, keep the `#`);
  `SKIP_GIT_CONVENTIONS=1` is not part of any normal path; replaced the older
  issue-prefix rule when `specs/` froze and `/implement-spec` was retired
  (#56, #60).
- `dry-run-phase3-full-walk-structure.md`: run phases 1 and 2 in one session
  and the walk in a fresh one; the full eleven-module walk completed
  2026-08-31 with 14 findings, so the next walk starts later than Data
  Quality, Mapping, and Transformation; the `--seeded` INV-133 walk is still
  owed; the graduation upstream gate is recorded as `submission blocked: dry
  run` and sent only after maintainer approval; write US spelling (INV-253).

### 5.54 `specs/`

The development record, a read-only archive since the 2026-09-15 cutover
(INV-307, #52); new work is GitHub issues. `specs/README.md` is the freeze
notice and its "What stays live" table is the authoritative list
`tests/test_specs_are_frozen.py` reads; it also records how each command that
once wrote specs was reworked, keeps `tests/list_specs.py` (INV-216), and
triages the frozen `todo.md`. No archive count is stated anywhere.

- Frozen archive: every other file, chiefly `<kebab-case-slug>.md` specs
  (problem, root cause, proposed change, acceptance criteria, affected files,
  invariants introduced) plus `todo.md` and `PreToolUseWriteError.md`. A
  spec's slug is a permanent address cited by `(Source: ...)` and ledger
  headings.
- `FROZEN-MANIFEST.txt`: the pinned set, one filename per line (`#` comments
  and blanks ignored). `tests/test_specs_are_frozen.py` fails if a listed
  file is gone or if any file in `specs/` is neither listed, a live record,
  nor the manifest itself. `pending_invariants.py` reads it to count frozen
  files as citation-ineligible.
- `INVARIANTS.md` (live): the canonical register. Opening constraints and
  rules: IDs are permanent, never renumbered, reused or deleted; an obsolete
  rule is marked, not removed; editing may only clarify wording, a change of
  meaning is a new ID; a new invariant takes the next unused `INV-NNN` (one
  above the highest), is added to its `### Index by subject` group in the
  same edit (`tests/test_invariants_index.py`), is phrased as one testable
  MUST/ALWAYS condition, and records `(Source: <slug>, YYYY-MM-DD.)`. Layout:
  numbered sections INV-001–004 foundational, 005–015 whole-Bootcamp,
  016–018 administration, 019–027 preface, 028–032 per-module, 033–046
  module-specific, 047–049 graduation, INV-050 project layout (outcomes
  1–50 are not indexed); then `## Invariants added from implemented specs`
  with the subject index (each development invariant in exactly one group;
  per group, fully and partly superseded lists; the "development record
  itself" group is the `coverage_reports.py shipped` exemption) and the
  HTML-comment marker "New invariants go directly below this line", under
  which entries `- **INV-NNN** — <rule> (Source: ...)` are prepended, so
  that section reads newest first. Supersession uses bullets `- **Superseded
  by:** INV-nnn`, `- **Partly superseded by:** INV-nnn`, `- **Supersedes:**
  INV-nnn`. Later changes are dated notes appended to the entry (⚠️ for no
  meaning change, ⛔ dated corrections), never rewrites; registration and
  amendment go only through `/review-invariants`.
- `IMPLEMENTED.md` (live, INV-182): the completion ledger and only
  completion signal, newest first, never deleted. A spec or issue run is done
  iff a `## <slug>` heading exists. Template fields: `Implemented`, `Files
  changed`, `MCP re-check` (server version, date, outcome, `owner-checked:`
  for absence claims), `Summary`, `Commit` (a resolvable hash, `uncommitted`
  or `committed (hash not recorded)`, enforced by
  `tests/test_spec_ledger_invariants.py`, which also requires each entry
  since its cutoff to register or disclaim an invariant). Later entries add
  `Approach`, `Verification`, `Tests`, `Differs from the issue`, and an
  `Invariant (INV-309)` answer. Dated non-spec records (`dry-run-<date>`,
  `production-readiness-audit-<date>` with a `Commit:` the audit resolver
  reads, `invariant-review-<date>`) are marked **Not a spec**. Pending
  decisions are `DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT
  minted` blocks (rule bullets with ⛔ quotes and `— in <path>`, drafted
  `**INV-NNN** —` wording, `Enforced by`, optional `**HELD <date>:**`) and
  `PROPOSED AMENDMENT to INV-nnn — awaiting the maintainer's sign-off; NOT
  applied` blocks; decided ones read `resolved INV-nnn` or `applied <date>`.
- `DECLINED.md` (live): correct specs or issues deliberately not built,
  appended under a template marker as `## <slug>` with `Declined`, `Decided
  by`, `Reason` (required) and `Revisit if`; written only on the
  maintainer's decision (INV-332); absence claims carry `MCP-NEGATIVE`
  markers (INV-217) and `coverage_reports.py negatives` scans it.
- `mcp-coverage.jsonl` (live, named exception, #142): the
  `delegate-to-mcp-server` verdict ledger (5.N `coverage_ledger.py`).

Root `invariant-manifest.json` is derived from `INVARIANTS.md` by
`invariant_manifest.py` (never edited by hand, INV-311; kept at the root, not
in `specs/`): `source`, `generator`, `note`, `count`, and `invariants`
entries with `id`, `index_group`, `section`, `status`, `superseded_by`,
`partly_superseded_by`, `summary`, `statement`. CI checks it with `--check`;
downstream ports read it to build their invariant-disposition registers.

### 5.55 `feedback/`

The committed archive of triaged bootcamp feedback, written only by
`feedback_ledger.py commit`. It holds
`SENZING_BOOTCAMP_PLUGIN_FEEDBACK_<unixtime>.md` files (bootcamper or
graduation-retrospective entries, each a `## Improvement: <title>` block
with `Source`, `Module`, `Routing`, `Upstream` and narrative fields),
`PROCESSED.jsonl` (append-only, last-wins per `entry_id`; fields
`entry_id`, `title`, `archive`, `archive_unixtime`, `processed`,
`disposition`, and `annotated` on corrections; older
dispositions name spec paths, newer ones issue numbers, `already-tracked` or
`needs-clarification`), and `README.md` stating the rules: never edit an
archived file or ledger line, never treat a file here as input, committed for
durability but never propagated (bootcamper text). `citations.py verify`
requires each archive to be named by a ledger entry; `compact-dev-environment`
may prune archives but never ledger lines.

### 5.56 `docs/`

Mirrored to the public repo except two maintainer pages.

- `index.html`, `index.css`, `images/` and `.nojekyll` (user-facing,
  propagated; moved here from the public repo by #452): the GitHub Pages
  quick-start site, one page with Before you start (plan, MCP network access,
  Python 3, an empty folder, recommended data), install and start for Claude
  Desktop (with its marketplace URL) and the Claude Code CLI, what happens
  next, tips (model and effort, bootcamp commands, update or uninstall),
  troubleshooting and other assistants. A header comment says its commands
  come from `README.md` and `docs/README.md` and must follow them. It carries
  this repo's slug and `senzing-bootcamp@senzing-bootcamp-dev`, rewritten to
  the public ones on propagation. `.nojekyll` is empty and makes Pages serve
  the files as-is.

- `README.md` (user-facing, propagated): Claude Code CLI install on macOS,
  Linux, WSL and Windows; `claude plugin marketplace add` with this repo's
  slug (rewritten to the public slug on propagation) and `claude plugin
  install senzing-bootcamp@senzing-bootcamp-dev` (the marketplace name is
  rewritten to `senzing-bootcamp` on propagation); update; model guidance
  (Sonnet for most modules, Opus for the correctness-critical ones) and an
  example `claude --model ... --effort medium --permission-mode auto`; the shipped
  slash commands (`/start-bootcamp`, `/bootcamp-feedback`, `/graduate`,
  `/bootcamp-note`, `/package-bootcamp`) with their plain-English
  equivalents; uninstall.
- `development.md` (maintainer, excluded from propagation): install
  `requirements-dev.txt`, run `python3 -m unittest discover -s tests`; why
  fpdf2, Pillow and imageio-ffmpeg are dev-only, the fpdf2 skip notice
  (silenced by `SBCP_QUIET_FPDF2_NOTICE=1`) and the two-leg CI matrix;
  installing the development plugin as `senzing-bootcamp@senzing-bootcamp-dev`
  beside the published one, enabled one at a time, and the one-time re-add for
  an older install (#449); the US
  English convention (INV-253, `tests/test_us_english_spelling.py`, waivers
  by path, word and count; listed exceptions); what downstream ports may rely
  on (`invariant-manifest.json`, INV-311, INV-313); a pointer to
  `FAMILY_WORKFLOW.md` as the normative home (never restated, INV-300); the
  INV-316 rule that a named command ships here or carries a marker
  (*(children only)*, *(retired)*, *(user level)* backed by an overlay); and
  the maintainer command index (INV-302: must match the shipped skills both
  ways) grouped Triage feedback, Development loop, Publish.
- `FAMILY_WORKFLOW.md` (normative family-wide, excluded from propagation):
  roles of the parent, its public mirror and four child ports with their
  invariant prefixes; rules R1–R12: the parent owns the curriculum and
  children never fork or renumber (R1); propagation is a pull from a tag
  (R2); public repos hold only installables (R3); the canonical operation
  register, binding both ways (R4, INV-316) with phase, parent and child
  requirement and boundary per operation; the four-phase per-change flow
  (generate issues, develop, test, publish; only test-to-develop goes back)
  plus the parent-only maintenance track; topology; issue ownership (R5
  specs deprecated, R6 owner files, R7 escalation closes on arrival, R8
  approval before action, with the choosing operation reporting dependencies
  with evidence and naming one issue); release and propagate boundaries (R9,
  R10); invariant registers and the inherited-disposition register (R11);
  one supersession syntax with three markers and two statuses (R12,
  INV-313); `PARENT_VERSION`/`PARENT_COMMIT` provenance names; the five live
  exceptions to the `specs/` freeze; bootstrapping a child (components A–I);
  and §10 dated amendments, each with Was / Now / For a child, newest
  first.

### 5.57 `README.md` and `MIGRATION.md`

Root `README.md` (user-facing, propagated with the slug rewrite): what the
eleven modules cover, requirements (network access to the Senzing MCP
server, a Claude Max 5x plan or several Pro windows, optionally a business
problem and 5,000–20,000 records), the supported interfaces, a step-by-step
Claude Desktop install (marketplace URL, Sync, Install, mode auto, Sonnet,
medium effort, "Start the bootcamp"), what the bootcamper finishes with
(working code and data, a recap PDF linking the shipped example PDF, a
`production/` starter), and troubleshooting (Desktop needs `git`).

`MIGRATION.md` (maintainer, excluded): the plugin began as a port of the
Kiro Power `docktermj/senzing-bootcamp-kiro-powers`. It gives the Kiro to
Claude path mapping (steering to skills, hooks to `hooks.json` plus scripts,
`mcp.json` to `.mcp.json` minus Kiro-only keys, config conventions), what is
not migrated, the migration procedure (run `scripts/sync-check.sh`, port per
mapping, smoke-test, update `.sync-state.json`, bump the version, commit),
the porting roadmap and per-file checklist by phase, and historical status
logs (phases 1–3, the hook-gating fix, graduation and feedback v0.2.0, the
bundled visualization app v0.3.0). It is a historical record; it is not
updated by current workflows.

### 5.58 `.sync-state.json` and `scripts/sync-check.sh`

Kiro-to-Claude sync infrastructure, excluded from propagation.
`.sync-state.json` records `source` (`repo`, `local` path, `branch`),
`syncedCommit`, `syncedCommitShort`, `syncedDate` and `notes` (the commit the
plugin was scaffolded from, bumped per migration).

`scripts/sync-check.sh [kiro-path]` (bash, `set -euo pipefail`) reads the
state with inline `python3`, expands `~`, and defaults the Kiro path to
`source.local`. Exit 1 when the state file is missing, the Kiro path has no
`.git`, or the synced commit is not in the Kiro repo. It warns (no exit)
when the synced commit is not an ancestor of HEAD. It prints the Kiro repo,
synced commit and HEAD, then either "no changes in mapped content paths" or
a `git diff --stat` over `senzing-bootcamp` and `.kiro/hooks` with the
full-diff command and porting reminder; exit 0.

### 5.59 `.github/linters/`

Configuration for the reusable `lint-workflows.yaml` job (super-linter).
`zizmor.yaml` disables `secrets-outside-env` and sets `unpinned-uses` to a
`ref-pin` policy for all actions, so the org's shared
`senzing-factory/build-resources` workflow may be consumed by tag while
third-party actions stay SHA-pinned (enforced by
`tests/test_ci_workflow_guards_the_fpdf2_matrix.py`). `.jscpd.json` is `{}`,
dropping super-linter's zero-duplication threshold because skills restate
passages by design. `README.md` explains both.

### 5.60 `requirements-dev.txt`

Development-only dependencies (never a plugin runtime requirement): `fpdf2`
(measures the preferred PDF renderer; without it those tests skip, #30),
`Pillow` and `imageio-ffmpeg` (the recap-video renderer's frame drawing and
ffmpeg fallback; without them `tests/test_recap_video.py` skips its drawing
tests, #299); `pytest` is mentioned as optional and commented out. Tests stay
stdlib-only and probe availability with `importlib.util.find_spec` (INV-108).

### 5.61 `resources/`

Maintainer-only brand assets, never propagated: `senzing-style-reference.pdf`
(the brand guide whose values `brand_tokens.py` inlines),
`certificate-of-completion.pdf` (the template the recap PDF's certificate
page is scaled from; cited by `generate_recap_pdf.py` and
`tests/test_recap_pdf_certificate.py`), and `2026-sz-light.png` (a logo
asset). No shipped code reads these files at runtime.

### 5.62 `tests/_wrapped_text.py` and `tests/_maintainer_surface.py`

Shared stdlib test helpers (INV-108).

`_wrapped_text.py` is the one wrap-aware matcher for guards about a phrase in
Markdown prose (INV-346, #426). `blocks(text)` cuts text into blocks of
`(lineno, line)` pairs: a blank line, a code-fence line (three backticks or
tildes, possibly indented; closed only by the same character), each table
row, each ATX heading and the leading front matter are boundaries or blocks
of their own; inside a fence only a blank line ends a block; outside a fence
leading `>` markers are stripped; consecutive list lines stay one block.
`match_lines(text, pattern)` collapses each block's whitespace to single
spaces, trims it, runs the compiled pattern per block, and returns the
1-based line where each match starts.

`_maintainer_surface.py` derives the maintainer operation set once
(INV-300): `skills()` (directories under `.claude/skills/` holding a
`SKILL.md`), `command_files()` and `commands()` (`.md` files directly under
`.claude/commands/`, empty when absent), `operations()` (their union),
`ships(name)` (leading slash ignored), `skill_file(name)`, and
`command_files_under_test()`, which returns the shipped commands or, when
none ship, the fixtures under `tests/fixtures/maintainer-commands/` so the
INV-303 enforcer never runs over an empty set. Guards for INV-302, INV-316,
INV-318 and INV-319 import it.

## 6. Exact contracts

### 6.1 Public API

Every public (no leading `_`) top-level function, class and constant of every
tracked Python source outside `tests/`, with bodies skipped as `...`. Public
methods and fields of public classes are included.

#### 6.1.1 `.claude/skills/auto-test/autotest.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/autotest.py`:

```python
SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
SANDBOX_ROOT = Path.home() / "senzing-autotest"
REPORT_DIR = SANDBOX_ROOT / "reports"
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"
MCP_URL = "https://mcp.senzing.com/mcp"
def make_worktree(root, ref):
    ...
def drop_worktree(worktree):
    ...
def build_sandbox(root, seed):
    ...
def write_mcp_config(root):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.2 `.claude/skills/auto-test/mcp_probe.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/mcp_probe.py`:

```python
SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
BASELINE = SKILL_DIR / "baseline" / "mcp-snapshot.json"
CONTRACT_TEST = REPO_ROOT / "tests" / "test_mcp_call_contracts.py"
DEFAULT_URL = "https://mcp.senzing.com/mcp"
CONTRACT_STALE_DAYS = 90
NEVER_CALL = frozenset({"submit_feedback", "download_resource"})
CONTENT_PROBES = (("get_capabilities", {}),)
PROSE_VALUES = {
    ("mapping_workflow", "action"): r"Actions:\s*([a-z_,\s]+?)\.",
    ("generate_scaffold", "language"): r"Languages:\s*([a-z#,\s]+?)\.",
    ("search_docs", "category"): r"'category' to filter:\s*([a-z_,\s]+?)(?:\.|\n|$)",
    ("sdk_guide", "language"): r"\d+\s+languages\s*\(([^)]+)\)",
    ("sdk_guide", "platform"): r"\d+\s+platforms\s*\(((?:[^()]|\([^)]*\))*)\)",
    ("get_sample_data", "dataset"): r"Available datasets:\s*((?:[^.()]|\([^)]*\))+)",
}
PROBE_SENTINEL = "zzz_probe_invalid"
PROBE_MATRIX = (
    ("mapping_workflow", "action", {}),
    ("sdk_guide", "topic", {}),
    ("sdk_guide", "platform", {"topic": "install"}),
    ("sdk_guide", "language", {"topic": "install"}),
    ("get_sdk_reference", "topic", {}),
    ("reporting_guide", "topic", {}),
    ("generate_scaffold", "workflow", {"language": "python"}),
    ("generate_scaffold", "language", {"workflow": "initialize"}),
    ("get_sample_data", "dataset", {}),
    ("search_docs", "category", {"query": "entity resolution"}),
)
ENUMERATED = "enumerated"      # rejected, and named the valid values
OPAQUE = "opaque"              # rejected, but did not say what is valid
SILENT = "silently-accepted"   # took the garbage value without complaint
FREE_TEXT_PARAMS = frozenset({"version", "filter", "query", "source", "email",
                              "firstname", "lastname", "message", "how_heard",
                              "file_path", "filename", "repo", "scale"})
CROSS_TOOL_AGREEMENT = (("language", ("sdk_guide", "generate_scaffold")),)
ALIASES = {
    "c#": "csharp", "cs": "csharp", "dotnet": "csharp",
    "node": "typescript", "nodejs": "typescript", "js": "typescript",
    "py": "python",
}
CONFABULATIONS = (
    ("add_data_source", "register_data_source"),
    ("addDataSource", "registerDataSource"),
    ("close_export", "close_export_report"),
    ("G2Engine", "SzEngine"),
    ("NAME_ORG", "BUSINESS_NAME_ORG"),
)
NEGATION_CUES = re.compile(
    r"(?i)\b(never|not|non-|no\s|instead|wrong|incorrect|avoid|CLI command|"
    r"rather than|do NOT|confabulat|deprecated|V3)\b")
BREAKING, WATCH, INFO = "BREAKING", "WATCH", "INFO"
def rpc(url, method, params=None, timeout=30, mid=1):
    ...
def extract_prose_values(tool_name, description):
    ...
def probe_values(url, timeout=30):
    ...
def snapshot(url, timeout=30, probe_content=True, probe_values_too=True):
    ...
def accepted_values(tool_meta, param):
    ...
def record_verified_extras(live, url, timeout=30):
    ...
def diff_baseline(live, base):
    ...
def verify_literal(url, tool, param, value, timeout=30, _cache={}):
    ...
def conformance(live, url=None):
    ...
def server_quality(live, url=None):
    ...
def cross_tool(live):
    ...
def audit_static_contract(live):
    ...
def load_baseline():
    ...
def save_baseline(snap):
    ...
def render(findings, as_json=False):
    ...
def collect(live, url=None):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.3 `.claude/skills/auto-test/transcript_lint.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/transcript_lint.py`:

```python
SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
BREAKING, WATCH, INFO = "BREAKING", "WATCH", "INFO"
APPARATUS = {
    "journey map": re.compile(r"(?i)journey map"),
    "before/after": re.compile(r"(?i)\bbefore\s*(?:/|and)\s*after\b"),
    "step overview": re.compile(r"(?i)step overview|what we'?ll (?:do|cover)"),
    "time estimate": re.compile(r"(?i)\b(?:takes|about|approx\w*)\s+\d+\s*(?:-|to)?\s*\d*\s*minutes?\b"),
    "model nudge": re.compile(r"(?i)\b(?:opus|sonnet|haiku)\s*5?\b.*\beffort\b|switch (?:to|the) model"),
}
POINTER = "\U0001f449"  # 👉
def load(path):
    ...
def check_one_pointer_per_turn(turns):
    ...
def check_module_numbers(turns):
    ...
def check_or_joined_choices(turns):
    ...
def check_apparatus(turns, phase):
    ...
def check_internal_markers(turns):
    ...
def check_repeat_questions(turns):
    ...
CHECKS = (check_one_pointer_per_turn, check_module_numbers, check_or_joined_choices,
          check_internal_markers, check_repeat_questions)
def lint(turns, phase=None):
    ...
def render(findings, turn_count):
    ...
def selftest():
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.4 `.claude/skills/auto-test/walk.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/walk.py`:

```python
SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "senzing-bootcamp"
POINTER = "\U0001f449"
FORBIDDEN_TOOLS = ("mcp__senzing__submit_feedback", "mcp__senzing__download_resource")
PERSONAS = {
    "terse": "You answer in as few words as possible — often a single word or "
             "number. You never elaborate and never ask questions.",
    "verbose": "You answer at length, volunteering extra context about your data "
               "and your company that was not asked for.",
    "confused": "You are new to entity resolution. Roughly one answer in three, "
                "you ask a short clarifying question back instead of answering.",
    "impatient": "You try to skip ahead. You often ask to jump straight to loading "
                 "data or seeing results rather than answering the current question.",
    "offscript": "You occasionally answer with something that does not fit the "
                 "question asked, or pick an option number that was not offered.",
}
BOOTCAMPER_BRIEF = """You are role-playing a person taking a hands-on Senzing \
entity-resolution bootcamp inside their terminal. Someone is guiding you.

Your situation: you work at a mid-sized insurance company. You want to find \
duplicate and linked customer records across two systems — a claims database and a \
policy database. You know SQL, you are comfortable in Python, and you are on Linux.

{persona}

Rules:
- Reply with ONLY what you would type. No narration, no stage directions, no
  markdown headers, no meta-commentary about the exercise.
- If you are asked to choose from a numbered list, reply with the number or the
  option text.
- Keep it to a couple of sentences at most.
- Never mention that this is a test or a simulation."""
def visible_text(stream_json_text):
    ...
def bootcamper_reply(prompt_text, persona, model, timeout=180):
    ...
def run_walk(project, out_path, turns, persona, mcp_config, model, bootcamper_model,
             opening, isolate_config, timeout):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.5 `.claude/skills/compact-dev-environment/citations.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/compact-dev-environment/citations.py`:

```python
INV = re.compile(r"INV-\d{3}")
INV_DEF = re.compile(r"^- \*\*(INV-\d{3})\*\*", re.MULTILINE)
SOURCE = re.compile(r"\(Source: `([^`]+)`")
LEDGER_HEADING = re.compile(r"^## (.+)$", re.MULTILINE)
META_SPECS = {"INVARIANTS", "todo", "IMPLEMENTED", "DECLINED", "RENUMBERING"}
IGNORE_MARKER = "citations.py: ignore-file"
AREAS = (
    ("plugin", Path("plugins") / "senzing-bootcamp"),
    ("specs", Path("specs")),
    ("tests", Path("tests")),
    ("skills", Path(".claude") / "skills"),
)
def defined_invariants(repo: Path) -> list:
    ...
def citations_by_area(repo: Path) -> dict:
    ...
def spec_names(repo: Path) -> set:
    ...
def declined_headings(repo: Path) -> set:
    ...
def ledger_headings(repo: Path) -> set:
    ...
def invariant_sources(repo: Path) -> dict:
    ...
def feedback_state(repo: Path) -> tuple:
    ...
def cmd_census(args) -> int:
    ...
def cmd_verify(args) -> int:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.6 `.claude/skills/compact-dev-environment/widened_scope.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/compact-dev-environment/widened_scope.py`:

```python
ENTRY = re.compile(r"^- \*\*(INV-\d{3})\*\* — (.+?)(?=\n- \*\*INV-|\n##|\Z)", re.M | re.S)
IDENT = re.compile(r"INV-\d{3}")
SCOPE_VERBS = ("supersed", "generalis", "generaliz", "amends", "restates",
               "replaces", "reverses", "retiring", "retires", "widens", "widened")
EXTRA_VERBS = ("extends", "hardens", "complements", "constrains", "corrects")
def entries(repo: Path) -> dict:
    ...
def one_way_links(bodies: dict, verbs: tuple) -> list:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.7 `.claude/skills/delegate-to-mcp-server/coverage_ledger.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/delegate-to-mcp-server/coverage_ledger.py`:

```python
LEDGER = Path("specs") / "mcp-coverage.jsonl"
PLUGIN = Path("plugins") / "senzing-bootcamp"
INVARIANTS = Path("specs") / "INVARIANTS.md"
VERDICTS = (
    "delegate",
    "contradicted",
    "retire-workaround",
    "keep-server-lacks-it",
    "keep-by-design",
    "not-a-senzing-fact",
)
REASON_REQUIRED = ("keep-by-design",)
PATTERNS = (
    ("attributes", r"\b(?:NAME_ORG|NAME_FULL|RECORD_TYPE|DATA_SOURCE|RECORD_ID)\b",
     "search_docs(category='data_mapping')"),
    ("flags", r"\bSZ_[A-Z][A-Z0-9_]{4,}\b",
     "get_sdk_reference(topic='flags')"),
    ("error-codes", r"\bSENZ-?\d{4}\b",
     "explain_error_code"),
    ("sdk-shapes", r"\b(?:search_by_attributes|get_entity_by_entity_id|find_network_by_entity_id|"
                   r"add_record|export_json_entity_report|why_entities|how_entity_by_entity_id|"
                   r"register_data_source|init_default_config)\b",
     "get_sdk_reference(topic='parameters', language=…)"),
    ("install-config", r"SENZING_[A-Z_]+|senzingsdk-[a-z]+|apt\.senzing\.com|\bSUPPORTPATH\b",
     "sdk_guide(topic='install' | 'configure')"),
    ("dated-claims", r"(?:MCP )?server \d+\.\d+\.\d+|verified \d{4}-\d{2}-\d{2}",
     "whichever tool owns the claim"),
)
LIMITATION_PATTERN = re.compile(
    r"\b(?:cannot|can not|does not|doesn't|no longer|never returns|is not able|unobtainable|"
    r"not documented|empty|fails|rejects)\b",
    re.IGNORECASE,
)
def read_ledger(repo: Path) -> dict:
    ...
def iter_markdown(repo: Path):
    ...
def inventory(repo: Path, only: str = None) -> list:
    ...
def cmd_inventory(args) -> int:
    ...
def expiry_reason(row: dict, server: str, index: str = None) -> str:
    ...
def produced_by(row):
    ...
def cmd_stale(args) -> int:
    ...
def cmd_record(args) -> int:
    ...
def cmd_summary(args) -> int:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.8 `.claude/skills/dry-run/coverage_reports.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/coverage_reports.py`:

```python
INV_DEF = re.compile(r"\*\*INV-(\d{3})\*\*")
INV_REF = re.compile(r"INV-(\d{3})")
LEDGER_HEAD = re.compile(r"^## (\S+)$", re.M)
FILES_CHANGED = re.compile(r"^- \*\*Files changed:\*\*(.*)$", re.M)
PATH_IN_TICKS = re.compile(r"`([A-Za-z0-9_./{}*-]+\.(?:md|py|sh|json|yaml|yml|js|png|pdf))`")
MCP_NEGATIVE = re.compile(
    r"MCP-NEGATIVE:\s*(?P<claim>.+?)\s*(?:—|--)\s*owner:\s*(?P<owner>.+?)\s*(?:—|--)\s*"
    r"server\s*(?P<version>[0-9][0-9.]*)\s*,\s*(?P<date>\d{4}-\d{2}-\d{2})"
)
MCP_NEGATIVE_TOKEN = re.compile(r"MCP-NEGATIVE:")
NEGATIVE_OPT_OUT = "MCP-NEGATIVE-SCAN: ignore-file"
NEGATIVE_ROOTS = ("plugins", "tests", os.path.join(".claude", "skills"), "docs")
NEGATIVE_EXTRA_FILES = (os.path.join("specs", "DECLINED.md"),)
PROSE_ROOT = os.path.join("plugins", "senzing-bootcamp")
MCP_TOOLS = (
    "explain_error_code", "search_docs", "sdk_guide", "get_sdk_reference", "reporting_guide",
    "generate_scaffold", "get_sample_data", "find_examples", "mapping_workflow",
    "analyze_record", "get_capabilities", "download_resource", "submit_feedback",
)
PROSE_TOOL = re.compile(r"(?i)(%s)" % "|".join(MCP_TOOLS))
PROSE_ABSENCE = re.compile(
    r"(?i)documents? (?:neither|no\b)|returns? no\b|carr(?:y|ies) no\b|contains? no\b|has no\b|"
    r"no indexed document|appears? nowhere|nowhere in|is not documented|not documented by|"
    r"returns? only|only generic|makes no\b|never names|never documents|"
    r"does (?:\*\*)?not(?:\*\*)? (?:name|document|carry|return|list|mention|cover|answer|contain)"
)
PROSE_DATED = re.compile(r"\b20\d\d-\d\d-\d\d\b|\bserver\s+\d+\.\d+")
PROSE_QUOTED_HISTORY = "MCP-NEGATIVE-SCAN: quoted-history"
PROSE_NOT_A_CLAIM = "MCP-NEGATIVE-SCAN: not-a-tool-claim"
PROSE_MARKER_WINDOW = 6
SKIP_DIRS = {"__pycache__", "vendor", "node_modules", ".git", ".history", ".pytest_cache"}
def report_invariants(repo):
    ...
OUTCOME_MAX = 50
FULLY_SUPERSEDED_LINE = re.compile(r"\*Fully superseded[^*]*\*(?P<ids>.*)")
def fully_superseded(inv_txt):
    ...
DEV_GROUP = "development record itself"
STATIC_ARTIFACT = (
    r"plugins/|"
    r"\bmodule-\d\d|\bModule \d|"
    r"SKILL\.md|phase[0-9A-Za-z-]*\.md|ground-rules\.md|module-completion\.md|"
    r"scripts/[\w-]+\.py|hooks/[\w-]+\.py|"
    r"bootcamp_progress\.json|bootcamp_preferences\.yaml|bootcamp_recap\.md|"
    r"\bthe progress file\b|"
    r"\bgraduation\b|bootcamp[- ]onboarding|bootcamp[- ]preparation"
)
MODULE_TABLE_ROW = re.compile(r"(?m)^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*(?:Required|Optional)")
MODULE_TABLE = os.path.join(
    "plugins", "senzing-bootcamp", "skills", "bootcamp-preparation", "SKILL.md")
def module_display_names(repo):
    ...
def shipped_artifact_re(repo):
    ...
INDEX_GROUP = re.compile(r"(?m)^- \*\*(?P<name>[^*]+)\*\* — .*?(?=^- \*\*|\Z)", re.DOTALL)
TEXT_SUFFIXES = frozenset(
    (".md", ".py", ".json", ".yaml", ".yml", ".sh", ".ps1", ".txt", ".js", ".html", ".css")
)
def find_uncited_in_shipped(repo):
    ...
def report_shipped(repo):
    ...
GAP_CLASS_ORDER = ("real", "moved", "bare", "glob")
GAP_CLASS_LABEL = {
    "real": "names a real current file",
    "moved": "path no longer exists (moved/renamed)",
    "bare": "bare filename — an artifact, not a repo path",
    "glob": "glob — the scan cannot match a wildcard",
}
def classify_gap(repo, path):
    ...
def criteria_name_the_file(repo, spec_name, path):
    ...
def report_affected(repo):
    ...
def find_negatives(repo):
    ...
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
    ...
def find_enumeration_rationales(found):
    ...
def find_malformed_negatives(repo):
    ...
def find_unmarked_negatives(repo):
    ...
def report_unmarked(repo):
    ...
def version_tuple(version):
    ...
def negatives_due(found, current):
    ...
def report_negatives(repo, current_server=None):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.9 `.claude/skills/dry-run/measure_label_occlusion.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/measure_label_occlusion.py`:

```python
def measure(png, fills, min_px=150, ink_below=250):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.10 `.claude/skills/dry-run/scaffold_project.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/scaffold_project.py`:

````python
DIRS = (
    "config",
    "data/raw",
    "data/mapping",
    "data/samples",
    "data/temp",
    "database",
    "docs/progress",
    "docs/feedback",
    "docs/visualizations",
    "docs/mapping",
    "logs",
    "src/transform",
    "src/load",
    "src/system_verification",
)
LONG_MODULE_NAME = "Data Quality, Mapping, and Transformation"
IN_PROGRESS_HEADING = f"{LONG_MODULE_NAME} — in progress"  # parses to the 41-char title
PROGRESS = {
    "current_module": "data_quality_mapping",
    "current_step": "11",
    "modules_completed": [
        "entity_resolution_concepts",
        "business_problem",
        "sdk_setup",
        "system_verification",
        "truthset_visualization",
        "data_collection",
    ],
    "selected_modules": [
        "bootcamp_preparation",
        "entity_resolution_concepts",
        "business_problem",
        "sdk_setup",
        "system_verification",
        "truthset_visualization",
        "data_collection",
        "data_quality_mapping",
        "data_processing",
        "query_visualize_discover",
        "graduation",
    ],
    # Names a container that does not exist -> exercises warn-and-continue (INV-101).
    "docker_containers": [
        {"name": "bootcamp-dryrun-absent", "image": "postgres:16", "purpose": "repository"}
    ],
    "license_record_limit": 0,
    "step_history": {
        "data_quality_mapping": {
            "last_completed_step": "11",
            "updated_at": "2026-01-01T00:00:00-07:00",
        }
    },
}
PREFERENCES = """path: core
programming_language: Python
name: Ada Lovelace
os: Linux
arch: x86_64
git_init: true
verbosity:
  preset: standard
"""
SEEDED_PREFERENCES = """path: core
selected_modules:
  - bootcamp_preparation
  - entity_resolution_concepts
  - business_problem
  - sdk_setup
  - system_verification
  - truthset_visualization
  - data_collection
  - data_quality_mapping
  - data_processing
  - query_visualize_discover
  - graduation
verbosity:
  preset: minimal
programming_language: Java
"""
RECAP = f"""# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-01-01T09:00:00-07:00
**Programming language:** Python
**Path:** Core
**Plugin version:** 0.0.0-dryrun

---

## Data collection — 2026-01-01T11:00:00-07:00

### Information Shared
- CORD datasets and the Senzing Entity Specification.

### Questions & Responses
- **Q:** How would you like to provide the data for this source?
    - **R:** Option 2, a file path.

### Actions Taken
- Registered `data/raw/customers.csv` in `config/data_sources.yaml`.

### End-of-Module Summary
**What you accomplished:**
- Collected one source into `data/raw/`.

**Files produced:**
- `data/raw/customers.csv` — the raw source.

**Why it matters:** Nothing downstream runs without the data in the project.

---
"""
CHECKPOINT = f"""<!-- RECAP-CHECKPOINT:START -->
## {IN_PROGRESS_HEADING}

### Information Shared
- A line with an em dash — an ellipsis … and a middle dot ·
- Mapping CUSTOMERS to the Senzing Entity Specification.

### Questions & Responses
- **Q:** Which mapping mode would you like?
    - **R:** Verbose.

### Actions Taken
- Profiled `data/raw/customers.csv`.

### End-of-Module Summary
**What you accomplished:**
- Mapping in progress.
<!-- RECAP-CHECKPOINT:END -->
"""
FEEDBACK = """# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp.

**Started:** 2026-01-01

## Your Feedback

## Improvement: A precious entry that must survive graduation untouched

**Date:** 2026-01-01
**Module:** Data collection
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the banner did not appear
**Upstream:** not applicable

### What happened

If graduation's normalization pass rewrites, empties or deletes this file, INV-067 is
broken and this sentence will be missing.
"""
MESSY_MARKDOWN = """## Messy heading
text immediately after a heading, no blank line
- a list with no blank line before it
```
a fenced block with no info string
```
**Label :** colon spacing is wrong
"""
RECORDS = "\n".join(
    json.dumps(r)
    for r in (
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1001",
            "FEATURES": [
                {"NAME_FULL": "Aurelia Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Way, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1002",
            "FEATURES": [
                {"NAME_FULL": "Relia Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Way, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-1003",
            "FEATURES": [
                {"NAME_FULL": "Aurelia B Quorndon"},
                {"DATE_OF_BIRTH": "1980-05-14"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "3 Underhill Street, Las Vegas, NV 89101, US"},
            ],
        },
        {
            "DATA_SOURCE": "VERIFY",
            "RECORD_ID": "V-2001",
            "FEATURES": [
                {"NAME_FULL": "Tobias Fennimore"},
                {"DATE_OF_BIRTH": "1962-11-02"},
                {"ADDR_TYPE": "HOME",
                 "ADDR_FULL": "884 Kestrel Row, Reno, NV 89502, US"},
            ],
        },
    )
)
MODES = ("mid", "fresh", "seeded")
ALL_MODES = frozenset(MODES)
PIPELINE_DEFAULTS = (
    ("CONFIGPATH", "/etc/opt/senzing"),
    ("RESOURCEPATH", "/opt/senzing/er/resources"),
    ("SUPPORTPATH", "/opt/senzing/data"),
)
FIXTURE_MAP = [
    # Mid only: Module 2 Step 8 writes this file, so --fresh/--seeded (which start before it)
    # must not have it, or the env script's pre-Step-8 branch is never walked (#328).
    ("config/engine_config.json", "config/engine_config.json", frozenset({"mid"}),
     "COMPLETE PIPELINE -> passes the config pre-flight and reaches the SDK gate "
     "(exit 1, libSz.so) or initializes where the SDK is present"),
    ("config/engine_config_incomplete.json", "config/engine_config_incomplete.json", ALL_MODES,
     "empty PIPELINE -> stops AT the config pre-flight (exit 2); the other gate, kept "
     "so both stay covered"),
    ("config/bootcamp_progress.json", "config/bootcamp_progress.json", frozenset({"mid"}),
     "makes every hook consider the bootcamp active; mid-module so resume paths run"),
    ("  └ docker_containers", None, frozenset({"mid"}),
     "names an ABSENT container -> warn-and-continue (INV-101)"),
    ("config/bootcamp_progress.json", "config/bootcamp_progress.json", frozenset({"fresh", "seeded"}),
     "empty {} -> hooks see a project with NO active bootcamp; onboarding runs from the top"),
    ("config/bootcamp_preferences.yaml", "config/bootcamp_preferences.yaml", frozenset({"mid", "seeded"}),
     "saved verbosity + language to test honor-don't-ask (INV-133)"),
    ("config/bootcamp_preferences.yaml", "config/bootcamp_preferences.yaml", frozenset({"fresh"}),
     "deliberately EMPTY -> every question must be asked (the INERT direction of INV-133)"),
    ("docs/bootcamp_recap.md", "docs/bootcamp_recap.md", frozenset({"mid"}),
     "a completed section carrying all four subsections (INV-103)"),
    ("docs/progress/recap_checkpoint.md", "docs/progress/recap_checkpoint.md", frozenset({"mid"}),
     "an UNFINALIZED block -> fold idempotency, run it 3x (INV-059). This fixture does "
     "NOT reach the PDF cover's 46-char chip clip by any documented sequence, so do not "
     "report that path as exercised. Folded, its heading sits inside the "
     "RECAP-CHECKPOINT fence, which generate_recap_pdf.py strips before module parsing, "
     "so the section is absent from the cover, the contents and the body (audit_recap "
     "warns, correctly, that a module was folded but never finalized). Unfenced, as "
     "module-completion step 2d leaves it, parse_recap strips the '— in progress' "
     "suffix, so the chip is the bare 41-character title, and no real module title is "
     "long enough to clip. The chip-clip path is covered by unit test in "
     "tests/test_recap_pdf_font_safety.py. Measured 2026-09-24"),
    ("docs/feedback/...FEEDBACK.md", "docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md", ALL_MODES,
     "a precious entry the normalizer must leave byte-identical (INV-067)"),
    ("docs/loading_strategy.md", "docs/loading_strategy.md", frozenset({"mid"}),
     "deliberately messy Markdown for the normalizer (INV-060)"),
    ("src/system_verification/verification_data.jsonl",
     "src/system_verification/verification_data.jsonl", frozenset({"mid"}),
     "the file System verification Step 2 writes, so a resumed run finds it; also the "
     "records for the viz server's --no-serve snapshot build"),
]
def mode_name(fresh: bool, seeded: bool) -> str:
    ...
def fixtures_for(mode: str):
    ...
def explain(mode: str = "mid"):
    ...
def build(root: Path, fresh: bool, seeded: bool = False) -> None:
    ...
def main() -> int:
    ...
````

<!-- markdownlint-enable MD013 -->

#### 6.1.11 `.claude/skills/feedback-to-issues/feedback_ledger.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/feedback-to-issues/feedback_ledger.py`:

```python
LEDGER_NAME = "PROCESSED.jsonl"
ARCHIVE_DIR = "feedback"
ARCHIVE_STEM = "SENZING_BOOTCAMP_PLUGIN_FEEDBACK"
def normalize(text: str) -> str:
    ...
def entry_id(entry_text: str) -> str:
    ...
def split_entries(text: str) -> list:
    ...
def read_ledger(repo: Path) -> dict:
    ...
def classify(candidate: Path, repo: Path) -> dict:
    ...
def cmd_check(args) -> int:
    ...
def cmd_commit(args) -> int:
    ...
def cmd_annotate(args) -> int:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.12 `.claude/skills/production-readiness-audit/conformance.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/production-readiness-audit/conformance.py`:

```python
DEFAULT_REPO = pathlib.Path(__file__).resolve().parents[3]
INV_ID = re.compile(r"INV-\d{3}")
SCAN_ROOTS = ("plugins/senzing-bootcamp", ".claude/skills", ".claude/skill-overlays")
RETIRED_ROOTS = (".claude/commands",)
UNCOUNTED_RULE_HOMES = ("docs/",)
ANCHORED_RULE = re.compile(
    r"^\s*>?\s*⛔"
    r"|\*\*[^*]*\b(?:MUST|NEVER|ALWAYS)\b[^*]*\*\*"
    r"|^\s*-?\s*\*\*.*?\*\*.*\b(?:MUST|NEVER)\b"
)
HARD_RULE = ANCHORED_RULE
CODE_SPAN = re.compile(r"`[^`]*`")
IMPERATIVE = (r"never|always|do not|don't|use|keep|prefer|treat|stop|ask|read|write|check"
              r"|state|name|strip|report|verify|cite|record|leave|derive|scope")
MID_LINE_RULE = re.compile(r"⛔\s*(?:\*\*|[A-Z]|(?:%s)\b)" % IMPERATIVE, re.IGNORECASE)
NOUN_USE = re.compile(
    r"(?:\b(?:a|an|the|its|any|each|every|marked|old|same)\s+(?:\w+\s+)?)⛔"
    r"|⛔\s*(?:gates?|convention|marker|lead-in|sign|glyphs?)\b",
    re.IGNORECASE)
def classify(line):
    ...
def paths(args):
    ...
def shipped_markdown(plugin):
    ...
def rel(p, repo):
    ...
def sections(lines):
    ...
def cmd_rules(args):
    ...
def rule_rows(lines):
    ...
def own_citations(lines, i):
    ...
def cmd_per_rule(args):
    ...
def added_rule_lines(repo, ref, upto=None):
    ...
def added_rules_outside_the_corpus(repo, ref, upto=None):
    ...
def last_audit_ref(repo):
    ...
def cmd_since(args):
    ...
def cmd_reverse_check(args):
    ...
def cmd_duplication(args):
    ...
def cmd_enumerations(args):
    ...
def cmd_size(args):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.13 `.claude/skills/release/release.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/release/release.py`:

```python
SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_REPO = SKILL_DIR.parent.parent.parent
RELEASE_BRANCH = "main"
CHANGELOG_NAME = "CHANGELOG.md"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
MANIFEST_REL = "plugins/senzing-bootcamp/.claude-plugin/plugin.json"
VERSION_SITES = (
    {
        "path": MANIFEST_REL,
        "pattern": re.compile(r'^(\s*"version":\s*")(\d+\.\d+\.\d+)(")', re.M),
        "why": "the plugin manifest -- the version Claude Code reports for the install",
    },
    {
        "path": "plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.md",
        "pattern": re.compile(r'^(\*\*Plugin version:\*\*[ \t]*)(\d+\.\d+\.\d+)([ \t]*)$', re.M),
        "why": ("the shipped reference recap's meta row -- "
                "tests/test_example_recap_sync.py pins it to the manifest"),
    },
    {
        "path": "BLUEPRINT.md",
        "pattern": re.compile(r'^(\s*"version":\s*")(\d+\.\d+\.\d+)(")', re.M),
        "why": ("BLUEPRINT.md's verbatim copy of the plugin manifest (section 3) -- "
                "/update-blueprint compares it with plugin.json line by line"),
    },
)
CHANGELOG_HEADER = """\
# Changelog

Every released version of the Senzing Bootcamp Claude Plugin, newest first. The
downstream development repositories (Kiro, ChatGPT, Copilot) port from a **tagged**
release rather than from HEAD, so an entry here with no matching git tag is not a
release anyone can target.

Written by `.claude/skills/release/release.py`. Do not hand-edit an entry's heading:
the version, this file and the tag are written together on purpose.
"""
SEED_NOTE = (
    "> Entries **%s and earlier** were reconstructed from git history when this file was\n"
    "> first created. They were not authored at release time, so they list commit subjects\n"
    "> rather than curated release notes.\n")
class Refusal(Exception):
    ...
def git(repo, *args, check=True):
    ...
def semver(text):
    ...
def tags_in_order(repo):
    ...
def bump(current, part):
    ...
def fmt(version):
    ...
def read_sites(repo):
    ...
def current_version(repo):
    ...
def rewrite_sites(repo, old, new):
    ...
def subjects_between(repo, start, end):
    ...
def tag_date(repo, ref):
    ...
def entry(version, date, bullets):
    ...
def seed_changelog(repo, tags):
    ...
def plan_changelog(repo, new, today, tags):
    ...
def check_preconditions(repo, allow_branch):
    ...
def check_target(repo, old, new, tags):
    ...
DIFF_LINE_BUDGET = 60
def show_diff(relpath, old_text, new_text):
    ...
def parse_args(argv):
    ...
def resolve_target(args, old):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.14 `.claude/skills/review-invariants/invariant_manifest.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/review-invariants/invariant_manifest.py`:

```python
REPO = pathlib.Path(__file__).resolve().parents[3]
INVARIANTS = REPO / "specs" / "INVARIANTS.md"
MANIFEST = REPO / "invariant-manifest.json"
ENTRY = re.compile(r"(?m)^- \*\*(INV-\d{3})\*\*\s*—\s*(.+?)(?=\n- \*\*INV-\d{3}\*\*|\n## |\Z)", re.S)
GROUP = re.compile(r"(?m)^- \*\*(.+?)\*\*\s*—.*?\n((?:.*\n)*?)(?=^- \*\*|\Z)")
SUMMARY_MAX = 300
SUPERSEDED_BULLET = re.compile(r"^\s*- \*\*Superseded by:\*\* (INV-\d{3})", re.M)
PARTLY_SUPERSEDED_BULLET = re.compile(r"^\s*- \*\*Partly superseded by:\*\* (INV-\d{3})", re.M)
SUPERSEDES_BULLET = re.compile(r"^\s*- \*\*Supersedes:\*\* (INV-\d{3})", re.M)
SUPERSESSION_WORDS = re.compile(r"supersede|Supersede|withdrawn|Corrected \d{4}|Amended \d{4}")
def flat(s):
    ...
def groups_by_id(text):
    ...
def sections_by_id(text):
    ...
def status_of(body):
    ...
def build():
    ...
def render(manifest):
    ...
def report(manifest, stream=sys.stdout):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.15 `.claude/skills/review-invariants/pending_invariants.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/review-invariants/pending_invariants.py`:

```python
REPO = Path(__file__).resolve().parents[3]
LEDGER = REPO / "specs" / "IMPLEMENTED.md"
INVARIANTS = REPO / "specs" / "INVARIANTS.md"
SPECS = REPO / "specs"
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
AWAITING = "awaiting the maintainer's sign-off; NOT minted"
HELD_IN_BLOCK = "must be approved before implementation"
AMENDMENT = "PROPOSED AMENDMENT"
AMENDMENT_AWAITING = "awaiting the maintainer's sign-off; NOT applied"
AMENDMENT_TARGET = re.compile(r"PROPOSED AMENDMENT to (INV-\d{3})")
HELD_IN_LEDGER = re.compile(r"\*\*HELD\s+(\d{4}-\d{2}-\d{2}):\*\*\s*(.+?)(?=\n\s*\n|\Z)", re.S)
BOILER = re.compile(r"\*\(written as NNN deliberately.*?\)\*\s*", re.S)
ENFORCER = re.compile(r"Enforced\s+by\s+`([^`]+)`")
ENFORCER_OPENS = re.compile(r"Enforced\s+by\s+`")
BULLET = re.compile(r"^\s+- .*⛔")
QUOTE = re.compile(r"\*\*(?:⛔\s*)?(.+?)\*\*", re.S)
LOC = re.compile(r"—\s*in `([^`]+)`")
DESCRIBED = re.compile(r"^\s+- `([^`]+)`[^—]*—\s*⛔\s*(.+?)(?:\s*\*\(.*)?$")
CITED = re.compile(r"\(INV-\d{3}\)")
def flat(s):
    ...
DEFERRAL_HEADER = re.compile(r"^- \*\*DEFERRED INVARIANT\b")
def blocks(include_resolved=False):
    ...
def hold_reason(block_text):
    ...
def parse(b):
    ...
def enforcer_label(p):
    ...
def queue():
    ...
def next_id():
    ...
RESOLUTION_ROOTS = (PLUGIN / "skills", PLUGIN / "scripts", PLUGIN, REPO)
RETIRED_COMMAND = re.compile(r"\.claude/commands/([a-z0-9][a-z0-9-]*)\.md")
def resolve(loc):
    ...
SITE_SUFFIXES = (".md", ".py")
def shipped_files():
    ...
FROZEN_MANIFEST = SPECS / "FROZEN-MANIFEST.txt"
def frozen_names():
    ...
def scan_scope():
    ...
def print_scan_scope(scanned, unscanned, ineligible):
    ...
def rel_to_repo(path):
    ...
def cmd_list():
    ...
def cmd_show(n):
    ...
def cmd_sites(n):
    ...
def cmd_check():
    ...
def main(argv):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.16 `plugins/senzing-bootcamp/scripts/brand_tokens.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/brand_tokens.py`:

```python
OBSIDIAN = "#0F0D0C"          # global dark background
DEEP = "#18160F"             # nav & cards on dark; also dark ink on light
SURFACE_DARK = "#201E16"     # elevated surface on dark
EMBER_HOT = "#FF4E1F"        # section labels on dark; hotter accent tone
EMBER_CORE = "#F57826"       # headlines/accent on light; primary accent
EMBER_GRAD_START = "#FF4E1F"  # button/grad-text gradient start
EMBER_GRAD_END = "#F0920A"   # button/grad-text gradient end
EMBER_SOFT = "#FDEEE3"       # derived: light ember tint for chips/pills on light
SIGNAL_GREEN = "#1D9E75"
WHITE = "#FFFFFF"            # light section background
WARM_OFF_WHITE = "#FAF8F3"   # warm off-white (never cold gray)
DARK_INK = "#18160F"         # headlines on light
BODY_INK = "#4A4640"         # body text on light (softer than headline ink)
WARM_LINE = "#E5DFD3"        # derived: warm border/divider on light sections
TEXT_ON_DARK = "#FFFFFF"
MUTED_ON_DARK = "rgba(255,255,255,0.6)"
CARD_BORDER_ON_DARK = "rgba(255,255,255,0.08)"
FONT_STACK = "Roboto, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
CODE_FONT_STACK = "'Fira Code', 'Courier New', Courier, monospace"
PDF_FONT = "Helvetica"
SOURCE_COLORS = {
    "CUSTOMERS": EMBER_CORE,
    "REFERENCE": "#3B6EA5",
    "WATCHLIST": "#C8922A",
}
FALLBACK_COLORS = ["#8b5cf6", "#ec4899", "#0ea5e9", "#a3a34a", "#ef4444", "#14b8a6"]
SOURCE_STROKES = ["#FFFFFF", "#18160F", "#FAF8F3"]
SOURCE_STROKE_WIDTHS = [1.5, 3.0]
SOURCE_FILL_SHADES = [0.0, 0.30, -0.30, 0.55, -0.55]
SOURCE_STROKE_STATES = 1 + len(SOURCE_STROKES) * len(SOURCE_STROKE_WIDTHS)
SOURCE_ENCODING_CAPACITY = (
    len(FALLBACK_COLORS) * SOURCE_STROKE_STATES * len(SOURCE_FILL_SHADES)
)
def shade_fill(fill, factor):
    ...
def color_for_sources(sources):
    ...
def hex_to_rgb(value):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.17 `plugins/senzing-bootcamp/scripts/capture_screenshots.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/capture_screenshots.py`:

```python
MANIFEST_SCHEMA = 1
TABS = {
    "graph": ("entity-graph", "Entity Graph"),
    "network": ("relationship-network", "Relationship Network"),
    "merges": ("record-merges", "Record Merges"),
    "stats": ("merge-statistics", "Merge Statistics"),
    "matchkeys": ("match-keys", "Match Keys"),
    "features": ("feature-scores", "Feature Scores"),
    "overlap": ("cross-source", "Cross-Source"),
    "probe": ("search-probe", "Search / Probe"),
}
DEFAULT_TABS = ("graph", "stats", "matchkeys", "features", "overlap", "probe")
RESERVED_TABS = tuple(t for t in TABS if t not in DEFAULT_TABS)
SINGLE_PAGE_ID = "page"
SINGLE_PAGE_LABEL = "Full page"
SINGLE_PAGE_LABEL_VIEWPORT = "Top of page (viewport only)"
SETTLED_YES = "settled"
SETTLED_NO = "unsettled"
SETTLED_UNKNOWN = "unknown"
SETTLED_NA = "n/a"
FULL_PAGE_FULL = "full"
FULL_PAGE_CLAMPED = "clamped"
FULL_PAGE_VIEWPORT = "viewport"
def resolve_tabs(spec: str) -> list:
    ...
def manifest_path(out_dir: Path, name: str) -> Path:
    ...
def write_manifest(
    out_dir: Path, name: str, requested, absent, written, missed, suppressed=(),
    failed_reason: str = "no image written by any backend", settled=None,
) -> bool:
    ...
def capture(
    target: str,
    out_dir: Path,
    name: str,
    tabs,
    query: str = "",
    is_url: bool = False,
) -> list:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.18 `plugins/senzing-bootcamp/scripts/checkpoint-tick.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/checkpoint-tick.py`:

```python
created = recap_checkpoint.ensure_checkpoint()
```

<!-- markdownlint-enable MD013 -->

#### 6.1.19 `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`:

```python
PROGRESS = os.path.join("config", "bootcamp_progress.json")
DEFAULT_RUNTIME = "docker"
KNOWN_RUNTIMES = {
    "docker": "docker",
    "podman": "podman",
    "container": "container",  # Apple's container CLI (macOS Apple Silicon)
}
STATE_PROBE_RUNTIMES = ("docker", "podman")
def entry_runtime(entry):
    ...
def runtime_cli(runtime):
    ...
def tracked_containers():
    ...
def stop_started_containers():
    ...
def resume_summary():
    ...
NAME_CHARSET = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z")
SLUG_MAX = 32
SLUG_FALLBACK = "project"
CONFLICT_SUFFIXES = tuple(range(2, 10))
PORT_SPAN = 99
LOOPBACK = "127.0.0.1"
def project_slug(project_dir):
    ...
def project_hash6(project_dir):
    ...
def derived_container_name(base, project_dir=None):
    ...
def container_name(base, runtime=DEFAULT_RUNTIME):
    ...
def free_port(preferred):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.20 `plugins/senzing-bootcamp/scripts/feedback-capture.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/feedback-capture.py`:

```python
def plugin_version():
    ...
raw = sys.stdin.read()
lower = prompt.lower()
FEEDBACK = re.compile(
    # The noun, in any construction: "bootcamp feedback", "I have some feedback about
    # module 5", "I'd like to give feedback", "can I give you some feedback", "sharing
    # feedback". Either order, since both "give feedback" and "feedback to give" occur.
    r"(?:bootcamp|plugin|power) feedback"
    r"|feedback (?:on|about|for|regarding) (?:the )?" + _OURS +
    r"|" + _GIVE + _GAP + r"feedback"
    r"|feedback" + _GAP + _GIVE +
    # An explicit report, already framed as one by the user.
    r"|report (?:an? )?(?:issue|bug|problem|defect)"
    # Fault language WITH a bootcamp/plugin referent - the attributed half. Kept narrow:
    # the referent must appear near the fault word, not merely somewhere in the prompt.
    r"|(?:bug|issue|problem|defect|broken|wrong|error)(?:\W+\w+){0,6}?\W+" + _OURS +
    r"|" + _OURS + r"(?:\W+\w+){0,6}?\W+(?:is |are |seems? )?(?:bug|issue|problem|defect|"
    r"broken|wrong)"
)
NOTE = re.compile(
    # An explicit imperative to record something.
    r"\b(?:make|take|add|write|jot|capture|create|start)\b"
    r"(?:\W+\w+){0,2}?\W+(?:a |an |this |that |some |my )?" + _NOTE_NOUN +
    # "note to self", "for my notes", "on my list", "in my notes".
    r"|\bnote to self\b"
    r"|\b(?:for|in) my (?:notes?|list|memos?)\b"
    r"|\b(?:on|to) my (?:to-?do )?list\b"
    r"|\bbootcamp note\b"
    # "jot/write this down", "put this down".
    r"|\b(?:jot|write|put)\b(?:\W+\w+){0,2}?\W+down\b"
    # "remind me", "don't let me forget" - imperative, so unambiguous.
    r"|\bremind me\b"
    r"|\b(?:do ?n[o']?t|dont) let me forget\b"
    # "remember to <verb>" is an instruction to record; "remember when/that/how" is not.
    r"|\bremember to \w+"
)
VERBOSITY = re.compile(
    # Same qualifier tolerance, lower stakes: verbosity is re-adjustable at any time and
    # carries no consent or durability guarantee, so a false positive is self-correcting.
    r"change verbosity|more detail|less detail|more code walkthrough|"
    r"too verbose|too terse|more verbose|less verbose|"
    r"(?:be|answer|reply|respond|make it|keep it)" + _GAP +
    r"(?:more |less |)(?:concise|verbose|detailed|wordy|brief|terse|short|shorter|"
    r"longer|succinct)|"
    r"(?:shorter|longer|briefer|more concise|less wordy|more wordy)\W+"
    r"(?:answers?|replies|responses?|explanations?)"
)
ctx = ""
```

<!-- markdownlint-enable MD013 -->

#### 6.1.21 `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`:

```python
TABLE_HEAD_FILL = tuple(min(255, c + 12) for c in WARM_LINE)
COVER_TITLE_FALLBACK = "Data Discoveries"
COVER_SUBTITLE = "What Senzing found in your data"
DEFAULT_INPUT = "docs/bootcamp_data_discoveries.md"
DEFAULT_OUTPUT = "docs/bootcamp_data_discoveries.pdf"
REQUIRED_SECTIONS = [
    "headline numbers",
    "merges and match keys",
    "review queue",
    "why and how",
    "relationship networks",
    "what was not found",
]
MIN_CONTENT_RETENTION = 0.60
@dataclass
class Block:
    kind: str  # h2 | h3 | bullet | subbullet | label | code | table | text
    text: str
    label: str = ""
@dataclass
class Discoveries:
    title: str = ""
    subtitle: str = ""
    meta: List[Tuple[str, str]] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)
    def headings(self) -> List[str]:
        ...
ITEM_GAP_MM = 3.6
ITEM_GAP_PT = 5.0
def parse_discoveries(text: str) -> Discoveries:
    ...
@dataclass
class DiscoveriesAudit:
    ok: bool
    fatal: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    retention: float = 0.0
    missing_sections: List[str] = field(default_factory=list)
    sections_present: int = 0
    sections_expected: int = 0
def audit_discoveries(
    doc: Discoveries,
    source: str,
    required_sections: Optional[Sequence[str]] = None,
) -> DiscoveriesAudit:
    ...
def render_with_fpdf2(doc: Discoveries, output: Path) -> bool:
    ...
def parse_table(text: str) -> Tuple[List[str], List[List[str]]]:
    ...
def render_with_stdlib(doc: Discoveries, output: Path) -> bool:
    ...
def main(argv: Optional[List[str]] = None, description: Optional[str] = None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.22 `plugins/senzing-bootcamp/scripts/generate_document_pdf.py`

No public items: the file is run as a script.

#### 6.1.23 `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`:

```python
DEFAULT_INPUT = "docs/bootcamp_recap.md"
DEFAULT_OUTPUT = "docs/bootcamp_recap.pdf"
REQUIRED_SECTIONS = [
    "Information Shared",
    "Questions & Responses",
    "Actions Taken",
    "End-of-Module Summary",
]
END_SUMMARY_BLOCKS = [
    "What you accomplished",
    "Files produced",
    "Why it matters",
]
CERTIFICATE_NAME_PLACEHOLDER = "Bootcamper"
RECAP_CHECKPOINT_START = "<!-- RECAP-CHECKPOINT:START -->"
RECAP_CHECKPOINT_END = "<!-- RECAP-CHECKPOINT:END -->"
BOOTCAMP_NOTES_START = "<!-- BOOTCAMP-NOTES:START -->"
BOOTCAMP_NOTES_END = "<!-- BOOTCAMP-NOTES:END -->"
BOOTCAMP_NOTES_TITLE = "Notes, Ideas and Questions"
IMAGE_LINE_RE = re.compile(r"^(?:[-*+]\s+)?!\[(.*?)\]\((.+?)\)$")
IMAGE_URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")
MIN_CONTENT_RETENTION = 0.60
@dataclass
class ModuleSection:
    number: Optional[int]
    title: str
    date: str = ""
    subsections: List[Tuple[str, List[str]]] = field(default_factory=list)
    def subsection(self, name: str) -> Optional[List[str]]:
        ...
    def missing_required(self) -> List[str]:
        ...
    def missing_summary_blocks(self) -> List[str]:
        ...
@dataclass
class NoteEntry:
    title: str
    type: str = ""
    captured: str = ""
    module: str = ""
    body: List[str] = field(default_factory=list)
    context: str = ""
    elaboration: str = ""
@dataclass
class NotesSection:
    title: str = BOOTCAMP_NOTES_TITLE
    entries: List[NoteEntry] = field(default_factory=list)
    source_chars: int = 0
    def __bool__(self) -> bool:
        ...
@dataclass
class Recap:
    title: str
    meta: List[Tuple[str, str]]  # ("Bootcamper", "Ada"), ...
    modules: List[ModuleSection]
    notes: Optional[NotesSection] = None
def parse_table(text: str) -> Tuple[List[str], List[List[str]]]:
    ...
def stray_fence_markers(text: str):
    ...
DISCARDED_FENCES: Tuple[Tuple[str, str], ...] = (
    (RECAP_CHECKPOINT_START, RECAP_CHECKPOINT_END),
)
def parse_recap(text: str) -> Recap:
    ...
def verify_recap(recap: Recap, expected_titles: Optional[List[str]] = None) -> List[str]:
    ...
def set_image_context(recap_path: Path) -> None:
    ...
def resolve_recap_image(
    path: str, base_dirs: Optional[Sequence[Path]] = None
) -> Optional[Path]:
    ...
def recap_image_targets(source_text: str) -> List[str]:
    ...
def unresolvable_image_targets(
    source_text: str, base_dirs: Optional[Sequence[Path]] = None
) -> List[str]:
    ...
def image_embed_note(referenced: int) -> str:
    ...
TAB_MANIFEST_GLOBS = ("*-tabs.json", "*/*-tabs.json")
def find_tab_manifests(base_dirs: Optional[Sequence[Path]] = None) -> List[dict]:
    ...
MODULE_VISUALIZATIONS = {
    # module name token in `modules_completed` -> the `{name}` its capture step uses
    "truthset_visualization": "truthset_verification",
    "query_visualize_discover": "results_visualization",
}
DEFAULT_PROGRESS = Path("config") / "bootcamp_progress.json"
def read_completed_modules(path=DEFAULT_PROGRESS) -> List[str]:
    ...
def expected_visualizations(completed: Sequence[str]) -> List[str]:
    ...
def manifest_names(manifests: Sequence[dict]) -> set:
    ...
def missing_visualization_reports(
    expected: Sequence[str], manifests: Sequence[dict]
) -> List[str]:
    ...
def tab_coverage_problems(source_text: str, manifests: Sequence[dict]) -> List[str]:
    ...
def manifest_undercount_problems(manifests: Sequence[dict]) -> List[str]:
    ...
def tab_coverage_note(source_text: str, manifests: Sequence[dict]) -> str:
    ...
@dataclass
class RecapAudit:
    fatal: List[str]
    warnings: List[str]
    source_chars: int
    rendered_chars: int
    @property
    def retention(self) -> float:
        ...
    def retention_note(self) -> str:
        ...
def audit_recap(
    recap: Recap,
    source_text: str,
    expected_titles: Optional[List[str]] = None,
) -> RecapAudit:
    ...
TABLE_HEAD_FILL = tuple(min(255, c + 12) for c in LINE)
MUTED = tuple(round(s + (l - s) * 0.48) for s, l in zip(SLATE, LIGHT))
def reset_dropped_characters() -> None:
    ...
def dropped_character_warning() -> Optional[str]:
    ...
def render_with_fpdf2(recap: Recap, output: Path) -> bool:
    ...
DEFAULT_PREFERENCES = Path("config") / "bootcamp_preferences.yaml"
def read_preferences_name(path=DEFAULT_PREFERENCES) -> str:
    ...
def set_certificate_name_override(name: str) -> None:
    ...
def certificate_name(recap: Recap) -> str:
    ...
def recap_missing_certificate_name(recap: Recap) -> bool:
    ...
def recap_certificate_name(recap: Recap) -> str:
    ...
def recap_certificate_name_unprintable(recap: Recap) -> Tuple[str, List[str]]:
    ...
def render_with_stdlib(recap: Recap, output: Path) -> bool:
    ...
def main(argv: Optional[List[str]] = None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.24 `plugins/senzing-bootcamp/scripts/generate_recap_video.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_video.py`:

```python
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STORYBOARD = "docs/video/storyboard.json"
DEFAULT_OUTPUT = "docs/bootcamp_recap.mp4"
DEFAULT_RECAP = "docs/bootcamp_recap.md"
DEFAULT_PREFERENCES = "config/bootcamp_preferences.yaml"
EXIT_RENDERED = 0
EXIT_INVALID_STORYBOARD = 1
EXIT_MISSING_CAPABILITY = 2
EXIT_RENDER_FAILED = 3
WIDTH, HEIGHT, FPS = 1920, 1080, 30
AUDIO_RATE = 48000
AUDIO_CHANNELS = 2
SAMPLES_PER_FRAME = AUDIO_RATE // FPS
NARRATION_LEAD = 0.3
NARRATION_TAIL = 0.5
WORDS_PER_MINUTE = 160
MAX_SCENE_SECONDS = 60.0
FADE_IN = 0.3
FADE_OUT = 0.8
CAPTION_SIZE = 44
CAPTION_MAX_WIDTH = 1560
CAPTION_LINES = 2
CAPTION_BOTTOM = HEIGHT - 44
NETWORK_MODULES = ("urllib", "http", "socket", "requests", "ftplib", "smtplib")
DEFAULT_PIPER_VOICE = "en_US-ljspeech-high"
PIPER_VOICE_DIR = "data/temp/piper-voices"
DEFAULT_VOICE_MODEL = f"{PIPER_VOICE_DIR}/{DEFAULT_PIPER_VOICE}.onnx"
PIPER_LENGTH_SCALE = "1.0"
PIPER_SENTENCE_SILENCE = "0.15"
def estimated_narration_seconds(text: str) -> float:
    ...
PALETTE, _BRAND, PALETTE_NOTE = _load_palette()
P = PALETTE
MUTED_ON_DARK = _mix(P["OBSIDIAN"], P["WHITE"], 0.6)
MUTED_ON_LIGHT = _mix(P["BODY_INK"], P["WARM_OFF_WHITE"], 0.48)
def source_fills(labels: Sequence[str]) -> List[Tuple[int, int, int]]:
    ...
@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str
    required: bool = True
    minimum: float = 0
    max_items: int = 0
    item_fields: Tuple["FieldSpec", ...] = ()
    help: str = ""
FIELD_KINDS = ("text", "count", "number", "seconds", "date", "image", "path", "text_list",
               "items", "boolean")
def F(name, kind, required=True, **kw) -> FieldSpec:
    ...
COMMON_FIELDS = (
    F("type", "text", help="one of the scene types"),
    F("duration", "seconds", help="planned seconds; extended if the narration needs longer"),
    F("narration", "text", help="spoken by the voice-over, and the caption's default"),
    F("caption", "text", False, help="burned-in caption; defaults to the narration"),
)
VIDEO_FIELDS = (
    F("bootcamper", "text", help="the Bootcamper's name, as the video should say it"),
    F("graduation_date", "date", help="YYYY-MM-DD"),
    F("title", "text", False),
    F("music", "boolean", False,
      help="the synthesized music bed under the narration; defaults to true, false turns it off"),
)
TOP_LEVEL_KEYS = ("version", "video", "scenes")
@dataclass(frozen=True)
class SceneType:
    name: str
    summary: str
    fields: Tuple[FieldSpec, ...]
    draw: Callable
    check: Optional[Callable] = None
def project_relative_problem(value, root: Path) -> Optional[str]:
    ...
def validate_storyboard(data, root) -> List[str]:
    ...
def schema_description() -> dict:
    ...
class CapabilityMissing(Exception):
    ...
def load_pillow():
    ...
def missing_encoders(ffmpeg: str) -> List[str]:
    ...
def missing_filters(ffmpeg: str) -> List[str]:
    ...
def find_ffmpeg() -> Tuple[str, List[str]]:
    ...
@dataclass(frozen=True)
class SpeechEngine:
    name: str
    command: Callable[[str, str], Tuple[List[str], Dict[str, str]]]
def find_speech_engine() -> Tuple[Optional[SpeechEngine], List[str]]:
    ...
def choose_voice(no_voice: bool) -> Tuple[Optional[SpeechEngine], Optional[str]]:
    ...
def decode_to_pcm(ffmpeg: str, audio_file: str) -> bytes:
    ...
def synthesize_pcm(engine: SpeechEngine, text: str, ffmpeg: str, workdir: Path,
                   stem: str) -> bytes:
    ...
def spell_numbers(text: str) -> str:
    ...
def piper_config_path(model: Path) -> Path:
    ...
def find_piper_voice(model: Path) -> Tuple[Optional[SpeechEngine], Optional[str]]:
    ...
def voice_with_piper(scenes: Sequence[dict], piper: SpeechEngine, ffmpeg: str, workdir: Path,
                     note: Callable[[str], None]) -> Optional[List[bytes]]:
    ...
class RenderContext:
    def __init__(self, pil, video: dict, root: Path):
        ...
    def note(self, message: str) -> None:
        ...
    def font(self, style: str, size: int):
        ...
def wrap_text(font, text: str, max_width: float) -> List[str]:
    ...
SCENE_TYPES: Dict[str, SceneType] = {t.name: t for t in (
    SceneType("title_card", "a module name plus its highlight, for a module with nothing on "
              "screen",
              (F("module", "text"), F("highlight", "text", False)),
              _draw_title_card),
    SceneType("image", "a slow pan and zoom over a screenshot",
              (F("image", "image", help="project-relative path to a PNG or JPEG"),
               F("heading", "text", False),
               F("module", "text", False, help="used by the title-card fallback")),
              _draw_image),
    SceneType("counter", "animated bars and numbers, such as record counts per source",
              (F("title", "text"),
               F("items", "items", max_items=8,
                 item_fields=(F("label", "text"), F("value", "number"))),
               F("unit", "text", False)),
              _draw_counter),
    SceneType("mapping", "source fields flowing to Senzing attributes",
              (F("source", "text"),
               F("fields", "items", max_items=8,
                 item_fields=(F("from", "text"), F("to", "text"))),
               F("title", "text", False)),
              _draw_mapping),
    SceneType("loading", "records flowing into entities, with a rising counter",
              (F("records", "count"), F("entities", "count"), F("source", "text", False),
               F("title", "text", False)),
              _draw_loading, _entities_not_above_records),
    SceneType("entity_merge", "records converging into resolved entities",
              (F("records", "count", minimum=1), F("entities", "count", minimum=1),
               F("sources", "text_list", False, max_items=12), F("title", "text", False)),
              _draw_entity_merge, _entities_not_above_records),
    SceneType("certificate", "the Certificate of Completion, from the recap's own fields",
              (F("recap", "path", False, help=f"defaults to {DEFAULT_RECAP}"),
               F("preferences", "path", False, help=f"defaults to {DEFAULT_PREFERENCES}"),
               F("modules", "text_list", False,
                 help="used only when no recap can be read")),
              _draw_certificate),
    SceneType("tag_line", "the closing card",
              (F("text", "text", False,
                 help="defaults to 'Resolved: <bootcamper>, Senzing graduate.'"),),
              _draw_tag_line),
)}
@dataclass
class CertificateFields:
    name: str
    date: str
    modules: List[str]
    citation: str
    issuer: str
    colophon: str
    text: Dict[str, str]
    source: str
def certificate_fields(scene: dict, video: dict, root: Path,
                       note: Callable[[str], None]) -> CertificateFields:
    ...
@dataclass
class PlannedScene:
    index: int
    type: str                       # the type as written
    kind: str                       # the drawer used (a title card for a missing image)
    data: dict
    planned: float
    duration: float
    frames: int
    caption: str
    narration_seconds: float
    voiced: bool
    pcm: bytes = b""
    chunks: List[str] = field(default_factory=list)
    is_last: bool = False
    @property
    def label(self) -> str:
        ...
def caption_chunks(ctx, caption: str) -> List[str]:
    ...
def plan_timeline(storyboard: dict, ctx: RenderContext, engine: Optional[SpeechEngine],
                  ffmpeg: Optional[str], workdir: Optional[Path],
                  voices: Optional[Sequence[bytes]] = None) -> List[PlannedScene]:
    ...
def write_audio_track(plan: Sequence[PlannedScene], path: Path) -> None:
    ...
MUSIC_VOLUME = 0.3
DUCKING = "sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"
LEVELER = ("asplit=2[lv][lk];"
           "[lv][lk]sidechaincompress=threshold=0.05:ratio=4:attack=5:release=150:makeup=1")
MUSIC_BPM = 120
MUSIC_FADE_IN = 2.0
MUSIC_FADE_OUT = 3.0
MUSIC_PROGRESSION = ((60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60))
def synthesize_music_bed(seconds: float) -> bytes:
    ...
def write_music_bed(seconds: float, path: Path) -> None:
    ...
def audio_filter_graph(voice: Optional[int], music: Optional[int]) -> Optional[str]:
    ...
def caption_at(ps: PlannedScene, t: float) -> str:
    ...
def burn_caption(ctx, img, text: str) -> None:
    ...
def frame_image(ctx: RenderContext, ps: PlannedScene, t: float):
    ...
def render_scene_frame(storyboard: dict, index: int, t: float, project_root=".",
                       pil=None):
    ...
def encode_command(ffmpeg: str, audio: Optional[Path], output: Path,
                   music: Optional[Path] = None) -> List[str]:
    ...
def stream_frames(ctx, plan, ffmpeg: str, audio: Optional[Path], output: Path,
                  log_path: Path, music: Optional[Path] = None) -> Tuple[bool, str]:
    ...
def load_storyboard(path: Path) -> Tuple[Optional[dict], List[str]]:
    ...
def main(argv: Optional[List[str]] = None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.25 `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`:

```python
DEFAULT_FENCE_LANG = "text"
def mojibake_lines(text: str) -> list:
    ...
def normalize_text(text: str) -> str:
    ...
def target_files(docs_dir: Path) -> list:
    ...
def normalize_file(path: Path, dry_run: bool = False) -> str:
    ...
def main(argv=None) -> int:
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.26 `plugins/senzing-bootcamp/scripts/package_bootcamp.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/package_bootcamp.py`:

```python
ROOT_PREFIX = "senzing-bootcamp-{profile}-{date}"
ALWAYS_EXCLUDE = (
    ".env",
    ".env.production",
    "licenses",
    "config/license.json",
    "data/raw",
    "data/temp",
    "logs",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "target",
    "backups/packages",
)
SHARE_EXCLUDE = ("backups", "docs/mapping")
DATABASE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
SHARE_INCLUDE = (
    "docs",
    "production",
)
TRANSFER_EXTRA = (
    "backups/revisit",
    "config",
    "src",
)
SIZE_WARN_BYTES = 2 * 1024 * 1024 * 1024
SCAN_BLOCK_BYTES = 1 << 20
SCAN_OVERLAP_BYTES = 4096
def is_excluded(relpath, profile):
    ...
def candidate_roots(profile):
    ...
def collect(project_root, profile):
    ...
UNEXAMINED = "unexamined"
def sha256_of(path):
    ...
def read_progress(project_root):
    ...
def plugin_version():
    ...
def business_problem_line(project_root):
    ...
def build_manifest(profile, members, skipped, project_root, date):
    ...
WRAP_WIDTH = 85
SQLITE_RESTORE = "a SQLite file; copy it back to `database/` to restore it"
PG_DUMP_SUFFIX = ".dump"
PG_RESTORE = ("a `pg_dump` file; restore it into a fresh database with "
              "`pg_restore -U <user> -d <db> <file>` (or `psql -U <user> -d <db> -f <file>` for a "
              "plain dump), never with a `<` redirection")
def included_parts(manifest):
    ...
def open_me_first(manifest, project_root):
    ...
def human(size):
    ...
def run(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.27 `plugins/senzing-bootcamp/scripts/precompact-recap.py`

No public items: the file is run as a script.

#### 6.1.28 `plugins/senzing-bootcamp/scripts/recap_checkpoint.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/recap_checkpoint.py`:

```python
CHECKPOINT = os.path.join("docs", "progress", "recap_checkpoint.md")
RECAP = os.path.join("docs", "bootcamp_recap.md")
PROGRESS = os.path.join("config", "bootcamp_progress.json")
START = "<!-- RECAP-CHECKPOINT:START -->"
END = "<!-- RECAP-CHECKPOINT:END -->"
SCAFFOLD = "<!-- RECAP-CHECKPOINT:SCAFFOLD -->"
def bootcamp_active():
    ...
def current_module():
    ...
UNREADABLE = object()
def checkpoint_state():
    ...
def ensure_checkpoint(module=None):
    ...
def fold_checkpoint():
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.29 `plugins/senzing-bootcamp/scripts/secret_patterns.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/secret_patterns.py`:

```python
SECRET_PATTERN = (
    r"BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"
    r"|AKIA[0-9A-Z]{16}"
    r"|AQAAAD[A-Za-z0-9+/=]{16,}"
)
SECRET_PATTERN_NAMES = (
    "PEM private key",
    "AWS access-key ID",
    "Senzing license payload",
)
def find_secret(text):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.30 `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`:

```python
BIND_HOST = "127.0.0.1"
SOURCE_KEY_SEP = "|"
GRAPH_NODE_CAP = 1500
SERVER_NONCE = uuid.uuid4().hex
def confirm_server_identity(port, host=BIND_HOST, timeout=5.0):
    ...
class Model:
    def __init__(self):
        ...
    def build(self, engine, flags, record_keys):
        ...
    def build_from_export(self, engine, flags):
        ...
    def data_sources(self):
        ...
    def stats(self):
        ...
    def records(self, entity_id):
        ...
    def overlap(self):
        ...
    def match_keys(self):
        ...
    def feature_scores(self):
        ...
    def color_keys(self):
        ...
    def graph(self, cap=None):
        ...
    def merges(self):
        ...
    SEARCH_NAME_ATTRS = ("NAME_FULL", "NAME_ORG")
    def search(self, engine, flags, query):
        ...
    def how(self, engine, sz, entity_id):
        ...
    def why(self, engine, sz, entity_id):
        ...
    def compute_feature_dist(self, engine, sz, cap=40):
        ...
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
__D3_SCRIPT__
__DATA_SHIM__
<style>
:root{__ROOT_VARS__}
*{box-sizing:border-box}
body{margin:0;font-family:__FONT_STACK__;color:var(--ink);background:var(--bg)}
header{background:var(--navy);color:#fff;padding:12px 20px;border-bottom:3px solid var(--gold);position:sticky;top:0;z-index:10}
header h1{margin:0;font-size:18px}
.banner{display:flex;gap:10px;flex-wrap:wrap;padding:12px 20px;background:#fff;border-bottom:1px solid var(--line)}
.stat{flex:1;min-width:120px;text-align:center}
.stat .n{font-size:24px;font-weight:700;color:var(--blue)}
.stat .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.stat .arrow{color:var(--gold);font-weight:700;align-self:center}
nav{display:flex;gap:4px;padding:0 20px;background:#fff;border-bottom:1px solid var(--line)}
nav button{border:none;background:none;padding:10px 14px;font-size:14px;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent}
nav button.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600}
main{padding:0}
.tab{display:none;padding:16px 20px}
.tab.active{display:block}
#graph-container{position:relative;height:calc(100vh - 175px);min-height:360px;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;padding:0}
#graph-container svg{width:100%;height:100%;display:block}
.legend{position:absolute;top:10px;right:10px;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:12px}
.legend .row{display:flex;align-items:center;gap:6px;margin:2px 0}
.legend .dot{width:12px;height:12px;border-radius:50%}
.node circle{stroke:#fff;stroke-width:1.5px;cursor:pointer}
.node text,.node-labels text{font-size:10px;fill:var(--ink);pointer-events:none}
/* Label visibility is driven by a class on the container, set explicitly at
   init -- an unchecked checkbox fires no change event, so the initial state
   cannot be left to the handler (contract: "Init-state note"). */
.hide-node-labels .node text,.hide-node-labels .node-labels text{display:none}
/* ⛔ `.node-labels` is listed in BOTH rules above deliberately. Node labels moved out of
   the per-datum `.node` group on 2026-09-02 so no circle can paint over a neighbor's
   text; a selector left matching only `.node text` would have silently un-hidden every
   label at production scale, regressing `visualization-legibility-at-production-scale`
   -- the auto-off at LABEL_AUTO_OFF works by adding `hide-node-labels` to the container
   and letting it descend. Keep both selectors in step. */
.hide-edge-labels .edge text{display:none}
.gctl{position:absolute;top:10px;left:10px;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:12px;z-index:2}
.gctl label{display:flex;align-items:center;gap:6px;margin:2px 0;cursor:pointer}
.gctl .why{color:var(--muted);margin-top:4px;max-width:220px}
.legend .row{cursor:pointer;user-select:none}
.legend .row.off{opacity:.35}
.legend .cnt{color:var(--muted);margin-left:auto;padding-left:8px}
.edge line{stroke:var(--line);stroke-width:1.5px}
.edge text{font-size:9px;fill:var(--muted)}
.tooltip{position:absolute;pointer-events:none;background:var(--navy);color:#fff;padding:6px 9px;border-radius:6px;font-size:12px;opacity:0;max-width:240px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:10px}
.card h4{margin:0 0 6px;font-size:15px}
.recs{display:flex;gap:10px;flex-wrap:wrap}
.rec{border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:12px;min-width:150px;background:var(--bg)}
.chip{display:inline-block;border:1px solid var(--blue);color:var(--blue);background:var(--accent-soft);border-radius:12px;padding:1px 8px;font-size:11px;margin:2px 2px 0 0;font-family:__CODE_FONT__}
.mk span{display:inline-block;border:1px solid var(--gold);background:var(--accent-soft);color:var(--ink);border-radius:4px;padding:0 5px;margin:1px;font-family:__CODE_FONT__;font-size:11px}
#search-in{padding:8px 10px;border:1px solid var(--line);border-radius:6px;font-size:14px;width:min(420px,100%)}
button.probe{border:1px solid var(--line);background:#fff;border-radius:16px;padding:5px 12px;margin:2px;cursor:pointer;font-size:13px}
.muted{color:var(--muted)}
.modal-bg{position:fixed;inset:0;background:rgba(15,13,12,.5);display:none;align-items:center;justify-content:center;z-index:50}
/* Entity-detail dialogs are a primary "wow moment" surface and get the same
   care as the headline tabs: a real header bar separated from the body, a
   circular close control, and a subtle entrance transition (contract:
   "Modal chrome"). */
.modal{background:#fff;border-radius:10px;max-width:420px;width:90%;overflow:hidden;
  box-shadow:0 18px 48px rgba(15,13,12,.28);animation:modal-in .16s ease-out}
@keyframes modal-in{from{opacity:0;transform:translateY(8px) scale(.985)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.modal{animation:none}}
.modal .mhead{background:var(--navy);color:#fff;padding:14px 18px;display:flex;align-items:flex-start;gap:12px}
.modal .mhead h3{margin:0;font-size:16px;color:#fff;flex:1}
.modal .mhead .muted{color:rgba(255,255,255,.72);font-size:12px;margin-top:2px}
.modal .mclose{flex:none;width:28px;height:28px;border-radius:50%;border:none;cursor:pointer;
  background:rgba(255,255,255,.15);color:#fff;font-size:16px;line-height:1;padding:0;margin:0}
.modal .mclose:hover{background:rgba(255,255,255,.28)}
.modal .mbody{padding:16px 18px 18px}
.modal h3{margin:0 0 8px}
.modal button{margin-top:10px;border:none;background:var(--blue);color:#fff;border-radius:6px;padding:6px 12px;cursor:pointer}
.modal.wide{max-width:680px}
.actions{margin-top:8px;display:flex;gap:6px}
.actions button{border:1px solid var(--blue);background:var(--accent-soft);color:var(--blue);border-radius:6px;padding:3px 10px;font-size:12px;cursor:pointer}
.explain pre{max-height:52vh;overflow:auto;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;font-family:__CODE_FONT__;font-size:11px;white-space:pre-wrap;word-break:break-word}
.bucket-list{margin-top:14px}
.bucket-list .rec{cursor:pointer}
.explain h4{margin:12px 0 4px}
.explain details{margin-top:14px}
.explain summary{cursor:pointer;color:var(--muted);font-size:12px}
.legend-note{font-size:12px;color:var(--muted);margin:6px 0 0}
.verdict{border-left:4px solid var(--blue);background:var(--accent-soft);padding:8px 12px;border-radius:0 6px 6px 0;margin:4px 0 10px}
.why-table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
.why-table th,.why-table td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.why-table th{background:var(--bg);font-size:10px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
.why-table td.feat{font-weight:600;white-space:nowrap}
.score-bar{height:7px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:4px}
.score-bar>span{display:block;height:100%}
.bucket{display:inline-block;border-radius:10px;padding:1px 8px;font-size:11px;font-weight:600;border:1px solid transparent}
.b-strong{background:#e6f4ea;color:#137333;border-color:#cdebd6}
.b-mid{background:#fef7e0;color:#8a6d00;border-color:#f3e2a6}
.b-weak{background:#fdeee3;color:#a1440a;border-color:#f6cfae}
.b-none{background:#fce8e6;color:#a50e0e;border-color:#f4c7c3}
.step{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;background:#fff}
.step .num{display:inline-block;background:var(--blue);color:#fff;border-radius:50%;width:22px;height:22px;line-height:22px;text-align:center;font-weight:700;font-size:12px;margin-right:6px}
nav{flex-wrap:wrap}
.kpis{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.kpi{flex:1;min-width:130px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.kpi .n{font-size:26px;font-weight:700;color:var(--blue)}
.kpi .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.section-h{margin:16px 0 6px;font-size:14px}
.heat{border-collapse:collapse;font-size:12px;margin-top:8px}
.heat th,.heat td{border:1px solid var(--line);padding:6px 10px;text-align:center}
.heat th{background:var(--bg);color:var(--muted);font-weight:600}
.heat td.rowh{background:var(--bg);color:var(--muted);font-weight:600;text-align:right}
.heat td.cell{color:var(--ink);font-variant-numeric:tabular-nums}
</style></head>
<body>
<header><h1>__TITLE__</h1></header>
<div class="banner" id="banner"></div>
<nav id="nav"></nav>
<main>
  <section class="tab active" id="tab-graph"><div id="graph-container"><div class="tooltip" id="tt"></div></div></section>
  <section class="tab" id="tab-stats"><div id="hist"></div></section>
  <section class="tab" id="tab-matchkeys"><div id="matchkeys"></div></section>
  <section class="tab" id="tab-features"><div id="features"></div></section>
  <section class="tab" id="tab-overlap"><div id="overlap"></div></section>
  <section class="tab" id="tab-probe">__PROBE_BODY__</section>
</main>
<div class="modal-bg" id="modal-bg" onclick="if(event.target.id==='modal-bg')closeModal()"><div class="modal" id="modal"></div></div>
<script>
// Six tabs. "Record Merges" was removed because Search / Probe's per-entity result is a
// strict superset of it (name, record count, entity match key -- plus per-record match
// keys and feature scores); its one unique capability, browsing all merges with no query,
// moved to the "Show all merged entities" button on that tab. "Relationship Network" was
// removed because it rendered a filtered view of this tab's own /api/graph data; it is now
// the "Show only entities with relationships" mode of Entity Graph. Both per the contract's
// de-duplication rule: when two candidate tabs share their data, they are one tab.
const ALL_TABS=[["graph","Entity Graph"],["stats","Merge Statistics"],["matchkeys","Match Keys"],["features","Feature Scores"],["overlap","Cross-Source"],["probe","Search / Probe"]];
// {source_code: {fill, stroke, cycle}} assigned from the sources actually loaded, so a
// bootcamper's own sources are always distinct. The last-resort literal is for a source
// absent from the model entirely; it is deliberately NOT equal to any assigned color, so
// "unassigned" never masquerades as a real category.
const SRC_COLORS=__SRC_COLORS__;
const UNKNOWN_SRC="#9aa0a6";
function srcStyle(src){return SRC_COLORS[src]||{fill:UNKNOWN_SRC,stroke:"#FFFFFF",stroke_width:null,cycle:0};}
function color(src){return srcStyle(src).fill;}
function srcStroke(src){return srcStyle(src).stroke;}
// The stroke WIDTH decides whether a stroke is drawn at all, and every draw site must key
// on it -- not on `cycle`. `cycle` says which palette wrap a source landed in; it does not
// reach the canvas, and keying on it capped the rendered encoding space at 24 sources while
// the assigned map went on looking collision-free past that.
function srcStrokeW(src){return srcStyle(src).stroke_width||0;}
// The key a NODE is colored by: its whole source set, joined, not one member of it.
// Coloring by data_sources[0] made every cross-source entity render as whichever of its
// sources sorted first, so 1,951 cross-source vendors appeared to be GLEIF-only. Fill,
// stroke and stroke width must all read THIS, or a partial version of the same
// misencoding survives. Single-source entities degenerate to their own source code, which
// is why their appearance is unchanged.
function srcKeyOf(d){var s=(d&&d.data_sources)||[];return s.length?s.slice().sort().join("|"):"";}
function isCombo(k){return k.indexOf("|")>=0;}
function comboLabel(k){return k.split("|").join(" + ");}
const CSSV=getComputedStyle(document.documentElement);
function cssv(n,f){var v=CSSV.getPropertyValue(n).trim();return v||f;}
const C_BLUE=cssv('--blue','#F57826'),C_GOLD=cssv('--gold','#FF4E1F'),C_GREEN=cssv('--green','#1D9E75'),C_MUTED=cssv('--muted','#4A4640');
function hexRgb(h){h=(h||"").replace('#','');if(h.length===3)h=h.split('').map(function(c){return c+c;}).join('');var n=parseInt(h,16)||0;return [(n>>16)&255,(n>>8)&255,n&255];}
let STATS=null;
// A tab is shown only when its data exists: 2+ sources for cross-source overlap,
// multi-record entities for match keys / feature scores. The others always apply.
// (The relationship view is no longer a tab -- it is a mode of Entity Graph, gated
// on the same relationships_total > 0 condition inside addGraphControls.)
function tabApplicable(id){const s=STATS||{};
  if(id==="overlap")return (s.data_sources_total||0)>=2;
  if(id==="features")return (s.multi_record_entities||0)>0;
  if(id==="matchkeys")return (s.multi_record_entities||0)>0;
  return true;}
// "all" shows the full entity population; "network" shows only entities connected by a
// relationship, with edges styled by relationship type -- what the removed Relationship
// Network tab rendered. Both modes are served by the same /api/graph payload.
// Above this many entities the full population is a mesh with no practical way to
// locate anything, so Entity Graph opens on the relationship subgraph instead. The
// toggle still switches both ways; only the DEFAULT is scale-aware. Stated in
// visualization-api-reference.md so a server in any language picks the same value.
// (Label defaults are already scale-aware; hiding labels does not thin 4,464 edges.)
const GRAPH_SUBGRAPH_DEFAULT_ABOVE=400;
let graphMode="all";
let graphModeAutoSet=false;
// The last /api/graph payload drawGraph fetched, so addGraphControls can word its notes from
// the payload's own `capped`, `total` and `related_total` instead of the capped subset (#327).
let graphPayload={};
// The live force simulation for the graph tab. Toggling the mode re-enters drawGraph, and
// the previous simulation would otherwise keep ticking against DOM nodes that have been
// removed — wasted work and a source of jank. Stopped before each redraw.
let graphSim=null;
// ⛔ (INV-298) The settled signal, on the document element so any driver in any language can
// wait on it -- `document.documentElement.getAttribute("data-graph-settled")==="1"`. An
// attribute rather than a JS global on purpose: `graphSim` is a top-level `let`, which never
// reaches `window`, so nothing outside this script could observe it (found 2026-09-03 by an
// injected probe that read nothing). Removing the attribute rather than setting "0" keeps
// "not settled" and "no animated view on this page" the same observable state, so a waiter
// cannot mistake a static tab for an unsettled one.
function graphSettled(done){
  const el=document.documentElement;
  if(done){el.setAttribute("data-graph-settled","1");}
  else{el.removeAttribute("data-graph-settled");}
}
function drawFor(id){
  if(id==="graph")drawGraph();
  else if(id==="stats")drawHist();
  else if(id==="matchkeys")drawMatchKeys();
  else if(id==="features")drawFeatures();
  else if(id==="overlap")drawOverlap();}
function activate(id){
  // Re-activating the tab that is ALREADY active must not redraw it. drawFor() rebuilds
  // the tab, and for the Entity Graph that means a fresh d3.forceSimulation — so
  // re-activating the default tab mid-capture restarts the layout and the screenshot
  // catches the nodes still collapsed in a corner: a plausible-looking empty graph, at
  // exit 0, in the keepsake. Both capture paths hit this (an injected activate('<tab>')
  // and ?tab=<id> deep-linking), and a user clicking the active nav button did too.
  const already=d3.select("#tab-"+id);
  if(!already.empty()&&already.classed("active")&&d3.select("#navbtn-"+id).classed("active"))return;
  d3.selectAll("nav button").classed("active",false);d3.select("#navbtn-"+id).classed("active",true);
  d3.selectAll(".tab").classed("active",false);d3.select("#tab-"+id).classed("active",true);drawFor(id);}
function buildNav(){const nav=d3.select("#nav");nav.html("");
  const tabs=ALL_TABS.filter(function(t){return tabApplicable(t[0]);});
  tabs.forEach(function(t,i){nav.append("button").attr("id","navbtn-"+t[0]).attr("class",i===0?"active":"").text(t[1]).on("click",function(){activate(t[0]);});});
  d3.selectAll(".tab").classed("active",false);if(tabs.length)d3.select("#tab-"+tabs[0][0]).classed("active",true);}
async function getJSON(u){const r=await fetch(u);return r.json();}
async function loadBanner(){const s=await getJSON("/api/stats");
  const items=[["Records Loaded",s.records_total],["Resolved Entities",s.entities_total],["Multi-Record",s.multi_record_entities],["Cross-Source",s.cross_source_entities],["Relationships",s.relationships_total]];
  const b=d3.select("#banner");b.html("");
  items.forEach((it,i)=>{const d=b.append("div").attr("class","stat");d.append("div").attr("class","n").text(it[1]);d.append("div").attr("class","l").text(it[0]);
    if(i<items.length-1)b.append("div").attr("class","arrow").text("→");});}
let graphDrawn=false;
async function drawGraph(){
  const c=document.getElementById("graph-container");const W=c.clientWidth,H=c.clientHeight;
  const g=await getJSON("/api/graph");const box=d3.select("#graph-container");
  graphPayload=g;
  d3.select("#graph-container svg").remove();
  d3.select("#graph-container .legend").remove();
  d3.select("#graph-container .empty-note").remove();
  if(graphSim){graphSim.stop();graphSim=null;}
  // ⛔ (INV-298) The capture waits on this signal instead of a time budget. Cleared as a
  // layout BEGINS and set when it reaches its final positions, so a screenshot is never a
  // picture of a still-moving graph. A deadline cannot express this: measured 2026-09-03 on
  // the 85-entity Truth Set, five captures at 30s and five at 120s produced the SAME image
  // while five at 300s produced TWO -- the deadline does not select the layout, and
  // lengthening it made reproducibility worse. `graphSettled(false)` here covers the redraw
  // paths too (mode switch, and a drag that restarts the simulation).
  graphSettled(false);
  const links0=g.edges.map(function(e){return {source:e.source_entity_id,target:e.target_entity_id,match_key:e.match_key,rtype:e.relationship_type||"RELATED"};});
  // Scale-aware default, applied once: above the threshold, open on the relationship
  // subgraph rather than the full population. Only when a subgraph actually exists,
  // and never overriding a choice the bootcamper has already made with the toggle.
  if(!graphModeAutoSet){
    graphModeAutoSet=true;
    if(g.nodes.length>GRAPH_SUBGRAPH_DEFAULT_ABOVE&&links0.length){graphMode="network";}
  }
  const network=graphMode==="network";
  // ⛔ (INV-298/INV-299) A capture-oriented render: settle the layout synchronously, fit it
  // to the viewport, and drop labels above CAPTURE_LABEL_MAX. Requested with `?capture=1`,
  // which `capture_screenshots.py` appends.
  // ⚠️ Scoped to the CAPTURE deliberately -- the interactive artifact is NOT affected. The
  // tick starvation this works around is specific to headless virtual time: a real browser
  // advances requestAnimationFrame normally, so a bootcamper opening the standalone snapshot
  // already gets a properly settled layout and keeps its animation, its labels and its zoom.
  const capture=/[?&]capture=1/.test(location.search);
  // In network mode, keep only entities that a relationship actually connects -- the
  // subgraph the removed Relationship Network tab showed.
  let nodes;
  if(network){
    const connected=new Set();links0.forEach(function(e){connected.add(e.source);connected.add(e.target);});
    nodes=g.nodes.filter(function(n){return connected.has(n.entity_id);}).map(function(n){return Object.assign({},n,{id:n.entity_id});});
  }else{
    nodes=g.nodes.map(function(n){return Object.assign({},n,{id:n.entity_id});});
  }
  if(!nodes.length){
    box.append("div").attr("class","muted empty-note").style("padding","14px")
       .text(network?(g.capped?"None of the "+g.related_total+" entities with relationships are among the "+
                                g.nodes.length+" shown."
                              :"No relationships between entities were found in this data.")
                    :"No entities to graph.");
    addGraphControls("graph-container",0);
    // (INV-298) Nothing to lay out is already settled -- without this a waiter on an empty
    // graph has no signal to wait for and falls back to its timeout, which is the fixed
    // deadline this replaces.
    graphSettled(true);
    return;
  }
  // EDGE-KEY MAPPING: forceLink resolves against id via source/target; map before use.
  const idset=new Set(nodes.map(function(n){return n.id;}));
  const links=links0.filter(function(e){return idset.has(e.source)&&idset.has(e.target);});
  const rtypes=Array.from(new Set(links.map(function(e){return e.rtype;})));
  const rcolor=d3.scaleOrdinal().domain(rtypes).range([C_BLUE,C_GOLD,C_GREEN,"#8b5cf6","#ec4899","#0ea5e9"]);
  const svg=box.append("svg").attr("width",W).attr("height",H).attr("viewBox",[0,0,W,H]);
  const root=svg.append("g");
  // scaleExtent's floor is lowered for the capture fit: a settled 85-entity layout needs
  // well under 0.2 to fit, and clamping there would leave nodes off-canvas.
  const zoomB=d3.zoom().scaleExtent([0.05,4]).on("zoom",function(ev){root.attr("transform",ev.transform);});
  svg.call(zoomB);
  // Node labels are truncated to fit, so the distinctness rule applies here exactly as it
  // does to match keys (contract: "Defaults at production scale" item 1). Two entities whose
  // names share the first 19 characters -- ACME HOLDINGS INTERNATIONAL LLC vs ...INC, routine
  // in organization data -- would otherwise render as the same string, and the graph would
  // show two nodes nothing distinguishes. Compare the FITTED labels, not the names, and
  // suffix only a genuine collision: two entities that really share a name may legitimately
  // render alike. The full name stays on hover via the group tooltip above.
  const NODE_LABEL_MAX=20;
  const nodeLabel={};
  (function(){const taken={};
    nodes.forEach(function(n){
      const full=n.entity_name||"";
      let lab=full.length>NODE_LABEL_MAX?full.slice(0,NODE_LABEL_MAX-1)+"…":full;
      if(taken[lab]!==undefined&&taken[lab]!==full){
        let k=2;while(taken[lab+" ("+k+")"]!==undefined)k++;
        lab=lab+" ("+k+")";
      }
      taken[lab]=full;
      nodeLabel[n.entity_id]=lab;
    });})();
  const sim=graphSim=d3.forceSimulation(nodes)
    .force("link",d3.forceLink(links).id(function(d){return d.id;}).distance(network?100:90))
    .force("charge",d3.forceManyBody().strength(network?-180:-160))
    .force("center",d3.forceCenter(W/2,H/2))
    // ⛔ Collide accounts for the LABEL's extent, not just the circle -- but only while
    // labels are actually shown. Above LABEL_AUTO_OFF they default off, and inflating the
    // collision radius for text nobody renders would over-separate the very production-scale
    // layout `visualization-legibility-at-production-scale` tuned. ~2.9px per character at
    // font-size 10 is a deliberate estimate: SVG text has no measurable width before layout,
    // and a estimate that is close is worth more here than exactness.
    .force("collide",d3.forceCollide().radius(function(d){
      const r=radius(d)+6;
      if(nodes.length>LABEL_AUTO_OFF)return r;
      const lab=nodeLabel[d.entity_id]||"";
      return Math.max(r,lab.length*2.9);}));
  const edge=root.append("g").selectAll("g").data(links).join("g").attr("class","edge");
  const line=edge.append("line");
  // Relationship-type color plus a dash pattern, so the types stay distinguishable in a
  // monochrome screenshot (contract: pair color with a non-color distinction).
  if(network){
    line.attr("stroke",function(d){return rcolor(d.rtype);}).attr("stroke-width",2)
        .attr("stroke-dasharray",function(d){return rdash(d.rtype);});
  }
  edge.append("text").text(function(d){return d.match_key||"";});
  const node=root.append("g").selectAll("g").data(nodes).join("g").attr("class","node")
    .call(d3.drag().on("start",dstart).on("drag",dragged).on("end",dend))
    .on("click",function(ev,d){openModal(d);})
    .on("mousemove",function(ev,d){const tt=d3.select("#tt");
      tt.style("opacity",1).style("left",(ev.offsetX+14)+"px").style("top",(ev.offsetY+8)+"px")
        .html("<b>"+esc(d.entity_name)+"</b><br>ID "+d.entity_id+" · "+d.record_count+" record(s)<br>"+d.data_sources.join(", "));})
    .on("mouseout",function(){d3.select("#tt").style("opacity",0);});
  node.append("circle").attr("r",radius).attr("fill",function(d){return color(srcKeyOf(d));})
    .attr("stroke",function(d){var k=srcKeyOf(d);return srcStrokeW(k)?srcStroke(k):null;})
    .attr("stroke-width",function(d){return srcStrokeW(srcKeyOf(d))||null;});
  // ⛔ Labels live in their OWN group, appended after the node group, so paint order can never
  // put a circle over text. They used to be a text child of each per-datum node group, which
  // paints node1-circle, node1-text, node2-circle, node2-text -- so node 2's disc covered
  // ⚠️ Do NOT write the node group's class attribute literally in this comment: the JS is inlined
  // into the served page, so `test_viz_tab_consolidation` counting rendered nodes in the DOM
  // counts the comment too. It did, and reported 10 nodes for a 9-entity fixture.
  // node 1's label. Observed at N=2, the smallest possible graph: "Aurelia B Quorndon" rendered
  // as "relia B Quorndon" with the leading "Au" behind the neighboring circle, and byte-identical
  // across an 8s and a 30s virtual-time budget, so it was the settled state and not a
  // layout-settling artifact. The per-node `dy` was already radius-scaled and was never the cause.
  // (INV-299) A dense capture keeps the structure and drops the names. Applied through the
  // app's OWN auto-off mechanism below rather than a bespoke `display:none` here, so that
  // BOTH label sets go (entity names and match keys — the interactive threshold governs both)
  // and the on-screen checkboxes agree with what was actually drawn.
  const captureLabels=!(capture&&nodes.length>CAPTURE_LABEL_MAX);
  const labelLayer=root.append("g").attr("class","node-labels");
  const label=labelLayer.selectAll("text").data(nodes).join("text").attr("text-anchor","middle")
      .text(function(d){return nodeLabel[d.entity_id];});
  label.append("title").text(function(d){return d.entity_name||"";});
  function place(){
    edge.select("line").attr("x1",function(d){return d.source.x;}).attr("y1",function(d){return d.source.y;})
      .attr("x2",function(d){return d.target.x;}).attr("y2",function(d){return d.target.y;});
    edge.select("text").attr("x",function(d){return (d.source.x+d.target.x)/2;}).attr("y",function(d){return (d.source.y+d.target.y)/2;});
    node.attr("transform",function(d){return "translate("+d.x+","+d.y+")";});
    // Same offset the `<text>` child used to get from `dy`: the node's OWN radius plus a
    // constant, so a data-scaled disc cannot swallow its own label.
    label.attr("x",function(d){return d.x;})
         .attr("y",function(d){return d.y+radius(d)+11;});
  }
  sim.on("tick",place);
  // ⛔ (INV-298/INV-299) PRESETTLE: drive the layout to completion, then place once.
  // `simulation.tick()` advances the physics WITHOUT dispatching events, which is why
  // `place` is a named function called explicitly here.
  // ⚠️ This is not an optimization — it is the only way a headless capture ever sees a
  // finished layout. Measured 2026-09-03 through `capture_screenshots.py` on the 85-entity
  // Truth Set: the animation path ran **5 of the ~300 ticks the layout needs**, at every
  // virtual-time budget from 5s to 300s, because d3's timer is driven by
  // requestAnimationFrame and headless virtual time does not advance it. The nodes sat near
  // their initial phyllotaxis positions, which look plausibly spread out — which is why it
  // went unnoticed.
  if(capture){
    sim.stop();
    const need=Math.ceil(Math.log(sim.alphaMin())/Math.log(1-sim.alphaDecay()));
    for(let i=0;i<need;i++){sim.tick();}
    place();
    fitToExtent();
    graphSettled(true);
  }
  // ⛔ (INV-299) A SETTLED layout must still be a VISIBLE one. `forceCenter` centers the
  // centroid and bounds nothing, so the finished 85-entity layout spreads well outside
  // 1440x900: presettling alone put most nodes off-canvas and lost more of the graph than the
  // unsettled clump it replaced. The near-initial layout was accidentally masking this.
  function fitToExtent(){
    let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
    nodes.forEach(function(d){
      const r=radius(d)+14;
      x0=Math.min(x0,d.x-r);x1=Math.max(x1,d.x+r);
      // the label sits BELOW the node, so the extent is asymmetric -- but only when the
      // labels are actually drawn, or the fit reserves space for text nobody renders.
      y0=Math.min(y0,d.y-r);y1=Math.max(y1,d.y+r+(captureLabels?18:0));
    });
    if(!isFinite(x0))return;
    const w=Math.max(1,x1-x0),h=Math.max(1,y1-y0);
    const k=Math.min(4,Math.max(0.05,0.94*Math.min(W/w,H/h)));
    svg.call(zoomB.transform,
      d3.zoomIdentity.translate((W-k*(x0+x1))/2,(H-k*(y0+y1))/2).scale(k));
  }
  if(network){drawRelationshipLegend(box,links,rtypes,rcolor,edge);}
  else{drawLegend(nodes);}
  addGraphControls("graph-container",nodes.length,!captureLabels);
  // (INV-298) d3 fires "end" when alpha decays below alphaMin -- the layout's own definition
  // of finished, rather than an outside guess at how long that takes.
  sim.on("end",function(){graphSettled(true);});
  function dstart(ev,d){if(!ev.active){graphSettled(false);sim.alphaTarget(0.3).restart();}d.fx=d.x;d.fy=d.y;}
  function dragged(ev,d){d.fx=ev.x;d.fy=ev.y;}
  function dend(ev,d){if(!ev.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}
}
// Relationship-type legend with click-to-filter, carried over unchanged from the removed
// Relationship Network tab. Built FROM the drawn edges, so an entry cannot exist without
// matching marks on screen.
function drawRelationshipLegend(box,links,rtypes,rcolor,edge){
  const l=box.append("div").attr("class","legend");
  l.append("div").style("font-weight","600").style("margin-bottom","3px").text("Relationship");
  const rcount={};links.forEach(function(e){rcount[e.rtype]=(rcount[e.rtype]||0)+1;});
  const roff={};
  rtypes.forEach(function(ty){const r=l.append("div").attr("class","row");
    r.append("span").attr("class","dot").style("background",rcolor(ty));
    r.append("span").text(humLevel(ty));
    r.append("span").attr("class","cnt").text(rcount[ty]||0);
    r.attr("title","Show only this relationship type (click again to restore)");
    r.on("click",function(){roff[ty]=!roff[ty];d3.select(this).classed("off",!!roff[ty]);
      const anyOff=rtypes.some(function(x){return roff[x];});
      edge.style("display",function(d){return (!anyOff||!roff[d.rtype])?null:"none";});});});
}
function radius(d){return Math.min(Math.max(8+d.record_count*4,8),40);}
// Above this node count both label sets default OFF. Chosen because a default
// tuned against the 159-record Truth Set produced ~1000 overlapping labels when
// the same app was reused for production-scale data in Module 7 (contract:
// "Scale principle"). Toggles stay available either way.
const LABEL_AUTO_OFF=150;
// ⛔ (INV-299) A CAPTURE is not an interactive view, and needs a lower label ceiling.
// Interactive labels stay on to 150 because the reader can zoom, pan and toggle them; a
// still image offers none of that, and a settled layout fitted into 1440x900 renders a 10px
// label at the fit scale -- about 2-3px at 85 entities, which is a smudge rather than a name.
// The recap carries the entity names as text beside the image, so the captured graph's job
// there is STRUCTURE. Above this count a capture drops the labels and keeps the structure
// legible; below it, it keeps both. Measured 2026-09-03 on the 85-entity Truth Set.
const CAPTURE_LABEL_MAX=40;
// Non-color encoding companion to the relationship-type color, so the types
// stay distinguishable in a monochrome recap screenshot and for color-vision
// deficiency (contract: "Pair color with a non-color distinction").
const R_DASH={possibly_same:"",possibly_related:"6,4",disclosed:"2,3",ambiguous:"10,3,2,3"};
function rdash(ty){return R_DASH[String(ty||"").toLowerCase()]||"6,4";}
function addGraphControls(containerId,nodeCount,forceLabelsOff){
  const c=d3.select("#"+containerId);
  c.select(".gctl").remove();
  // (INV-299) `forceLabelsOff` is the capture ceiling asserting itself over the interactive
  // one. An explicit parameter rather than a faked `nodeCount`, so the reason is legible at
  // the call site and this function keeps telling the truth about the graph it was given.
  const auto=!!forceLabelsOff||nodeCount>LABEL_AUTO_OFF;
  // Apply the initial state to the container explicitly -- do NOT rely on the
  // checkbox change event, which does not fire for an unchecked box at load.
  const el=document.getElementById(containerId);
  el.classList.toggle("hide-node-labels",auto);
  el.classList.toggle("hide-edge-labels",auto);
  const box=c.append("div").attr("class","gctl");
  function toggle(cls,label,on){
    const row=box.append("label");
    const inp=row.append("input").attr("type","checkbox").property("checked",on);
    row.append("span").text(label);
    inp.on("change",function(){el.classList.toggle(cls,!this.checked);});}
  toggle("hide-node-labels","Entity name labels",!auto);
  toggle("hide-edge-labels","Match key labels",!auto);
  // Mode switch: the full entity population, or only the entities a relationship
  // connects. Replaces the standalone Relationship Network tab, and is shown only when
  // there are relationships to see — the same condition that used to gate that tab.
  if(((STATS||{}).relationships_total||0)>0){
    const row=box.append("label");
    const inp=row.append("input").attr("type","checkbox").attr("id","graph-network-only")
                 .property("checked",graphMode==="network");
    row.append("span").text("Show only entities with relationships");
    inp.on("change",function(){graphMode=this.checked?"network":"all";drawGraph();});
  }
  if(auto)box.append("div").attr("class","why")
    .text("Labels hidden — "+nodeCount+" entities would overlap. Use the toggles to show them.");
  // Same reasoning as the label note: without it the bootcamper reads a default as
  // their data, and concludes the graph is showing everything there is.
  // (#327) When the payload is capped, `nodeCount` counts a capped subset: name it as part of
  // the datastore's `related_total`, state the cap, and never offer "all".
  const capped=!!graphPayload.capped;
  if(graphMode==="network"&&(capped||(STATS||{}).entities_total>GRAPH_SUBGRAPH_DEFAULT_ABOVE))
    box.append("div").attr("class","why")
      .text(capped?"Showing "+nodeCount+" of the "+graphPayload.related_total+" entities that have "+
                   "relationships — the graph is capped at "+graphPayload.nodes.length+" of "+
                   graphPayload.total+" entities."
            :"Showing the "+nodeCount+" entities that have relationships, of "+
            STATS.entities_total+" total — the full population is too dense to read at this "+
            "scale. Uncheck the toggle above to show them all.");
  if(graphMode!=="network"&&capped)
    box.append("div").attr("class","why")
      .text("Showing "+graphPayload.nodes.length+" of "+graphPayload.total+" entities — the graph "+
            "is capped; entities spanning the most sources are kept first.");}
// Built FROM the rendered nodes, never from a static color config: a legend
// entry then cannot exist without matching marks on screen, which is what makes
// "the legend shows colors that appear nowhere in the graph" impossible.
// Clicking an entry filters the view and toggles back.
function drawLegend(nodes){d3.select("#graph-container .legend").remove();
  const counts={};(nodes||[]).forEach(function(n){(n.data_sources||[]).forEach(function(s){counts[s]=(counts[s]||0)+1;});});
  // Combination entries, counted over the nodes that actually carry them, so a
  // cross-source color on screen always has a row naming what it means. A color a viewer
  // cannot name is not an improvement over the wrong color.
  const comboCounts={};
  (nodes||[]).forEach(function(n){const k=srcKeyOf(n);if(isCombo(k))comboCounts[k]=(comboCounts[k]||0)+1;});
  const srcs=Object.keys(counts).sort();
  const combos=Object.keys(comboCounts).sort();
  if(!srcs.length)return;
  const off={};
  const l=d3.select("#graph-container").append("div").attr("class","legend");
  if(combos.length){
    l.append("div").attr("class","why").style("margin","0 0 4px")
      .text("Entities in more than one source have their own color:");
    combos.forEach(function(k){const r=l.append("div").attr("class","row");
      r.append("span").attr("class","dot").style("background",color(k))
        .style("box-shadow",srcStrokeW(k)?("inset 0 0 0 "+srcStrokeW(k)+"px "+srcStroke(k)):null);
      r.append("span").text(comboLabel(k));
      r.append("span").attr("class","cnt").text(comboCounts[k]);
      r.attr("title","Entities appearing in "+comboLabel(k));});
  }
  // "Entities per source", NOT "Single-source": these counts are PARTICIPATION -- every
  // entity drawing on that source, cross-source entities included -- because `counts`
  // above increments once per source per node. The label is a claim about a denominator,
  // and single-source was never the denominator in use. On a two-source run this block
  // read `CRM_CUSTOMERS 65` / `WEBSTORE_ACCOUNTS 70` against 121 entities with 14 spanning
  // both (65 + 70 - 14 = 121, inclusion-exclusion); the true single-source figures were 51
  // and 56, and nothing on screen contradicted the misreading because each figure agreed
  // with every other total in the app.
  //
  // The rows are participation-shaped throughout, which is why relabeling is the fix and
  // recomputing is not: the tooltip filters the SOURCE, the click handler keeps a node when
  // ANY of its sources is on, and the swatch is the per-source color while a cross-source
  // entity is drawn in its own combination color. Changing the counts would put the label
  // in agreement with the heading and out of agreement with all three.
  //
  // Emitted unconditionally -- it sat inside `if(combos.length)` and so vanished on
  // single-source runs, where the label happens to be correct. That hid the defect from
  // the simple case and showed it only on the runs this module exists to demonstrate.
  l.append("div").attr("class","why").style("margin",combos.length?"6px 0 4px":"0 0 4px")
    .text("Entities per source:");
  if(combos.length){
    l.append("div").attr("class","why").style("margin","0 0 4px").style("font-style","italic")
      .text("An entity in more than one source is counted in each of its sources below.");
  }
  srcs.forEach(function(s){const r=l.append("div").attr("class","row");
    r.append("span").attr("class","dot").style("background",color(s))
      // Same expression as the node's stroke, so the swatch and the node cannot disagree
      // about a source's encoding -- including its WIDTH, which is a channel above 24
      // sources.
      .style("box-shadow",srcStrokeW(s)?("inset 0 0 0 "+srcStrokeW(s)+"px "+srcStroke(s)):null);
    r.append("span").text(s);
    r.append("span").attr("class","cnt").text(counts[s]);
    r.attr("title","Show only "+s+" (click again to restore)");
    r.on("click",function(){off[s]=!off[s];d3.select(this).classed("off",!!off[s]);
      const anyOff=srcs.some(function(x){return off[x];});
      d3.selectAll("#graph-container .node").style("display",function(d){
        if(!anyOff)return null;
        const keep=(d.data_sources||[]).some(function(x){return !off[x];});
        return keep?null:"none";});});});}
function openModal(d){const m=d3.select("#modal");document.getElementById("modal").className="modal";
  const body="<p><b>Data sources:</b> "+esc(d.data_sources.join(", "))+"<br><b>Records:</b> "+d.record_count+"</p>"+
    "<div id='node-actions'></div>";
  m.html(modalShell(d.entity_name,"Entity "+d.entity_id,body));
  // Same three actions as every other entity surface -- the graph node modal is
  // not an exception (contract: "Per-entity actions").
  addEntityActions(d3.select("#node-actions"),d.entity_id,d.entity_name);
  document.getElementById("modal-bg").style.display="flex";}
function closeModal(){document.getElementById("modal-bg").style.display="none";}
// Shared modal chrome: header bar (title + subtitle + circular close) and a body
// wrapper. Every entity dialog -- Records, Why?, How? -- goes through this, so
// they cannot drift apart visually.
function modalShell(title,subtitle,bodyHtml){
  return "<div class='mhead'><div><h3>"+esc(title)+"</h3>"+
    (subtitle?"<div class='muted'>"+esc(subtitle)+"</div>":"")+
    "</div><button class='mclose' onclick='closeModal()' title='Close' aria-label='Close'>&times;</button></div>"+
    "<div class='mbody'>"+bodyHtml+"</div>";}
// The canonical per-entity action set (contract: "Per-entity actions"). ONE
// renderer, invoked from every surface that shows an entity — graph node modal,
// the merged-entity cards on Search / Probe, every aggregate drill-down, and
// search results. Adding a
// button here reaches all of them; that is the point. Wiring actions per
// code-path is how surfaces previously shipped with different subsets.
function addEntityActions(sel,eid,name){if(eid===undefined||eid===null)return;
  const a=sel.append("div").attr("class","actions");
  a.append("button").attr("title","Show the records that make up this entity").text("Records").on("click",function(){showRecords(eid,name);});
  a.append("button").attr("title","Why did these records resolve together?").text("Why?").on("click",function(){explain("why",eid,name);});
  a.append("button").attr("title","How was this entity constructed?").text("How?").on("click",function(){explain("how",eid,name);});}
// Renders a list of entities with the full action set — shared by every
// aggregate drill-down (histogram buckets, cross-source cells, match-key rows)
// and by the largest-entities list, so all of them behave identically.
function renderEntityList(box,entities,emptyMsg){
  if(!entities||!entities.length){box.append("p").attr("class","muted").text(emptyMsg||"No entities.");return;}
  entities.forEach(function(e){
    const row=box.append("div").attr("class","card");
    row.append("h4").text(e.entity_name||("Entity "+e.entity_id));
    const meta=[];
    if(e.record_count!==undefined)meta.push(e.record_count+" record"+(e.record_count===1?"":"s"));
    if(e.data_sources&&e.data_sources.length)meta.push(e.data_sources.join(" + "));
    meta.push("Entity "+e.entity_id);
    row.append("div").attr("class","muted").text(meta.join(" · "));
    addEntityActions(row,e.entity_id,e.entity_name);});}
async function showRecords(eid,name){const m=d3.select("#modal");
  document.getElementById("modal").className="modal wide explain";
  const sub=(name||"")+" · Entity "+eid;
  m.html(modalShell("Records in this entity",sub,"<p class='muted'>Loading…</p>"));
  document.getElementById("modal-bg").style.display="flex";
  let data;try{data=await getJSON("/api/records?entity_id="+encodeURIComponent(eid));}catch(e){data={error:String(e)};}
  let body="";
  if(data&&data.error){body="<p class='muted'>"+esc(data.error)+"</p>";}
  else{const recs=(data&&data.records)||[];
    if(!recs.length){body="<p class='muted'>No records returned for this entity.</p>";}
    // Columns come from the fields the endpoint actually returned, never from a fixed
    // list: this server's /api/records carries data_source/record_id/match_key, so a
    // hardcoded Name/Address/Phone header rendered three empty columns for every row
    // and read as missing data rather than as a payload that never had those fields.
    else{const cols=[["match_key","Match key"],["name","Name"],["address","Address"],["phone","Phone"]]
        .filter(function(c){return recs.some(function(r){return r[c[0]];});});
      body="<table class='tbl'><thead><tr><th>Source</th><th>Record</th>"+
        cols.map(function(c){return "<th>"+esc(c[1])+"</th>";}).join("")+"</tr></thead><tbody>";
      recs.forEach(function(r){body+="<tr><td>"+esc(r.data_source)+"</td><td>"+esc(r.record_id)+"</td>"+
        cols.map(function(c){return "<td>"+esc(r[c[0]]||"")+"</td>";}).join("")+"</tr>";});
      body+="</tbody></table>";}}
  m.html(modalShell("Records in this entity",sub,body));}
function explainTitle(kind){return kind==="why"?"Why did these records resolve together?":"How was this entity built?";}
async function explain(kind,eid,name){const m=d3.select("#modal");
  document.getElementById("modal").className="modal wide explain";
  const sub=(name||"")+" · Entity "+eid;
  m.html(modalShell(explainTitle(kind),sub,"<p class='muted'>Loading…</p>"));
  document.getElementById("modal-bg").style.display="flex";
  let data;try{data=await getJSON("/api/"+kind+"?entity_id="+encodeURIComponent(eid));}catch(e){data={error:String(e)};}
  let body="";
  if(data&&data.error){body="<p class='muted'>"+esc(data.error)+"</p>";}
  else{body=(kind==="why"?renderWhy(data):renderHow(data));
    body+="<details><summary>Show the raw Senzing response (JSON)</summary><pre>"+esc(JSON.stringify(data&&data.result!==undefined?data.result:data,null,2))+"</pre></details>";}
  m.html(modalShell(explainTitle(kind),sub,body));}
function mkChips(mk){return (mk||"").split(/(?=[+-])/).filter(function(p){return p;})
  .map(function(p){return "<span class='chip'>"+esc(p)+"</span>";}).join("")||"<span class='muted'>(none)</span>";}
function humLevel(l){return ({RESOLVED:"the same entity",POSSIBLY_SAME:"possibly the same entity",
  POSSIBLY_RELATED:"possibly related",DISCLOSED_RELATION:"a disclosed relationship",
  NO_RELATION:"not related"})[l]||(l?l.toLowerCase().replace(/_/g," "):"related");}
function bucketMeta(b){b=(b||"").toUpperCase();
  if(b==="SAME")return ["b-strong","#137333","Same"];
  if(b==="CLOSE")return ["b-strong","#137333","Close"];
  if(b==="LIKELY")return ["b-mid","#8a6d00","Likely"];
  if(b==="PLAUSIBLE")return ["b-weak","#a1440a","Plausible"];
  if(b==="NO_CHANCE"||b==="UNLIKELY")return ["b-none","#a50e0e","No match"];
  return ["b-mid","#8a6d00",b||"—"];}
function renderWhy(data){const wr=((data.result||{}).WHY_RESULTS)||[];
  if(!wr.length)return "<p class='muted'>Senzing returned no comparison detail for these records.</p>";
  const mi=wr[0].MATCH_INFO||{};const key=mi.WHY_KEY||mi.MATCH_KEY||"";const rule=mi.WHY_ERRULE_CODE||mi.ERRULE_CODE||"";const level=mi.MATCH_LEVEL_CODE||"";
  let h="<div class='verdict'>Senzing considers these records <b>"+esc(humLevel(level))+"</b> — on match key "+mkChips(key)+(rule?" (rule <code>"+esc(rule)+"</code>)":"")+".</div>";
  const fs=mi.FEATURE_SCORES||{};const feats=Object.keys(fs);
  if(feats.length){
    h+="<h4>Feature-by-feature comparison</h4>";
    h+="<table class='why-table'><thead><tr><th>Feature</th><th>Record A</th><th>Record B</th><th>How well it matched</th></tr></thead><tbody>";
    feats.forEach(function(ft){(fs[ft]||[]).forEach(function(sc){
      const bm=bucketMeta(sc.SCORE_BUCKET);const sv=(sc.SCORE===0||sc.SCORE)?sc.SCORE:"";
      h+="<tr><td class='feat'>"+esc(ft)+"</td><td>"+esc(sc.INBOUND_FEAT_DESC||"")+"</td><td>"+esc(sc.CANDIDATE_FEAT_DESC||"")+"</td>"+
        "<td><span class='bucket "+bm[0]+"'>"+esc(bm[2])+(sv!==""?" · "+sv:"")+"</span>"+
        (sv!==""?"<div class='score-bar'><span style='width:"+Math.max(3,Math.min(100,sv))+"%;background:"+bm[1]+"'></span></div>":"")+"</td></tr>";
    });});
    h+="</tbody></table><p class='legend-note'>Each row compares one feature across the two records. The score (0–100) and its bucket show how strongly that feature agreed — green = strong, amber = likely, orange = plausible, red = no match.</p>";
  }
  return h;}
function _recordChips(members){var out=[];(members||[]).forEach(function(mb){(mb.RECORDS||[]).forEach(function(r){
  out.push("<span class='chip'>"+esc((r.DATA_SOURCE||"?")+":"+(r.RECORD_ID||"?"))+"</span>");});});
  return out.join("")||"<span class='muted'>—</span>";}
function renderHow(data){const hr=(data.result||{}).HOW_RESULTS||{};const steps=hr.RESOLUTION_STEPS||[];
  // An UNSETTLED final state (#169, INV-330) is either of the two signs Phase D's how-state audit
  // uses (#154): FINAL_STATE.NEED_REEVALUATION non-zero (an integer per the response
  // schema), or more than one FINAL_STATE.VIRTUAL_ENTITIES[]. Either one makes both
  // one-entity sentences below false, so the notice replaces them. The notice reports the
  // values the response carries and nothing more; it gives NEED_REEVALUATION no meaning
  // (INV-080/INV-149; the contract's /api/how entry carries the dated MCP-NEGATIVE marker).
  // No FINAL_STATE, or neither sign: no notice and today's rendering, byte for byte.
  const ve=((hr.FINAL_STATE||{}).VIRTUAL_ENTITIES)||[];const nr=(hr.FINAL_STATE||{}).NEED_REEVALUATION;
  const signs=[];
  if(typeof nr==="number"&&nr!==0)signs.push("<code>FINAL_STATE.NEED_REEVALUATION</code> is <b>"+esc(String(nr))+"</b>");
  if(Array.isArray(ve)&&ve.length>1)signs.push("<code>FINAL_STATE.VIRTUAL_ENTITIES</code> lists <b>"+ve.length+"</b> virtual entities");
  const unsettled=signs.length>0;
  const notice="<div class='verdict how-unsettled'><b>Unsettled final state.</b> Senzing's How response for this entity shows "+
    signs.join(", and ")+". This page therefore does not describe these records as one entity; what the response holds is shown below as returned.</div>";
  if(steps.length){
    let h=unsettled?notice:"<div class='verdict'>Senzing built this entity in <b>"+steps.length+"</b> step(s), each merging two groups of records.</div>";
    steps.forEach(function(st,i){const mi=st.MATCH_INFO||{};const mk=mi.MATCH_KEY||"";const rule=mi.ERRULE_CODE||"";
      const v1=st.VIRTUAL_ENTITY_1||{};const v2=st.VIRTUAL_ENTITY_2||{};
      h+="<div class='step'><div><span class='num'>"+(st.STEP||(i+1))+"</span><b>Merged on</b> "+mkChips(mk)+(rule?" · <code>"+esc(rule)+"</code>":"")+"</div>"+
        "<div class='recs' style='margin-top:8px'><div class='rec'><b>Group A</b><br>"+_recordChips(v1.MEMBER_RECORDS)+"</div>"+
        "<div class='rec'><b>Group B</b><br>"+_recordChips(v2.MEMBER_RECORDS)+"</div></div></div>";});
    return h;}
  // Unsettled with no steps: each virtual entity is its own group. Pooling them is what
  // made two groups read as one entity.
  var grouped="";
  if(unsettled){grouped="<h4>"+ve.length+" virtual entit"+(ve.length===1?"y":"ies")+" in the final state</h4><div class='recs'>";
    ve.forEach(function(v,i){var k=0;(v.MEMBER_RECORDS||[]).forEach(function(m){k+=((m.RECORDS||[]).length);});
      grouped+="<div class='rec how-group' style='min-width:auto'><b>Group "+(i+1)+"</b>"+
        (v.VIRTUAL_ENTITY_ID?" · <code>"+esc(String(v.VIRTUAL_ENTITY_ID))+"</code>":"")+
        " · "+k+" record"+(k===1?"":"s")+"<br>"+_recordChips(v.MEMBER_RECORDS)+"</div>";});
    grouped+="</div>";}
  var members=[];ve.forEach(function(v){(v.MEMBER_RECORDS||[]).forEach(function(m){members.push(m);});});
  var n=0;members.forEach(function(m){n+=((m.RECORDS||[]).length);});
  return unsettled?notice+grouped:"<div class='verdict'>These records resolved <b>directly</b> into one entity — Senzing found them consistent enough to merge with no intermediate steps.</div>"+
    "<h4>"+n+" record"+(n===1?"":"s")+" in this entity</h4>"+
    "<div class='recs'><div class='rec' style='min-width:auto'>"+_recordChips(members)+"</div></div>";}
async function drawHist(){const s=await getJSON("/api/stats");const box=d3.select("#hist");box.html("");
  box.append("p").html("<b>"+s.records_total+"</b> records collapsed into <b>"+s.entities_total+"</b> entities, including <b>"+s.multi_record_entities+"</b> multi-record entities.");
  box.append("p").attr("class","muted").text("Click a bar to list the entities in that bucket.");
  const data=[["1 record","1"],["2 records","2"],["3 records","3"],["4+ records","4+"]]
    .map(function(z){return {label:z[0],key:z[1],n:s.histogram[z[1]]||0};});
  const W=Math.min(720,box.node().clientWidth),H=300,m={t:20,r:10,b:40,l:44};
  const svg=box.append("svg").attr("width",W).attr("height",H);
  const x=d3.scaleBand().domain(data.map(function(d){return d.label;})).range([m.l,W-m.r]).padding(0.25);
  const maxN=d3.max(data,function(d){return d.n;})||1;
  const y=d3.scaleLinear().domain([0,maxN]).nice().range([H-m.b,m.t]);
  svg.append("g").attr("transform","translate(0,"+(H-m.b)+")").call(d3.axisBottom(x));
  // This axis counts ENTITIES, which are whole. d3's .ticks(n) asks for "about n
  // ticks" and picks whatever step fits, so a domain of [0,1] is labeled in fifths
  // — "0.4 entities". Small maxima are the NORMAL bootcamp shape (the built-in
  // evaluation license caps ingestion at 500 DSRs), so pick integer tick VALUES.
  // .tickFormat("d") alone is not enough: it rounds the labels while leaving the
  // fractional positions, yielding duplicates like 0,0,0,1,1,1.
  const yStep=Math.max(1,Math.ceil(maxN/5));
  svg.append("g").attr("transform","translate("+m.l+",0)")
    .call(d3.axisLeft(y).tickValues(d3.range(0,maxN+1,yStep)).tickFormat(d3.format("d")));
  svg.selectAll("rect").data(data).join("rect").attr("x",function(d){return x(d.label);}).attr("y",function(d){return y(d.n);})
    .attr("width",x.bandwidth()).attr("height",function(d){return y(0)-y(d.n);}).attr("rx",4).style("cursor","pointer")
    .attr("fill",function(d,i){return i===0?"__ACCENT__":"__ACCENT_HOT__";})
    .on("click",function(ev,d){showBucket(s,d.key,d.label);});
  svg.selectAll("text.v").data(data).join("text").attr("class","v").attr("x",function(d){return x(d.label)+x.bandwidth()/2;})
    .attr("y",function(d){return y(d.n)-6;}).attr("text-anchor","middle").attr("font-size",13).attr("font-weight",600).text(function(d){return d.n;});
  box.append("div").attr("id","bucket-list").attr("class","bucket-list");
  // The largest resolved entities — formerly the Results Dashboard's only
  // unique content, folded in here when that duplicate tab was removed
  // (contract: "De-duplication (required)"). Headline counts stay in the page
  // summary strip and are deliberately NOT repeated on this tab.
  box.append("h3").attr("class","section-h").text("Largest resolved entities");
  const samp=s.sample_entities||[];
  const sbox=box.append("div");
  renderEntityList(sbox,samp,"No multi-record entities.");}
function showBucket(s,key,label){const box=d3.select("#bucket-list");if(box.empty())return;box.html("");
  const list=(s.bucket_entities&&s.bucket_entities[key])||[];
  const total=(s.histogram&&s.histogram[key])||list.length;
  box.append("h4").text(label+" — "+total+(total===1?" entity":" entities"));
  renderEntityList(box,list,"No entities in this bucket.");
  if(total>list.length)box.append("p").attr("class","muted").text("Showing first "+list.length+" of "+total+".");}
async function doSearch(){const q=document.getElementById("search-in").value;const box=d3.select("#results");box.html("<p class='muted'>Searching…</p>");
  const r=await getJSON("/api/search?q="+encodeURIComponent(q));box.html("");
  // Name what was searched, so an empty result reads as "no match under these
  // attributes" and not as "this name is not in your data" (INV-115).
  if(!r.results||!r.results.length){const tried=(r.attributes_tried||[]).join(" then ");
    const how=tried?("a "+tried+" search for "):"";
    box.append("p").attr("class","muted").text(r.error?("Search could not run: "+r.error)
      :("No entity matched "+how+'"'+q+'".'));return;}
  r.results.forEach(function(e){const card=box.append("div").attr("class","card");
    card.append("h4").text(e.entity_name);
    card.append("div").attr("class","muted").text("Entity "+e.entity_id+" · "+(e.record_count||"?")+" record(s) · "+(e.data_sources||[]).join(", "));
    if(e.match_key){const mk=card.append("div").attr("class","mk");e.match_key.split(/(?=[+-])/).forEach(function(p){if(p)mk.append("span").text(p);});}
    if(e.resolution_rule)card.append("div").append("code").text(e.resolution_rule);
    addEntityActions(card,e.entity_id,e.entity_name);});}
async function loadProbes(){const m=await getJSON("/api/merges");const box=d3.select("#probe-btns");box.html("");
  // The example chips drive the live search box. The static snapshot has none, so they would be
  // dead controls there — offer only the browse, which needs no engine.
  const live=!!document.getElementById("search-in");
  // Chips MUST be verified to return at least one match before being offered: a hint
  // that finds nothing is worse than no hint, and that is exactly what a chip named
  // after an organization did while search tried NAME_FULL only. Verify against the
  // live engine — the same path the click will take — and drop any that come back
  // empty rather than shipping a dead control.
  // Verified concurrently rather than one at a time: nothing about the check is
  // order-dependent, and a serial loop puts up to ten live engine round-trips in front
  // of the first paint of the app. Order and the six-chip cap are reapplied to the
  // results, so the chips offered are identical to the serial version's — only the
  // waiting is gone. The trade is that all candidates are now searched instead of
  // stopping at the sixth hit: the worst case (ten) is what it always was, the typical
  // case costs a few more searches, and both happen in one round-trip.
  if(live){const cands=(m.entities||[]).slice(0,10).filter(function(e){return e.entity_name;});
    // Each candidate catches its own failure, so one rejected search drops one chip
    // rather than rejecting the batch and taking every chip down with it.
    const verdicts=await Promise.all(cands.map(function(e){
      return getJSON("/api/search?q="+encodeURIComponent(e.entity_name))
        .then(function(r){const hit=!!(r&&r.results&&r.results.length);
          if(!hit)console.warn("dropped example chip (no match): "+e.entity_name);
          return hit;})
        .catch(function(err){console.warn("dropped example chip (search failed): "+e.entity_name);return false;});}));
    const good=cands.filter(function(e,i){return verdicts[i];}).slice(0,6);
    good.forEach(function(e){box.append("button").attr("class","probe").text(e.entity_name)
      .on("click",function(){document.getElementById("search-in").value=e.entity_name;doSearch();});});}
  // The one capability the removed Record Merges tab uniquely had: browse every merged
  // entity with no query. Search / Probe otherwise shows a strict superset per entity,
  // so this is what keeps the removal lossless rather than a trade.
  if((m.entities||[]).length){
    box.append("button").attr("class","probe").attr("id","show-all-merges")
       .text("Show all merged entities ("+m.entities.length+")")
       .on("click",function(){showAllMerges(m.entities);});
  }}
// Lists every multi-record entity, no query needed. Same per-entity actions as a search
// result, so the entity surfaces stay consistent (contract: per-entity actions everywhere).
function showAllMerges(entities){
  const box=d3.select("#results");box.html("");
  const si=document.getElementById("search-in");
  if(si)si.value="";
  if(!entities.length){box.append("p").attr("class","muted").text("No multi-record entities.");return;}
  box.append("p").attr("class","muted")
     .text("All "+entities.length+" merged entities. Search above to see per-record match keys and feature scores for one of them.");
  entities.forEach(function(e){const card=box.append("div").attr("class","card");
    card.append("h4").text(e.entity_name+"  ");
    card.select("h4").append("span").attr("class","chip").text((e.data_sources||[]).join(" + "));
    const mk=(e.records||[]).map(function(r){return r.match_key;}).filter(function(x){return x;})[0]||"";
    card.append("div").attr("class","muted").text(e.record_count+" records · Entity "+e.entity_id);
    // mkChips returns one HTML string, already escaped per chip — set it, do not iterate it.
    if(mk)card.append("div").html(mkChips(mk));
    addEntityActions(card,e.entity_id,e.entity_name);});}
// Cross-Source overlap heatmap: entities shared between each pair of data sources.
async function drawOverlap(){const o=await getJSON("/api/overlap");const box=d3.select("#overlap");box.html("");
  const src=o.sources||[],m=o.matrix||[];
  box.append("p").html("Each cell is the number of resolved entities that appear in <b>both</b> data sources; the diagonal is the entities present in that source.");
  if(src.length<2){box.append("p").attr("class","muted").text("Cross-source overlap needs at least two data sources.");return;}
  let max=1;for(let i=0;i<m.length;i++)for(let j=0;j<m.length;j++){if(i!==j&&m[i][j]>max)max=m[i][j];}
  const rgb=hexRgb(C_BLUE);
  const t=box.append("table").attr("class","heat");
  const head=t.append("thead").append("tr");head.append("th").text("");
  src.forEach(function(s){head.append("th").text(s);});
  const tb=t.append("tbody");
  src.forEach(function(s,i){const tr=tb.append("tr");tr.append("td").attr("class","rowh").text(s);
    src.forEach(function(_,j){const v=(m[i]&&m[i][j])||0;const td=tr.append("td").attr("class","cell").text(v);
      if(i===j){td.style("background","var(--bg)").style("font-weight","600");}
      else if(v>0){const a=0.15+0.85*v/max;td.style("background","rgba("+rgb[0]+","+rgb[1]+","+rgb[2]+","+a.toFixed(3)+")");if(a>0.55)td.style("color","#fff");}
      // Every aggregate drills down (contract: "Drill-down on every aggregate
      // view"). Cross-Source was previously the one dead end.
      if(v>0){td.style("cursor","pointer").attr("title","Show these entities")
        .on("click",function(){showOverlapCell(o,i,j,src[i],src[j]);});}
    });});
  box.append("div").attr("id","overlap-list");
  if(o.cell_capped)box.append("p").attr("class","muted").text("Entity lists are capped; the cell counts remain exact.");
}
function showOverlapCell(o,i,j,si,sj){const box=d3.select("#overlap-list");if(box.empty())return;box.html("");
  const key=Math.min(i,j)+","+Math.max(i,j);
  const list=(o.cell_entities&&o.cell_entities[key])||[];
  const total=(o.matrix&&o.matrix[i]&&o.matrix[i][j])||list.length;
  box.append("h4").text(i===j?(si+" — "+total+(total===1?" entity":" entities"))
    :(si+" ∩ "+sj+" — "+total+(total===1?" shared entity":" shared entities")));
  renderEntityList(box,list,"No entities in this cell.");
  if(total>list.length)box.append("p").attr("class","muted").text("Showing first "+list.length+" of "+total+".");}
// Match Keys: which feature combinations drove the most resolutions.
async function drawMatchKeys(){const d=await getJSON("/api/matchkeys");const box=d3.select("#matchkeys");box.html("");
  const items=d.match_keys||[];
  box.append("p").html("Which feature combinations (match keys) drove the most resolutions across your data.");
  if(!items.length){box.append("p").attr("class","muted").text("No match keys were recorded for the resolved records.");return;}
  // Gutter sized from the data, then labels fitted to it. Real match keys run to
  // 70+ chars ("+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+..."), and a
  // fixed 190px gutter with text-anchor:end pushed the head of every long key off
  // the left edge of the SVG -- so the four highest bars all rendered as
  // "...ISTRATION_COUNTRY+LEI_NUMBER" and could not be told apart. Counts were
  // right, labels useless, and the chart looked fine.
  const W=Math.min(720,box.node().clientWidth),barh=26;
  const longest=d3.max(items,function(z){return (z.match_key||"").length;})||0;
  const gutter=Math.max(150,Math.min(320,longest*5.9+14));
  const mm={t:6,r:44,b:6,l:Math.min(gutter,W*0.55)},H=mm.t+mm.b+items.length*barh;
  // MIDDLE-ellipsize, never left-trim. Right-trimming alone is not enough: real
  // keys are "+A+B+C..." sequences that often share a long prefix and differ only
  // in the last segment, so head-only truncation renders the top bars identically
  // -- the same unreadable chart, just failing from the other end. Keeping both
  // ends makes keys that differ at either end distinguishable.
  const maxChars=Math.max(8,Math.floor((mm.l-10)/5.9));
  function fitKey(k){k=k||"";if(k.length<=maxChars)return k;
    const tail=Math.max(6,Math.floor((maxChars-1)*0.5)),head=maxChars-1-tail;
    return k.slice(0,head)+"…"+k.slice(k.length-tail);}
  // The requirement is DISTINCTNESS, not the ellipsis strategy: no two rendered
  // labels may be identical unless their underlying values are. Middle-ellipsis
  // reduces collisions but cannot prevent them -- two keys sharing a long head AND
  // a long tail, differing only in the elided middle, still render identically, and
  // the top bars again cannot be told apart. So check, and disambiguate the ones
  // that collide with a positional suffix; the full value stays on hover either way.
  const fitted=items.map(function(z){return fitKey(z.match_key);});
  const seen={};
  fitted.forEach(function(label,i){
    if(seen[label]===undefined){seen[label]=i;return;}
    // Only a real collision (different source values) needs disambiguating.
    if(items[seen[label]].match_key===items[i].match_key)return;
    fitted[i]=label+" ("+(i+1)+")";
  });
  function labelFor(i){return fitted[i];}
  const svg=box.append("svg").attr("width",W).attr("height",H);
  const x=d3.scaleLinear().domain([0,d3.max(items,function(z){return z.count;})||1]).range([mm.l,W-mm.r]);
  const y=d3.scaleBand().domain(items.map(function(z){return z.match_key;})).range([mm.t,H-mm.b]).padding(0.2);
  svg.selectAll("rect").data(items).join("rect").attr("x",mm.l).attr("y",function(z){return y(z.match_key);})
    .attr("width",function(z){return Math.max(0,x(z.count)-mm.l);}).attr("height",y.bandwidth()).attr("rx",3).attr("fill",C_BLUE);
  svg.selectAll("text.k").data(items).join("text").attr("class","k").attr("x",mm.l-8).attr("y",function(z){return y(z.match_key)+y.bandwidth()/2;})
    .attr("text-anchor","end").attr("dominant-baseline","middle").attr("font-size",11).attr("font-family","__CODE_FONT__").text(function(z,i){return labelFor(i);})
    .append("title").text(function(z){return z.match_key;});
  svg.selectAll("text.c").data(items).join("text").attr("class","c").attr("x",function(z){return x(z.count)+5;}).attr("y",function(z){return y(z.match_key)+y.bandwidth()/2;})
    .attr("dominant-baseline","middle").attr("font-size",11).attr("font-weight",600).text(function(z){return z.count;});
  if(d.capped)box.append("p").attr("class","muted").text("Showing the top "+items.length+" of "+d.distinct+" distinct match keys.");
  // Clickable rows -> the entities carrying that match key (contract:
  // "Drill-down on every aggregate view"). Match Keys was the last dead end.
  svg.selectAll("rect").style("cursor","pointer").append("title").text(function(z){return z.match_key+" — click to show the entities with this match key";});
  svg.selectAll("rect").on("click",function(ev,z){showMatchKey(d,z.match_key,z.count);});
  box.append("div").attr("id","matchkey-list");
  if(d.entities_capped)box.append("p").attr("class","muted").text("Entity lists are capped; the counts remain exact.");
}
function showMatchKey(d,key,count){const box=d3.select("#matchkey-list");if(box.empty())return;box.html("");
  const list=(d.match_key_entities&&d.match_key_entities[key])||[];
  box.append("h4").text(key+" — "+count+(count===1?" record":" records"));
  renderEntityList(box,list,"No entities recorded for this match key.");
  if(list.length&&count>list.length)box.append("p").attr("class","muted").text("Showing first "+list.length+" entities.");}
// Feature Scores: how tightly each feature agreed across resolved records
// (from a capped why_records sample; the sample size is always shown).
async function drawFeatures(){const d=await getJSON("/api/features");const box=d3.select("#features");box.html("");
  const feats=d.features||[];
  box.append("p").html("How tightly each feature agreed across resolved records — greener means stronger agreement.");
  if(!feats.length){box.append("p").attr("class","muted").text("Feature-score details come from the live server; none were sampled (no multi-record entities, or the sample is unavailable in this snapshot).");return;}
  const order=["SAME","CLOSE","PLUS","LIKELY","PLAUSIBLE","UNLIKELY","NO_CHANCE"];
  const bcolor={SAME:"#137333",CLOSE:"#137333",PLUS:C_GREEN,LIKELY:"#8a6d00",PLAUSIBLE:"#a1440a",UNLIKELY:"#a50e0e",NO_CHANCE:"#a50e0e"};
  const rows=feats.map(function(f){const b=f.buckets||{};const total=Object.keys(b).reduce(function(s,k){return s+b[k];},0)||1;return {feature:f.feature,buckets:b,total:total};});
  const W=Math.min(720,box.node().clientWidth),barh=32,mm={t:6,r:10,b:6,l:130},H=mm.t+mm.b+rows.length*barh;
  const x=d3.scaleLinear().domain([0,1]).range([mm.l,W-mm.r]);
  const y=d3.scaleBand().domain(rows.map(function(z){return z.feature;})).range([mm.t,H-mm.b]).padding(0.25);
  const svg=box.append("svg").attr("width",W).attr("height",H);
  rows.forEach(function(r){let acc=0;const keys=order.filter(function(k){return r.buckets[k];}).concat(Object.keys(r.buckets).filter(function(k){return order.indexOf(k)<0;}));
    keys.forEach(function(k){const frac=r.buckets[k]/r.total;svg.append("rect").attr("x",x(acc)).attr("y",y(r.feature)).attr("width",Math.max(0,x(acc+frac)-x(acc))).attr("height",y.bandwidth()).attr("fill",bcolor[k]||C_MUTED).append("title").text(k+": "+r.buckets[k]);acc+=frac;});
    svg.append("text").attr("x",mm.l-8).attr("y",y(r.feature)+y.bandwidth()/2).attr("text-anchor","end").attr("dominant-baseline","middle").attr("font-size",12).attr("font-weight",600).text(r.feature);});
  box.append("p").attr("class","muted").text("Based on "+d.sampled+" of "+d.multi_record_total+" multi-record entities"+(d.capped?" (sampled to bound cost).":"."));
}
function esc(s){return (s||"").replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];});}
// Deep-link support: ?tab=<id> opens that tab, ?q=<text> runs a search on Search /
// Probe (defaulting the tab to probe). Makes any view of the app a shareable URL, and
// is how the screenshot helper captures one image per tab — including Search / Probe
// showing real results, which the static snapshot cannot do (it has no engine).
function applyDeepLink(){
  var p=new URLSearchParams(location.search||"");
  var tab=p.get("tab"), q=p.get("q");
  if(q!==null&&!tab)tab="probe";
  if(tab&&tabApplicable(tab)&&document.getElementById("tab-"+tab)&&document.getElementById("navbtn-"+tab))activate(tab);
  if(q!==null){var box=document.getElementById("search-in");if(box){box.value=q;doSearch();}}
}
async function init(){STATS=await getJSON("/api/stats");await loadBanner();buildNav();drawGraph();loadProbes();applyDeepLink();}
init();
window.addEventListener("resize",function(){
  if(d3.select("#tab-graph").classed("active"))drawGraph();});
</script></body></html>
"""
PROBE_BODY_LIVE = (
    '<div style="margin-bottom:10px">'
    '<input id="search-in" placeholder="Search a name (e.g. Robert Smith)"> '
    '<button class="probe" onclick="doSearch()">Search</button></div>'
    '<div id="probe-btns"></div><div id="results"></div>'
)
def render_page(title, data_shim="", probe_body=None, sources=None):
    ...
def make_handler(model, engine, flags, sz, title):
    ...
def build_model(settings, patterns):
    ...
def write_snapshot(model, engine, flags, title, out_path, port=8080, dataset=""):
    ...
REQUIRED_PIPELINE_KEYS = ("CONFIGPATH", "RESOURCEPATH", "SUPPORTPATH")
def resolve_settings(path, env_value, log):
    ...
def main(argv=None):
    ...
```

<!-- markdownlint-enable MD013 -->

#### 6.1.31 `plugins/senzing-bootcamp/scripts/session-end.py`

No public items: the file is run as a script.

#### 6.1.32 `plugins/senzing-bootcamp/scripts/session-start.py`

No public items: the file is run as a script.

#### 6.1.33 `plugins/senzing-bootcamp/scripts/stop-nudge.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/stop-nudge.py`:

```python
POINTER = "\U0001f449"  # 👉
def content_of(rec):
    ...
def assistant_text(rec):
    ...
def is_real_user_prompt(rec):
    ...
def truthy(value):
    ...
def pref_flag(key):
    ...
def nudge_disabled():
    ...
def bootcamp_complete():
    ...
def current_turn_records(transcript_path):
    ...
def ends_with_tool_use(rec):
    ...
def settled_final_text(records):
    ...
data = sys.stdin.read()
transcript = payload.get("transcript_path", "")
records = current_turn_records(transcript) if transcript else None
final_text = settled_final_text(records)
```

<!-- markdownlint-enable MD013 -->

#### 6.1.34 `plugins/senzing-bootcamp/scripts/write-gate.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/write-gate.py`:

```python
data = sys.stdin.read()
LOC_MSG = (
    "Write blocked: use a project-relative path, not a system temp or Downloads "
    "directory."
)
OUTSIDE_MSG = (
    "Write blocked: that path is outside the Bootcamp project. Every file the bootcamp "
    "writes stays inside the project directory -- use a project-relative path."
)
SECRET_MSG = (
    "Write blocked: a possible hardcoded secret was detected. Use environment "
    "variables instead."
)
TEMP_PREFIXES = ("/tmp/", "/var/tmp/", "/private/tmp/", "/private/var/folders/")
TEMP_SUBSTRINGS = ("/downloads/", "/appdata/local/temp/", "/windows/temp/")
def block(message):
    ...
file_path = ""
def norm(path):
    ...
```

<!-- markdownlint-enable MD013 -->

### 6.2 CLI

Every argparse declaration, verbatim (the statements that build each parser).
Exit codes are given in section 5 with each component.

#### 6.2.1 `.claude/skills/auto-test/autotest.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/autotest.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--walk", action="store_true",
                    help="also run a simulated bootcamp walk and lint it")
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--persona", default="terse")
    ap.add_argument("--phase", default="preparation",
                    choices=("preparation", "module0", "content"))
    ap.add_argument("--seed", choices=("fresh", "seeded"), default="fresh")
    ap.add_argument("--ref", default="HEAD", help="commit to pin the plugin at")
    ap.add_argument("--model", default=None)
    ap.add_argument("--keep", action="store_true", help="keep the sandbox")
    ap.add_argument("--isolate-config", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.2 `.claude/skills/auto-test/mcp_probe.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/mcp_probe.py`:

```python
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="check",
                    choices=("check", "update", "snapshot"))
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--json", action="store_true", help="machine-readable findings")
    ap.add_argument("--no-content", action="store_true",
                    help="skip the get_capabilities content probe")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.3 `.claude/skills/auto-test/transcript_lint.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/transcript_lint.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", nargs="?")
    ap.add_argument("--phase", choices=("preparation", "module0", "content"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.4 `.claude/skills/auto-test/walk.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/auto-test/walk.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--mcp-config", required=True, type=Path)
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--persona", default="terse", choices=sorted(PERSONAS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--bootcamper-model", default="claude-haiku-4-5-20251001",
                    help="the Bootcamper only produces short text; a small model "
                         "keeps the walk cheap")
...
    ap.add_argument("--opening", default="/senzing-bootcamp:start-bootcamp")
    ap.add_argument("--isolate-config", action="store_true",
                    help="per-run CLAUDE_CONFIG_DIR (needs ANTHROPIC_API_KEY)")
    ap.add_argument("--timeout", type=int, default=600)
```

<!-- markdownlint-enable MD013 -->

#### 6.2.5 `.claude/skills/compact-dev-environment/citations.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/compact-dev-environment/citations.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
...
    cen = sub.add_parser("census", help="what cites what")
    cen.add_argument("--area", choices=("invariants", "specs", "feedback"),
                     help="limit to one asset class")
    cen.add_argument("--verbose", action="store_true", help="per-invariant detail")
    cen.set_defaults(func=cmd_census)
...
    ver = sub.add_parser("verify", help="referential integrity; exit 2 if anything dangles")
    ver.set_defaults(func=cmd_verify)
```

<!-- markdownlint-enable MD013 -->

#### 6.2.6 `.claude/skills/compact-dev-environment/widened_scope.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/compact-dev-environment/widened_scope.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    parser.add_argument("--all-verbs", action="store_true",
                        help="also scan extends/hardens/complements (much noisier)")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.7 `.claude/skills/delegate-to-mcp-server/coverage_ledger.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/delegate-to-mcp-server/coverage_ledger.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
...
    inv = sub.add_parser("inventory", help="grep the plugin for Senzing-fact leads")
    inv.add_argument("--category", help="limit to one category")
    inv.add_argument("--verbose", action="store_true", help="every matching line, not per-file counts")
    inv.set_defaults(func=cmd_inventory)
...
    old = sub.add_parser("stale", help="rows decided against a different server or docs index")
    old.add_argument("--server", required=True, help="current get_capabilities server_version")
    old.add_argument("--index", help="current search_docs metadata.index_built; omitting it "
                                     "leaves the index axis unchecked and says so")
    old.set_defaults(func=cmd_stale)
...
    rec = sub.add_parser("record", help="append one verdict")
    rec.add_argument("--key", required=True, help="stable slug describing the claim")
    rec.add_argument("--verdict", required=True, choices=VERDICTS)
    rec.add_argument("--server", required=True, help="server_version this was decided against")
    rec.add_argument("--index", help="search_docs metadata.index_built at decision time")
    rec.add_argument("--where", help="path (orientation only; keys are not paths)")
    rec.add_argument("--claim", help="one line: what the SBCP asserts or holds")
    rec.add_argument("--reason", help="required for keep-by-design: the Step 6 test that failed")
    rec.add_argument("--tool", help="the MCP call that established the verdict")
    rec.add_argument("--issue", type=int,
                     help="GitHub issue number this produced, e.g. 142")
    rec.add_argument("--upstream", help="e.g. 'feature sent 2026-07-30'")
    rec.add_argument("--checked", help="ISO date (default: today)")
    rec.set_defaults(func=cmd_record)
...
    tot = sub.add_parser("summary", help="counts by verdict, versions, and open gaps")
    tot.set_defaults(func=cmd_summary)
```

<!-- markdownlint-enable MD013 -->

#### 6.2.8 `.claude/skills/dry-run/coverage_reports.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/coverage_reports.py`:

```python
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
```

<!-- markdownlint-enable MD013 -->

#### 6.2.9 `.claude/skills/dry-run/measure_label_occlusion.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/measure_label_occlusion.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("png")
    ap.add_argument("--fill", default="#8b5cf6",
                    help="node marker fill(s), comma-separated, from color_for_sources(). A "
                         "multi-source graph uses one color per SOURCE SET, so pass them all "
                         "(default: %(default)s)")
    ap.add_argument("--fail-under", type=float, default=None,
                    help="exit 1 if the clearance is below this many pixels")
    ap.add_argument("--min-marker-px", type=int, default=150,
                    help="ignore fill blobs smaller than this — legend swatches (default: "
                         "%(default)s)")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.10 `.claude/skills/dry-run/scaffold_project.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/scaffold_project.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("directory", nargs="?", help="where to build the project")
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="empty config for the phase-3 onboarding path (no saved state)",
    )
    ap.add_argument(
        "--seeded",
        action="store_true",
        help="pre-seed the honorable preferences so the honor-don't-ask path is exercised",
    )
    ap.add_argument(
        "--explain",
        action="store_true",
        help=(
            "print the fixture-to-invariant map for the mode implied by --fresh/--seeded "
            "(default: mid-bootcamp) and exit without writing"
        ),
    )
```

<!-- markdownlint-enable MD013 -->

#### 6.2.11 `.claude/skills/feedback-to-issues/feedback_ledger.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/feedback-to-issues/feedback_ledger.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
...
    check = sub.add_parser("check", help="classify a candidate's entries; writes nothing")
    check.add_argument("candidate")
    check.set_defaults(func=cmd_check)
...
    commit = sub.add_parser("commit", help="archive the candidate and record its entries")
    commit.add_argument("candidate")
    commit.add_argument(
        "--disposition",
        action="append",
        metavar="TITLE=SPEC",
        help="what an entry produced, e.g. \"Screenshot capture fails=specs/foo.md\" or "
             "\"Vague thing=needs-clarification\". Repeatable.",
    )
    commit.set_defaults(func=cmd_commit)
...
    annotate = sub.add_parser(
        "annotate", help="append a superseding line to set/correct one entry's disposition"
    )
    annotate.add_argument("entry_id")
    annotate.add_argument("disposition")
    annotate.set_defaults(func=cmd_annotate)
```

<!-- markdownlint-enable MD013 -->

#### 6.2.12 `.claude/skills/production-readiness-audit/conformance.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/production-readiness-audit/conformance.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None,
                        help="repository root (default: the one this script ships in)")
    sub = parser.add_subparsers(dest="cmd")
...
    sub.add_parser("rules", help="hard rules no invariant covers (reverse direction)")
...
    per = sub.add_parser("per-rule",
                         help="every hard rule + the invariants cited AT it (worklist)")
    per.add_argument("--uncited", action="store_true",
                     help="show only rules citing no invariant at the rule itself")
...
    since = sub.add_parser("since", help="hard-rule lines added since a git ref")
    since.add_argument("--ref", default=None, help="git ref to diff against")
    since.add_argument("--since-last-audit", action="store_true",
                       help="resolve the ref from the newest audit entry's Commit: field")
...
    rev = sub.add_parser("reverse-check",
                         help="added rules tested for a citation, and the ones it cannot test")
    rev.add_argument("--ref", default=None, help="git ref to diff against")
    rev.add_argument("--since-last-audit", action="store_true",
                       help="resolve the ref from the newest audit entry's Commit: field")
...
    dup = sub.add_parser("duplication", help="passages repeated across shipped files")
    dup.add_argument("--words", type=int, default=14, help="shingle length (default 14)")
    dup.add_argument("--top", type=int, default=12, help="file pairs to show (default 12)")
...
    sub.add_parser("enumerations", help="invariants that enumerate, i.e. go stale")
    sub.add_parser("size", help="Goldilocks measurements")
    sub.add_parser("all", help="every scan")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.13 `.claude/skills/release/release.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/release/release.py`:

```python
    parser = argparse.ArgumentParser(
        description="Bump the version, write the CHANGELOG entry, commit and tag -- as one "
                    "operation. Dry run unless --apply is given.")
    parser.add_argument("version", nargs="?", help="explicit target version, e.g. 0.6.0")
    parser.add_argument("--major", action="store_true", help="bump the major component")
    parser.add_argument("--minor", action="store_true", help="bump the minor component")
    parser.add_argument("--patch", action="store_true", help="bump the patch component")
    parser.add_argument("--apply", action="store_true",
                        help="actually edit, commit and tag (default: dry run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="explicitly request the default: print and change nothing")
    parser.add_argument("--repo", default=str(DEFAULT_REPO),
                        help="repository to release (default: this skill's own repo)")
    parser.add_argument("--allow-branch", action="store_true",
                        help="tag from a branch other than %s" % RELEASE_BRANCH)
    parser.add_argument("--allow-divergent-base", action="store_true",
                        help="release even though the manifest and the newest tag disagree")
    parser.add_argument("--message",
                        help="release commit subject (default: 'chore(release): <version>')")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.14 `.claude/skills/review-invariants/invariant_manifest.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/review-invariants/invariant_manifest.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the checked-in manifest differs from a fresh generation")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.15 `plugins/senzing-bootcamp/scripts/capture_screenshots.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/capture_screenshots.py`:

```python
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
...
    ap = argparse.ArgumentParser(
        description="Capture one PNG per tab of a local bootcamp visualization."
    )
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--html", help="Path to a local HTML snapshot to screenshot.")
    source.add_argument(
        "--url", help="localhost URL of the running visualization app (enables ?tab=/&q=)."
    )
    ap.add_argument(
        "--out-dir",
        default="docs/visualizations",
        help="Directory to write PNGs into (default: docs/visualizations).",
    )
    ap.add_argument(
        "--name",
        default="visualization",
        help="Base name for the PNG files (default: visualization).",
    )
    ap.add_argument(
        "--tabs",
        default="",
        help=f"Comma-separated tab ids, or 'all' (default, and the app's full tab set: "
        f"{','.join(DEFAULT_TABS)}). An omitted --tabs means ALL tabs, not none — for a "
        f"page with no tabs use --single.",
    )
    ap.add_argument(
        "--single",
        action="store_true",
        help="Capture the whole page as ONE image, for a single-page deliverable with no "
        "tabs (writes {name}.png). Cannot be combined with --tabs.",
    )
    ap.add_argument(
        "--query",
        default="",
        help="Search text for the Search / Probe tab; requires --url (the static "
        "snapshot has no engine to search).",
    )
```

<!-- markdownlint-enable MD013 -->

#### 6.2.16 `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`:

```python
    parser = argparse.ArgumentParser(
        prog="docker_lifecycle.py",
        description="Name a bootcamp container, or pick its host port, before creating it.")
    sub = parser.add_subparsers(dest="command")
    named = sub.add_parser(
        "container-name", help="print the project-derived name to create a container with")
    named.add_argument("base", help="the site's base name, e.g. senzing-bootcamp")
    named.add_argument("--runtime", default=DEFAULT_RUNTIME, type=str.lower,
                       choices=sorted(KNOWN_RUNTIMES),
                       help="the CLI that will create the container (default: docker)")
    port = sub.add_parser("free-port", help="print a free host loopback port")
    port.add_argument("preferred", type=_port_number, help="the port to try first, e.g. 5432")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.17 `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`:

```python
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if description is None else description
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="audit the input without rendering; non-zero exit if it would not render usefully",
    )
    parser.add_argument(
        "--require-sections",
        default=None,
        metavar="A;B;C",
        help="semicolon-separated section names this document must carry, replacing the "
        "discoveries defaults. Semicolons rather than commas because section names "
        "contain commas ('merges and match keys', 'why and how'). Matched the same way "
        "as the defaults: case- and punctuation-insensitively against H2 headings.",
    )
    parser.add_argument(
        "--subtitle",
        default=None,
        help="cover subtitle. Defaults to the discoveries line; override it for any other "
        "document, or a stakeholder-facing keepsake ships with the wrong one.",
    )
    parser.add_argument(
        "--no-section-check",
        action="store_true",
        help="skip the section check entirely. The content-retention floor still applies "
        "and is what actually prevents rendering unrelated Markdown.",
    )
```

<!-- markdownlint-enable MD013 -->

#### 6.2.18 `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preferences",
        default=str(DEFAULT_PREFERENCES),
        help=(
            "Bootcamp preferences YAML. Its top-level `name:` is the certificate name "
            "the Bootcamper was asked for (INV-113) and outranks the recap header."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify required sections exist; do not render.",
    )
    parser.add_argument(
        "--expect-modules",
        default="",
        help=(
            "Semicolon-separated module names that MUST each have a section; "
            "flags a wholly-missing module. Semicolon (not comma) because some "
            "names contain commas, e.g. 'Query, Visualize and Discover'."
        ),
    )
    parser.add_argument(
        "--progress",
        default=str(DEFAULT_PROGRESS),
        help=(
            "Progress JSON whose `modules_completed` supplies the EXPECTED set of "
            "visualizations. This is the tab-coverage denominator that does not come "
            "from the manifests, so a module that captured nothing is still visible."
        ),
    )
    parser.add_argument(
        "--expect-visualizations",
        default=None,
        help=(
            "Comma-separated visualization names to expect, overriding --progress. "
            "Mainly for tests and for a run whose progress file is unavailable."
        ),
    )
```

<!-- markdownlint-enable MD013 -->

#### 6.2.19 `plugins/senzing-bootcamp/scripts/generate_recap_video.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_video.py`:

```python
    parser = argparse.ArgumentParser(
        description="Render the graduation storyboard into docs/bootcamp_recap.mp4.",
        epilog="Exit codes: 0 rendered; 1 invalid storyboard; 2 a required capability is "
               "missing (ffmpeg or Pillow); 3 the encode failed. Nothing is written unless 0.")
    parser.add_argument("--storyboard", default=DEFAULT_STORYBOARD)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--project-root", default=".",
                        help="images and the recap resolve against this (default: the "
                             "current directory)")
    parser.add_argument("--voice-model", default=None,
                        help="a local Piper .onnx voice model, its .onnx.json beside it "
                             f"(default: {DEFAULT_VOICE_MODEL} under --project-root)")
    parser.add_argument("--no-voice", action="store_true",
                        help="skip the voice-over; the burned-in captions carry the narration")
    parser.add_argument("--check", action="store_true",
                        help="validate the storyboard and exit; needs neither Pillow nor ffmpeg")
    parser.add_argument("--schema", action="store_true",
                        help="print the scene types and their fields as JSON, and exit")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.20 `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--docs-dir",
        default="docs",
        help="Directory holding the Markdown docs (default: docs). Never recursed.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing.",
    )
```

<!-- markdownlint-enable MD013 -->

#### 6.2.21 `plugins/senzing-bootcamp/scripts/package_bootcamp.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/package_bootcamp.py`:

```python
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--profile", choices=("share", "transfer"), required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--date", default=None,
                        help="YYYYMMDD stamp for the archive name (default: today, UTC).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the manifest and total size; write nothing.")
    parser.add_argument("--output", default=None,
                        help="Override the archive path (default: "
                             "backups/packages/senzing-bootcamp-<profile>-<date>.zip).")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.22 `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`:

```python
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--settings", default="config/engine_config.json")
...
    ap.add_argument("--records", nargs="+", default=None,
                    help="JSONL file(s)/glob(s) of the records that were loaded. Omit to "
                         "build the model from the export stream instead (every resolved "
                         "entity, one pass) — preferred for a datastore larger than the "
                         "Truth Set")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--title", default="Senzing Entity Resolution")
    ap.add_argument("--dataset", default="",
                    help="what the loaded data IS, for snapshot wording (e.g. 'the Senzing "
                         "Truth Set', 'your CUSTOMERS and REFERENCE data'). Left empty the "
                         "snapshot says 'the loaded data' — never assume the Truth Set.")
    ap.add_argument("--snapshot", default=None,
                    help="also write a self-contained standalone HTML to this path")
    ap.add_argument("--no-serve", action="store_true",
                    help="build the model (and snapshot) then exit without serving")
```

<!-- markdownlint-enable MD013 -->

#### 6.2.23 `.claude/skills/propagate-to-public/propagate.sh`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/propagate-to-public/propagate.sh`:

```sh
# Usage: propagate.sh [path-to-public-repo]
```

<!-- markdownlint-enable MD013 -->

#### 6.2.24 `.claude/skills/retrofit-from-public/retrofit.sh`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/retrofit-from-public/retrofit.sh`:

```sh
# Usage: retrofit.sh [--base <dev-tag>] [path-to-public-repo]
...
usage="Usage: retrofit.sh [--base <dev-tag>] [path-to-public-repo]"
...
while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      [ "$#" -ge 2 ] && [ -n "$2" ] || { echo "--base needs a dev tag. $usage" >&2; exit 2; }
      base_tag="$2"; shift 2 ;;
    --base=*)
      base_tag="${1#--base=}"
      [ -n "$base_tag" ] || { echo "--base needs a dev tag. $usage" >&2; exit 2; }
      shift ;;
    -h|--help) echo "$usage"; exit 0 ;;
    --) shift; [ "$#" -eq 0 ] || { src="$1"; shift; }
        [ "$#" -eq 0 ] || { echo "Too many arguments. $usage" >&2; exit 2; }
        break ;;
    -*) echo "Unknown option '$1'. $usage" >&2; exit 2 ;;
    *) [ -z "$src" ] || { echo "Too many arguments. $usage" >&2; exit 2; }
       src="$1"; shift ;;
  esac
```

<!-- markdownlint-enable MD013 -->

#### 6.2.25 `scripts/sync-check.sh`

<!-- markdownlint-disable MD013 -->

From `scripts/sync-check.sh`:

```sh
# Usage: scripts/sync-check.sh [path-to-kiro-repo]
```

<!-- markdownlint-enable MD013 -->

### 6.3 Config and file formats

The plugin's configuration files, verbatim. The manifests `plugin.json` and
`marketplace.json` are in section 3. The files the skills create in the
Bootcamper's project (`config/bootcamp_progress.json`,
`config/data_sources.yaml`, `config/engine_config.json` and others) are
described with each skill in section 5; their layout is defined by the skill
text, which this blueprint does not embed.

#### 6.3.1 `plugins/senzing-bootcamp/.mcp.json`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/.mcp.json`:

```json
{
  "mcpServers": {
    "senzing": {
      "type": "http",
      "url": "https://mcp.senzing.com/mcp"
    }
  }
}
```

<!-- markdownlint-enable MD013 -->

#### 6.3.2 `plugins/senzing-bootcamp/hooks/hooks.json`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py\""
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/feedback-capture.py\""
          },
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint-tick.py\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/write-gate.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/stop-nudge.py\""
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/precompact-recap.py\""
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/session-end.py\""
          }
        ]
      }
    ]
  }
}
```

<!-- markdownlint-enable MD013 -->

#### 6.3.3 Environment variables

- `SENZING_BOOTCAMP_DISABLE_STOP_NUDGE`: read by `stop-nudge.py`; when set, the
  Stop hook does nothing.
- `SENZING_ENGINE_CONFIGURATION_JSON`: read by `senzing_viz_server.py` as the
  engine settings when no settings file or flag gives them.
- `CLAUDE_PLUGIN_ROOT`: set by Claude Code; `hooks.json` and the skills resolve
  bundled scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/`.

## 7. Test-pinned internals

Every non-public item a test refers to (call, attribute read, patch target or
`from … import`), by module, verbatim, with the test files that use it.

### 7.1 `.claude/skills/dry-run/coverage_reports.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/dry-run/coverage_reports.py`:

```python
def _index_groups(inv_txt):
    ...
def _scan_files(repo):
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_index_groups`: `test_coverage_reports.py`
- `_scan_files`: `test_coverage_reports.py`, `test_declined_ledger.py`

### 7.2 `.claude/skills/production-readiness-audit/conformance.py`

<!-- markdownlint-disable MD013 -->

From `.claude/skills/production-readiness-audit/conformance.py`:

```python
_PROPAGATED = ("plugins/", ".claude-plugin/", "docs/", "README.md")
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_PROPAGATED`: `test_since_last_audit_widens_past_a_work_commit.py`

### 7.3 `plugins/senzing-bootcamp/scripts/capture_screenshots.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/capture_screenshots.py`:

```python
_SETTLED_STATE = SETTLED_NA
def _settle_expected(tab: str) -> bool:
    ...
_MAX_FULL_PAGE_PX = 12000
def _single_page_label(outcome: str, page_height=None, captured_height=None) -> str:
    ...
def _tab_label(tab: str) -> str:
    ...
def _has_tab_controls(source: str) -> bool:
    ...
def _supports_deep_linking(source: str) -> bool:
    ...
def _identical_groups(paths) -> list:
    ...
_CHROME_VIRTUAL_TIME_MS = 15000
_ANIMATED_TABS = frozenset({"graph", "network"})
def _virtual_time_ms(tab: str = "") -> int:
    ...
_WINDOW = (1440, 900)
def _out_path(out_dir: Path, name: str, tab: str) -> Path:
    ...
def _with_capture(url: str) -> str:
    ...
def _tab_url(url: str, tab: str, query: str = "") -> str:
    ...
def _page_stats(source: str, target: str, is_url: bool) -> dict:
    ...
_APPLICABILITY = {
    "overlap": lambda s: (s.get("data_sources_total") or 0) >= 2,
    "features": lambda s: (s.get("multi_record_entities") or 0) > 0,
    "matchkeys": lambda s: (s.get("multi_record_entities") or 0) > 0,
}
def _tabs_applicable(stats: dict, tabs) -> tuple:
    ...
def _tabs_present(source: str, tabs) -> tuple:
    ...
def _snapshot_copy(html: Path, tab: str) -> Path:
    ...
def _capture_playwright(url: str, out: Path) -> bool:
    ...
def _capture_selenium(url: str, out: Path) -> bool:
    ...
def _windows_browser_candidates() -> list:
    ...
def _windows_registry_browsers() -> list:
    ...
def _chrome_search_paths() -> list:
    ...
def _chrome_exe():
    ...
def _measure_chrome_cli(exe: str, url: str):
    ...
def _capture_chrome_cli(url: str, out: Path) -> bool:
    ...
def _capture_wkhtmltoimage(url: str, out: Path) -> bool:
    ...
_BACKENDS = (
    _capture_playwright,
    _capture_selenium,
    _capture_chrome_cli,
    _capture_wkhtmltoimage,
)
_CURRENT_TAB = ""
_CAPTURE_IN_FLIGHT = False
_FULL_PAGE_OUTCOME = FULL_PAGE_VIEWPORT
def _single_page_mode() -> bool:
    ...
def _record_full_page(outcome: str, page_height=None, captured_height=None) -> None:
    ...
def _capture_one(url: str, out: Path, backend=None, tab: str = ""):
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_ANIMATED_TABS`: `test_every_capture_path_requests_the_render.py`,
  `test_settle_signal_is_reported.py`
- `_APPLICABILITY`: `test_capture_suppressed_tabs.py`,
  `test_comment_test_pointers_resolve.py`
- `_BACKENDS`: `test_capture_tabs.py`,
  `test_capture_verifies_tab_activation.py`, `test_windows_browser_discovery.py`
- `_CAPTURE_IN_FLIGHT`: `test_capture_tabs.py`
- `_CHROME_VIRTUAL_TIME_MS`: `test_snapshot_and_capture_fidelity.py`,
  `test_windows_browser_discovery.py`
- `_CURRENT_TAB`: `test_capture_single_page.py`, `test_capture_tabs.py`,
  `test_snapshot_and_capture_fidelity.py`
- `_FULL_PAGE_OUTCOME`: `test_capture_single_page.py`
- `_MAX_FULL_PAGE_PX`: `test_capture_single_page.py`
- `_SETTLED_STATE`: `test_settle_signal_is_reported.py`
- `_WINDOW`: `test_capture_single_page.py`
- `_capture_chrome_cli`: `test_capture_single_page.py`,
  `test_snapshot_and_capture_fidelity.py`, `test_windows_browser_discovery.py`
- `_capture_one`: `test_capture_tabs.py`, `test_settle_signal_is_reported.py`
- `_capture_playwright`: `test_capture_single_page.py`,
  `test_windows_browser_discovery.py`
- `_capture_selenium`: `test_capture_single_page.py`,
  `test_windows_browser_discovery.py`
- `_capture_wkhtmltoimage`: `test_windows_browser_discovery.py`
- `_chrome_exe`: `test_capture_tabs.py`, `test_settle_signal_is_reported.py`,
  `test_snapshot_and_capture_fidelity.py`, `test_windows_browser_discovery.py`
- `_chrome_search_paths`: `test_windows_browser_discovery.py`
- `_has_tab_controls`: `test_capture_single_page.py`
- `_identical_groups`: `test_capture_verifies_tab_activation.py`
- `_measure_chrome_cli`: `test_capture_single_page.py`
- `_out_path`: `test_capture_single_page.py`, `test_capture_tabs.py`,
  `test_recap_tab_coverage.py`, `test_tab_manifest_survives_recapture.py`
- `_page_stats`: `test_capture_suppressed_tabs.py`
- `_record_full_page`: `test_capture_single_page.py`
- `_settle_expected`: `test_every_capture_path_requests_the_render.py`,
  `test_settle_signal_is_reported.py`
- `_single_page_label`: `test_capture_single_page.py`
- `_single_page_mode`: `test_capture_single_page.py`
- `_snapshot_copy`: `test_capture_single_page.py`
- `_supports_deep_linking`: `test_capture_verifies_tab_activation.py`
- `_tab_label`: `test_capture_single_page.py`
- `_tab_url`: `test_capture_tabs.py`,
  `test_every_capture_path_requests_the_render.py`
- `_tabs_applicable`: `test_capture_suppressed_tabs.py`
- `_tabs_present`: `test_capture_tabs.py`
- `_virtual_time_ms`: `test_snapshot_and_capture_fidelity.py`
- `_windows_browser_candidates`: `test_windows_browser_discovery.py`
- `_windows_registry_browsers`: `test_windows_browser_discovery.py`
- `_with_capture`: `test_every_capture_path_requests_the_render.py`

### 7.4 `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/docker_lifecycle.py`:

```python
def _run(args, timeout=30):
    ...
def _can_bind(port, host=LOOPBACK):
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_run`: `test_container_lifecycle_runtimes.py`
- `_can_bind`: `test_container_names_are_project_derived.py`

### 7.5 `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_discoveries_pdf.py`:

```python
_FALLBACK_RGB = {
    "EMBER": (245, 120, 38),
    "DARK_INK": (24, 22, 15),
    "BODY_INK": (74, 70, 64),
    "WARM_LINE": (229, 223, 211),
}
def _needs_item_gap(blocks: List[Block], index: int) -> bool:
    ...
def _normalize(text: str) -> str:
    ...
_NEW_LINE_LABELS = ("near miss the one that teaches more", "measurement")
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_FALLBACK_RGB`: `test_brand_sync.py`
- `_NEW_LINE_LABELS`: `test_authored_shapes_are_stated.py`,
  `test_new_line_labels.py`
- `_needs_item_gap`: `test_discoveries_pdf.py`
- `_normalize`: `test_authored_shapes_are_stated.py`, `test_new_line_labels.py`

### 7.6 `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_pdf.py`:

```python
def _split_title_date(rest: str) -> Tuple[str, str]:
    ...
_UNSPACED_SUBSECTIONS: Tuple[str, ...] = ()
_UNSPACED_LABELS: Tuple[str, ...] = ()
_NEW_LINE_LABELS = ("why it matters",)
def _block_label(line: str) -> str:
    ...
def _summary_block_label(line: str) -> str:
    ...
def _is_top_level_bullet(line: str) -> bool:
    ...
def _next_nonblank_is_bullet(lines: List[str], index: int) -> bool:
    ...
def _still_in_list_item(line: str, was_in_item: bool) -> bool:
    ...
def _normalize_heading(name: str) -> str:
    ...
def _source_content_chars(text: str) -> int:
    ...
def _rendered_content_chars(recap: Recap) -> int:
    ...
_FALLBACK_RGB = {
    "NAVY": (24, 22, 15), "BLUE": (245, 120, 38), "SLATE": (74, 70, 64),
    "LIGHT": (250, 248, 243), "ACCENT": (255, 78, 31), "INK": (24, 22, 15),
    "GREEN": (29, 158, 117), "LINE": (229, 223, 211), "AMBER": (240, 146, 10),
}
_UNICODE_MAP = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "•": "-",
    "…": "...",
    "→": "->",
    "↔": "<->",
    "←": "<-",
    "⇒": "=>",
    "↑": "^",
    "↓": "v",
    "⚠": "!",
    "\ufe0f": "",  # variation selector-16, trails emoji like the warning sign
    # Comparison, currency and spacing characters a bootcamper's own
    # discoveries document carries but the plugin's templates never emit — so
    # scanning the templates could not find them. Each rendered as "?" until mapped.
    "≈": "~",
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
    "∞": "infinity",
    "€": "EUR",
    "™": "(TM)",
    "‑": "-",  # non-breaking hyphen
    "​": "",  # zero-width space
    "✅": "[done]",
    "✓": "[x]",
    "⛔": "",
    "\U0001f6d1": "",
    "\U0001f393": "",
    "\U0001f680": "",
    "\U0001f4c4": "",
    "\U0001f3c6": "",
}
_EXPECTED_DROP_PASSAGE = "> \U0001f916 Bootcamp-generated business case"
_EXPECTED_DROP_CHAR = "\U0001f916"
def _describe_dropped(ch: str) -> str:
    ...
def _fold_to_latin1(s: str) -> str:
    ...
def _safe(s: str) -> str:
    ...
def _width(pdf, text: str) -> float:
    ...
def _unrepresentable(text: str) -> List[str]:
    ...
def _wordmark_on_light():
    ...
def _partition_meta(
    meta: List[Tuple[str, str]]
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    ...
def _cert_fields(recap: Recap) -> Tuple[str, str, List[str]]:
    ...
def _cert_attribution(recap: Recap) -> List[str]:
    ...
_CERTIFICATE_NAME_OVERRIDE = ""
_CERT_CARD_X = 21.0
_CERT_CARD_Y = 26.0
_CERT_CARD_H = 158.0
_CERT_BORDER = 1.3         # ember card border stroke
_CERT_MODULE_LINES = 3     # module list is capped, so it cannot reach the seal
_CERT_Y_SEAL = 147.5       # top edge of the seal, not a baseline
def _cert_citation(labels: List[str]) -> str:
    ...
def _clip(s: str, n: int) -> str:
    ...
def _stdlib_certificate_stream(recap: Recap, w: float, h: float) -> str:
    ...
def _stdlib_subsection(add, add_wrapped, name: str, content: Optional[List[str]],
                       missing_blocks: Tuple[str, ...] = ()) -> None:
    ...
def _pdf_escape(s: str) -> str:
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_CERTIFICATE_NAME_OVERRIDE`: `test_recap_video.py`
- `_CERT_BORDER`: `test_recap_pdf_guard.py`
- `_CERT_CARD_H`: `test_recap_pdf_certificate.py`, `test_recap_pdf_guard.py`
- `_CERT_CARD_X`: `test_recap_pdf_certificate.py`
- `_CERT_CARD_Y`: `test_recap_pdf_certificate.py`, `test_recap_pdf_guard.py`
- `_CERT_MODULE_LINES`: `test_recap_pdf_certificate.py`
- `_CERT_Y_SEAL`: `test_recap_pdf_certificate.py`
- `_EXPECTED_DROP_CHAR`: `test_generated_scenario_marker_drop_is_exempt.py`
- `_EXPECTED_DROP_PASSAGE`: `test_generated_scenario_marker_drop_is_exempt.py`
- `_FALLBACK_RGB`: `test_brand_sync.py`
- `_NEW_LINE_LABELS`: `test_authored_shapes_are_stated.py`,
  `test_new_line_labels.py`
- `_UNICODE_MAP`: `test_example_recap_sync.py`,
  `test_stdlib_writer_character_safety.py`
- `_UNSPACED_LABELS`: `test_recap_pdf_guard.py`
- `_UNSPACED_SUBSECTIONS`: `test_recap_pdf_guard.py`
- `_block_label`: `test_recap_pdf_guard.py`
- `_cert_attribution`: `test_recap_pdf_guard.py`
- `_cert_citation`: `test_recap_pdf_certificate.py`
- `_cert_fields`: `test_certificate_name_source.py`,
  `test_recap_notes_section.py`, `test_recap_pdf_font_safety.py`,
  `test_recap_video.py`
- `_clip`: `test_dry_run_scaffold.py`, `test_recap_pdf_font_safety.py`
- `_describe_dropped`: `test_stdlib_writer_character_safety.py`
- `_fold_to_latin1`: `test_generated_scenario_marker_drop_is_exempt.py`
- `_is_top_level_bullet`: `test_recap_pdf_guard.py`
- `_next_nonblank_is_bullet`: `test_recap_pdf_guard.py`
- `_normalize_heading`: `test_authored_shapes_are_stated.py`,
  `test_new_line_labels.py`, `test_recap_pdf_guard.py`
- `_partition_meta`: `test_recap_pdf_guard.py`
- `_pdf_escape`: `test_stdlib_writer_character_safety.py`
- `_rendered_content_chars`: `test_recap_notes_section.py`
- `_safe`: `test_dropped_character_remedy_branches.py`,
  `test_dry_run_scaffold.py`, `test_recap_measure_font_safety.py`,
  `test_recap_pdf_font_safety.py`, `test_stdlib_writer_character_safety.py`
- `_source_content_chars`: `test_recap_notes_section.py`
- `_split_title_date`: `test_recap_measure_font_safety.py`
- `_stdlib_certificate_stream`: `test_recap_pdf_certificate.py`,
  `test_recap_pdf_guard.py`
- `_stdlib_subsection`: `test_recap_pdf_guard.py`
- `_still_in_list_item`: `test_recap_pdf_guard.py`
- `_summary_block_label`: `test_recap_summary_blocks.py`
- `_unrepresentable`: `test_recap_pdf_font_safety.py`
- `_width`: `test_recap_measure_font_safety.py`
- `_wordmark_on_light`: `test_recap_pdf_certificate.py`

### 7.7 `plugins/senzing-bootcamp/scripts/generate_recap_video.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/generate_recap_video.py`:

```python
_FALLBACK_RGB = {
    "OBSIDIAN": (15, 13, 12), "DEEP": (24, 22, 15), "SURFACE_DARK": (32, 30, 22),
    "EMBER_HOT": (255, 78, 31), "EMBER_CORE": (245, 120, 38), "EMBER_END": (240, 146, 10),
    "EMBER_SOFT": (253, 238, 227), "SIGNAL_GREEN": (29, 158, 117), "WHITE": (255, 255, 255),
    "WARM_OFF_WHITE": (250, 248, 243), "DARK_INK": (24, 22, 15), "BODY_INK": (74, 70, 64),
    "WARM_LINE": (229, 223, 211),
}
_TOKEN_NAMES = {
    "OBSIDIAN": "OBSIDIAN", "DEEP": "DEEP", "SURFACE_DARK": "SURFACE_DARK",
    "EMBER_HOT": "EMBER_HOT", "EMBER_CORE": "EMBER_CORE", "EMBER_END": "EMBER_GRAD_END",
    "EMBER_SOFT": "EMBER_SOFT", "SIGNAL_GREEN": "SIGNAL_GREEN", "WHITE": "WHITE",
    "WARM_OFF_WHITE": "WARM_OFF_WHITE", "DARK_INK": "DARK_INK", "BODY_INK": "BODY_INK",
    "WARM_LINE": "WARM_LINE",
}
PALETTE, _BRAND, PALETTE_NOTE = _load_palette()
def _find_spec(name: str):
    ...
def _imageio_ffmpeg() -> Tuple[Optional[str], str]:
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_BRAND`: `test_brand_sync.py`
- `_FALLBACK_RGB`: `test_brand_sync.py`
- `_TOKEN_NAMES`: `test_brand_sync.py`
- `_find_spec`: `test_recap_video.py`
- `_imageio_ffmpeg`: `test_recap_video.py`

### 7.8 `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py`:

```python
def _signature(text: str) -> list:
    ...
def _signatures_compatible(before: list, after: list) -> bool:
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_signature`: `test_normalize_docs_markdown.py`
- `_signatures_compatible`: `test_normalize_docs_markdown.py`

### 7.9 `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`

<!-- markdownlint-disable MD013 -->

From `plugins/senzing-bootcamp/scripts/senzing_viz_server.py`:

```python
_FALLBACK_SOURCE_COLORS = {"CUSTOMERS": "#F57826", "REFERENCE": "#3B6EA5", "WATCHLIST": "#C8922A"}
_FALLBACK_COLORS = ["#8b5cf6", "#ec4899", "#0ea5e9", "#a3a34a", "#ef4444", "#14b8a6"]
_FALLBACK_STROKES = ["#FFFFFF", "#18160F", "#FAF8F3"]
_FALLBACK_STROKE_WIDTHS = [1.5, 3.0]
_FALLBACK_FILL_SHADES = [0.0, 0.30, -0.30, 0.55, -0.55]
_FALLBACK_BRAND = {
    "bg": "#FAF8F3", "surface": "#FFFFFF", "dark": "#18160F",
    "ink": "#18160F", "muted": "#4A4640", "accent": "#F57826",
    "accent_hot": "#FF4E1F", "accent_soft": "#FDEEE3",
    "line": "#E5DFD3", "green": "#1D9E75",
    "font": "Roboto, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
    "code_font": "'Fira Code', 'Courier New', Courier, monospace",
}
    def _absorb(self, resp):
        ...
    @staticmethod
    def _encoding_check(nodes):
        ...
def _d3_script():
    ...
def _esc_html(s):
    ...
def _script_json(obj):
    ...
def _snapshot_probe_html(model, engine, flags, port=8080, dataset=""):
    ...
```

<!-- markdownlint-enable MD013 -->

Used by:

- `_FALLBACK_BRAND`: `test_brand_sync.py`
- `_FALLBACK_COLORS`: `test_brand_sync.py`
- `_FALLBACK_FILL_SHADES`: `test_brand_sync.py`
- `_FALLBACK_SOURCE_COLORS`: `test_brand_sync.py`
- `_FALLBACK_STROKES`: `test_brand_sync.py`
- `_FALLBACK_STROKE_WIDTHS`: `test_brand_sync.py`
- `_absorb`: `test_visualization_model_build_scales.py`
- `_d3_script`: `test_viz_server_refuses_to_render_without_d3.py`
- `_encoding_check`: `test_encoding_self_check_is_stated_as_behavior.py`
- `_esc_html`: `test_any_language_contract_complete.py`,
  `test_snapshot_and_capture_fidelity.py`
- `_script_json`: `test_any_language_contract_complete.py`,
  `test_capture_single_page.py`,
  `test_how_tab_names_an_unsettled_final_state.py`,
  `test_source_encoding_renders_distinctly.py`, `test_viz_tab_consolidation.py`
- `_snapshot_probe_html`: `test_snapshot_and_capture_fidelity.py`,
  `test_tab_set_is_singular.py`

## 8. Tests

### 8.1 Framework and tools

The suite uses only the Python standard library (INV-108), with `unittest` as
both framework and runner. Tests never import an optional package directly. They
probe it with `importlib.util.find_spec` and let the code under test import it.

- **Optional packages.** `requirements-dev.txt` declares `fpdf2`, `Pillow` and
  `imageio-ffmpeg`. They are used by the PDF and video generators, not by the
  tests. Without `fpdf2` the PDF generators use a stdlib renderer, and that path
  is tested as well.
- **CI.** `.github/workflows/test-suite.yaml` runs Python 3.12 on
  `ubuntu-latest` with the matrix `fpdf2: [present, absent]`, `fail-fast: false`
  and a 15-minute timeout. The checkout uses `fetch-depth: 0` because some tests
  resolve commit hashes from history, such as those recorded in
  `specs/IMPLEMENTED.md`. The suite runs as
  `python -m unittest discover -s tests 2>&1 | tee suite.log` with
  `shell: bash`, so `pipefail` is on.
- **The present leg** installs `requirements-dev.txt`. The log must not contain
  `fpdf2 is not installed`.
- **The absent leg** first fails if `import fpdf` works. The log must contain
  `fpdf2 is not installed` and match `OK (skipped=N)` with N of at least 1.
- **Recorded results.** The ledger entry `invariant-review-2026-10-04b`
  (in `specs/IMPLEMENTED.md`) records 6113 tests, both legs run in a clean
  worktree with an empty `HOME`: `OK (skipped=13)` on the present leg and
  `OK (skipped=117)` on the absent leg.
- **Local CI mirror.** This is a maintainer practice, set out in
  `.claude/skill-overlays/implement-github-issue.md`. Run both legs with `HOME`
  set to an empty directory outside `/tmp`, such as one under
  `.claude/worktrees/`.
  - Under the real `HOME`, some guards read user-level skills in `~/.claude/`
    that CI never has.
  - Under a `HOME` inside `/tmp`, the location tests fail spuriously.
  - Present leg: when `fpdf2` lives in the user site, set `PYTHONUSERBASE` to
    the real user base, or the empty `HOME` hides it.
  - Absent leg: run from a `python3 -m venv --without-pip` venv.
  - Use a clean worktree. Tree-scanning guards also read untracked files, and in
    this checkout, with other sessions' files under `.claude/worktrees/`, a run
    at this SHA reported `FAILED (failures=5, errors=6, skipped=13)` for that
    reason alone.

The helper modules have names that do not start with `test_`, so they are never
collected as tests:

- `tests/_fpdf2_support.py`:
  - `have_fpdf2()` checks `find_spec("fpdf")`.
  - On import, when `fpdf2` is absent, it writes one notice to stderr per
    process. The notice says `fpdf2 is not installed for <sys.executable>`, says
    the fpdf2 tests will be skipped and are not failing, and gives the hint
    `python3 -m pip install -r requirements-dev.txt`. It states no count. Any
    non-empty `SBCP_QUIET_FPDF2_NOTICE` silences it.
  - It exports the decorator `requires_fpdf2`.
  - It is a module rather than a `conftest.py`, which `unittest` never loads.
- `tests/_wrapped_text.py`: the shared wrap-aware matcher (INV-346), used by 50
  files. `blocks(text)` splits Markdown into blocks, and
  `match_lines(text, pattern)` returns the 1-based start line of each match. The
  rules are in 8.4.1.
- `tests/_maintainer_surface.py`: the maintainer operation set, used by 9 files:
  - `skills()`: directories under `.claude/skills/` that contain a `SKILL.md`;
  - `commands()` and `command_files()`: `.claude/commands/*.md`, empty when the
    directory is absent;
  - `operations()`: the union of the two;
  - `ships(name)`: ignores a leading slash;
  - `skill_file(name)`: the operation's `SKILL.md`;
  - `command_files_under_test()`: falls back to the fixtures when no command
    ships.
- `tests/list_specs.py`: a CLI,
  `python3 tests/list_specs.py [--repo PATH] [--check]`. The open set is the
  spec files minus the `specs/IMPLEMENTED.md` and `specs/DECLINED.md` headings.
  It reports any spec found in both. Listing exits 0, and `--check` exits 2 when
  a spec is in both.

Skip conventions. Every reason names its cause and states no count.

- `@requires_fpdf2` (38 uses in 13 files) applies only to tests of the fpdf2
  renderer, never to the fallback's. Older sites use
  `skipUnless(have_fpdf2(), …)` or `HAVE_FPDF`.
- `tests/test_recap_video.py` defines `requires_pillow` and
  `requires_pillow_and_ffmpeg`. It also skips when the `ebur128` filter is
  missing and on some `win32` or `darwin` audio paths.
- Capture tests skip with "no headless Chrome/Chromium available".
- Fixture-repository tests skip without `git`, and history tests skip on a
  shallow clone.
- `ThePs1RunsUnderPwsh` raises `unittest.SkipTest` from `setUpClass` when `pwsh`
  is missing, saying the shipped `senzing-env.ps1` is NOT executed (INV-163).
  The zsh cases skip with "the zsh branch is NOT runtime-verified".

Fixtures. `tests/fixtures/maintainer-commands/` holds two command files that
Claude Code never loads:

- `review-invariants.md`: a same-name front with
  `argument-hint: "[block number]"` and `$ARGUMENTS`;
- `dry-run-probe-only.md`: an alias that runs phase 1 of `dry-run`.

`tests/test_dev_commands_name_a_real_skill.py` reads them while no command
ships. Every other fixture is built in a temporary directory: project trees
holding `config/bootcamp_progress.json` (the marker of an active bootcamp), fake
CLIs, fake engines, throwaway git repositories and loopback HTTP servers.

### 8.2 Layout and running

- **Location.** All tests live in the top-level `tests/` directory, never under
  `plugins/`, which `propagate.sh` mirrors to the public repository.
- **Naming.** The 371 files are named `test_<claim>.py`, where the claim is a
  sentence in snake_case, such as
  `test_eula_question_precedes_every_install.py`.
  - Classes are CamelCase sentences, and methods are named `test_<claim>`.
  - Each module docstring states the defect, the invariant enforced
    (`Enforces **INV-NNN**`), the source issue or spec, and the run command.
- **Command.** Run `python3 -m unittest discover -s tests` from the repository
  root. Tests locate the repository from `__file__`. A full run takes about 7
  minutes. `pytest -q` also works.
- **Offline.** No test calls the MCP server or the network.

What the tests read:

- **Shipped plugin files** (the largest share):
  - the skill Markdown under `plugins/senzing-bootcamp/skills/`;
  - the commands under `plugins/senzing-bootcamp/commands/`;
  - `hooks/hooks.json` and `hooks/README.md`;
  - `.claude-plugin/plugin.json`;
  - `docs/model-selection.md` and the example recap under `docs/examples/`;
  - script source text.
- **Maintainer skills**: `.claude/skills/*/SKILL.md`, the scripts beside them,
  and `.claude/skill-overlays/*.md`.
- **Specs**: `specs/INVARIANTS.md` (49 files), `specs/IMPLEMENTED.md` (35),
  `specs/DECLINED.md` (12), `specs/README.md`, `specs/todo.md`, the frozen spec
  files and `invariant-manifest.json`.
- **Repository documents**: `README.md`, `docs/development.md`,
  `docs/FAMILY_WORKFLOW.md`, `requirements-dev.txt`, the CI workflow,
  `propagate.sh` and git history.

How scripts are loaded:

- **In process** (91 files). `importlib.util.spec_from_file_location` gives the
  script a private module name. Then `module_from_spec` creates the module, it
  is registered in `sys.modules`, and `spec.loader.exec_module` runs it. Loading
  by path is needed because the scripts are not a package and some names, such
  as `write-gate.py`, are not valid identifiers. Section 7 lists the non-public
  items these tests touch.
- **As a subprocess** (72 files, 45 of which also load in process).
  `sys.executable` runs the script with real arguments or stdin. Tests assert
  the exit code, exact stdout and stderr lines, and the files written. Hooks
  that read stdin at import time, such as `write-gate.py`, `feedback-capture.py`
  and `checkpoint-tick.py`, are tested only this way.
- **Stubs.** External tools are stubbed with fake CLIs on `PATH`, fake
  `subprocess` and `find_spec`, and fake engines. A `PYTHONPATH` shim `fpdf.py`
  that raises `ImportError` forces the stdlib renderer.
- **Shell snippets.** Env-script snippets are extracted from the Markdown and
  run under `bash`, `zsh` and `pwsh`.

### 8.3 Count

There are 6199 test methods in 371 files, matching `inventory.test_count_total`.
Each count below is the number of `test*` methods the file defines, taken from
`inventory.tests_by_file`. An AST recount agrees for every file, and the counts
sum to 6199.

Two files run more tests than they define, so discovery collects 6206:

- `tests/test_env_script_shell_portability.py` defines 45 and runs 49. Its mixin
  `_EveryStepInOneShell` runs 4 tests under both bash and zsh.
- `tests/test_since_states_its_corpus.py` defines 11 and runs 14. One class
  subclasses another and inherits its 3 tests.

Without `pwsh`, the run reports `Ran 6189`. The 7 tests of `ThePs1RunsUnderPwsh`
are skipped in `setUpClass`, which counts as one skip and adds nothing to the
run count. With `pwsh` installed, the run reports `Ran 6196`. No other count
looks wrong.

- `tests/test_a_restated_rule_keeps_its_authority.py`: 5
- `tests/test_a_single_statement_claim_names_its_authority.py`: 11
- `tests/test_absent_field_suspects_flags_first.py`: 10
- `tests/test_access_steps_terminal_step.py`: 10
- `tests/test_acknowledge_precedes_the_loading_it_precedes.py`: 8
- `tests/test_all_runs_every_argument_free_view.py`: 7
- `tests/test_amendments_are_queued.py`: 12
- `tests/test_answer_options_render_below_the_question.py`: 11
- `tests/test_any_language_citations_name_the_right_rule.py`: 4
- `tests/test_any_language_contract_complete.py`: 16
- `tests/test_apparatus_exempt_carve_out_is_recorded.py`: 7
- `tests/test_audit_files_issues_not_specs.py`: 11
- `tests/test_audit_skill_reads_the_newest_entries.py`: 4
- `tests/test_audit_skill_states_no_stale_count.py`: 9
- `tests/test_authored_shapes_are_stated.py`: 6
- `tests/test_auto_test_harness.py`: 11
- `tests/test_backgrounded_launch_records_the_server_pid.py`: 12
- `tests/test_blocked_submission_has_a_vocabulary_value.py`: 29
- `tests/test_bootcamp_notes_flow.py`: 33
- `tests/test_brand_sync.py`: 31
- `tests/test_broll_manifest.py`: 20
- `tests/test_build_version_provenance_is_per_platform.py`: 8
- `tests/test_bundled_script_and_production_paths.py`: 23
- `tests/test_business_problem_preserves_the_original_wording.py`: 17
- `tests/test_canonical_module_names.py`: 7
- `tests/test_canonical_operations_resolve.py`: 56
- `tests/test_capture_exit_codes_are_not_conflated.py`: 7
- `tests/test_capture_render_is_settled_and_fitted.py`: 14
- `tests/test_capture_single_page.py`: 41
- `tests/test_capture_suppressed_tabs.py`: 12
- `tests/test_capture_tabs.py`: 47
- `tests/test_capture_verifies_tab_activation.py`: 11
- `tests/test_certificate_name_source.py`: 19
- `tests/test_checklist_items_ship_their_exceptions.py`: 5
- `tests/test_ci_workflow_guards_the_fpdf2_matrix.py`: 12
- `tests/test_citation_census.py`: 24
- `tests/test_citations_verify_states_its_limit.py`: 5
- `tests/test_claimed_hook_triggers_are_real.py`: 8
- `tests/test_classpath_root_is_platform_qualified.py`: 6
- `tests/test_comment_test_pointers_resolve.py`: 10
- `tests/test_compact_dev_environment_leaves_specs_frozen.py`: 12
- `tests/test_completeness_denominator.py`: 23
- `tests/test_concepts_teaching_section_claims_no_exemption.py`: 12
- `tests/test_config_seeding_guidance.py`: 16
- `tests/test_confirmation_gate_is_satisfiable_on_a_generated_scenario.py`: 9
- `tests/test_conformance_scans.py`: 27
- `tests/test_conformance_sees_a_rule_beside_a_citation.py`: 8
- `tests/test_container_lifecycle_runtimes.py`: 18
- `tests/test_container_names_are_project_derived.py`: 36
- `tests/test_container_teardown_has_a_route_and_a_failure_report.py`: 8
- `tests/test_cord_fetch_has_a_403_remedy.py`: 17
- `tests/test_cord_fetch_integrity.py`: 50
- `tests/test_cord_is_disclosed_as_real_data.py`: 10
- `tests/test_coverage_check_looks_inside_root_arrays.py`: 6
- `tests/test_coverage_ledger.py`: 36
- `tests/test_coverage_reports.py`: 48
- `tests/test_data_collection_generated_scenarios.py`: 22
- `tests/test_data_collection_non_yielding_run.py`: 20
- `tests/test_database_backup_has_one_implementation.py`: 12
- `tests/test_database_type_write_precedes_the_step7_branches.py`: 14
- `tests/test_datastore_mount_crossing_is_measured.py`: 13
- `tests/test_dated_negatives_are_marked.py`: 14
- `tests/test_declined_ledger.py`: 25
- `tests/test_default_flags_production_caution.py`: 12
- `tests/test_deferral_freshness.py`: 5
- `tests/test_deferral_quotes_match_their_source.py`: 11
- `tests/test_deferrals_do_not_name_a_literal_next_id.py`: 5
- `tests/test_delegate_files_issues_not_specs.py`: 18
- `tests/test_dependency_reading_rules.py`: 13
- `tests/test_dev_commands_name_a_real_skill.py`: 11
- `tests/test_discoveries_pdf.py`: 57
- `tests/test_documented_commands_match_the_shipped_set.py`: 6
- `tests/test_documented_dev_commands_match_the_shipped_set.py`: 13
- `tests/test_download_resource_is_a_listing.py`: 27
- `tests/test_dropped_character_remedy_branches.py`: 10
- `tests/test_dry_run_files_issues.py`: 15
- `tests/test_dry_run_scaffold.py`: 15
- `tests/test_dry_run_scaffold_paths_exist.py`: 10
- `tests/test_dry_run_states_no_hook_count.py`: 11
- `tests/test_empty_input_checks_are_not_a_pass.py`: 9
- `tests/test_encoding_self_check_is_stated_as_behavior.py`: 31
- `tests/test_end_the_turn_questions_exist.py`: 18
- `tests/test_enforcer_clause_survives_a_line_break.py`: 9
- `tests/test_engine_verification_and_senz2027.py`: 33
- `tests/test_entity_specification_access_pattern.py`: 11
- `tests/test_env_script_names_every_required_export.py`: 8
- `tests/test_env_script_powershell.py`: 21
- `tests/test_env_script_shell_portability.py`: 45
- `tests/test_eula_question_precedes_every_install.py`: 19
- `tests/test_every_capture_path_requests_the_render.py`: 8
- `tests/test_every_invariant_is_cited_in_shipped_text.py`: 4
- `tests/test_every_line_reading_guard_gives_a_verdict.py`: 9
- `tests/test_example_recap_sync.py`: 15
- `tests/test_example_recap_uses_no_golden_record.py`: 5
- `tests/test_existing_install_still_runs_the_env_script.py`: 16
- `tests/test_expected_visualization_denominator.py`: 21
- `tests/test_family_amendments_cite_real_rules.py`: 9
- `tests/test_fastpath_gates_on_full_mapping.py`: 31
- `tests/test_feedback_asks_only_the_unanswered_questions.py`: 5
- `tests/test_feedback_capture_triggers.py`: 19
- `tests/test_feedback_ledger.py`: 25
- `tests/test_feedback_routing.py`: 47
- `tests/test_feedback_to_issues_files_in_its_own_repo.py`: 13
- `tests/test_filing_is_gated.py`: 20
- `tests/test_find_examples_coverage_is_uncitable.py`: 12
- `tests/test_first_source_is_chosen_by_step_fourteens_heuristics.py`: 18
- `tests/test_fpdf2_dependency_is_declared.py`: 12
- `tests/test_free_data_catalog_caveats.py`: 14
- `tests/test_gate_options_have_handling_steps.py`: 10
- `tests/test_generated_dataset_size_is_a_license_decision.py`: 18
- `tests/test_generated_gap_rates_reach_their_band.py`: 12
- `tests/test_generated_html_deliverables.py`: 9
- `tests/test_generated_scenario_dataset_eligibility.py`: 20
- `tests/test_generated_scenario_is_bounded.py`: 8
- `tests/test_generated_scenario_marker_drop_is_exempt.py`: 18
- `tests/test_global_shell_config_is_off_limits.py`: 7
- `tests/test_globalization_retrieval_strategy.py`: 15
- `tests/test_graduation_announces_what_it_produces.py`: 12
- `tests/test_graduation_ending_surfaces.py`: 7
- `tests/test_graduation_no_voice_guidance.py`: 20
- `tests/test_graduation_reads_persisted_answers.py`: 15
- `tests/test_graduation_video_step.py`: 74
- `tests/test_graph_colors_by_source_combination.py`: 25
- `tests/test_graph_label_distinctness.py`: 18
- `tests/test_graph_labels_paint_after_circles.py`: 13
- `tests/test_ground_rules_nonyielding_presentation.py`: 14
- `tests/test_group_score_is_not_a_join_prediction.py`: 15
- `tests/test_hard_rule_citations.py`: 6
- `tests/test_hard_rule_detector_sees_mid_line_stop_signs.py`: 8
- `tests/test_hold_reason_lives_in_the_ledger.py`: 11
- `tests/test_hook_entries_name_a_script.py`: 5
- `tests/test_how_analysis_names_the_confusable_keys.py`: 20
- `tests/test_how_call_requests_the_breakdown_it_promises.py`: 20
- `tests/test_how_tab_names_an_unsettled_final_state.py`: 21
- `tests/test_install_verification_citation.py`: 8
- `tests/test_interface_naming.py`: 12
- `tests/test_internal_connection_string_rejected.py`: 2
- `tests/test_inv174_per_record_applicability.py`: 12
- `tests/test_invariant_crossreferences.py`: 32
- `tests/test_invariant_enforcer_citations.py`: 4
- `tests/test_invariant_layout_tree.py`: 19
- `tests/test_invariant_manifest_matches_the_prose.py`: 13
- `tests/test_invariant_paths_resolve.py`: 9
- `tests/test_invariants_index.py`: 17
- `tests/test_issue_command_gates_invariant_capture.py`: 7
- `tests/test_issue_path_reverifies_senzing_facts.py`: 10
- `tests/test_java_filename_class_reconciliation.py`: 25
- `tests/test_java_json_dependency_gap_is_covered.py`: 7
- `tests/test_language_gate_names_the_cost.py`: 10
- `tests/test_ld_library_path_is_not_relayed_as_conditional.py`: 22
- `tests/test_ledger_files_are_well_formed.py`: 11
- `tests/test_legacy_sublist_format_is_supported.py`: 14
- `tests/test_legend_labels_its_actual_denominator.py`: 21
- `tests/test_license_cap_branch_offers_the_apply_route.py`: 27
- `tests/test_license_env_var_absent.py`: 5
- `tests/test_license_framing_consults_the_measured_limit.py`: 5
- `tests/test_license_limit_is_written_only_from_a_measurement.py`: 14
- `tests/test_license_limit_reading_is_complete.py`: 16
- `tests/test_license_record_limit_is_measured_only.py`: 6
- `tests/test_list_specs.py`: 10
- `tests/test_listing_selection_is_by_shape.py`: 12
- `tests/test_liveness_probe_is_not_a_document_search.py`: 7
- `tests/test_load_count_reconciliation_has_three_outcomes.py`: 21
- `tests/test_load_reconciliation_has_two_stages.py`: 54
- `tests/test_loader_concurrency_reads_database_type.py`: 15
- `tests/test_maintainer_docs_stay_out_of_public.py`: 8
- `tests/test_maintainer_tooling_stays_out_of_public.py`: 9
- `tests/test_manifest_status_does_not_regress.py`: 5
- `tests/test_mapping_rejection_fallback.py`: 18
- `tests/test_mapping_samples_stay_out_of_senzing_ready.py`: 20
- `tests/test_mapping_workflow_violation_budget_is_documented.py`: 16
- `tests/test_markdown_hygiene.py`: 11
- `tests/test_match_key_suppressor_buckets.py`: 25
- `tests/test_mcp_call_contracts.py`: 23
- `tests/test_mcp_freshness_vocabulary.py`: 11
- `tests/test_mcp_negative_rationale_shape.py`: 31
- `tests/test_mcp_output_is_never_suppressed.py`: 4
- `tests/test_mcp_sourcing_instructions_name_a_route.py`: 8
- `tests/test_minimal_verbosity_scope.py`: 14
- `tests/test_model_effort_nudge_edges.py`: 21
- `tests/test_model_guidance_behavior.py`: 32
- `tests/test_model_guidance_sync.py`: 18
- `tests/test_model_nudge_trigger_direction.py`: 7
- `tests/test_model_selection_covers_every_skill.py`: 5
- `tests/test_model_switch_rule_is_stated_once.py`: 18
- `tests/test_module06_license_reconciliation.py`: 19
- `tests/test_module06_orchestrator_guidance.py`: 20
- `tests/test_module06_phase_ordering.py`: 15
- `tests/test_module07_why_flags.py`: 17
- `tests/test_module3_check_lists_agree.py`: 24
- `tests/test_module5_full_output_file_path_is_written_at_step_18.py`: 18
- `tests/test_module5_phase1_gates_and_scoring.py`: 14
- `tests/test_module5_phase3_exits_return_to_the_per_source_loop.py`: 9
- `tests/test_module5_step16_asks_about_loading_only_after_the_last_source.py`:
  5
- `tests/test_module6_data_dirs_are_copied_or_excluded.py`: 5
- `tests/test_module7_discover_instructions.py`: 17
- `tests/test_module_0_suggested_queries_are_measured.py`: 18
- `tests/test_module_5_describes_the_entity_specification_as_served.py`: 9
- `tests/test_module_7_points_at_the_factory_lifetime_rule.py`: 9
- `tests/test_module_instructions_do_not_hardcode_the_port.py`: 6
- `tests/test_module_selection_sync.py`: 9
- `tests/test_negatives_report_labels_stale_markers.py`: 9
- `tests/test_network_endpoint_keys_diverge_within_one_response.py`: 18
- `tests/test_new_hard_rules_are_cited_or_deferred.py`: 3
- `tests/test_new_line_labels.py`: 11
- `tests/test_no_absence_branch_asserts_a_licensing_finding.py`: 5
- `tests/test_no_host_control_is_offered_as_a_question.py`: 24
- `tests/test_no_instruction_writes_into_specs.py`: 7
- `tests/test_no_pip_install_senzing.py`: 18
- `tests/test_no_progress_gate_returns_to_data_collection.py`: 20
- `tests/test_no_stale_blocked_claim.py`: 9
- `tests/test_non_yielding_steps.py`: 20
- `tests/test_normalize_docs_markdown.py`: 34
- `tests/test_one_commit_convention.py`: 8
- `tests/test_one_question_per_turn_is_registered.py`: 12
- `tests/test_open_me_first_matches_the_manifest.py`: 20
- `tests/test_organization_search.py`: 23
- `tests/test_overview_bullets_are_not_counted.py`: 8
- `tests/test_package_bootcamp.py`: 35
- `tests/test_packaging_consent_gate_ships.py`: 15
- `tests/test_pages_site_commands_match_docs_readme.py`: 10
- `tests/test_partial_row_and_schema_coverage.py`: 39
- `tests/test_pattern_gallery_shortfall.py`: 21
- `tests/test_payload_key_collides_with_registered_feature.py`: 23
- `tests/test_pdf_verification_toolchain.py`: 20
- `tests/test_per_source_figures_are_reconciled.py`: 11
- `tests/test_phase3_interaction_prose.py`: 36
- `tests/test_phase3_names_every_server_language.py`: 8
- `tests/test_phase_c_loads_each_source_from_its_subset_record.py`: 26
- `tests/test_phase_d_how_state_audit.py`: 36
- `tests/test_phasec_generated_path_asks_once.py`: 12
- `tests/test_plugin_manifest_reads_resolve_inside_the_plugin.py`: 13
- `tests/test_poor_band_requires_a_mapping_cause.py`: 15
- `tests/test_post_yes_switch_reads_the_dial.py`: 19
- `tests/test_preparation_recap_template.py`: 9
- `tests/test_prescribed_search_queries.py`: 25
- `tests/test_profile_report_relocation_covers_both_filenames.py`: 15
- `tests/test_project_local_visualization_finds_its_d3.py`: 8
- `tests/test_project_readme_is_created.py`: 13
- `tests/test_propagate_publishes_the_pages_site.py`: 8
- `tests/test_propagate_publishes_the_published_marketplace_name.py`: 11
- `tests/test_python_sources_compile_cleanly.py`: 7
- `tests/test_quality_assessment_type_name_check.py`: 35
- `tests/test_quality_iteration_returns_to_step_3b.py`: 23
- `tests/test_quality_presence_test.py`: 18
- `tests/test_quality_score_and_preview_prereq.py`: 27
- `tests/test_quality_score_inputs_are_checked_before_scoring.py`: 11
- `tests/test_quality_verdict_needs_evidence.py`: 13
- `tests/test_question_options_render_beneath.py`: 12
- `tests/test_readme_does_not_undercount_claude_interfaces.py`: 7
- `tests/test_reassurance_precedes_question.py`: 18
- `tests/test_recap_checkpoint_is_lifted_before_module_parsing.py`: 15
- `tests/test_recap_checkpoint_writer.py`: 26
- `tests/test_recap_header_is_owned.py`: 22
- `tests/test_recap_measure_font_safety.py`: 14
- `tests/test_recap_notes_section.py`: 22
- `tests/test_recap_pdf_bulleted_images.py`: 11
- `tests/test_recap_pdf_certificate.py`: 17
- `tests/test_recap_pdf_font_safety.py`: 27
- `tests/test_recap_pdf_guard.py`: 52
- `tests/test_recap_pdf_images.py`: 18
- `tests/test_recap_pdf_text_column.py`: 9
- `tests/test_recap_sdk_version_is_the_installed_one.py`: 7
- `tests/test_recap_structure_checked_per_module.py`: 12
- `tests/test_recap_summary_blocks.py`: 30
- `tests/test_recap_tab_coverage.py`: 19
- `tests/test_recap_video.py`: 131
- `tests/test_record_limit_negative_is_rescoped.py`: 13
- `tests/test_registration_idempotency_is_constructed.py`: 12
- `tests/test_related_entities_guidance.py`: 20
- `tests/test_release_bumps_version_changelog_and_tag_together.py`: 32
- `tests/test_release_covers_every_version_site.py`: 8
- `tests/test_results_validation_is_diagnostic.py`: 35
- `tests/test_resume_requires_a_recorded_module.py`: 12
- `tests/test_retired_vocabulary.py`: 5
- `tests/test_retrofit_files_issues.py`: 40
- `tests/test_reverse_check_counts_what_it_cannot_test.py`: 16
- `tests/test_reverse_contract_flags_the_maintainer_surface.py`: 7
- `tests/test_reversed_decision_capture.py`: 35
- `tests/test_review_invariants_queue.py`: 5
- `tests/test_review_invariants_stops_at_the_working_tree.py`: 9
- `tests/test_root_readme_exception.py`: 12
- `tests/test_routing_report_payload_limitation_is_relayed.py`: 10
- `tests/test_rule_bullets_are_read_or_reported.py`: 17
- `tests/test_rule_citations_name_their_file.py`: 7
- `tests/test_sample_data_source_codes_are_scoped.py`: 7
- `tests/test_sampling_and_validation_routing.py`: 27
- `tests/test_saved_preferences_honored.py`: 13
- `tests/test_scaffold_banner_matches_build.py`: 25
- `tests/test_scaffold_citations_and_database_type.py`: 23
- `tests/test_scaffold_engine_config_reaches_the_sdk.py`: 8
- `tests/test_screenshot_embed_timing_is_satisfiable.py`: 10
- `tests/test_screenshot_retention_and_order.py`: 19
- `tests/test_sdk_parameter_shapes.py`: 39
- `tests/test_sdk_setup_prerequisites.py`: 41
- `tests/test_sdk_update_offer.py`: 56
- `tests/test_search_docs_calls_pass_a_query.py`: 10
- `tests/test_secret_patterns_are_shared.py`: 12
- `tests/test_server_launch_warns_about_protected_launchers.py`: 7
- `tests/test_settle_signal_is_reported.py`: 11
- `tests/test_shape_claims_precede_mapping_claims.py`: 25
- `tests/test_shared_feature_collision_trigger_is_narrowed.py`: 13
- `tests/test_shipped_negative_markers_are_html_comments.py`: 14
- `tests/test_since_last_audit_widens_past_a_work_commit.py`: 7
- `tests/test_since_states_its_corpus.py`: 11
- `tests/test_since_view_sees_the_maintainer_surface.py`: 7
- `tests/test_sites_states_the_corpus_it_scanned.py`: 14
- `tests/test_skills_state_their_commands_argument_handling.py`: 14
- `tests/test_snapshot_and_capture_fidelity.py`: 24
- `tests/test_source_encoding_renders_distinctly.py`: 9
- `tests/test_sourcing_reaches_beyond_technical_facts.py`: 18
- `tests/test_spec_absence_claims_name_their_owner.py`: 10
- `tests/test_spec_ledger_invariants.py`: 17
- `tests/test_specs_are_frozen.py`: 25
- `tests/test_sqlite_load_time_prompt_is_defined_and_matched.py`: 18
- `tests/test_sqlite_preload_check_reads_the_loadable_total.py`: 16
- `tests/test_sqlite_subset_notes_read_the_recorded_decision.py`: 11
- `tests/test_stdlib_writer_character_safety.py`: 14
- `tests/test_step1_filesystem_fallback.py`: 10
- `tests/test_step2_record_type_contradiction.py`: 9
- `tests/test_step3_name_rejection_names_its_fix.py`: 10
- `tests/test_step_8b_uses_module_6s_sqlite_threshold.py`: 23
- `tests/test_steps_name_the_route_that_supplies_them.py`: 23
- `tests/test_supersession_has_one_syntax.py`: 16
- `tests/test_suppressed_branch_has_no_pinned_question.py`: 9
- `tests/test_synthesized_entities_have_their_own_identifiers.py`: 16
- `tests/test_synthesized_scenario_has_quality_gaps.py`: 21
- `tests/test_tab_manifest_survives_recapture.py`: 14
- `tests/test_tab_set_is_singular.py`: 25
- `tests/test_the_2026_09_30_audit_rules_cite_their_invariants.py`: 4
- `tests/test_the_227_mis_citations_do_not_return.py`: 5
- `tests/test_the_gate_sees_every_scanned_root.py`: 7
- `tests/test_the_range_boundary_reports_what_it_retires.py`: 10
- `tests/test_the_seven_triaged_rules_keep_their_citations.py`: 3
- `tests/test_todo_triage_is_recorded.py`: 9
- `tests/test_tool_directives_do_not_override_interaction.py`: 30
- `tests/test_truth_set_spelling.py`: 5
- `tests/test_truthset_acquisition_call.py`: 14
- `tests/test_truthset_download_is_the_dataset.py`: 20
- `tests/test_truthset_is_not_called_single_source.py`: 6
- `tests/test_truthset_visualization_reports_empty_as_failure.py`: 9
- `tests/test_unattended_loop_is_label_gated.py`: 13
- `tests/test_undecodable_recap_is_never_overwritten.py`: 10
- `tests/test_update_offer_order_and_existing_install_outcome.py`: 24
- `tests/test_us_english_spelling.py`: 18
- `tests/test_user_level_copies_govern.py`: 15
- `tests/test_verbatim_check_limitation.py`: 43
- `tests/test_verbatim_check_limitations_freshness.py`: 23
- `tests/test_version_precedence_handles_an_unmanaged_install.py`: 10
- `tests/test_visualization_api_contract.py`: 19
- `tests/test_visualization_model_build_scales.py`: 33
- `tests/test_viz_capped_graph_notes.py`: 12
- `tests/test_viz_defaults_at_scale.py`: 16
- `tests/test_viz_endpoint_sync.py`: 7
- `tests/test_viz_histogram_integer_ticks.py`: 6
- `tests/test_viz_server_bind_and_identity.py`: 22
- `tests/test_viz_server_process_handle.py`: 17
- `tests/test_viz_server_refuses_to_render_without_d3.py`: 12
- `tests/test_viz_settings_resolution.py`: 12
- `tests/test_viz_tab_consolidation.py`: 38
- `tests/test_volume_option_reply_has_no_count.py`: 14
- `tests/test_walk_hook_conflict_is_documented.py`: 10
- `tests/test_welcome_licensing_names_data_collection.py`: 6
- `tests/test_why_key_details_flag_claim_is_withdrawn.py`: 26
- `tests/test_why_key_details_flag_is_cited_not_guessed.py`: 12
- `tests/test_why_side_match_family_is_renamed.py`: 7
- `tests/test_windows_browser_discovery.py`: 23
- `tests/test_windows_forms_at_hand_run_sites.py`: 40
- `tests/test_windows_powershell_guidance.py`: 21
- `tests/test_wrapped_text.py`: 32
- `tests/test_write_gate.py`: 23

### 8.4 Key cases

Most of the suite asserts exact wording or phrases in the skill Markdown. This
blueprint describes that Markdown but does not embed it, by the maintainer's
choice, so those tests cannot pass on a rebuild from this blueprint alone. They
need the original text. These are heuristic estimates, accurate to about 10%:

- About 230 of the 371 files (about 3,500 tests, 57%) read only Markdown or
  register text and never run a script.
- Counted per test method, about 3,600 tests (59%) assert that a phrase is
  present, absent, in order or in place. This includes wording checks inside
  files that also run code.
- About 76 files (about 1,000 tests, overlapping the figures above) also assert
  ids, citations and wording in `specs/INVARIANTS.md`, `specs/IMPLEMENTED.md` or
  `specs/DECLINED.md`.
- About 118 files (about 2,300 tests) execute code. A rebuild can satisfy these
  from sections 6 and 7 and from 8.4.7 to 8.4.9.

#### 8.4.1 Shared guard conventions and helpers

- **Non-vacuity (INV-265).** Nearly every guard asserts that its corpus was
  found and that a known site matched ("the scan is not vacuous").
- **Negative controls.** Guards run their own matcher on a copy with the old
  wording pasted back, and assert that it fails.
- **Wrap-aware matching.** `tests/test_wrapped_text.py` (32 tests) pins the
  block rules of `tests/_wrapped_text.py`.
  - A match is reported at its start line. CR counts as whitespace.
  - These lines end a block:
    - a blank line;
    - a fence line;
    - a table row, whose first non-blank character is `|`;
    - an ATX heading line;
    - the front matter, from a `---` on line 1 to the next `---`.

    A heading, a table row and a fence line are each their own block.
  - The pattern runs on one block at a time, so `^` and `$` anchor at the
    block's edges.
  - Leading `>` markers are stripped, nested ones included. A line holding only
    `>` is blank.
  - A fence indented inside a list item is still a fence. A `~~~` fence can hold
    backtick lines. Inside a fence, `#`, `|` and `---` lines are content, and
    only a blank line ends a block.
  - The lines of one list, with no blank line between them, form one block.
- **Line-by-line guards.**
  `tests/test_every_line_reading_guard_gives_a_verdict.py` requires every test
  that reads a corpus line by line to use the matcher or to state an INV-346
  verdict that names an issue number.
- **Hygiene.**
  - US English only, checked in prose and in snake_case, camelCase and UPPER
    identifiers. Waivers must match exactly.
  - No space before a comma, no trailing whitespace and no mojibake in shipped
    Markdown.
  - Every Python source compiles with no warning.
  - Retired terms appear only on lines that mark them as retired.
  - A comment that names a test points at an existing test file.

#### 8.4.2 Invariant-register guards

These read `specs/INVARIANTS.md`:

- **The topical index** sits before the append marker. Every development
  invariant appears in exactly one group, every indexed id is defined, and the
  supersession lists match what the invariants themselves declare.
- **The manifest.** `invariant-manifest.json` must equal a fresh run of
  `.claude/skills/review-invariants/invariant_manifest.py`.
  - `status` takes only the three stated values, and no entry is newly
    `unclear`.
  - A superseded entry names its successor.
- **Supersession** is decided by bullets only, never by prose. A partial
  supersession leaves the invariant active, and every `superseded by` has a back
  link.
- **Paired cross-references** must point both ways: INV-162 and INV-193, INV-048
  and INV-110, INV-123 and INV-146, INV-107 and INV-184, INV-050 and INV-202.
- **Enforcers.** An invariant that names its enforcing test is cited back by
  that test.
- **Paths.** Every repository path in the register resolves, dot-prefixed paths
  included.
- **Shipped coverage.** Every invariant that binds a shipped artifact is cited
  in shipped text.
- **The layout tree.** Every entry of INV-050's tree is produced somewhere, or
  annotated with a date (INV-202).
- **Citation pins.** Named rules cite named invariants at their own line, and
  each cited invariant still promises what the rule claims:
  - "stated once" claims cite INV-300;
  - INV-251 covers two or more 👉 questions in a turn;
  - INV-017 allows exactly two root-Markdown exceptions;
  - INV-218 governs install verification, and INV-129 does not.

#### 8.4.3 Ledger and specs-archive guards

- **Frozen archive.** The manifest of frozen spec files must equal the
  directory. The five live records are named the same way in the
  `specs/README.md` table, in INV-307 and in every sanctioned copy. No
  instruction creates a file under `specs/` or pins a spec count.
- **Issues, not specs.** The audit, `/delegate-to-mcp-server`, `/dry-run` and
  `/feedback-to-issues` file GitHub issues in this repository, gated on the
  maintainer's yes. They never write specs.
- **Well-formed ledgers.**
  - No literal `\n` appears in prose.
  - Entry headings start a line, and two independent parses agree on the entry
    count.
  - No heading appears twice, and no spec is in both ledgers.
- **`specs/DECLINED.md` entries** carry a date, who decided, a reason and what
  would reopen the decision.
- **`specs/IMPLEMENTED.md` entries** account for their invariants, or carry a
  `DEFERRED INVARIANT` block with drafted wording. Every recorded commit hash
  resolves.
- **Deferral blocks.**
  - Quoted rules appear verbatim in the file they name.
  - The next id is written `NNN`, never as a literal number.
  - A hold records its reason inside the block.
  - An amendment is queued and kept distinct from a new invariant.
  - `pending_invariants.py` counts blocks, not mentions, and `next-id` is one
    past the highest id.
  - A wrapped `Enforced by` clause is still read, and an unreadable one is
    reported.
- **`tests/list_specs.py`.** A declined spec is not open, a spec in both ledgers
  is flagged, and `--check` exits non-zero while listing exits 0. Exactly three
  items in `specs/todo.md` are live, each with a recorded disposition.

#### 8.4.4 Interaction protocol (ground rules, onboarding, preparation)

- **👉 questions.**
  - Options render beneath the question, never on its line, and
    runtime-generated lists follow the same rule.
  - Anything meant to inform the answer comes before the 👉.
  - A turn holds at most one 👉.
  - A step that asks nothing shares the next asking step's turn.
  - An "end the turn" instruction resolves to a pinned question.
  - No question offers a host or session control.
- **Model and effort.**
  - The switch question and the gate "Are you done modifying the model and
    effort?" are pinned only in `ground-rules.md`.
  - The comparison is with the live session, dial by dial, and only the dial
    that differs is named.
  - A step-down is flagged.
  - The table is a floor.
  - Both tables in `docs/model-selection.md` cover every skill.
- **Preferences.** Saved preferences are honored at Step 0 (INV-133). Module
  names come from one table of eleven modules. `minimal` verbosity merges
  content rather than dropping it.
- **Feedback.** It is triaged to its owner, and the `host` verdict is never
  forwarded. It is always recorded locally. It is forwarded only after a pinned,
  numbered consent question that shows the exact message.
- **Notes** never leave the machine. They are recited before they are saved,
  appended and verified, and folded into the recap at graduation (INV-254).

#### 8.4.5 Per-module skill guards

These are almost all wording guards. Each item lists the main behaviors pinned.

- **Module 0.** Suggested `search_docs` queries are measured, with a stamp and a
  rank. The text never says "golden record". The knowledge check is offered by a
  pinned yes/no question and uses numbered multiple-choice items.
- **Module 1.**
  - `docs/business_problem.md` keeps verbatim quote slots.
  - Step 15 shows both versions. On the generated path, zero quotes is correct.
  - The project `README.md` is created before it is filled.
- **Module 2.**
  - The pinned EULA question comes before every install.
  - The env script finds its root under bash and zsh, and returns rather than
    exits.
  - On Windows it is a dot-sourced `senzing-env.ps1`, never a `.bat`.
  - The Senzing SDK is never installed with `pip install`.
  - Updates are offered per platform: apt, yum or dnf, brew and scoop, with no
    in-place update for Docker.
  - `LD_LIBRARY_PATH` is required on `linux_apt`.
  - The license variable is `SENZING_LICENSE_FILE`, not `SENZING_LICENSE_PATH`.
  - The SENZ7221, SENZ2027 and SENZ7426 diagnostics are covered.
  - All five server languages, Rust included, are named.
- **Module 3.** The eight installation checks must pass. Results validation is
  diagnostic and never required to pass. The liveness probe is
  `get_capabilities`.
- **Module 3b.**
  - The Truth Set is downloaded, not saved from the preview.
  - A CORD 403 or 429 is never retried blindly.
  - The six tabs are `graph`, `stats`, `matchkeys`, `features`, `overlap` and
    `probe`.
  - The server PID is captured, and the port is never hardcoded.
  - Without D3, rendering is refused.
  - An empty visualization counts as a failure.
- **Module 4.**
  - A 429 body is never saved as data.
  - The record count must match the MCP listing.
  - CORD is disclosed as real data.
  - A synthesized scenario carries quality gaps, has unique identifiers, and
    stays bounded.
- **Module 5.**
  - A quality-score formula with three bands.
  - The presence test: `False` and `0` count as present.
  - Completeness is measured per record type (INV-174).
  - The fast path is gated on full mapping (INV-198).
  - A `mapping_workflow` rejection gets at most two retries and then a pinned
    three-option question. The malformed-advance budget is five violations.
  - Samples go to `data/mapping/`, and the full output to `data/senzing-ready/`
    at Step 18.
- **Module 6.**
  - Load reconciliation has two stages and four outcomes.
  - Each source is loaded from its `load_subset:` block.
  - One SQLite threshold is checked against the loadable total.
  - Loader concurrency reads `database_type`.
  - Phase D audits how each multi-record entity was built.
- **Module 7.**
  - A why call parses `WHY_KEY_DETAILS`.
  - A how call requests the `MATCH_KEY_DETAILS` flag.
  - `find_network` uses two endpoint conventions.
  - The teardown question is asked once.
  - The visualization model is built from the export stream.
- **Graduation.**
  - Step 1c, the video, has pinned offers, a two-minute budget, the Intro first,
    and ends on the certificate and then the tag line. It uses name-free
    screenshots only.
  - PDF verification needs no Unix-only tool.
  - Database backup has one procedure.
  - Every artifact produced is announced.
  - Every `data/` directory that Module 6 names is copied, or excluded on
    purpose.

#### 8.4.6 MCP call contracts and Senzing-fact provenance

`tests/test_mcp_call_contracts.py` (23 tests) holds a static copy of the server
contract, stamped `CONTRACT_VERIFIED_ON = "2026-08-12"` and
`MCP_SERVER_VERSION = "1.32.9"`.

- **Tools.** `MCP_TOOLS` lists the server's 13 tools:
  - `analyze_record`, `download_resource`, `explain_error_code`, `find_examples`
    and `generate_scaffold`;
  - `get_capabilities`, `get_sample_data`, `get_sdk_reference` and
    `mapping_workflow`;
  - `reporting_guide`, `sdk_guide`, `search_docs` and `submit_feedback`.

  Three classification sets must partition this list exactly, and every tool the
  plugin references must be classified.
- **Required parameters**, which every documented call must show:
  - `analyze_record`: `workspace_dir`;
  - `explain_error_code`: `error_code`;
  - `generate_scaffold`: `language` and `workflow`;
  - `get_sample_data`: `dataset`;
  - `get_sdk_reference`, `reporting_guide` and `sdk_guide`: `topic`;
  - `mapping_workflow`: `file_paths` and `workspace_dir` on `start`;
  - `search_docs`: `query`.
- **Conditional or no requirements.** `find_examples` and `submit_feedback` have
  conditional requirements. `get_capabilities` and `download_resource` require
  nothing.
- **Mapping workflow.** The only actions are `start`, `advance`, `back`,
  `status` and `reset`. `workspace_dir` is never `/tmp`, `%TEMP%`, `~/` or
  `/var/tmp`.
- **Other call shapes.** Every `reporting_guide` call passes `language`. The
  license request is gated by a pinned consent question.

Related guards:

- `download_resource` returns a URL listing. `inline` is allowed for it alone.
- No `search_docs` reference passes `category=` without `query=`.
- Selection from an MCP listing goes by a property, never by position (INV-267).
- Every prescribed query is stamped or paired with a re-query rule.
- Every `MCP-NEGATIVE` marker in shipped Markdown sits inside an HTML comment
  and names its owning route. Its rationale rests on neither a count nor a name
  list.
- Tool output is never withheld from the bootcamper.
- A conversational directive in a tool response never overrides the interaction
  rules.
- `tests/test_auto_test_harness.py` checks the plugin against
  `.claude/skills/auto-test/baseline/mcp-snapshot.json`: no breaking conformance
  findings, no forbidden tool probed, and the linter's self-test passing.

#### 8.4.7 Script behavior

These cover the scripts in `plugins/senzing-bootcamp/scripts/`, and they are the
tests a rebuild can pass from behavior alone.

- **`write-gate.py`** (`tests/test_write_gate.py`).
  - **Harness.** The script runs as a subprocess. Its stdin is
    `{"tool_input": {"file_path": …, "content": …}}`, and the project holds
    `config/bootcamp_progress.json`. Exit 0 allows the write and exit 2 blocks
    it.
  - **Allowed:**
    - `config/prefs.yaml`;
    - an absolute path inside the project;
    - a project that lives under `/tmp`;
    - an upper-cased variant of the project path.
  - **Blocked as temporary or downloads:**
    - `/tmp/…` and `/var/tmp/…`;
    - `/home/someone/Downloads/…` and `~/Downloads/…`;
    - `%TEMP%\…` and `%Tmp%\…`;
    - `~/AppData/Local/Temp/…`;
    - a path under the directory named by `TMPDIR`, `TEMP` or `TMP`.

    For the environment-variable case, the probe `/opt/relocated-temp-xyz` must
    produce stderr containing "system temp or Downloads".
  - **Blocked as outside the project.** Stderr contains "outside the Bootcamp
    project" for these targets:
    - `~/escape.txt`;
    - `/opt/not-the-project/x.txt`;
    - `/etc/senzing-bootcamp-probe.conf`;
    - a `config/` path followed by 12 `..` segments;
    - `~/tmp/scratch.txt`, because `/tmp/` matches only at the start of the
      path.
  - **Secrets** are blocked anywhere:
    - a PEM header line reading `BEGIN RSA PRIVATE KEY` between
      dash runs;
    - `AKIA` followed by 16 characters;
    - `AQAAAD` followed by a base64 run (48 characters here).

    A `.lic` path with ordinary content is allowed, and so is prose that
    mentions `AQAAAD`.
  - **Activation.** With no progress file, every write is allowed. Unparseable
    JSON fails open, but a PEM marker in raw non-JSON input is still blocked.
- **`secret_patterns.py`** (`tests/test_secret_patterns_are_shared.py`).
  `package_bootcamp.py` and `write-gate.py` use identical patterns.
  `find_secret` returns `PEM private key`, `AWS access-key ID` or
  `Senzing license payload`, and returns `None` for clean text. It never echoes
  the secret and never filters by file extension.
- **`package_bootcamp.py`** (`tests/test_package_bootcamp.py`,
  `tests/test_open_me_first_matches_the_manifest.py`).
  - **Arguments:** `--project-root`, `--profile share|transfer`, `--date` and
    `--dry-run`. A dry run reports a size and writes nothing.
  - **Layout.** The zip has one root directory, holding `OPEN_ME_FIRST.md` and
    `PACKAGE_MANIFEST.json`.
  - **`share`** carries results only. It has no database, no `data/raw/`, no
    credentials and no `docs/mapping/`.
  - **`transfer`** adds config, mappings, the revisit state snapshot and a
    database backup, but never the live database.
  - **Excluded and named in the manifest**, without echoing any secret:
    - `.git/`;
    - secret-bearing members, including `.pem` files, extensionless keys,
      secrets inside binaries and secrets that straddle a scan block;
    - unreadable members;
    - symlinks that resolve outside the project.

    A genuine PNG still travels.
  - **Safety.** A second archive never contains the first. A `.sha256` sidecar
    is written. Exclusions match path segments.
  - `OPEN_ME_FIRST.md` names only what the `included` list carries.
- **`generate_recap_pdf.py`** (`tests/test_recap_pdf_guard.py` and 15 more
  files). Its arguments are `--input`, `--output` and `--check`.
  - **Not a recap.** A non-recap input exits non-zero, with no `PDF generated:`
    line and no PDF. Stderr says "does not look like a bootcamp recap", mentions
    a "sub-section" and gives a "source characters" figure.
  - **Missing sub-section.** A recap with one sub-section missing still renders.
    It exits 0 and prints `WARNING`.
  - **Broken `fpdf2`.** The message says "could not be imported" and names
    `sys.executable`, and stdout says `renderer: stdlib`. The stdlib output
    still ends in a landscape certificate.
  - **`--check`** writes nothing. It fails on a duplicate section, a stray
    `RECAP-CHECKPOINT` block or a missing summary block, while rendering still
    ships.
  - **Images** are found relative to the document. A missing image is reported
    once, and remote URLs are never fetched. The text `embedded N of M` takes M
    from the capture manifest.
  - **The certificate** prefers the `name` from preferences.
  - **Characters.** Nothing outside Latin-1 reaches the core font, and no `?`
    appears on either renderer. Dropped characters are reported in ASCII by
    Unicode name.
  - **Encoding.** A recap that is not UTF-8 is refused and never rewritten.
- **`generate_discoveries_pdf.py`** (`tests/test_discoveries_pdf.py`).
  - **Arguments:** `--input`, `--output`, `--check`, `--require-sections`,
    `--no-section-check` and `--subtitle`.
  - **Sections.** Six named sections are required, matched case-insensitively. A
    recap-shaped or headingless document is refused, and an empty
    `--require-sections` is an error.
  - **`generate_document_pdf.py`** only delegates to this script.
- **`generate_recap_video.py`** (`tests/test_recap_video.py`, 131 tests).
  - **Exit codes:** 0 rendered, 1 invalid storyboard, 2 missing capability, 3
    encode failed. Nothing is written unless the code is 0.
  - **Errors** name the field at fault.
  - **Images** must be project-relative local files. A missing or unreadable
    image becomes a title card.
  - **Narration** is never truncated; its scene extends instead.
  - **Audio.** The music is a deterministic stdlib bed: an 8 s cycle at 48 kHz
    stereo. It is ducked by `sidechaincompress` and normalized by
    `loudnorm=I=-16:TP=-1.5:LRA=11`.
  - **Output:** H.264 `yuv420p`, 1920x1080, 30 fps, with audio at -16 ± 1 LUFS
    and a true peak of at most -1.0 dBFS.
  - **Voice.** Piper runs as `sys.executable -m piper` with the default voice
    `en_US-ljspeech-high`. A failure on one scene re-voices the whole video with
    the platform engine.
  - **Numbers are spelled out for Piper only.** "All 1,540 records loaded into
    1,310 entities." becomes "All one thousand five hundred forty records loaded
    into one thousand three hundred ten entities.". `CORD2`, `v4` and `4th` stay
    unchanged.
- **`capture_screenshots.py`** (13 files).
  - **Output.** One PNG per tab, named after the tab, in the order given, with
    duplicate tabs dropped.
  - **Exit codes:**
    - 1 for a remote `--url`, citing INV-091;
    - 1 for `--query` without `--url`;
    - 1 for an unknown tab id, with every valid id listed and nothing written;
    - 2 for `--html` together with `--url`, as an argparse usage error.
  - **Absent and suppressed tabs.** A tab absent from the page is skipped, and
    the run exits 0. If every tab is suppressed, the run exits 2 before
    launching a browser.
  - **`--single`** produces exactly one full-page image.
  - **Verification.** A server that ignores `?tab=` fails the capture. Identical
    captures are deleted. An unsettled animated tab is reported.
  - **The manifest** merges re-captures.
- **`senzing_viz_server.py`** (19 files).
  - **Bind and identity.** The server binds loopback, never the wildcard. It
    serves a per-process `server_nonce` on `/api/stats`, and a foreign answer
    stops startup.
  - **D3.** Without D3 it refuses to render and never falls back to a CDN.
  - **Settings.** A stub `config/engine_config.json` containing
    `{"PIPELINE": {}}` never beats a complete
    `SENZING_ENGINE_CONFIGURATION_JSON`. Missing keys are named.
  - **Search.** Name search tries `NAME_FULL` and then `NAME_ORG`.
  - **Drawing.**
    - Node color comes from the whole sorted source set.
    - Labels stay distinct when truncated.
    - A capped graph reports its true total.
    - Histogram ticks are integers.
  - **Payload.** The keys match the contract exactly.
- **`normalize_docs_markdown.py`** (`tests/test_normalize_docs_markdown.py`). It
  spaces headings and lists and gives fences a language, and it is idempotent.
  Any dropped, rewritten or reordered line is rejected, and the original file is
  restored. It reads only the top-level `docs/*.md` files. `--dry-run` writes
  nothing.
- **`recap_checkpoint.py` and `checkpoint-tick.py`.**
  - The hook creates `docs/progress/recap_checkpoint.md` without overwriting a
    narrative.
  - Folding an unfilled scaffold writes nothing, and folds never duplicate.
  - Status goes to stderr.
- **`docker_lifecycle.py`.**
  - It stops each container with its recorded `runtime`. Legacy entries under
    `docker_containers` count as `docker`.
  - An unknown runtime is never executed.
  - An absent CLI runs nothing and is named, and the hooks still exit 0.
  - `container-name` (`tests/test_container_names_are_project_derived.py`)
    derives `<base>-<slug>-<hash6>`, moves to `-2` … `-9` past an unrecorded
    container, returns a recorded name unchanged, and issues no command but
    `ps`. `free-port` skips a bound port and never sets `SO_REUSEADDR`. Two
    projects sharing a basename each stop only their own container.
- **`brand_tokens.py`** (`tests/test_brand_sync.py`). Every inlined fallback
  palette equals `brand_tokens.py`. Source colors are deterministic and never
  signal green, and exceeding capacity triggers a warning.

#### 8.4.8 Hooks

- **Registration.** `hooks/hooks.json` names one existing script per event, each
  reached through `${CLAUDE_PLUGIN_ROOT}` and none relying on an `args` array:
  - `SessionStart`: `session-start.py`;
  - `UserPromptSubmit`: `feedback-capture.py` and `checkpoint-tick.py`;
  - `PreToolUse`: `write-gate.py`;
  - `Stop`: `stop-nudge.py`;
  - `PreCompact`: `precompact-recap.py`;
  - `SessionEnd`: `session-end.py`.
- **`feedback-capture.py`** reads `{"prompt": …}` and stays silent outside a
  bootcamp.
  - **Fires** on "I have some feedback about module 5", "report a bug" and "this
    plugin is broken".
  - **Stays quiet** on "I found a bug" and "my loader is broken".
  - **The note branch** fires on "remember to check the counts" but not on "do
    you remember what module 3 covered".
  - **Precedence.** Feedback wins when a prompt matches both branches.
- **Resume and version.** A progress file that records no module is not a live
  bootcamp, and `session-start.py` prints nothing for it. `feedback-capture.py`
  injects the running plugin's own version, or `unknown`.

#### 8.4.9 Maintainer skills and tooling

These are the scripts under `.claude/skills/`:

- **`release/release.py`.**
  - **Mode.** It defaults to a dry run. `--apply` together with `--dry-run` is
    refused.
  - **Version.** Give an explicit version or exactly one of `--major`, `--minor`
    and `--patch`. Tags are compared numerically.
  - **Effect.** One commit moves `VERSION_SITES` and `CHANGELOG.md`. An
    annotated tag is created at `HEAD`, and nothing is ever pushed.
  - **Refusals:** a dirty tree, a branch other than `main`, a version that does
    not advance, and version sites that disagree.
- **`production-readiness-audit/conformance.py`.**
  - **Views:** `rules`, `per-rule`, `since`, `reverse-check`, `duplication`,
    `enumerations`, `size` and `all`.
  - They report hard rules without a cited invariant.
  - `since --since-last-audit` widens its range past a work commit.
- **`dry-run/coverage_reports.py`.**
  - **Reports:** `invariants`, `shipped`, `affected`, `negatives`, `unmarked`
    and `both`.
  - `--server` splits stale negatives.
- **Other maintainer tools.**
  - **`dry-run/scaffold_project.py`** builds `fresh`, `seeded` and `mid`
    projects, never inside the repository or under `/tmp`.
  - **`compact-dev-environment/citations.py`** `census` and `verify` catch
    citations of deleted invariants and dangling sources.
  - **`feedback-to-issues/feedback_ledger.py`** `check` and `commit` assign ids
    that are stable across BOM, CRLF and blank-line changes.
  - **`delegate-to-mcp-server/coverage_ledger.py`** verdicts expire when the
    server version or the docs index changes.
- **Propagation.**
  - `propagate.sh` never reaches `.claude/`, `.github/` or the maintainer docs.
  - `propagate.sh` publishes the marketplace as `senzing-bootcamp`: no
    whole-name `senzing-bootcamp-dev` survives in any propagated file, and
    longer names and the plugin name are untouched (#449).
  - `propagate.sh` publishes the six Pages site files, and no propagated file
    of any type still holds the dev slug; with `.html` off the rewrite
    suffixes, the slug survives in `docs/index.html` and is caught (#452).
  - `retrofit.sh` writes nothing and lists at most 40 lines.
  - Documented command sets equal the shipped sets.
  - Every outward act states its gate.

#### 8.4.10 CI and release hygiene

- **The CI workflow.** `tests/test_ci_workflow_guards_the_fpdf2_matrix.py`
  requires:
  - both matrix cells;
  - the absent leg's negative control and checks;
  - `shell: bash` on every step that pipes;
  - third-party actions pinned to a SHA;
  - `fetch-depth: 0`;
  - the documented runner.
- **The example recap.** `tests/test_example_recap_sync.py` requires the example
  recap PDF to match its source Markdown and the plugin version in the manifest.
- **The Pages site.** `tests/test_pages_site_commands_match_docs_readme.py`
  requires the `claude plugin …` commands inside `<code>` in `docs/index.html`
  to equal, as a set, those in `docs/README.md`'s `console` fences, indented or
  not. Either side yielding none fails and names its file; a changed page
  command is caught (#455).

## 9. Not embedded

### Secrets

The project reads no secret. CI uses no repository secret. Secret-shaped strings
in `tests/` are fixtures for the secret scanners and are not reproduced here.

### Generated files

- `invariant-manifest.json`: `python3
  .claude/skills/review-invariants/invariant_manifest.py` (run in the repository
  root).
- `.claude/skills/auto-test/baseline/mcp-snapshot.json`: `python3
  .claude/skills/auto-test/mcp_probe.py update` (run in the repository root;
  needs the live MCP server).
- `specs/mcp-coverage.jsonl`: appended record lines written by
  `.claude/skills/delegate-to-mcp-server/coverage_ledger.py`; not regenerable.
- `feedback/PROCESSED.jsonl`: appended record lines written by
  `.claude/skills/feedback-to-issues/feedback_ledger.py`; not regenerable.

### Vendored code

- `plugins/senzing-bootcamp/scripts/vendor/d3.v7.min.js`: D3,
  <https://d3js.org>, version 7.9.0 (minified), copied in so the visualizations
  render offline (INV-091).

### Binaries and large fixtures

- `CHANGELOG.md`: release notes, large because every version has an entry.
- `docs/images/apple-touch-icon.png`: Pages site touch icon.
- `docs/images/favicon-32.png`: Pages site favicon.
- `docs/images/senzing-logo.png`: Pages site logo.
- `invariant-manifest.json`: generated invariant manifest (above).
- `plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.pdf`:
  example graduation recap shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.truthset.png`:
  example graduation recap shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/data_quality_assessment.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-cross-source.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-entity-graph.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-feature-scores.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-match-keys.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-merge-statistics.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/results_visualization-search-probe.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-cross-source.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-entity-graph.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-feature-scores.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-match-keys.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-merge-statistics.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/docs/examples/visualizations/truthset_verification-search-probe.png`:
  example visualization screenshot shown to Bootcampers.
- `plugins/senzing-bootcamp/scripts/senzing_logo_light.png`:
  Senzing logo used in rendered documents (section 9).
- `plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/graduation/SKILL.md`: large skill file,
  described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-02-sdk-setup/SKILL.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/visualization-api-reference.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-04-data-collection/SKILL.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase1-quality-assessment.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md`:
  large skill file, described in section 5, not embedded.
- `plugins/senzing-bootcamp/skills/module-07-query-visualize-discover/phase1-query-visualize.md`:
  large skill file, described in section 5, not embedded.
- `resources/2026-sz-light.png`: Senzing brand artwork (section 9).
- `resources/certificate-of-completion.pdf`: certificate template referenced by
  graduation (section 9).
- `resources/senzing-style-reference.pdf`: Senzing brand style reference
  (section 9).
- `specs/IMPLEMENTED.md`: the implementation ledger, a live record (section 5).
- `specs/INVARIANTS.md`: the invariant register, a live record (section 5).
- `specs/mcp-coverage.jsonl`: MCP coverage log (above).

### Licenses

No license file is tracked; `plugin.json` declares `Apache-2.0`. The five paths
below are classified as license files by name only: each is a frozen spec about
Senzing licensing, with no SPDX identifier.

- `specs/license-cap-branch-offers-no-way-to-apply-the-license-that-may-have-arrived.md`:
  not a license; a frozen spec (no SPDX).
- `specs/license-limit-assumed-when-it-could-be-measured.md`:
  not a license; a frozen spec (no SPDX).
- `specs/license-record-limit-has-a-detected-only-contract-nothing-enforces.md`:
  not a license; a frozen spec (no SPDX).
- `specs/license-request-omits-a-required-field-the-server-demands.md`:
  not a license; a frozen spec (no SPDX).
- `specs/license-request-option.md`: not a license; a frozen spec (no SPDX).

## 10. Decision log

- #1: ship the plugin at 0.4.1 with feedback-driven hardening, deliverable fixes
  and a first test suite (real bootcamp runs exposed defects that prose review
  kept missing, so durable rules became tested invariants)
- #18: add the `/propagate-to-public` slash command (publishing to the public
  repo is a release-path action that must be invoked explicitly, never inferred)
- #19: add the `/retrofit-from-public` slash command (changes made directly in
  the public repo must be brought back so the two repos do not drift)
- #20: add the `/dry-run` slash command (verifying every MCP call against the
  live server finds defects reading cannot, as part of the pre-publish gate)
- #21: add the `/auto-test` slash command (the sandboxed probe for MCP server
  drift belongs in the pre-publish test gate and must be runnable on demand)
- #22: add the `/production-readiness-audit` slash command (the last static gate
  before dry-run should run on demand, not only when the model chooses it)
- #23: add the `/delegate-to-mcp-server` slash command (the MCP server ships on
  its own cadence, so syncing with it must be run deliberately and periodically)
- #24: add the `/compact-dev-environment` slash command (with 500+ files under
  `specs/`, consolidation has to be triggered rather than hoped for)
- #25: add the `/review-invariants` slash command (walking the deferred
  invariant blocks is an interactive, deliberately started session)
- #26: add the `/unattended-spec-loop` slash command (a long-running, explicitly
  started backlog loop needs a command entry point)
- #27: add the `/release` skill and command that bump the version, write the
  CHANGELOG entry and tag as one operation (manual releases let the changelog
  and tag drift apart, and downstream ports pull from tagged releases)
- #30: declare `fpdf2` as a test dependency and skip rather than fail without it
  (without it 41 tests failed as misleading assertion errors that read as
  product defects)
- #33: add CI that runs the suite with and without `fpdf2` on every pull request
  (nothing ran the tests, and both the `fpdf2` and stdlib-fallback renderer
  paths ship)
- #38: show new hard rules on the maintainer surface to the conformance check
  and defer four invariants (four durable guarantees landed with enforcing tests
  but no registered or deferred invariant)
- #39: pin the maintainer command set in `docs/development.md` against the
  shipped commands in both directions (the documented list had drifted, naming a
  nonexistent command and omitting real ones)
- #47: register INV-301 through INV-306 and close the 2026-09-14 review (six
  shipping, test-guarded rules had no invariant, so nothing bound future work to
  them)
- #49: rename `/feedback-to-specs` to `/feedback-to-issues`, filing GitHub
  issues in this repo only (feedback should become GitHub issues now that
  `specs/` is being replaced, and cross-repo routing belongs elsewhere)
- #50: add the `/implement-github-issue` command and gate issue closure on
  registering or deferring an invariant (the skill had no command, and
  guarantees had been shipping without invariants)
- #51: rename the loop to `/unattended-issue-loop` working only issues with an
  opt-in label (the `specs/` backlog was frozen, and unattended work across
  every open issue would skip needed judgment)
- #52: freeze `specs/` read-only and record the 2026-09-15 cutover (GitHub
  issues replace `specs/` as the tracking mechanism while its ledgers stay as
  record and live rules)
- #53: record the `specs/todo.md` triage and drop the stale pointer
  (re-measurement showed the ~219 open specs never existed and only `todo.md`
  was outside the ledgers)
- #54: make `/retrofit-from-public` file issues instead of writing into the dev
  tree (under the issue-driven workflow public-repo divergence should be tracked
  as issues, not applied directly)
- #55: add a Mermaid diagram of the repository and per-change flow to
  `docs/development.md` (nothing showed how the commands fit together across the
  parent and its child ports)
- #56: adopt Conventional Commits repo-wide with a `Refs` footer instead of the
  `#n` subject prefix (the spec-scoped `#n` convention no longer described any
  work once `specs/` froze)
- #58: record a Hold verdict in the ledger block rather than the spec file
  (issue-driven deferrals have no spec file, so the Hold verdict was
  unreachable)
- #59: make `pending_invariants.py check` and `sites` resolve sites across the
  repo and report what they could not verify (they resolved only under
  `plugins/` and printed a clean result while checking nothing)
- #60: retire `/implement-spec` with its skill and test anchors, keeping
  `list_specs.py` (`/implement-github-issue` superseded it, and INV-303 requires
  command and skill to go together)
- #63: register INV-308 and INV-309, closing the 2026-09-16 review (two
  shipping, guarded rules needed an address so a later contradiction is caught)
- #69: make `/production-readiness-audit` record findings as issues or in the
  ledger, never in `specs/` (it still wrote spec files into the archive the
  freeze guard rejects)
- #72: suffix the duplicate `invariant-review-2026-09-16` ledger heading (two
  identical headings made the done-iff-heading rule ambiguous and no guard
  caught it)
- #74: stop the reverse-contract gate discarding hard rules outside `plugins/`
  (its parser silently dropped every rule from the widened maintainer surface)
- #76: make `conformance.py` report the rules an audit record retires from the
  `--since-last-audit` range (a new audit record silently retired rules that
  were never examined)
- #77: make `pending_invariants.py sites` state its scanned corpus on every run
  (it scanned only `plugins/` for candidates and said so only when it found
  nothing)
- #78: make `/review-invariants` stop at the working tree instead of committing
  (it committed the most permanent change in the repo onto whatever branch was
  checked out, usually `main`)
- #79: add a review queue for amendments to already-registered invariants
  (amending a registered invariant had no marker, block shape or queue)
- #80: stop the INV-282 check reporting clean over lines it cannot reach (it
  compared a widened `since` set with a `plugins/`-only set, so
  maintainer-surface rules could never match)
- #83: make `reverse-check` report the untested span's citation rate (NOT CLEAN
  had become the normal verdict for maintainer-surface work even when nothing
  was wrong)
- #88: publish a machine-readable invariant manifest per release (downstream
  ports need an authoritative list of invariant IDs and statuses to build their
  disposition registers)
- #90: correct `docs/development.md`, which said not to run
  `/unattended-issue-loop` (its audit half had been fixed in #69, so the warning
  blocked a working command)
- #91: correct the INV-308 disclosure in `test_review_invariants_queue.py` to
  its actual coverage (later guards had closed the gap it still claimed was
  open)
- #92: separate files ineligible as citation sites from merely unscanned ones in
  `sites` (59% of the unscanned count was the frozen archive, overstating the
  actionable gap)
- #96: widen the comment-pointer guard to every root and fold in the second
  guard (stale test pointers under `tests/` or `.claude/` were unguarded)
- #97: pin `citations.py verify`'s statement of what it does not check (deleting
  that statement would have broken no test)
- #105: make `pending_invariants.py` read an `Enforced by` clause that wraps
  across lines (a wrapped clause was invisible and reported as no enforcer
  named)
- #106: hold every issue-filing instruction to the ask-before-filing gate beside
  it (the gate shipped in three commands and was registered as an invariant in
  none)
- #108: make `conformance.py` state its scanned corpus and count what ships
  outside it (a zero result did not say it never looked where a rule was added,
  e.g. `docs/`)
- #110: make `parse()` read every rule bullet or report it as unparsed
  (older-shape bullets were silently dropped, misrepresenting a block's rules)
- #111: adopt `docs/FAMILY_WORKFLOW.md` as the normative cross-repository
  workflow, rules R1-R12 (the family of repositories needed one home for the
  shared workflow so children link rather than restate)
- #112: mandate one supersession syntax and derive manifest status from a bullet
  (33 invariants had `status: unclear`, so child ports could not tell what was
  still in force)
- #113: move `list_specs.py` beside the tests that consume it (an orphaned spec
  enumerator in the maintainer command surface implied the retired mechanism
  still lived)
- #114: make `/delegate-to-mcp-server` file GitHub issues instead of spec files
  (it was the last command still writing into the frozen `specs/`, so it could
  not be run)
- #117: record the R8 and R12 amendments in `docs/FAMILY_WORKFLOW.md` itself
  (the page carried no amendment record, so a child could not tell those rules
  had moved)
- #119: require `implement-github-issue` with no argument to report dependencies
  and a suggested order, amending R8 (the maintainer's choice of issue should be
  informed rather than blind)
- #122: stop one word in INV-216's correction flipping it to `status: unclear`
  in the manifest ("superseded" in an unrelated phrase matched the supersession
  pattern)
- #124: make `implement-github-issue` name the issue it suggests and stop,
  amending R8 (ending on "which issue?" after recommending one forced a needless
  extra turn)
- #126: bring the in-repo `implement-github-issue` skill up to R8 (its copy had
  diverged from the user-level one and lacked #119 and #124)
- #128: share one rules block between both `implement-github-issue` copies and
  detect drift (the two copies kept diverging with nothing to notice)
- #134: point Module 7 Step 2 at the factory-lifetime rule (INV-152) (writing
  several query programs is exactly when a shared engine helper breaks that
  rule)
- #135: warn in `/dry-run` that a host `PostToolUse` Markdown hook fights the
  walk (host configuration causes friction for maintainers, though no bootcamper
  can meet it)
- #140: register INV-313 through INV-316 and name `check-skill-drift` in the
  family workflow (a normative page omitted a parent operation, so a child could
  reuse its name)
- #141: retire R12's stale premise and re-arm the guard behind it (R12 claimed a
  minority of invariants were `unclear` when #112 had made it zero)
- #142: stop documenting writes into the frozen `specs/` archive, such as
  `specs/RENUMBERING.md` (INV-307 forbids new files there, so following the
  procedure turned the suite red)
- #143: name the `Partly superseded by:` marker in R12 and publish it in the
  manifest (it is used six times but neither R12 nor the schema gave child ports
  a form for it)
- #149: stop calling bare-globalization `search_docs` hits a stub in Module 5
  (the server's results improved, so the anti-pattern had inverted into a false
  alarm)
- #150: stop saying `search_docs` has no evaluation record-limit figure in
  Module 2 (the server now answers it, so the shipped absence claim was wrong)
- #151: flag positive universals over results as a census in
  `coverage_reports.py` (a universally quantified rationale is as fragile as a
  count across index rebuilds)
- #152: stop the dry-run scaffold banner claiming an unreachable recap-PDF chip
  clip (following its stated sequence could not exercise the clip with that
  fixture)
- #153: make `/dry-run` draft findings into the ledger and file issues, not
  specs (it was missed in the freeze rework and still wrote into frozen
  `specs/`)
- #154: audit every multi-record entity's how state in Data processing Phase D
  (validation passed entities that `howEntity` reported as needing
  re-evaluation)
- #155: store no record count when the volume question gets a bare option reply
  (the option number was passed as `record_count`, selecting the demo loader for
  a production tier)
- #156: scope Phase C's no-hand-written rule to SDK calls (no MCP route returns
  a multi-source orchestrator, so the rule could not be met)
- #157: reconcile the load count in two stages, collected file then working
  sample (comparing against the collected file made every sampled source an
  unexplained delta)
- #158: check PERSON-typed records for organization names in Module 5 (mistyped
  CORD ICIJ officer records silently block matches the quality assessment cannot
  see)
- #159: compare legend combination rows in the graph encoding self-check
  (counting per-source legend rows false-alarmed on a capped real-data graph)
- #160: state how to split a match key before counting suppressors (relationship
  keys carry roles and escaped hyphens that the obvious split misreads)
- #161: name a shared Java class's file after the class (the snake_case,
  package-private rule fails to compile once other files use the class)
- #162: put the volume question's framing before its 👉 pointer (the pinned block
  broke the rule that informing text precedes the question)
- #163: key the SQLite pre-load heads-up on the loadable record total (it fired
  on the production tier rather than on the data about to be loaded)
- #164: stop Phase C re-opening the settled SQLite load-size decision (an
  unguarded note re-asked a settled question with an unsourced 1,000-record
  threshold)
- #165: choose Phase B's first source by Step 14's load-order heuristics (no
  rule picked the first source, so the heuristics never applied where they
  matter most)
- #166: pin Module 7's teardown-gate step, relationship-cluster count and
  2-degree path method (the guide had to guess all three during the walk)
- #167: record an unanswered upstream offer as `offer pending` in feedback
  entries (the batched graduation offer left entries with placeholders or wrong
  values)
- #168: read the installed SDK version from SDK setup's progress record at
  graduation (the remote MCP server cannot know what is installed locally)
- #169: name an unsettled final state on the visualization How tab (it presented
  entities needing re-evaluation or with several virtual entities as built into
  one)
- #191: make `retrofit.sh` report every path instead of stopping at the first
  diff (`set -e` with `pipefail` aborted the script exactly when there was
  something to report)
- #192: ask the EULA question in Module 2 before installing anything (the SDK
  was installed before the Bootcamper accepted the license, contradicting the
  update path)
- #193: state `JSON_DATA`'s flag requirement instead of calling it
  `get_record`-only (the server now serves it on entity, find, why and search
  calls)
- #194: route update commands and 4.x upgrades in Module 2 to `search_docs` (the
  server now documents both, so the absence claims were wrong)
- #195: describe a gated `reporting_guide` reply as carrying no content (the
  server now omits the content arrays rather than returning them empty)
- #196: replace the fixed `why_*` composite defect as Module 7's worked example
  (the server defect no longer reproduces)
- #197: report an unreachable `access_steps` example instead of treating an
  elided retrieval as failed (`find_examples` now elides content deliberately
  and rewords its step-3 note)
- #198: make `get_stats` the empty `response_schemas` example and read the
  license limit from `recordLimit` (the server now documents `get_version` and
  `get_license`)
- #199: scope Module 2's macOS `SUPPORTPATH` literal to cask 4.4.x (the server
  says the literal has drifted and must not be pinned)
- #200: restamp three MCP citations re-read at server 1.37.14 (they were
  accurate but stamped with old versions or the wrong response)
- #202: compare the public repo against the last-propagated tag in `retrofit.sh`
  (comparing against dev's current tree made unpropagated dev work read as
  public edits)
- #214: record the 2026-09-28 production-readiness audit, whose 16 findings
  became #214 to #229, in the ledger (it is committed alone so the next audit
  range starts there; the CORD-cap finding itself is not yet fixed)
- #215: let the user-level copies govern `unattended-issue-loop` and
  `implement-github-issue` (the loaded copies ran different procedures than the
  repo's copies, commands and tests described)
- #216: name in INV-314 what an unattended run may create without a per-record
  yes (the loop and implement skill post comments and issues unattended,
  contradicting "create nothing")
- #218: make every license reading an owner or an INV-300 pointer (#198's new
  procedure reached two of six sites, leaving four restating the old one)
- #219: point Module 3's `SENZ7426` relay at Module 2 Step 8 (it relayed a macOS
  `SUPPORTPATH` literal that holds for cask 4.4.x only)
- #220: apply a Module 5 retype decision at mapping steps 10 and 11 (#158's
  decision arrived at step 13, after the mapping had already been declared)
- #221: give Module 4 Step 8b's sample one role in Phase B's load reconciliation
  (#157 had cited it as both a sample and a subset limit, double-counting one
  decision)
- #222: read release notes before Module 2's update offer and state the
  existing-install and decline outcomes (the offer asked before its content
  existed, and two paths had no stated outcome)
- #223: state both closed `Upstream:` vocabularies and their mapping (INV-281
  assumed one vocabulary where the entry and issue sides used two that had
  drifted)
- #224: describe `/retrofit-from-public` as a report, not the retired copy into
  dev (its command, skill and `docs/development.md` still described behavior #54
  removed)
- #225: describe `download_resource`'s chunked inline reply with `offset` and
  stop naming removed dashboard tabs (two passages contradicted INV-234 and
  INV-155 after both changed)
- #227: name the governing invariant at the mis-cited sites (several new lines
  cited INV-311, INV-012 and others for rules they do not govern)
- #228: cite or defer the 16 uncited maintainer-surface hard rules
  (`reverse-check` found them citing nothing and named in no deferral)
- #231: re-cite the INV-065 sites to the rules that own identifier stripping
  (INV-065 registers the sanitized recap fixture, yet ~15 sites cited it for
  stripping)
- #232: report an empty how-state population as nothing to check (reporting
  "checked 0 of 0" as "no finding" is the pass-on-empty INV-265 forbids)
- #233: check the `.claude/` maintainer surface in the reverse-contract guard
  and demote four local instructions to prose (rules there were counted but
  never checked)
- #234: correct ten pieces of stale plugin text flagged by the 2026-09-28 audit
  (the audit found wrong or outdated wording in plugin files, a script comment
  and a test)
- #235: align the INV-132, INV-157 and INV-204 sites with the server, each with
  a guard (the three invariants no longer said what the server and plugin
  actually do)
- #236: make the deferral-quote test read rules through `parse()` (its own regex
  broke INV-315 and could miss three defect shapes)
- #237: record every Phase B subset choice in a per-source `load_subset` block
  (license-cap options 1 and 3 and the SQLite first-1,000 choice left nothing
  reconciliation could cite)
- #238: load each Phase C source from its `load_subset` record (the license cap
  and SQLite limit apply to the whole load, but later sources had no subset
  record)
- #239: define `implement-github-issue` and `unattended-issue-loop` only at user
  level, keeping repo rules in `.claude/skill-overlays/` (the maintainer decided
  a skill name is defined in exactly one place)
- #240: retire `/check-skill-drift` (once each skill name has one definition
  there is nothing left to compare)
- #241: state each same-name command's rules in its skill (when a skill and a
  command share a name the skill wins, so the command may never run)
- #257: replace stale counts with properties, widen the `specs/` freeze to every
  file and probe the layout tree by path (pinned counts drifted and the freeze
  and layout guards had gaps)
- #258: make `specs/README.md`'s "What stays live" table the parsed live-record
  list (the live records needed one authoritative, machine-checked list)
- #259: load each source's `load_subset` block in Phase C Step 19 (the step
  still loaded from the old markers, contradicting INV-325 and #221)
- #260: record the 2026-09-29 invariant review: INV-317 to INV-331, two
  amendments, six holds (the session's working-tree changes needed an
  issue-named branch to land on)
- #262: delete the ten same-name maintainer command files (each skill now
  carries its rules, so the commands were redundant definitions)
- #273: record the 2026-09-30 invariant review: INV-332 to INV-336, twelve
  amendments, two holds (the session's changes needed an issue-named branch to
  land on)
- #277: record the second 2026-09-30 invariant review: INV-337, INV-303's note,
  #164 re-held (the session's changes needed an issue-named branch to land on)
- #280: apply INV-307's dated correction from the third 2026-09-30 review (#258
  met the held amendment's revisit condition)
- #282: use one check list and one success rule in Module 3 (its three
  definitions of success disagreed and two contradicted INV-229)
- #283: map a retyped name as `NAME_ORG` and cite INV-336 in Module 5 (the
  template and citations disagreed with INV-336)
- #284: queue the EULA-before-install and existing-install rules for invariant
  review (Module 2 shipped both hard rules with no invariant recording them)
- #285: record audit findings where INV-317 allows instead of "never into
  `specs/`" (the audit skill contradicted the invariant it cited)
- #286: exclude `data/subsets/` at graduation and queue its INV-050 tree entry
  (the maintainer decided subsets are evaluation artifacts, yet neither list
  accounted for them)
- #287: give Module 2 Phase 3 a bindings route for every server language,
  including Rust (it omitted Rust and contradicted INV-222 on package managers)
- #288: retire "pending" wording for amendments the 2026-09-30 reviews applied
  (text and tests still described applied amendments as pending)
- #289: apply amended INV-132 at the Module 6 and Module 7 sites (they used the
  retired topic name and sent readers to local lookup before MCP)
- #290: cite the governing invariant at seven hard rules (each cited none or the
  wrong one, against INV-183)
- #291: point every live-record list at the `specs/README.md` table (two lists
  and a pinned spec count had drifted from it)
- #292: align Modules 5 and 6 with INV-335, the license-cap question and the
  listing-reply section (they restated rules that had since changed)
- #293: point graduation to ground-rules for the model-switch rule (its own copy
  had drifted from the one in ground-rules)
- #294: add INV-316 markers for `/order-github-issues` and `/escalate-to-parent`
  and an overlay for the former (maintainer documents named them with nothing
  saying where they are defined)
- #296: mark the remaining user-level command names and widen the INV-316 guard
  to skills and overlays (the guard scanned only two documents)
- #298: save each module's graduation-video B-roll to `docs/video/broll.json` at
  completion (graduation should read one manifest instead of reconstructing the
  bootcamp from memory)
- #299: add the bundled `generate_recap_video.py` renderer from a storyboard to
  an mp4 (the agent writes the content and a tested, deterministic script
  renders it)
- #300: add graduation Step 1c to offer, script and render the graduation video
  (bootcampers get a personalized two-minute video built from the B-roll and
  recap)
- #320: take the C# package source from the Windows `sdk_guide` install reply
  (the negative was asked only for Linux, so Windows bootcampers were told it
  was undocumented)
- #321: build `OPEN_ME_FIRST.md` from the package manifest's included list
  (static text promised a revisit bundle and file the archive might not contain)
- #322: cite `mapping_workflow` step 2 for the root-level payload key rule (the
  tool now documents the rule that Module 5 called observation-only)
- #323: wrap the two bare `MCP-NEGATIVE` markers in HTML comments (maintainer
  metadata rendered as body text in shipped skills)
- #324: give `generate_document_pdf.py` its own help text and subtitle (its
  usage example put the discoveries subtitle on another document's cover)
- #325: write the data-source registry the copied orchestrator reads at
  graduation (the orchestrator copied into `production/` could not run without
  `config/data_sources.yaml`)
- #326: keep name-bearing screenshots, such as Merge Statistics and Search /
  Probe, out of the graduation video (the video must hold aggregates only, yet
  those tabs show customer names)
- #327: state the cap in the Entity Graph notes on a capped payload (the
  relationship-mode note reported the capped subset as the whole population)
- #328: let the environment script load before Step 8 writes
  `config/engine_config.json` (Steps 4 to 7 could not source it on a fresh
  project, and its error blamed path resolution)
- #329: record `database_type` before Step 7's database branches (placed after
  the PostgreSQL branch, the rule was never reached on the SQLite path)
- #330: use Module 6's SQLite threshold in Data collection Step 8b (its
  "load-time threshold" was undefined, with three sourced numbers giving
  different answers)
- #332: make visualizations refuse to render when the vendored D3 asset is
  missing, never falling back to a CDN (the modules and INV-091 contradicted
  each other, and a CDN fallback breaks the offline guarantee)
- #333: align Module 5's mapping prose with server 1.37.16 (four instructions
  were stale or misplaced on a walk, including a per-source loading gate)
- #334: name the current model family and an effort proxy in the model/effort
  nudge (the table named superseded models and the unreadable-effort fallback
  had nothing to fall back to)
- #335: record measured `search_docs` routes for what Modules 0 and 1 teach (the
  recorded queries missed content the steps must teach, so the guide composed
  its own)
- #336: ask the shared-feature collision question only when sameness is unclear
  (it fired on every parsed-versus-full or renamed-but-identical field pair)
- #337: offer a return to Data collection when the 70-79% quality gate has
  nothing left to fix (the gate re-offered a dead "improve" option, and its only
  exit had no question or procedure)
- #338: save each source's Module 5 sample to `data/mapping/` (samples in
  `data/senzing-ready/` were counted as loadable and demanded a mapper doc)
- #339: add a loudness-normalized stereo mix with a synthesized, ducked music
  bed to the recap video (the video needed an audio track, reporting voice and
  music separately so music alone never reads as narration)
- #340: tell the Bootcamper per platform how to get a voice when the recap video
  rendered without one (they should never have to ask why there is no sound)
- #341: narrate the recap video with a local Piper neural voice after a one-time
  install offer (the `espeak-ng` narration sounded robotic and unprofessional)
- #342: record measured `search_docs` routes for the pattern gallery's other
  sources (INV-212 and INV-291 require measured routes, yet three documents had
  none)
- #343: give each generated entity its own identifiers in synthesized data
  (generated people could share name and email and be correctly merged, reading
  as false merges)
- #345: define where Step 8b's SQLite load-time marker lives and record the
  loadable total in it (Module 6 could not reliably find the decision it must
  not re-ask)
- #347: open the graduation video on an intro scene naming the Bootcamper and
  date (the reporter asked for a 3% intro, since the video started straight on
  Bootcamp preparation)
- #372: level the voice before the mix so a voiced recap video reaches -16 LUFS
  (voiced mixes measured -17.6 to -17.9 LUFS because loudnorm hit the true-peak
  ceiling)
- #377: fix four stale documentation lines noticed during the 2026-10-01 runs
  (each was out of scope for the issue that noticed it)
- #379: restamp the Module 0 primer's routes on the 2026-10-02 index (the index
  now returns the MDM FAQ answer at a different rank)
- #381: narrow Module 2's existing-install announcement to the install (it
  announced the skip to verification that INV-339 forbids)
- #382: state INV-091's full refusal in Module 3b and caption the inert tab (the
  Truth Set server steps gave only the no-CDN half and still offered omitting a
  tab)
- #383: stamp and rank every inline `search_docs` route a step depends on
  (INV-291's 2026-10-02 note binds inline routes that nothing had stamped or
  ranked)
- #384: return every Module 5 Phase 3 exit to the per-source loop (a test load
  on one source had no path back to the remaining sources)
- #385: write `license_record_limit` with its INV-295 measured-at marker in
  Module 4 (two write sites omitted it and the guard was file-scoped)
- #386: leave `specs/` frozen in `/compact-dev-environment` and route invariant
  changes to `/review-invariants` (it still archived and deleted specs and
  routed merges to a command that cannot mint)
- #387: state the documented `WHY_KEY_DETAILS` flag requirement in Module 7 Step
  3a (it said no flag was documented, contradicting the plugin's other sites)
- #388: point three Module 7 references at the step and state that own them
  (they named the wrong step or state nothing writes)
- #389: name Data collection in the welcome's licensing bullet (the welcome said
  SDK setup walks through licensing, contradicting INV-093)
- #390: resolve graduation's screenshot remedy to the bundled
  `capture_screenshots.py` (a bare name fails from the project, and the INV-185
  guard was narrower than the rule)
- #391: give hand-run Windows commands a PowerShell 5.1 form (license apply,
  recap render, the return guide and the database backup failed there)
- #392: give Module 7's return to Data Quality, Mapping and Transformation a
  receiving route (the offered option had no resume step, against INV-284)
- #393: apply INV-340 at three graduation-video sites (one cited the wrong
  invariant and others called the video narrated unconditionally)
- #394: defer the synthesized-source disclosure rule as an invariant (Module 5
  shipped it as a hard rule that no invariant recorded)
- #395: make `/auto-test` record findings before fixing them and name Phase 6
  (it restated dry-run's rules fix-first, against INV-317, and the overlay and
  guard had drifted)
- #396: send Module 5 test runs to `data/mapping/` and write the full output to
  `data/senzing-ready/` (partial runs had no output path and no step wrote the
  full output)
- #397: fix eight small coherence and concision drifts in Modules 1, 3b and 4,
  graduation and the install page (each was confirmed at its site as stale or
  redundant)
- #417: re-measure the 15 search-route records stamped before the 2026-09-24
  index rebuild (#383 found a record from that era had gone stale)
- #418: give the last two line-reading guards their wrap-aware verdicts (three
  guards in one audit round missed phrases wrapped across lines)
- #419: replace `senzing-env.bat` with a dot-sourced `senzing-env.ps1` (a `.bat`
  run from PowerShell sets variables in a child `cmd.exe` that never reach the
  session)
- #420: give graduation Step 1c's recap venv a Windows form (on Windows
  `python3` is often a Store stub or absent)
- #421: draft an INV-207 note naming the Phase 6 section (the invariant still
  named a Step 4 that no longer exists)
- #422: state the full output's `file_path` write once, at Step 18 (Step 17
  conditioned it on a file Step 18 now always writes, two sites for one write)
- #423: re-point two guards at the rules that ship now (their assertions and
  docstrings described rules that had changed)
- #424: make `plugins/` guards match their phrases across line wraps
  (single-line reading let a wrapped sentence slip past them)
- #425: make maintainer-skill and docs guards match their phrases across line
  wraps (single-line reading let a wrapped sentence slip past them)
- #426: add the shared wrap-aware matcher `tests/_wrapped_text.py` and move
  #387's guard onto it (the wrap sweeps needed one matcher, one candidate scan
  and one drafted invariant)
- #438: fail the suite when a line-reading test gives no INV-346 verdict (#419
  added a test with no verdict, which only a hand-run scan caught)
- #439: replace Module 4 Step 8b's stale nearby-wordings warning (that phrasing
  now returns the Hardware Sizing FAQ at rank 1)
- #440: correct three Module 5 descriptions of the Entity Specification's
  structure (they no longer matched what `search_docs` serves)
- #446: add `BLUEPRINT.md`, written by `/create-blueprint` (nothing described
  the project in one transportable file for `/update-blueprint` and
  `/verify-blueprint` to work from)
- #449: name the dev marketplace `senzing-bootcamp-dev` and rewrite it back on
  propagation (one name with two sources kept the dev repo from being added
  where the published plugin was installed)
- #452: move the GitHub Pages quick-start site into dev's `docs/` and rewrite
  `.html` and `.css` on propagation (the site existed only in the public repo,
  so every propagation would have deleted it)
- #466: name Claude Desktop in `README.md`'s plugin-install note (it said
  "Claude App", which INV-158 retires, so the suite was red on `main`)
- #448: read the CORD `download_url` cap from the response and treat a
  truncated source's count as a floor on the uncapped route (Module 4 still
  stated a 10,000 cap after #214 closed without its fix)
- #461: name every container Module 2 creates from its project with
  `docker_lifecycle.py container-name`, and pick PostgreSQL's host port with
  `free-port` (a fixed `senzing-bootcamp` name collided across two bootcamp
  projects, and the hooks find containers by exact name)
- #455: compare the Pages site's `claude plugin …` commands with
  `docs/README.md`'s, as sets, in a new test (the page repeats the README's
  install commands, and nothing checked that it followed them)
