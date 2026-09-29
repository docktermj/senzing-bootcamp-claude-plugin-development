"""Every MCP call the plugin documents must match the tool's real contract.

Three prose audits and 399 tests all passed while **Module 5's mapping workflow could not
execute at all**. It took a dry run against the live Senzing MCP server to see it, because
the defect is invisible to any check that only reads the plugin: the instructions are
coherent, well-written, internally consistent, and wrong about the tool they call.

What the 2026-07-26 dry run found:

* `mapping_workflow(action='start')` requires BOTH `file_paths` and `data.workspace_dir`
  — the tool's own words are "The call WILL FAIL without both", and "do NOT assume /tmp
  exists". `workspace_dir` appeared **nowhere** in the plugin, so Module 5 failed on its
  first call. `analyze_record` requires it too, and also never passed it.
* Five of the eight `mapping_workflow` action names were payload FIELD names written as
  actions — `profile_summary`, `entity_plan`, `schema_mappings`, `paths`, `verdict`. The
  only valid actions are start/advance/back/status/reset. One of the five sat on workflow
  step 3, and the plugin had filed a step-3 rejection upstream as an MCP-server defect.
* `get_sdk_reference`'s `methods` topic — which answers parameter shapes — was missing
  from the tool-routing table, and INV-132 asserted the reference could not answer them
  at all, routing the guide away from MCP toward local introspection.

These assertions are **static**: they encode the contract as observed on 2026-07-26 rather
than calling the server, so the suite stays offline, stdlib-only, and fast (INV-108). That
is a deliberate trade — a static copy can go stale, which is why CONTRACT_VERIFIED_ON is
recorded and why the assertions are about *shape* (required params present, action names in
the enum) rather than about response content. Re-run a dry run to refresh it; a tool that
gains a required parameter will not be caught here until someone does.

**Widened 2026-08-11** (`specs/required-params-guard-covers-two-of-nine-tools.md`).
`REQUIRED_PARAMS` held two entries under a comment that read as though it enumerated every
tool with a required parameter. It named the two that had a *known* defect; seven more
tools the plugin calls also mark parameters required, and `generate_scaffold` — called at
16 sites — did not appear in this file at all. The plugin was correct at every one of
those sites, so nothing was broken; what was missing was the tripwire, which is the same
silence that let the original `workspace_dir` defect survive three audits and 399 tests.
Two things changed as a result:

* Every tool the plugin references is now **classified** — into `REQUIRED_PARAMS`,
  `CONDITIONALLY_REQUIRED`, or `NO_REQUIRED_PARAMS` — and `MCP_TOOLS` must be exactly
  partitioned by the three, so a tool cannot sit in none of them. A hand-maintained
  subset was the defect; a partition is what stops it recurring.
* The param scan is **word-boundary matched**, not a substring test. `error_code` is a
  substring of `explain_error_code`, so the old `param in text` check would have passed
  for that tool no matter what the calling files said — a guard that could not fail.
  `test_the_param_scan_is_not_satisfied_by_the_tool_name` pins that.

The residual staleness is a **new** server tool the plugin starts calling: `MCP_TOOLS` is
a dated copy, so a 14th tool is invisible here until a dry run refreshes it. That is the
same trade the paragraph above names, and it is bounded — the partition catches every
tool the copy does know.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

# When the contract below was last checked against https://mcp.senzing.com/mcp.
# Refreshed by `dry-run` phase 1 on 2026-08-12: all 42 action/topic/category/workflow/
# platform/dataset/language literals still in enum, required-parameter lists unchanged,
# and `get_capabilities` still reports tool_count 13, matching MCP_TOOLS below.
CONTRACT_VERIFIED_ON = "2026-08-12"
# The server the required-parameter lists and MCP_TOOLS below were read from, via the
# loaded tool schemas and `get_capabilities` on that date. Recorded because the server
# ships independently of this plugin: without a version, "the schema requires this" is
# an undated claim.
MCP_SERVER_VERSION = "1.32.9"

# mapping_workflow's action enum, verbatim from the tool schema.
VALID_WORKFLOW_ACTIONS = {"start", "advance", "back", "status", "reset"}

# Every tool the MCP server exposes (`get_capabilities` reported tool_count 13 on
# 1.32.9, 2026-08-11). The three classification sets below must partition this exactly,
# which is what makes "a tool the plugin calls is uncovered" a test failure rather than
# a silent gap.
MCP_TOOLS = {
    "analyze_record",
    "download_resource",
    "explain_error_code",
    "find_examples",
    "generate_scaffold",
    "get_capabilities",
    "get_sample_data",
    "get_sdk_reference",
    "mapping_workflow",
    "reporting_guide",
    "sdk_guide",
    "search_docs",
    "submit_feedback",
}

# Tools the plugin must show with specific parameters. Two provenances, in one dict
# because the check is identical either way — the trailing comment says which:
#
# * schema-required — the parameter is in the tool's JSON `inputSchema.required` array,
#   so a schema-respecting client cannot send the call without it at all.
# * contract-required — the schema's `required` array does not carry it, but the tool's
#   own description says the call fails without it. `mapping_workflow` is the case that
#   matters: its `required` array is EMPTY and `workspace_dir` is nested inside the
#   free-form `data` object, yet the contract reads "The call WILL FAIL without both".
#   That is exactly the defect that made Module 5 unexecutable, so it is checked here
#   even though no schema field would ever have caught it.
REQUIRED_PARAMS = {
    "analyze_record": ("workspace_dir",),                   # schema-required
    "explain_error_code": ("error_code",),                  # schema-required
    "generate_scaffold": ("language", "workflow"),          # schema-required
    "get_sample_data": ("dataset",),                        # schema-required
    "get_sdk_reference": ("topic",),                        # schema-required
    "mapping_workflow": ("file_paths", "workspace_dir"),    # contract-required on 'start'
    "reporting_guide": ("topic",),                          # schema-required
    "sdk_guide": ("topic",),                                # schema-required
    "search_docs": ("query",),                              # schema-required
}

# Tools whose requirement is real but CONDITIONAL, so a flat "these params must appear"
# dict cannot express it. Listed with the reason so a later reader cannot mistake the
# absence for an oversight — which is the mistake this whole file exists to prevent.
CONDITIONALLY_REQUIRED = {
    "find_examples": (
        "requires one OF query | repo+file_path | repo+list_files. Nothing is "
        "unconditionally required, so a flat check would either be vacuous or reject "
        "the two legitimate non-query modes. INV-160 already routes the plugin to "
        "search mode (`query=`), and test_the_scan_is_not_vacuous-style coverage of "
        "that routing lives in the ground-rules tests."
    ),
    "submit_feedback": (
        "requirement depends on `category`: license_request needs firstname + work "
        "email + how_heard, while bug/feature/question/general needs message. The "
        "schema marks none of them required. The license_request branch is the one "
        "that sends personal data and is guarded by consent instead — see "
        "TestLicenseRequestIsConsentGated below (INV-135)."
    ),
}

# Tools that genuinely require nothing, with why — so the set cannot be read as a
# dumping ground for tools nobody classified.
NO_REQUIRED_PARAMS = {
    "get_capabilities": "only an optional `version`; a bare call is the documented use.",
    "download_resource": (
        "`filename`/`filenames` are both optional — calling with neither returns the "
        "list of available resources rather than failing."
    ),
}

# workspace_dir must stay inside the project: INV-200 binds MCP tool ARGUMENTS, not only
# file writes. The server requires the parameter and warns "do NOT assume /tmp exists",
# so a tool-suggested path outside the project is overridden, never followed.
FORBIDDEN_WORKSPACE_DIRS = ("/tmp", "%TEMP%", "~/", "/var/tmp")

SKILLS = PLUGIN / "skills"


def skill_text():
    """Every shipped skill/command file, as (path, text)."""
    for root in (SKILLS, PLUGIN / "commands"):
        for path in sorted(root.rglob("*.md")):
            if "pytest_cache" in path.parts:
                continue
            yield path, path.read_text(encoding="utf-8", errors="replace")


def files_calling(tool):
    """Files that actually invoke the named tool (not just mention it in prose)."""
    pattern = re.compile(rf"`?{re.escape(tool)}\(")
    for path, text in skill_text():
        if pattern.search(text):
            yield path, text


def mentions(text, name):
    """True if `name` appears as a standalone token, not inside a longer identifier.

    A plain `name in text` test is unsound for parameters whose name is a substring of
    their own tool: `error_code` sits inside `explain_error_code`, so every file calling
    the tool would satisfy the check without ever naming the parameter.
    """
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text) is not None


def tools_the_plugin_references():
    """Which MCP_TOOLS members appear anywhere in shipped skill/command text.

    Deliberately name-based rather than `tool(`-based: the plugin calls
    `submit_feedback` and `get_capabilities` by name in prose, describing their arguments
    in words, so a paren-only scan reports them as uncalled and would exempt them from
    classification for the wrong reason.
    """
    joined = "".join(text for _, text in skill_text())
    return {tool for tool in MCP_TOOLS if mentions(joined, tool)}


class TestActionNamesAreInTheEnum(unittest.TestCase):
    """A payload field name used as an action is rejected by the server."""

    def test_no_invented_workflow_actions(self):
        offenders = []
        for path, text in skill_text():
            for n, line in enumerate(text.splitlines(), 1):
                for action in re.findall(r"action='([a-z_]+)'", line):
                    if action not in VALID_WORKFLOW_ACTIONS:
                        offenders.append(
                            f"{path.relative_to(REPO_ROOT)}:{n} uses action='{action}', "
                            f"which is not in the enum {sorted(VALID_WORKFLOW_ACTIONS)} — "
                            "it is a payload field name; advance with action='advance' "
                            "and put the field in data/payload"
                        )
        self.assertEqual(
            [],
            offenders,
            "invalid mapping_workflow action(s) — the server rejects these:\n  "
            + "\n  ".join(offenders),
        )

    def test_the_advance_action_is_actually_used(self):
        """If nothing advances, the workflow instructions describe a dead end."""
        joined = "".join(text for _, text in skill_text())
        self.assertIn("action='advance'", joined)


class TestRequiredParamsArePresent(unittest.TestCase):
    """A required parameter the plugin never names is a call that fails outright."""

    def test_every_tool_shows_its_required_params(self):
        missing = []
        for tool, params in REQUIRED_PARAMS.items():
            callers = list(files_calling(tool))
            self.assertTrue(
                callers, f"no file appears to call {tool}; has it been renamed?"
            )
            for param in params:
                if not any(mentions(text, param) for _, text in callers):
                    where = ", ".join(
                        str(p.relative_to(REPO_ROOT)) for p, _ in callers
                    )
                    missing.append(
                        f"{tool} requires `{param}`, which appears in none of its "
                        f"calling files ({where}) — the call fails without it"
                    )
        self.assertEqual(
            [],
            missing,
            "required MCP parameter(s) absent from the instructions:\n  "
            + "\n  ".join(missing),
        )

    def test_workspace_dir_is_project_local(self):
        """The parameter exists to keep tool output inside the project."""
        offenders = []
        for path, text in skill_text():
            for n, line in enumerate(text.splitlines(), 1):
                if "workspace_dir" not in line:
                    continue
                for bad in FORBIDDEN_WORKSPACE_DIRS:
                    # An explicit "never /tmp" instruction is the opposite of a defect.
                    if bad in line and not re.search(
                        r"never|not|do NOT|forbid|outside", line, re.IGNORECASE
                    ):
                        offenders.append(
                            f"{path.relative_to(REPO_ROOT)}:{n} points workspace_dir at "
                            f"{bad}: {line.strip()[:90]}"
                        )
        self.assertEqual([], offenders, "\n  ".join(offenders))


class TestEveryCalledToolIsClassified(unittest.TestCase):
    """The completeness gate (INV-201): no tool the plugin calls can be silently uncovered.

    `REQUIRED_PARAMS` was a hand-maintained pair for two of nine tools, under a comment
    that read as though it enumerated them all. Nothing failed when a tool was absent,
    because the dict is data — so `generate_scaffold`, called at 16 sites, was simply not
    in this file. These tests turn "absent" into "failing".
    """

    def test_the_three_sets_partition_every_server_tool(self):
        classified = set(REQUIRED_PARAMS) | set(CONDITIONALLY_REQUIRED) | set(NO_REQUIRED_PARAMS)
        unclassified = MCP_TOOLS - classified
        self.assertEqual(
            set(),
            unclassified,
            "MCP tool(s) in no classification set: "
            + ", ".join(sorted(unclassified))
            + ". Add each to REQUIRED_PARAMS with its required parameters, to "
            "CONDITIONALLY_REQUIRED with the reason a flat check cannot express it, or "
            "to NO_REQUIRED_PARAMS with why it needs nothing. Leaving a tool out is the "
            "exact defect this test exists for.",
        )
        stray = classified - MCP_TOOLS
        self.assertEqual(
            set(),
            stray,
            "classified name(s) that are not server tools: "
            + ", ".join(sorted(stray))
            + " — either a typo or a tool the server dropped; MCP_TOOLS is the authority "
            f"(read from server {MCP_SERVER_VERSION} on {CONTRACT_VERIFIED_ON}).",
        )

    def test_no_tool_is_classified_twice(self):
        """Overlap would let a tool be exempted and checked at once, reading as covered."""
        for a, b in (
            ("REQUIRED_PARAMS", "CONDITIONALLY_REQUIRED"),
            ("REQUIRED_PARAMS", "NO_REQUIRED_PARAMS"),
            ("CONDITIONALLY_REQUIRED", "NO_REQUIRED_PARAMS"),
        ):
            with self.subTest(pair=f"{a}/{b}"):
                overlap = set(globals()[a]) & set(globals()[b])
                self.assertEqual(
                    set(), overlap, f"{sorted(overlap)} appears in both {a} and {b}"
                )

    def test_every_referenced_tool_is_classified(self):
        """The set that actually matters: what the plugin reaches for."""
        referenced = tools_the_plugin_references()
        classified = set(REQUIRED_PARAMS) | set(CONDITIONALLY_REQUIRED) | set(NO_REQUIRED_PARAMS)
        missing = referenced - classified
        self.assertEqual(
            set(),
            missing,
            "the plugin references MCP tool(s) that no classification set covers: "
            + ", ".join(sorted(missing)),
        )

    def test_the_reference_scan_is_not_vacuous(self):
        """If the scan stopped matching, every completeness check above passes empty."""
        referenced = tools_the_plugin_references()
        self.assertGreaterEqual(
            len(referenced),
            11,
            "found only %d of %d MCP tools referenced in the plugin (%s) — the scan has "
            "drifted, and with nothing to check the completeness tests pass vacuously"
            % (len(referenced), len(MCP_TOOLS), ", ".join(sorted(referenced))),
        )

    def test_the_param_scan_is_not_satisfied_by_the_tool_name(self):
        """`error_code` is a substring of `explain_error_code`.

        Under the old `param in text` check this tool's entry could never fail: the
        calling files contain the tool's own name, which contains the parameter's. The
        word-boundary matcher is what makes the entry meaningful, so it is pinned here
        rather than left as an implementation detail of `mentions()`.
        """
        self.assertFalse(
            mentions("call explain_error_code(SENZ0037) for the code", "error_code"),
            "the parameter scan still matches `error_code` inside "
            "`explain_error_code`; every entry whose parameter is a substring of its "
            "tool name is then unfailable",
        )
        self.assertTrue(
            mentions("explain_error_code(error_code='SENZ0037')", "error_code"),
            "the scan no longer sees a genuinely named parameter",
        )


class TestEveryReportingGuideCallPassesLanguage(unittest.TestCase):
    """`reporting_guide` withholds its content until `language` is supplied.

    Verified on server 1.32.2, 2026-07-30: `topic='evaluation'`, `topic='graph'` and
    `topic='entity_views'` called without `language` return a `needs_input` decision tree
    with empty payload sections — the 4-Point ER Evaluation Framework appears only once a
    language is passed, and `entity_views` returns nothing at all. `topic='data_mart'`
    gates again on `scale`. `topic='quality'` does not gate, which is why this went
    unnoticed: the parameter is **optional in the schema**, so a bare call looks correct.

    This guard deliberately carries **no topic allowlist**. An earlier version listed the
    three topics then known to gate; `entity_views` was found one sweep later and the list
    was already wrong, so a bare `entity_views` call would have passed. "Which topics gate"
    is a per-topic fact about a server that ships independently — the kind of thing this
    repo cannot keep current — so the rule is unconditional instead (INV-192). Passing
    `language` where a topic does not gate only adds content, so the blanket rule costs
    nothing and cannot go stale.
    """

    def test_no_reporting_guide_call_omits_language(self):
        pattern = re.compile(r"reporting_guide\(\s*topic\s*=[^)]*\)")
        offenders = []
        for path in sorted(SKILLS.rglob("*.md")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for match in pattern.finditer(line):
                    if "language" not in match.group(0):
                        offenders.append(
                            "%s:%d: %s" % (path.relative_to(REPO_ROOT), number, match.group(0))
                        )
        self.assertEqual(
            [],
            offenders,
            "reporting_guide called without `language` — most topics answer that with a "
            "needs_input decision tree and no content. Pass it "
            "unconditionally; do not add a per-topic exception here (INV-192):\n  "
            + "\n  ".join(offenders),
        )

    def test_the_gate_is_documented_where_the_tool_is_routed(self):
        text = (SKILLS / "bootcamp-onboarding" / "ground-rules.md").read_text(encoding="utf-8")
        self.assertIn("needs_input", text)
        self.assertRegex(text, r"(?i)gate, not an answer")

    def test_the_routing_rule_is_unconditional_not_a_topic_list(self):
        """INV-192: naming a subset of gating topics reads as the whole set.

        The enumeration this replaced named three topics and omitted `entity_views`,
        which gates and returns an entirely empty payload. A reader consulting that list
        would have concluded `entity_views` was safe to call bare.
        """
        text = (SKILLS / "bootcamp-onboarding" / "ground-rules.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?i)every call, whatever the topic")
        self.assertNotRegex(
            text,
            r"(?i)`topic='quality'` does \*\*not\*\*",
            "ground-rules again singles out topics as non-gating; that list went stale in "
            "a day and the rule is unconditional now",
        )

    def test_the_scan_is_not_vacuous(self):
        """A regex that stops matching would make the guard pass silently."""
        found = sum(
            len(re.findall(r"reporting_guide\(\s*topic", line))
            for path in SKILLS.rglob("*.md")
            for line in path.read_text(encoding="utf-8").splitlines()
        )
        self.assertGreater(found, 5, "found almost no reporting_guide calls; the glob drifted")


class TestParameterShapeRoutingGoesToMcp(unittest.TestCase):
    """INV-080 forbids routing away from MCP; INV-132 briefly did exactly that."""

    def test_ground_rules_routes_parameter_shapes_to_the_methods_topic(self):
        text = (SKILLS / "bootcamp-onboarding" / "ground-rules.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "topic='methods'",
            text,
            "the tool-routing table omits get_sdk_reference's `methods` topic — the one "
            "that answers parameter shapes. Without it the guide is sent to local "
            "binding introspection, which needs a working installed SDK and contradicts "
            "the MCP-first invariant (INV-080).",
        )

    def test_invariants_no_longer_claim_mcp_cannot_reach_parameter_shapes(self):
        text = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        self.assertIn(
            "The reference reaches parameter shapes under **any** topic",
            text,
            "INV-132's correction has been reverted; it would again assert that the MCP "
            "reference cannot answer parameter shapes, which the live server disproves.",
        )
        self.assertNotIn(
            "document neither the argument types nor what a flag family selects",
            text.split("(Corrected in place 2026-07-30")[0],
            "INV-132 again asserts that `flags` and `response_schemas` document neither "
            "argument types nor flag-family membership. Both are false: filtered by a "
            "method, every topic returns a `method_signatures` block, and flag entries "
            "carry composite_members/depends_on/response_paths (server 1.32.2, "
            "2026-07-30). The phrase is allowed only inside the correction note that "
            "quotes what the invariant used to say.",
        )


class TestLicenseRequestIsConsentGated(unittest.TestCase):
    """INV-135: the one call that sends personal data needs an explicit yes."""

    LICENSE_STEP = PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md"

    def license_window(self):
        """The license-request step's text, from its first mention to well past the gate.

        Deliberately generous: the window is measured from the first `license_request`
        occurrence, and the section grew when the `how_heard` requirement and its provenance
        were written in (2026-08-12). A window sized to yesterday's prose is how a guard
        quietly stops covering the thing it names.
        """
        text = self.LICENSE_STEP.read_text(encoding="utf-8")
        start = text.find("license_request")
        self.assertNotEqual(-1, start, "the license-request path has moved")
        return text[start:start + 8000]

    def test_the_license_request_carries_a_pinned_consent_question(self):
        text = self.LICENSE_STEP.read_text(encoding="utf-8")
        self.assertIn("license_request", text, "the license-request path has moved")
        window_start = text.find("license_request")
        window = text[window_start : window_start + 4000]
        self.assertRegex(
            window,
            r"👉 \*\*Send this evaluation-license request",
            "the license_request call has no pinned consent question near it. This call "
            "transmits the Bootcamper's name and work email off their machine (INV-135); "
            "it must never run without an explicit yes.",
        )

    def test_the_step_names_every_required_field(self):
        """The gate existing is not enough — it must ask for the right things.

        `submit_feedback` has NO `required` array: every property is nullable, so the real
        requirement lives in each property's description (the INV-192 class). Until
        2026-08-12 this step grouped `how_heard` with the optional `lastname` — "optionally a
        last name and how they heard about Senzing" — while the server documents `how_heard`
        as "required for license_request" and `lastname` as "optional". Verified on server
        1.32.9, 2026-08-12.
        """
        window = self.license_window()
        for needed, why in (
            ("first name", "the given name the server requires"),
            ("work", "the work-email requirement (personal domains are rejected)"),
            ("how_heard", "the third required field, documented only in the property description"),
        ):
            with self.subTest(field=needed):
                self.assertIn(
                    needed, window,
                    "the license step does not name %r — %s. INV-135 requires the consent "
                    "question to state what is sent, so an incomplete field list means the "
                    "Bootcamper consents to a payload that is not the payload." % (needed, why))

        # ⛔ Presence of the token is NOT the requirement — assert the CLAIM, and assert it
        # against the FIELD-LIST STATEMENT only.
        #
        # Two failures were needed to get this right, both caught by running the mutation:
        #   1. Checking only that "how_heard" appeared anywhere in the window passed on a
        #      reverted file, because the token survived in a quoted `get_capabilities`
        #      manifest lower down. A guard a restored defect satisfies is worse than none.
        #   2. Widening to "no 'optional' near 'heard'" then failed on the CORRECT file, for
        #      the same reason inverted: that quoted manifest legitimately reads
        #      "lastname (optional), email (…), and how_heard".
        # So the claim is checked where the claim is made — the sentence before the ⛔ — and
        # the quoted provenance below it is deliberately out of scope.
        statement = window.split("⛔")[0]
        self.assertIn("requires", statement,
                      "the field-list statement no longer precedes the ⛔ note; re-scope this")
        with self.subTest(check="not grouped with the optional field"):
            self.assertNotRegex(
                statement, r"(?i)optional(?:ly)?[^.]{0,100}heard",
                "the field list files how-they-heard under 'optional'. The server documents "
                "`how_heard` as 'required for license_request' and `lastname` as 'optional' "
                "(server 1.32.9, 2026-08-12) — grouping them is the defect this guards.")
        with self.subTest(check="stated as required"):
            self.assertRegex(
                statement, r"(?i)requires?[^.]{0,200}heard",
                "no sentence states that how-they-heard is required; the field list must say "
                "so, since the schema's `required` array does not (INV-192).")

    def test_the_consent_question_states_the_full_payload(self):
        """INV-135: the pinned question says what leaves the machine. All three, or none."""
        window = self.license_window()
        question = re.search(r"👉 \*\*Send this evaluation-license request[^\n]*", window)
        self.assertIsNotNone(question, "the pinned consent question has moved")
        asked = question.group(0).lower()
        for phrase in ("name", "work email", "heard"):
            with self.subTest(states=phrase):
                self.assertIn(
                    phrase, asked,
                    "the consent question does not mention %r, so it understates what is "
                    "transmitted: %s" % (phrase, question.group(0)))

    def test_the_contract_entry_and_the_shipped_step_agree(self):
        """The repo held both answers before this: the CONDITIONALLY_REQUIRED comment named
        `how_heard` while the shipped step called it optional, and nothing compared them."""
        entry = CONDITIONALLY_REQUIRED["submit_feedback"]
        self.assertIn("how_heard", entry,
                      "the contract entry stopped naming how_heard — if the server changed, "
                      "update the shipped step too and re-verify against it")
        self.assertIn("how_heard", self.license_window(),
                      "the contract entry names how_heard as required and the shipped license "
                      "step does not — these must not drift apart again")

    def test_the_defect_report_path_scopes_its_stripping_rule(self):
        """Otherwise INV-321's 'strip the email' and this call contradict each other."""
        text = (SKILLS / "bootcamp-onboarding" / "feedback.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "license_request",
            text,
            "feedback.md's strip-everything-identifying rule does not say it governs "
            "only the defect categories, so it reads as forbidding the license request's "
            "required email — a rule the plugin both requires and forbids.",
        )


class TestContractProvenance(unittest.TestCase):

    def test_the_verification_date_is_recorded(self):
        """A static copy of a live contract is only trustworthy with a date on it."""
        self.assertRegex(CONTRACT_VERIFIED_ON, r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
