"""Module 2 reads its release notes before the update offer, and every install path has one outcome.

#192 and #194 reordered and extended Module 2's Step 1b and Step 3 without re-reading their
neighbors, which left four defects:

1. **The offer asked before its content existed.** The release-notes lookup sat under
   `### After updating` and said "Put what applies in the offer", but `### The offer` came
   first and ended the turn on its 👉 question. A guide following the order asked before it
   looked.
2. **The existing-install path met the EULA question.** Step 1 said to skip "Step 3's install
   commands", but #192 made Phase 1 (EULA acceptance) Step 3's entry point, and it is not an
   install command. Phase 3 installs per-project bindings for Java, C#, Rust and TypeScript
   (Rust added by #287), which an existing SDK install does not provide. The environment script had no heading, so the name
   Step 1 quoted for it matched nothing.
3. **An update whose EULA was declined had no outcome.** Step 1b reused Phase 1's wording, and
   Phase 1's decline branch said "Stop here", against Step 1b's non-blocking rule.
4. **The migration tool names were not versioned.** The v4.4.0 release notes replace
   `sz_dbupgrade` with `sz_dbtool upgrade` and fold `sz_configupgrade` into `sz_configtool`.
   Re-verified on server 1.37.15, docs index 2026-09-28 23:38 UTC, 2026-09-28:
   `search_docs(query='sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native
   command-line tools', category='release_notes')` returns the *v4.4.0 Detailed Release Notes*
   "Command-line Tools & SDKs" table (v4.0 - v4.3 | v4.4.0 and later).

What these tests pin:

* the lookup block, its target bullets and the populated-repository paragraph sit in a section
  before `### The offer`, and `### After updating` holds none of them; the offer relays above
  its single 👉 question (INV-251); a named version is looked up and relayed with no new 👉
* Step 1's existing-install path skips Phase 1 and Phase 2, does not re-ask the EULA, runs
  Phase 3 and the environment script, and the environment script's quoted name is a heading
  in Step 3
* an update whose EULA is declined keeps the working install, records `update-declined`, is
  not offered again (INV-006) and continues; Phase 1's "Stop here" is scoped to a fresh install
  or the upgrade from below V4.0
* the migration tools are named by the V4 version doing the migration, with a dated citation

Negative controls rebuild the pre-fix order and the missing heading and require the checks to
fail.

Source issue: #222. Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE2 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-02-sdk-setup", "SKILL.md"
)

OFFER = "### The offer"
AFTER = "### After updating"
EULA_QUESTION = "👉 **Do you accept the Senzing End User License Agreement (EULA)?**"
ENV_SCRIPT_HEADING = "### Create the project-local environment script"

#: The pieces of the release-notes lookup the issue names, by text that is unique in the file.
LOOKUP_PIECES = (
    "A 4.x → 4.y update is covered by the target version's release notes",
    "- **Target 4.4.0.**",
    "- **Any other target**",
    "- **`search_docs` unreachable.**",
    "If the bootcamper already has a populated repository",
)


def read():
    with open(MODULE2, encoding="utf-8") as handle:
        return handle.read()


def flat(text):
    return re.sub(r"\s+", " ", text)


def span(text, start_marker, end_marker):
    start = text.index(start_marker)
    return text[start : text.index(end_marker, start + len(start_marker))]


def step_1b(text):
    start = text.index("## Step 1b:")
    return text[start : text.index("\n## ", start + 10)]


def step_3(text):
    return span(text, "## Step 3: Install Senzing SDK", "\n## Step 4:")


def subsection(section, heading):
    """From `heading` to the next heading of level 2 or 3."""
    start = section.index(heading)
    nxt = re.search(r"(?m)^#{2,3} ", section[start + len(heading) :])
    return section[start : start + len(heading) + nxt.start()] if nxt else section[start:]


def enclosing_heading(section, position):
    """The last `###` heading before `position`."""
    return section.rindex("\n### ", 0, position)


def order_problems(text):
    """Every lookup piece that does not sit in a section before `### The offer`."""
    section = step_1b(text)
    if OFFER not in section:
        return ["`### The offer` is not in Step 1b"]
    offer_at = section.index(OFFER)
    out = []
    for piece in LOOKUP_PIECES:
        if piece not in section:
            out.append("%r is not in Step 1b" % piece)
        elif section.index(piece) > offer_at:
            out.append("%r comes after `### The offer`" % piece)
    if AFTER in section:
        after = subsection(section, AFTER)
        out.extend("%r is under `### After updating`" % p for p in LOOKUP_PIECES if p in after)
    return out


def heading_problems(text):
    """Step 1's quoted name for the environment script must be a heading inside Step 3."""
    name = "Create the project-local environment script"
    out = []
    if '("%s")' % name not in text:
        out.append("Step 1 no longer quotes the environment script's name")
    if not re.search(r"(?m)^### %s$" % re.escape(name), step_3(text)):
        out.append("the quoted name matches no heading in Step 3")
    return out


