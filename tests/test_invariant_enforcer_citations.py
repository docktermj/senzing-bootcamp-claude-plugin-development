"""An invariant that names its enforcing test must be cited back by that test.

`INVARIANTS.md` rule 3 binds a new invariant to an index entry, and
`tests/test_invariants_index.py` fails when that stops being true. Nothing bound an
invariant to the **test it names as its enforcer** — *"`tests/test_brand_sync.py` enforces
this and MUST pass"* — so the citation was a convention with no enforcement. Measured
2026-08-12: **11 of 22** such pairs had no back-citation.

That is not a docstring nicety. `.claude/skills/dry-run/coverage_reports.py invariants` is
the repo's only signal for *"this rule has no guard"*, and it keys on the ID appearing
**anywhere** under `tests/`. A missing back-citation is therefore scored one of two wrong
ways:

* **False alarm** — the invariant reads as unguarded while a dedicated test enforces it,
  sending a future audit to build a guard that already exists (5 of the 11).
* **False all-clear** — an unrelated file mentions the ID in passing, so the invariant reads
  as covered and the gap becomes undiscoverable (6 of the 11). INV-183's five "citations"
  were all *rationale* references — *"a rule deliberately restated at the step it governs is
  INV-183"* — and none was in the test INV-183 names.

The false all-clear is why this test exists rather than a report: `production-readiness-audit-2026-08-11`
finding (3) recorded three of these as "three docstring lines", nothing failed while it went
undone, and by 2026-08-12 all three were still missing with one of them newly masked.

⛔ **Never satisfy this test by deleting an unrelated mention.** Those references are
legitimate and are the reasoning the repo wants recorded. The fix is always the missing
citation, never the removal of a correct one.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
TESTS = REPO_ROOT / "tests"

#: One invariant entry: "- **INV-nnn** — body", to the next entry or heading.
ENTRY = re.compile(r"^- \*\*(INV-\d{3})\*\* — (.+?)(?=\n- \*\*INV-|\n##|\Z)", re.M | re.S)
#: A test file named inside an invariant's text.
NAMED_TEST = re.compile(r"tests/(test_[a-z0-9_]+\.py)")

#: Invariant->test pairs found on 2026-08-12, when all 11 gaps were closed. Counts PAIRS,
#: not invariants: one invariant may name several tests, and one test may be named by
#: several invariants (test_model_guidance_sync.py serves INV-114 and INV-140). A pinned
#: literal, derived by running the extractor -- not copied from the spec.
#:
#: 22 -> 23 on 2026-08-12: INV-205 was recorded naming
#: tests/test_tool_directives_do_not_override_interaction.py as its enforcer. Re-derived by
#: running the extractor, not incremented to make the assertion pass -- and the same session
#: that added INV-205 was caught by this guard for omitting the back-citation, which is the
#: whole reason the pair count is pinned rather than computed.
#:
#: 23 -> 24 later the same day: INV-206 (an MCP payload example must be one that was executed
#: successfully) names the SAME file, so one test file now serves two invariants -- the case
#: the "counts PAIRS, not invariants" note above exists for. Re-derived by running the
#: extractor. This guard fired again, on the same omission as last time: INV-206 was recorded
#: before its enforcer cited it back. Twice in one day is the argument for the pin.
#:
#: 24 -> 25 on 2026-08-13: INV-207 (a claim about the repo's own reference graph is verified
#: AFTER it is recorded) names tests/test_spec_ledger_invariants.py. Re-derived by running
#: the extractor. Third consecutive new invariant, and the first where the back-citation was
#: written before this guard had to ask for it.
#:
#: 25 -> 26 on 2026-08-13 (dry run, phase 1): INV-208 (the plugin names no license-path
#: environment variable in any spelling) names tests/test_license_env_var_absent.py, which
#: cites INV-208 back. Re-derived by running the extractor. Fourth consecutive new invariant;
#: this time the guard DID fire -- the pair was complete but the pin was not moved, which is
#: the arithmetic half of the check rather than the missing-back-citation half.
#:
#: 26 -> 27 on 2026-08-13 (dry run, follow-up): INV-209 (an MCP-NEGATIVE marker names the
#: route that OWNS the fact) names tests/test_dated_negatives_are_marked.py, which cites
#: INV-209 back in `test_every_marker_names_the_route_that_owns_the_fact`. Re-derived by
#: running the extractor. Note INV-208 and INV-209 are the same defect at two altitudes --
#: the wrong claim, and the convention that let it look reviewed -- so the pair count grew
#: twice for one root cause.
#:
#: 27 -> 28 on 2026-08-13 (dry run, implementing the viz-settings spec): INV-210 (a script
#: taking config from several sources picks by CONTENT and validates before acting) names
#: tests/test_viz_settings_resolution.py, which cites INV-210 back. Re-derived by running
#: the extractor.
#:
#: 28 -> 29 on 2026-08-13 (dry run, implementing the reassurance spec): INV-211 (anything
#: informing an answer precedes its 👉) names tests/test_reassurance_precedes_question.py,
#: which cites INV-211 back. Re-derived by running the extractor.
#: 29 -> 30 on 2026-08-13 (dry run, implementing the pattern-gallery spec): INV-212 (a step
#: that retrieves bootcamper-facing content carries a retrieval strategy) names
#: tests/test_pattern_gallery_shortfall.py, which cites INV-212 back. Re-derived by running
#: the extractor.
#:
#: 30 -> 31 on 2026-08-13 (dry run, follow-up): INV-213 (a spec asserting server absence names
#: the owning route) names tests/test_spec_absence_claims_name_their_owner.py, which cites
#: INV-213 back. Re-derived by running the extractor. INV-209 and INV-213 are one rule at two
#: altitudes -- shipped prose, and the spec that is the input to implementation.
#:
#: 31 -> 32 on 2026-08-13 (dry run, final spec): INV-214 (a verbosity preset governs form as
#: well as kind) names tests/test_minimal_verbosity_scope.py, which cites INV-214 back.
#: Re-derived by running the extractor.
#:
#: 32 -> 33 on 2026-08-13: INV-216 (the candidate set is computed and subtracts DECLINED.md)
#: names tests/test_list_specs.py, which cites INV-216 back. Re-derived by running the
#: extractor. Arose from a process failure rather than a spec: a hand-computed listing
#: re-offered a declined spec.
#:
#: 33 -> 41 on 2026-08-14: eight invariants recorded in one batch, each naming the guard
#: written with it and cited back by that guard. Re-derived by running the extractor, not
#: by adding eight to the previous figure.
#:   INV-222 -> test_no_pip_install_senzing.py                    (SDK is not a pip package)
#:   INV-223 -> test_viz_server_process_handle.py                 (stop a server by pid)
#:   INV-224 -> test_answer_options_render_below_the_question.py  (options beneath the 👉)
#:   INV-225 -> test_non_yielding_steps.py                        (a step with no 👉)
#:   INV-226 -> test_recap_header_is_owned.py                     (update needs a creator)
#:   INV-227 -> test_resume_requires_a_recorded_module.py         (resume on content)
#:   INV-228 -> test_truthset_download_is_the_dataset.py          (verify the written count)
#:   INV-229 -> test_results_validation_is_diagnostic.py          (diagnose, do not grade)
#:   INV-230 -> test_truth_set_spelling.py                        (prose vs identifier)
#:   INV-231 -> test_internal_connection_string_rejected.py       (no in-memory CONNECTION)
#:   INV-232 -> test_capture_suppressed_tabs.py                   (suppressed tab, no shot)
#:   INV-233 -> test_end_the_turn_questions_exist.py              (the 👉 must exist)
#:   INV-234 -> test_download_resource_is_a_listing.py            (a listing, not content)
#:   INV-235 -> test_capture_single_page.py                       (label what you captured)
#:   INV-236 -> test_post_yes_switch_reads_the_dial.py            (read the dial, then reply)
#:   INV-237 -> test_java_filename_class_reconciliation.py        (package-private, not renamed)
#:   INV-238 -> test_completeness_denominator.py                  (0/0 is undefined, not 0)
#:   INV-239 -> test_synthesized_scenario_has_quality_gaps.py     (generated data can fail)
#:
#: 51 -> 53 on 2026-08-14, on maintainer review of the same batch: two invariants were split
#: so each states one condition, and both share the enforcer of the invariant they came from --
#: the "one test may be named by several invariants" case again. Re-derived by running the
#: extractor, not by adding two.
#:   INV-240 -> test_download_resource_is_a_listing.py            (state the rule, not the token)
#:   INV-241 -> test_capture_single_page.py                       (assert content, not a proxy)
#:
#: 53 -> 56 on 2026-08-14, across an unattended /implement-spec run of six specs. Three new
#: invariants, each naming the guard written with it and cited back by that guard. Re-derived
#: by running the extractor at each step, not incremented -- and this guard fired on the first
#: two of the three, both times because the pin was not moved rather than because a
#: back-citation was missing, which is the arithmetic half of the check.
#:   INV-242 -> test_recap_pdf_bulleted_images.py                 (state the shape a script parses)
#:   INV-243 -> test_module06_orchestrator_guidance.py            (reconcile a per-source figure)
#:   INV-244 -> test_module06_license_reconciliation.py           (absence is not a measurement)
#:
#: 56 -> 57 on 2026-08-14, on maintainer review of that run: INV-243 was split so each entry
#: states one condition, and the extracted half shares the enforcer of the invariant it came
#: from -- the "one test may be named by several invariants" case again, and the same split
#: shape as INV-234 -> INV-240. Re-derived by running the extractor, not by adding one.
#:   INV-245 -> test_module06_orchestrator_guidance.py            (do not print a disproved figure)
#:
#: 57 -> 58 on 2026-08-14, on the same review: INV-242's guard was widened from one site to every
#: Markdown surface a bundled generator parses, so the invariant now names a SECOND enforcer --
#: one invariant naming several tests, the other half of the "counts PAIRS" note above. The
#: widened guard found a real breach the narrow one could not see. Re-derived by running the
#: extractor.
#:   INV-242 -> test_authored_shapes_are_stated.py                 (state every parsed shape)
#:
#: 58 -> 59 on 2026-08-14, implementing the audit's own findings: INV-246 (a multi-site guard
#: derives its site set by scanning, never by hardcoding paths) names
#: tests/test_module06_license_reconciliation.py, which already enforced INV-244 -- so that file
#: now serves two invariants. Re-derived by running the extractor. The rule exists because a
#: hardcoded two-path list in that very file certified two sites and was blind to the third.
#:   INV-246 -> test_module06_license_reconciliation.py            (derive the site set)
#:
#: 59 -> 60 on 2026-08-15: INV-247 (every 👉 question traces to a step in a shipped skill file;
#: no session- or host-level control is offered as a bootcamp question) names its new guard,
#: tests/test_no_host_control_is_offered_as_a_question.py. Re-derived by running the extractor.
#: Note what that guard's own docstring says: it covers the shipped half only. The reported
#: defect was a question improvised at runtime that exists in no file, so the pair records an
#: enforcer of the rule, not a detector of the symptom.
#:   INV-247 -> test_no_host_control_is_offered_as_a_question.py   (close the question set)
#:
#: 65 -> 66 on 2026-08-16: INV-253 (US English is the only spelling written in this
#: repository) names its new guard, tests/test_us_english_spelling.py. Re-derived by
#: running the extractor. ⚠️ That guard's vocabulary is hardcoded and cannot be otherwise —
#: the corpus is what is being judged — so the pair records an enforcer of the rule, not a
#: detector of every breach of it.
#:   INV-253 -> test_us_english_spelling.py                        (the house spelling)
#:
#: 66 -> 73 on 2026-08-16: the bootcamp-notes feature registered five invariants
#: (INV-254..INV-258), two of which name two enforcers each — INV-254 is split between the
#: hook's trigger vocabulary and the shipped flow's prose, and INV-258 between the Markdown
#: fold at graduation and the rendered PDF. Re-derived by running the extractor.
#:   INV-254 -> test_feedback_capture_triggers.py, test_bootcamp_notes_flow.py
#:   INV-255 -> test_bootcamp_notes_flow.py                        (the 📌 banners)
#:   INV-256 -> test_bootcamp_notes_flow.py                        (append, then verify)
#:   INV-257 -> test_bootcamp_notes_flow.py                        (their words stay theirs)
#:   INV-258 -> test_bootcamp_notes_flow.py, test_recap_notes_section.py
#:
#: 73 -> 76 on 2026-08-17: the production-readiness audit found seven hard rules shipped
#: with no invariant in one unattended run; the maintainer approved three invariants for
#: them (INV-259 graph source encoding, INV-260 viz bind/identity, INV-261 cross-source
#: join predictions), each naming the guard that already existed for its rule. Re-derived
#: by running the extractor.
#:   INV-259 -> test_graph_colors_by_source_combination.py    (color by the source SET)
#:   INV-260 -> test_viz_server_bind_and_identity.py          (loopback + identity probe)
#:   INV-261 -> test_group_score_is_not_a_join_prediction.py  (measured or unmeasured)
# 80 as of 2026-08-21: INV-262, INV-263 and INV-264 were registered at the maintainer's
# sign-off, and INV-052's dated verification note now names
# `test_hook_entries_name_a_script.py` as its enforcer. Re-derived by running the extractor,
# not relaxed. (datastore mount-crossing measurement) was registered at the
# maintainer's sign-off and names `test_datastore_mount_crossing_is_measured.py`. Re-derived
# by running the extractor, not relaxed.
# 82 as of 2026-08-23: INV-266 names `test_generated_scenario_marker_drop_is_exempt.py` as its
# enforcer. INV-265 and INV-267 were registered in the same edit and name no test in their own
# text — their guards cite them rather than the reverse — so they add no pair here. Re-derived by
# running the extractor, not relaxed.
# 85 as of 2026-08-27: INV-269, INV-270 and INV-271 each name their enforcer
# (`test_env_script_names_every_required_export.py`, `test_encoding_self_check_is_stated_as_behavior.py`,
# `test_expected_visualization_denominator.py`), and each of those tests now cites the invariant
# back. INV-268 was registered in the same edit and names no test in its own text — its rule is
# guarded through `test_why_key_details_flag_claim_is_withdrawn.py`, which is not an "Enforced by"
# claim — so it adds no pair here. Re-derived by running the extractor, not relaxed.
# 89 as of 2026-08-27 (second registration pass): INV-272, INV-273, INV-274 and INV-275 each name
# their enforcer and each of those tests now cites the invariant back. INV-273 and INV-274 share
# one enforcer (`test_sourcing_reaches_beyond_technical_facts.py`), so they contribute two pairs
# against one file. Re-derived by running the extractor, not relaxed.
# 90 as of 2026-08-27 (third registration pass): INV-276 names its enforcer
# (`test_undecodable_recap_is_never_overwritten.py`) and that test cites the invariant back.
# One invariant, one test, one pair. Re-derived by running the extractor, not relaxed.
# 97 as of 2026-08-28 (the six deferred invariants signed off in one pass): INV-277 through
# INV-282 each name their enforcer and each of those tests now cites the invariant back.
# Six invariants, SEVEN pairs — INV-282 names two enforcers
# (`test_license_limit_is_written_only_from_a_measurement.py` and
# `test_new_hard_rules_are_cited_or_deferred.py`), because it governs how both derive their
# matchers. Re-derived by running the extractor, not relaxed.
# 101 on 2026-09-01: INV-285 (a provenance label covering several independently-moving
# facts is stated per fact) names `test_build_version_provenance_is_per_platform.py`, and
# that test now cites INV-285 back. One invariant, one test, one pair. Re-derived by
# running the extractor -- this guard fired on the omission before the back-citation was
# added, which is the pin doing its job at the first registration after it was pinned.
#
# ⚠️ 2026-09-02: INV-287 was registered naming NO enforcer and was written up here as
# adding no pair. That comment then hid it: `coverage_reports.py invariants` counts any
# test mentioning an id as coverage, so the one invariant with no guard was the one its
# gap report did not list. INV-287 is now enforced by
# `tests/test_checklist_items_ship_their_exceptions.py` and DOES add a pair.
# 102 on 2026-09-01: INV-286 (a question whose options are complements is asked as a
# multi-select and every chosen option recorded in full) names
# `test_question_options_render_beneath.py`, which now cites INV-286 back. One invariant,
# one test, one pair. Re-derived by running the extractor.
# 103 on 2026-09-02: INV-288 (a fence's span never extends past the next opening marker
# of its own type) names `test_recap_checkpoint_is_lifted_before_module_parsing.py`,
# which now cites INV-288 back. One invariant, one test, one pair. Re-derived by running
# the extractor. INV-287, registered the same day, adds no pair: it names no enforcer,
# deliberately and says so in its own text.
# 104 on 2026-09-02: INV-289 (reuse by instruction names its scale dependence) names
# `test_visualization_model_build_scales.py`, which now cites INV-289 back. Re-derived by
# running the extractor.
# 105 on 2026-09-02: INV-290 (two sources reporting one environment fact are resolved by
# the cause of their disagreement) names
# `test_version_precedence_handles_an_unmanaged_install.py`, which now cites it back.
# Re-derived by running the extractor.
# 106 on 2026-09-02: INV-291 (a retrieval query a step depends on is measured before it
# ships) names `test_module_0_suggested_queries_are_measured.py`, which now cites it back.
# Re-derived by running the extractor.
# 107 on 2026-09-02: INV-292 (prefer the programmatic route; a refusal is not a throttle)
# names `test_cord_fetch_has_a_403_remedy.py`, which now cites it back. Re-derived.
# 108 on 2026-09-02: INV-293 (a provider's disclosure obligation binds every acquisition
# path) names `test_cord_is_disclosed_as_real_data.py`, which now cites it back.
# Re-derived.
# 109 on 2026-09-02: INV-294 (structure is classified by contents, never by name) names
# `test_coverage_check_looks_inside_root_arrays.py`, which now cites it back. Re-derived.
# 110 on 2026-09-02: INV-295 (a measurement records when it was taken) names
# `test_license_limit_reading_is_complete.py`, which now cites it back. Re-derived. This
# closes the 2026-09-02 review: nine deferrals decided, EXPECTED_PAIRS 100 -> 110 across
# it, every step re-derived rather than incremented.
# 111 on 2026-09-02: INV-287 gained an enforcer after all —
# `test_checklist_items_ship_their_exceptions.py` — closing the one invariant this
# review registered unguarded. Re-derived by running the extractor.
# 113 as of 2026-09-02: INV-296 and INV-297 were registered from
# `proceed-on-sqlite-keeps-the-tier-s-thread-count`, each naming
# tests/test_loader_concurrency_reads_database_type.py as its enforcer.
# 114 on 2026-09-03: INV-300 (a single-statement claim names its authority) names
# `test_a_single_statement_claim_names_its_authority.py`, which cites it back. Re-derived by
# running `pairs()` and reading its length — 114, with the new pair confirmed present by
# name — not by incrementing 113.
# 116 on 2026-09-14: INV-301 (a release moves every version record or none) names TWO
# enforcers — `test_release_bumps_version_changelog_and_tag_together.py` and
# `test_release_covers_every_version_site.py` — and both cite it back, so one invariant
# contributes two pairs. Re-derived by running the extractor and reading its length,
# which reported 116 with both new pairs present by name; 114 + 2 only confirms it.
# 118 on 2026-09-14: INV-302 (the maintainer command surface agrees with its docs in both
# directions) names TWO enforcers -- test_documented_dev_commands_match_the_shipped_set.py
# and test_dev_commands_name_a_real_skill.py -- and both cite it back. Re-derived by running
# the extractor, which reported 118 with both new pairs present by name.
# 119 on 2026-09-14: INV-303 (every command names a skill that resolves) names ONE enforcer,
# test_dev_commands_name_a_real_skill.py, which already cited INV-302 for the mirror
# direction and now cites both. Re-derived by running the extractor -- 119, with the new
# pair present by name.
# 120 on 2026-09-14: INV-304 (the propagate mirror never publishes .claude/) names
# test_maintainer_tooling_stays_out_of_public.py, which cites it back. Re-derived by
# running the extractor -- 120, with the new pair present by name.
# 121 on 2026-09-14: INV-305 (the fpdf2 CI matrix runs both cells and proves the absence)
# names test_ci_workflow_guards_the_fpdf2_matrix.py, which cites it back. Re-derived by
# running the extractor -- 121, with the new pair present by name.
# 122 on 2026-09-14: INV-306 (an optional dependency is declared and its absence skips)
# names test_fpdf2_dependency_is_declared.py, which cites it back. Re-derived by running
# the extractor -- 122, with the new pair present by name. This closes the 2026-09-14
# review: six deferrals decided, EXPECTED_PAIRS 114 -> 122 across it, every step
# re-derived rather than incremented.
# 124 on 2026-09-16: INV-307 (specs/ is a read-only archive) adds TWO pairs, not one. It names
# test_specs_are_frozen.py as its enforcer AND test_spec_ledger_invariants.py descriptively --
# the extractor matches any tests/ path in the body, which is why the jump is +2. Both cite it
# back, and the second one legitimately: that file's either/or acceptance of a Source citation
# is exactly what makes INV-307's deletion direction necessary, so a reader arriving at either
# guard needs the other. Re-derived by running the extractor -- 124, both pairs present by name.
# 125 on 2026-09-16: INV-308 (a verification tool reports what it could not verify) names
# test_review_invariants_queue.py, which cites it back. Re-derived by running the
# extractor -- 125, with the new pair present by name. Only +1, unlike INV-307's +2:
# this invariant names no second test file in its body.
# 126 on 2026-09-16: INV-309 (the issue path accounts for the rules it ships) names
# test_issue_command_gates_invariant_capture.py, which cites it back. Re-derived by
# running the extractor -- 126, with the new pair present by name. This closes the
# 2026-09-16 review: two deferrals decided, EXPECTED_PAIRS 124 -> 126 across it.
# 127 on 2026-09-16: INV-213's actor was clarified to the issue-driven path (#60), and the
# amendment names test_issue_path_reverifies_senzing_facts.py as the guard that now enforces
# it -- a SECOND enforcer for INV-213, alongside test_spec_absence_claims_name_their_owner.py
# which still guards the artifact end. Both cite it back. Re-derived by running the extractor
# -- 127. No id was minted in that review; the pair count moved because an existing
# invariant's body gained a test path, which is the first time that has happened.
# 128 on 2026-09-21: INV-310 (a permanent or append-only act on this repository's own records
# stops at the working tree) names test_review_invariants_stops_at_the_working_tree.py, which
# cites it back and states what it does NOT establish -- that no offline test can watch a run
# refrain from committing. Re-derived by running the extractor -- 128, with the new pair present
# by name. This closes the 2026-09-21 review: one deferral decided, EXPECTED_PAIRS 127 -> 128.
# 129 on 2026-09-22: INV-311 (a derived artifact published for downstream ports names its source
# and cannot drift from it) names test_invariant_manifest_matches_the_prose.py, which cites it
# back and states what it does NOT establish -- that a consumer reads the artifact correctly,
# which nothing in this repository can observe. Re-derived by running the extractor -- 129, with
# the new pair present by name.
# 130 on 2026-09-22: INV-312 (a command bringing another repository's changes into this one
# writes nothing and files issues instead) names test_retrofit_files_issues.py, which cites it
# back and states that the behavior cannot be observed offline -- the source repository is
# absent on some machines. Re-derived by running the extractor -- 130. This closes the
# 2026-09-22 review: two deferrals decided, EXPECTED_PAIRS 128 -> 130 across it.
# 131 on 2026-09-22 (#113): INV-216 gained a SECOND enforcer,
# tests/test_invariant_paths_resolve.py, when its 2026-09-22 correction moved
# list_specs.py to tests/ and added the guard that the path it names resolves —
# nothing had checked that before, so the invariant could have pointed at nothing
# with every other guard green. Re-derived by running the extractor, not incremented.
# 132 on 2026-09-24: INV-313 (a published derived register takes supersession status from
# an explicit marker, two states only, a partial supersession staying active with its
# successor in a field of its own) names test_supersession_has_one_syntax.py, which cites
# it back and states what it does NOT establish -- that a supersession recorded is correct,
# that a clause marked partial really is partial, or that a downstream consumer reads the
# field as intended; the first two are human judgments and the third lives in another
# repository. Re-derived by running the extractor -- 132, with the new pair present by
# name. This closes the 2026-09-24 review's first deferral: EXPECTED_PAIRS 131 -> 132.
# 133 on 2026-09-24: INV-314 (a maintainer command creating a record outside this repository
# shows the exact text and gets assent first; unattended it creates nothing) names
# test_filing_is_gated.py, which cites it back and states what it does NOT establish -- that
# a run actually asks, that a maintainer answered, or that an unattended run refrained; those
# are live-turn properties only dry-run phase 3 observes. Re-derived by running the
# extractor -- 133, with the new pair present by name. EXPECTED_PAIRS 132 -> 133.
# 134 on 2026-09-24: INV-315 (a rule statement carries its kind; only quotations are checked;
# a description is labeled unverified where it is SHOWN; an unmatched statement is reported
# unparsed) names test_rule_bullets_are_read_or_reported.py, which cites it back and states
# what it does NOT establish -- that a described rule is a faithful summary, which nothing
# can establish by construction. Re-derived by running the extractor -- 134, with the new
# pair present by name. EXPECTED_PAIRS 133 -> 134.
# 135 on 2026-09-24: INV-316 (a command named in a maintainer-facing document resolves or is
# marked at the point of use, and a document that is the REGISTER of an operation set lists
# every shipped command) names test_canonical_operations_resolve.py, which cites it back and
# states what it does NOT establish -- that a diagram renders, that a row's cell values are
# right, or that the drawing is a true account of the system. Re-derived by running the
# extractor -- 135, with the new pair present by name. This closes the 2026-09-24 review:
# four deferrals decided, EXPECTED_PAIRS 131 -> 135 across it.
# 136 on 2026-09-28: INV-160's 2026-09-28 dated note (#197: once `raw_url` and `git clone`
# have both failed, report the example as unreachable, never retry, pass `inline` or
# reconstruct it from memory) names test_access_steps_terminal_step.py, which cites INV-160
# back and states it pins the behavior, not the server's sentence (INV-219). It is INV-160's
# first named enforcer; no new invariant was registered. Re-derived by running the
# extractor -- 136, with the new pair present by name. EXPECTED_PAIRS 135 -> 136.
# 137 on 2026-09-29: INV-317 (#228 D1: a maintainer run records each finding durably as it is
# found, before fixing it, and never ends with one held only in conversation) names
# test_dry_run_files_issues.py, which cites it back and states it does NOT read
# `/production-readiness-audit` and cannot observe a live run. Re-derived by running the
# extractor -- 137, with the new pair present by name. EXPECTED_PAIRS 136 -> 137.
# 139 on 2026-09-29: INV-318 (#228 D2: no maintainer command applies `unattended-ok` to an issue
# it files) names two tests, test_dry_run_files_issues.py and
# test_audit_files_issues_not_specs.py. Each cites it back and states it pins the sentence, not
# a run's behavior. Re-derived by running the extractor -- 139, with both new pairs present by
# name. EXPECTED_PAIRS 137 -> 139.
# 141 on 2026-09-29: INV-319 (#228 D3: a filing command files in this repository only) names
# test_feedback_to_issues_files_in_its_own_repo.py and test_delegate_files_issues_not_specs.py.
# Each cites it back and states it pins the rule where written, not a run. Re-derived by running
# the extractor -- 141, with both new pairs present by name. EXPECTED_PAIRS 139 -> 141.
# 142 on 2026-09-29: INV-320 (#238: Phase C fixes every later source's limit before the run)
# names test_phase_c_loads_each_source_from_its_subset_record.py, which cites it back and states
# it pins the text, not a live loader. Re-derived by running the extractor -- 142, with the new
# pair present by name. EXPECTED_PAIRS 141 -> 142.
# 143 on 2026-09-29: INV-321 (#231: a defect report sent off the machine carries no identifier)
# names test_feedback_routing.py, which cites it back and states it pins the text, not a live
# submission. Re-derived by running the extractor -- 143, with the new pair present by name.
# EXPECTED_PAIRS 142 -> 143.
# 144 on 2026-09-29: INV-322 (#231: a file the bootcamp writes locally carries no host
# identifier) names test_bootcamp_notes_flow.py, which cites it back for the notes context block
# only. Re-derived by running the extractor -- 144, with the new pair present by name.
# EXPECTED_PAIRS 143 -> 144.
# 145 on 2026-09-29: INV-324 (#237: the remaining license cap counts the repository through the
# SDK, never from the registry) names test_load_reconciliation_has_two_stages.py, which cites it
# back and states it pins Phase B's text only. Re-derived by running the extractor -- 145, with
# the new pair present by name. EXPECTED_PAIRS 144 -> 145.
# 146 on 2026-09-29: INV-325 (#237: every subset choice writes its `load_subset:` block, the only
# record the reconciliation cites) names test_load_reconciliation_has_two_stages.py, which cites
# it back and states it pins the pointers, not a live run. Re-derived by running the extractor --
# 146, with the new pair present by name. EXPECTED_PAIRS 145 -> 146.
# 147 on 2026-09-29: INV-326 (#157: a step that writes a working sample records it in the
# `sample:` block) names test_load_reconciliation_has_two_stages.py, which cites it back and
# states it pins the text, not a live run. Re-derived by running the extractor -- 147, with the
# new pair present by name. EXPECTED_PAIRS 146 -> 147.
# 148 on 2026-09-29: INV-327 (#165: the first source is chosen by Phase C Step 14's heuristics)
# names test_first_source_is_chosen_by_step_fourteens_heuristics.py, which cites it back and
# states it pins the text, not a live choice. Re-derived by running the extractor -- 148, with
# the new pair present by name. EXPECTED_PAIRS 147 -> 148.
# 149 on 2026-09-29: INV-328 (#155: a numbered option is persisted as a category and a null,
# never as a count) names test_volume_option_reply_has_no_count.py, which cites it back and
# states it pins the text, not a live call. Re-derived by running the extractor -- 149, with the
# new pair present by name. EXPECTED_PAIRS 148 -> 149.
# 150 on 2026-09-29: INV-329 (#168: the recap reports the SDK version setup measured, or
# "Unknown") names test_recap_sdk_version_is_the_installed_one.py, which cites it back and states
# it pins the text, not a live recap. Re-derived by running the extractor -- 150, with the new
# pair present by name. EXPECTED_PAIRS 149 -> 150.
# 151 on 2026-09-29: INV-330 (#169: a How rendering names an unsettled final state) names
# test_how_tab_names_an_unsettled_final_state.py, which cites it back and states it pins the
# reference text, not a generated build. Re-derived by running the extractor -- 151, with the
# new pair present by name. EXPECTED_PAIRS 150 -> 151.
# 152 on 2026-09-29: INV-331 (#163: a pre-load heads-up triggers on the loadable total) names
# test_sqlite_preload_check_reads_the_loadable_total.py, which cites it back and states it pins
# the text, not a live prompt. Re-derived by running the extractor -- 152, with the new pair
# present by name. EXPECTED_PAIRS 151 -> 152.
# 154 on 2026-09-29: INV-332 (declining an issue is the maintainer's alone; a run that cannot
# implement one records it blocked) names test_unattended_loop_is_label_gated.py and
# test_declined_ledger.py, which cite it back and state what they do NOT establish -- that a
# live run refrains from declining. Re-derived by running the extractor -- 154, with both new
# pairs present by name. EXPECTED_PAIRS 152 -> 154.
# 155 on 2026-09-29: INV-333 (an empty argument never chooses a maintainer operation's costly work:
# /dry-run's phase 3, /auto-test's walk, /release's bump are asked about) names
# test_skills_state_their_commands_argument_handling.py, which cites it back and states what it does
# NOT establish -- that a live run asks. Re-derived by running the extractor -- 155, with the new
# pair present by name. EXPECTED_PAIRS 154 -> 155.
# 156 on 2026-09-30: INV-334 (the how-state audit checks every multi-record entity, reports one of
# four outcomes, and reports M = 0 as nothing to check) names test_phase_d_how_state_audit.py, which
# cites it back and states what it does NOT establish -- that a live run performs the audit.
# Re-derived by running the extractor -- 156, with the new pair present by name.
# EXPECTED_PAIRS 155 -> 156.
# 158 on 2026-09-30: INV-335 (Module 5's type/name check before mapping, its fast-path gate and the
# recorded decision) and INV-336 (Phase 2 reads that decision before workflow steps 2 and 3) both name
# test_quality_assessment_type_name_check.py, which cites both back and states what it does NOT
# establish -- that a live run performs the check or reads the decision in time. Re-derived by running
# the extractor -- 158, with both new pairs present by name. EXPECTED_PAIRS 156 -> 158.
# 159 on 2026-09-30: INV-337 (a skill governed at user level is not also defined here; the repository
# keeps only its overlay) names test_user_level_copies_govern.py, which cites it back and states what it
# does NOT establish -- what the user-level copy says on any machine. Re-derived by running the
# extractor -- 159, with the new pair present by name. EXPECTED_PAIRS 158 -> 159.
# 161 on 2026-09-30 (second review): INV-338 (the EULA question precedes every Senzing install, an
# update included) names test_eula_question_precedes_every_install.py and
# test_update_offer_order_and_existing_install_outcome.py; both cite it back and state what they do NOT
# establish -- that a live run asks before installing. Re-derived by running the extractor -- 161, with
# both new pairs present by name. EXPECTED_PAIRS 159 -> 161.
# 163 on 2026-10-01: INV-339 (an existing install skips only the installation; Phase 3 and the
# environment script still run) names test_existing_install_still_runs_the_env_script.py and
# test_update_offer_order_and_existing_install_outcome.py; both cite it back and state what they do NOT
# establish -- that a live run follows it. Re-derived by running the extractor -- 163, with both new
# pairs present by name. EXPECTED_PAIRS 161 -> 163.
# 164 on 2026-10-01: INV-340 (graduation's video step: offered once, nothing written on no, aggregates
# only, never blocking) names test_graduation_video_step.py, which cites it back and states what it does
# NOT establish -- that a live run follows it. Re-derived by running the extractor -- 164, with the new
# pair present by name. EXPECTED_PAIRS 163 -> 164.
# 165 on 2026-10-01: INV-341 (every completed module saves one aggregates-only B-roll entry) names
# test_broll_manifest.py, which cites it back and states what it does NOT establish -- that a live run
# writes a conforming entry. Re-derived by running the extractor -- 165, with the new pair present by
# name. EXPECTED_PAIRS 164 -> 165.
# 166 on 2026-10-01: INV-342 (the recap-video renderer's contract) names test_recap_video.py, which cites
# it back and states what it does NOT establish -- the macOS and Windows speech paths. Re-derived by
# running the extractor -- 166, with the new pair present by name. EXPECTED_PAIRS 165 -> 166.
# 167 on 2026-10-01: INV-343 (Module 5 Phase 2 emits no type_discriminator by default) names
# test_quality_assessment_type_name_check.py, which cites it back and states what it does NOT establish
# -- that a live run follows it. Re-derived by running the extractor -- 167, with the new pair present by
# name. EXPECTED_PAIRS 166 -> 167.
# 168 on 2026-10-01: INV-229's dated correction (#282: no count of the installation checks is asserted)
# names test_module3_check_lists_agree.py as an enforcer, which already cites INV-229 back. Re-derived by
# running the extractor -- 168, with the new pair present by name. EXPECTED_PAIRS 167 -> 168.
# 169 on 2026-10-02: INV-239's dated note (#343: distinct invented entities carry their own
# identifiers) names test_synthesized_entities_have_their_own_identifiers.py, which already cites
# INV-239 back. Re-derived by running the extractor -- 169, the one new pair present by name and none
# removed. EXPECTED_PAIRS 168 -> 169.
# 170 on 2026-10-02: INV-239's second dated note (#337: a regeneration requested after Module 5's gate
# has fired is exempt from the 70-79% requirement) names
# test_no_progress_gate_returns_to_data_collection.py, which already cites INV-239 back. Re-derived by
# running the extractor -- 170, the one new pair present by name and none removed.
# EXPECTED_PAIRS 169 -> 170.
# 171 on 2026-10-02: INV-342's audio-contract note (#339) names test_graduation_video_step.py for Step
# 1c's reading of the Voice:/Music: lines, and that file now cites INV-342 back, stating it does not
# establish that the renderer prints them. (test_recap_video.py, the note's other enforcer, was
# already a pair.) Re-derived by running the extractor -- 171, the one new pair present by name and
# none removed. EXPECTED_PAIRS 170 -> 171.
# 172 on 2026-10-02: INV-340's no-voice note (#340) names test_graduation_no_voice_guidance.py, which
# already cites INV-340 back. Re-derived by running the extractor -- 172, the one new pair present by
# name and none removed. EXPECTED_PAIRS 171 -> 172.
# 173 on 2026-10-02: INV-209's placement note (#323: a marker in shipped Markdown sits inside an HTML
# comment) names test_shipped_negative_markers_are_html_comments.py, which already cites INV-209 back.
# Re-derived by running the extractor -- 173, the one new pair present by name and none removed.
# EXPECTED_PAIRS 172 -> 173.
# 174 on 2026-10-02: INV-291's note (#335: a measured route records what it returned and its rank)
# names test_pattern_gallery_shortfall.py, which already cites INV-291 back
# (test_module_0_suggested_queries_are_measured.py was already a pair). Re-derived by running the
# extractor -- 174, the one new pair present by name and none removed. EXPECTED_PAIRS 173 -> 174.
# 176 on 2026-10-02: INV-331's note (#330, with #345: Step 8b uses Phase A's threshold, and its marker
# records the figure compared) names test_step_8b_uses_module_6s_sqlite_threshold.py, which now cites
# INV-331 back, and test_sqlite_load_time_prompt_is_defined_and_matched.py, which already did.
# Re-derived by running the extractor -- 176, both new pairs present by name and none removed.
# EXPECTED_PAIRS 174 -> 176.
# 178 on 2026-10-02: INV-091's dated correction (#332: the CDN fallback is withdrawn; the server
# refuses to render without the vendored D3) names test_viz_server_refuses_to_render_without_d3.py
# and test_project_local_visualization_finds_its_d3.py, which both already cite INV-091 back.
# Re-derived by running the extractor -- 178, both new pairs present by name and none removed.
# EXPECTED_PAIRS 176 -> 178.
# 180 on 2026-10-02: INV-175's note (#328: the root marker and the pre-Step-8 branch) names
# test_env_script_shell_portability.py and test_scaffold_banner_matches_build.py, which now both cite
# INV-175 back. Re-derived by running the extractor -- 180, both new pairs present by name and none
# removed. EXPECTED_PAIRS 178 -> 180.
# 182 on 2026-10-02: INV-154's note (#327: the capped Entity Graph notes state the cap) names
# test_viz_capped_graph_notes.py, which already cited INV-154 back, and test_viz_defaults_at_scale.py,
# which now does. Re-derived by running the extractor -- 182, both new pairs present by name and none
# removed. EXPECTED_PAIRS 180 -> 182.
# 183 on 2026-10-02: INV-084's note (#338: data/senzing-ready/ holds only full outputs, folded in at
# review rather than minted) names test_mapping_samples_stay_out_of_senzing_ready.py, which now cites
# INV-084 back. Re-derived by running the extractor -- 183, the one new pair present by name and none
# removed. EXPECTED_PAIRS 182 -> 183.
# 184 on 2026-10-02: INV-344 (inside a per-source loop, no whole-run question while another source
# remains) names test_module5_step16_asks_about_loading_only_after_the_last_source.py, which cites it
# back and states what it does NOT establish -- that a live run follows it. Re-derived by running the
# extractor -- 184, the new pair present by name and none removed. EXPECTED_PAIRS 183 -> 184.
# 185 on 2026-10-02: INV-186's note (#325: the source registry is copied into production/ as a
# projection, folded in at review rather than minted) names test_bundled_script_and_production_paths.py,
# which already cites INV-186 back. Re-derived by running the extractor -- 185, the one new pair
# present by name and none removed. EXPECTED_PAIRS 184 -> 185.
# 186 on 2026-10-03: INV-345 (on a synthesized source, disclose the deliberate gaps before the gate's
# question, and never regenerate silently; #394) names test_gate_options_have_handling_steps.py, which
# cites it back and states what it does NOT establish -- that a live turn obeys it. Re-derived by
# running the extractor -- 186, the new pair present by name and none removed. EXPECTED_PAIRS 185 -> 186.
# 187 on 2026-10-03: INV-344's note (#384: Phase 3's exits return to the per-source loop) names
# test_module5_phase3_exits_return_to_the_per_source_loop.py, which already cites INV-344 back.
# Re-derived by running the extractor -- 187, the one new pair present by name and none removed.
# EXPECTED_PAIRS 186 -> 187.
# 188 on 2026-10-03: INV-291's note (#383: an inline route records a rank band and a stamp, not an
# exact rank) names test_prescribed_search_queries.py, which already cites INV-291 back. Re-derived by
# running the extractor -- 188, the one new pair present by name and none removed.
# EXPECTED_PAIRS 187 -> 188.
# 189 on 2026-10-04: INV-175's dated correction (#419: the Windows env script is a dot-sourced
# senzing-env.ps1, never a .bat) names test_env_script_powershell.py, which already cites INV-175
# back. Re-derived by running the extractor -- 189, the one new pair present by name and none
# removed. EXPECTED_PAIRS 188 -> 189.
# 191 on 2026-10-04: INV-346 (a guard whose rule is about a phrase or a sentence matches it across a
# line wrap; #426) names test_wrapped_text.py and test_why_key_details_flag_is_cited_not_guessed.py,
# each of which cites it back and states what it does NOT establish. Re-derived by running the
# extractor -- 191, both new pairs present by name and none removed. EXPECTED_PAIRS 189 -> 191.
# 192 on 2026-10-04: INV-346's dated correction (#438: every line-reading test gives a verdict) names
# test_every_line_reading_guard_gives_a_verdict.py, which already cites INV-346 back. Re-derived by
# running the extractor -- 192, the one new pair present by name and none removed.
# EXPECTED_PAIRS 191 -> 192.
EXPECTED_PAIRS = 192


def pairs():
    """[(INV-nnn, 'test_x.py')] for every test file an invariant names."""
    text = INVARIANTS.read_text(encoding="utf-8")
    out = []
    for ident, body in ENTRY.findall(text):
        flat = re.sub(r"\s+", " ", body)
        for name in sorted(set(NAMED_TEST.findall(flat))):
            out.append((ident, name))
    return sorted(set(out))


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_expected_number_of_pairs_is_found(self):
        found = pairs()
        self.assertEqual(
            EXPECTED_PAIRS, len(found),
            "the invariant->test extractor found %d pairs, expected %d. If an invariant "
            "was added or reworded, re-derive EXPECTED_PAIRS by running this extractor "
            "and update it deliberately — do not relax the assertion." % (len(found), EXPECTED_PAIRS))

    def test_known_pairs_are_present(self):
        """A count alone passes on the wrong set; name members that must be in it."""
        found = pairs()
        for pair in (("INV-204", "test_liveness_probe_is_not_a_document_search.py"),
                     ("INV-183", "test_generated_html_deliverables.py"),
                     ("INV-107", "test_brand_sync.py")):
            with self.subTest(pair=pair):
                self.assertIn(pair, found)


class EveryNamedEnforcerExistsAndCitesItsInvariant(unittest.TestCase):
    def test_the_named_test_file_exists(self):
        for ident, name in pairs():
            with self.subTest(invariant=ident, test=name):
                self.assertTrue(
                    (TESTS / name).is_file(),
                    "%s names tests/%s as its enforcer and that file does not exist — "
                    "either the test was renamed without updating the invariant, or the "
                    "invariant claims a guard that was never written" % (ident, name))

    def test_the_named_test_cites_the_invariant_back(self):
        for ident, name in pairs():
            path = TESTS / name
            if not path.is_file():
                continue          # reported by the test above; do not double-fail
            with self.subTest(invariant=ident, test=name):
                # assertTrue, not assertIn: assertIn prints the whole container on failure,
                # which here is an entire test file. The message IS the value of this guard,
                # so the haystack must stay out of it.
                self.assertTrue(
                    ident in path.read_text(encoding="utf-8"),
                    "%s names tests/%s as its enforcer, but that file never cites %s. "
                    "coverage_reports.py keys on the ID appearing anywhere under tests/, "
                    "so this gap reads either as a falsely-unguarded invariant or — if any "
                    "unrelated file mentions %s — as a false all-clear. Add the citation to "
                    "the test's docstring; never delete the unrelated mention."
                    % (ident, name, ident, ident))


if __name__ == "__main__":
    unittest.main()
