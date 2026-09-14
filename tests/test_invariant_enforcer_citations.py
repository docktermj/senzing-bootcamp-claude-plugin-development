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
EXPECTED_PAIRS = 120


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