class TheLookupPrecedesTheOffer(unittest.TestCase):
    def setUp(self):
        self.text = read()
        self.section = step_1b(self.text)

    def test_every_lookup_piece_is_before_the_offer(self):
        self.assertEqual(order_problems(self.text), [])

    def test_the_lookup_has_a_section_of_its_own_before_the_offer(self):
        at = self.section.index(LOOKUP_PIECES[0])
        heading = self.section[enclosing_heading(self.section, at) + 1 :].split("\n", 1)[0]
        self.assertIn("Before the offer", heading)
        self.assertLess(self.section.index(heading), self.section.index(OFFER))

    def test_the_old_instruction_is_gone(self):
        self.assertNotIn("Put what applies in the offer", self.section)

    def test_the_offer_relays_above_its_single_question(self):
        offer = subsection(self.section, OFFER)
        asked = [m.start() for m in re.finditer(r"(?m)^\s*>?\s*👉", offer)]
        self.assertEqual(len(asked), 1, "the offer must ask exactly one 👉 question")
        before = flat(offer[: asked[0]])
        self.assertRegex(before, r"(?i)comes only after the lookup above")
        self.assertRegex(before, r"(?i)above the question, relay the items")
        self.assertIn("INV-251", before)

    def test_no_newer_version_means_no_lookup_and_no_offer(self):
        lookup = flat(subsection(self.section, "### Before the offer"))
        self.assertRegex(lookup, r"(?i)^### Before the offer[^.]*Only when a newer version")
        self.assertRegex(lookup, r"(?i)there is no lookup and no offer")

    def test_a_named_version_is_looked_up_and_relayed_without_a_new_question(self):
        offer = flat(subsection(self.section, OFFER))
        self.assertRegex(
            offer, r"(?i)\*\*On a named version:\*\* run the lookup above for that version"
        )
        self.assertRegex(offer, r"(?i)relay what applies in the next turn, above the EULA question")
        self.assertRegex(offer, r"(?i)Do not ask another 👉 question about it \(INV-251\)")
        self.assertRegex(offer, r"(?i)undocumented, not known to be unnecessary")

    def test_after_updating_still_verifies(self):
        after = flat(subsection(self.section, AFTER))
        self.assertRegex(after, r"(?i)Re-run Step 4")
        self.assertRegex(after, r"(?i)rejoining the existing-install path")


class TheExistingInstallPathHasOneOutcome(unittest.TestCase):
    def setUp(self):
        self.text = read()
        start = self.text.index("**If the SDK is found and version is V4.0+:**")
        self.branch = flat(
            self.text[start : self.text.index("**If the SDK is found but version is incompatible", start)]
        )

    def test_it_skips_phase_1_and_phase_2(self):
        self.assertRegex(
            self.branch,
            r"(?i)Step 3's install commands: Step 3's Phase 1 \(EULA acceptance\) and Phase 2 "
            r"\(the SDK package\)",
        )

    def test_it_does_not_re_ask_the_eula(self):
        self.assertRegex(self.branch, r"(?i)\*\*Do not re-ask the EULA\.\*\*")

    def test_it_runs_phase_3_for_the_per_project_bindings(self):
        self.assertRegex(self.branch, r"(?i)\*\*Still run Step 3's Phase 3\*\*")
        self.assertRegex(self.branch, r"(?i)Java, C#, Rust and TypeScript bindings are per-project")
        self.assertRegex(self.branch, r"(?i)For Python, Phase 3 installs nothing")

    def test_it_still_writes_the_environment_script(self):
        self.assertRegex(self.branch, r"(?i)Still do Step 3's environment-script work")
        self.assertRegex(self.branch, r"(?i)\*\*Step 3's Phase 3\*\* \(install language bindings\)")

    def test_every_route_onto_it_is_named(self):
        self.assertRegex(
            self.branch,
            r"(?i)the same whether Step 1b finds no newer version, the bootcamper declines the "
            r"update, or they decline the EULA for it",
        )

    def test_the_environment_script_name_is_a_heading(self):
        self.assertEqual(heading_problems(self.text), [])

    def test_the_heading_leads_the_environment_script_prose(self):
        section = step_3(self.text)
        at = section.index("create a project-local environment script at `src/scripts/senzing-env.sh`")
        self.assertEqual(
            section.rindex("\n### ", 0, at) + 1, section.index(ENV_SCRIPT_HEADING),
            "another heading sits between the environment-script heading and its prose",
        )

    def test_step_3_says_where_an_existing_install_enters(self):
        section = flat(step_3(self.text))
        self.assertRegex(section, r"(?i)skips Phase 1 and Phase 2, is not asked the EULA again, and starts at Phase 3")
        self.assertNotIn("**Phase 3: Install language bindings (only after EULA acceptance):**", section)
        self.assertRegex(section, r"(?i)\*\*Phase 3: Install language bindings \(after Phase 1's EULA acceptance, or directly on Step 1's existing-install path")


class AnUpdateWhoseEulaIsDeclinedContinues(unittest.TestCase):
    def setUp(self):
        self.text = read()
        self.section = flat(step_1b(self.text))

    def test_step_1b_states_the_outcome(self):
        at = self.section.index("**If they decline the EULA here")
        outcome = self.section[at : at + 700]
        for needle in ('"Keeping [installed]."', "`update-declined`", "INV-006", "INV-048",
                       "continue on the existing-install path in Step 1",
                       "never recorded as a failure"):
            with self.subTest(needle=needle):
                self.assertIn(needle, outcome)

    def test_it_comes_after_the_eula_pointer(self):
        self.assertLess(
            self.section.index("Ask the EULA question before any package installs"),
            self.section.index("**If they decline the EULA here"),
        )

    def test_phase_1_stop_here_is_scoped(self):
        phase_1 = flat(span(step_3(self.text), "**Phase 1: EULA acceptance", "**Phase 2:"))
        decline = phase_1[phase_1.index("**If they decline the EULA:**") :]
        self.assertLess(decline.index("On a fresh install, or the upgrade from below V4.0"),
                        decline.index("Stop here."))
        self.assertRegex(decline, r"(?i)An update of a working V4\.0\+ install declined here does not stop")
        self.assertEqual(self.text.count(EULA_QUESTION), 1, "the EULA question was duplicated")


class TheMigrationToolsAreNamedByVersion(unittest.TestCase):
    def setUp(self):
        self.section = flat(step_1b(read()))

    def test_the_tools_are_called_v3_to_v4_migration_tools(self):
        self.assertIn(
            "`sz_dbupgrade`, `sz_configupgrade` and `sz_configtool` are V3→V4 migration tools",
            self.section,
        )

    def test_each_version_range_names_its_tools(self):
        self.assertIn("`sz_dbupgrade` and `sz_configupgrade` for v4.0–v4.3", self.section)
        self.assertIn(
            "`sz_dbtool upgrade` and `sz_configtool` (configuration upgrades folded in) for "
            "4.4.0 and later",
            self.section,
        )

    def test_a_point_release_still_needs_none_of_them(self):
        self.assertIn("A 4.x → 4.y update needs none of them.", self.section)

    def test_the_relabel_carries_a_dated_citation(self):
        self.assertIn(
            "search_docs(query='sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 "
            "native command-line tools', category='release_notes')",
            self.section,
        )
        self.assertIn("server 1.37.15, docs index 2026-09-28 23:38 UTC, 2026-09-28", self.section)


class TheChecksCatchThePreFixShape(unittest.TestCase):
    """Negative controls: the shapes #222 fixed must fail the checks above."""

    def test_the_lookup_after_the_offer_is_reported(self):
        text = read()
        section = step_1b(text)
        lookup = subsection(section, "### Before the offer")
        body = lookup.split("\n", 1)[1]
        # The pre-fix order: the lookup's body under `### After updating`, below the offer.
        mutant_section = section.replace(lookup, "")
        after = subsection(mutant_section, AFTER)
        mutant_section = mutant_section.replace(after, after + body)
        mutant = text.replace(section, mutant_section)
        self.assertNotEqual(mutant, text)
        problems = order_problems(mutant)
        self.assertEqual(len(problems), 2 * len(LOOKUP_PIECES), problems)

    def test_a_missing_heading_is_reported(self):
        mutant = read().replace(ENV_SCRIPT_HEADING + "\n", "")
        self.assertEqual(heading_problems(mutant), ["the quoted name matches no heading in Step 3"])


if __name__ == "__main__":
    unittest.main()
