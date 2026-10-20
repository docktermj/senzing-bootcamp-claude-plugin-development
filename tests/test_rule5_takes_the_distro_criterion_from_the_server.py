"""Module 2's routing rule 5 takes the linux_apt / linux_yum criterion from the server.

Enforces **INV-398**, registered by the maintainer 2026-10-20: where an MCP tool publishes the
criterion for choosing among a parameter it defines, shipped guidance states no criterion of
its own. ⚠️ It asserts the shipped steps STATE each clause and **cannot** establish that a live
guide makes the call or reads the file -- `dry-run` phase 3 observes that -- and asserts
nothing about the server, the suite being offline (INV-108).

Rule 5 of **Routing rules (apply in order)** in `module-02-sdk-setup/SKILL.md` resolved the one
branch that needs a distribution with a criterion the plugin owned and never named a method for:

    5. Linux -> **`platform='linux_apt'`** or **`platform='linux_yum'`** based on the package
       manager.

The detection that feeds it, in the same step, sends the guide to `uname`/`systeminfo`, and the
pinned fallback question (INV-056) offers "Linux (x86-64)" and "Linux (ARM64)" -- neither of which
carries a distribution. So a guide following Step 2 literally arrived at rule 5 holding `uname`
output and an unstated criterion.

The server now answers it in the very response Step 2 already names as the live route.
`sdk_guide(topic='install')` with no `platform`, on server 1.39.1, 2026-10-16, returns
`needs_input.decision_tree.question`:

    What operating system is the TARGET host (the machine Senzing will be installed on)? On
    Linux, read /etc/os-release on that host (ID / ID_LIKE) to choose: rhel, centos, rocky,
    almalinux, ol, fedora or amzn -> linux_yum; debian or ubuntu -> linux_apt. `uname` does NOT
    show the distribution, so do not choose from uname output.

and `sdk_guide(topic='install', platform='linux_apt')` carries the same rule as its first
`compatibility_notes` entry. So the plugin stopped asserting a criterion of its own: rule 5 names
the call, says what to extract, and relays the mapping the response gives, with the package
manager demoted from *criterion* to *fallback* (INV-125) that names the route that decided it.

⚠️ **This guard reads the shipped text, and the server fact is NOT asserted here.** The suite is
offline (INV-108), so the version and date above are a dated record on the `MCP re-check` line of
this change's `specs/IMPLEMENTED.md` entry, never something a test confirms. What a test can hold
is that the plugin says where the criterion comes from and does not state one of its own.

⛔ **Anti-vacuity (INV-265): a passage this guard cannot locate is a FAILURE, never a skip.**
`TheScanIsNotVacuous` fails first when a region moves, and every check below returns a problem
rather than quietly inspecting an empty string.

**What this cannot establish:** that a live guide makes the call, reads `/etc/os-release`, or falls
back as written -- only `dry-run` phase 3 observes that; and nothing about the server.

Every read collapses whitespace before matching, so a re-flow of the shipped Markdown cannot hide
a clause from it (INV-346).

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #680.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE2 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"
PREP = PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"

#: Rule 5's wording before #680 -- the criterion the plugin owned. Kept as the negative control:
#: every check below must report it, or the check is measuring nothing.
PRE_680_RULE_5 = (
    "5. Linux → **`platform='linux_apt'`** or **`platform='linux_yum'`** based on the "
    "package manager.")


def flat(text):
    """Whitespace-collapsed text, so a clause is found however the Markdown is wrapped."""
    return re.sub(r"\s+", " ", text)


def read(path):
    return path.read_text(encoding="utf-8")


def region(text, start, end, what):
    """The collapsed text between two markers, or a failure naming what moved."""
    begin = text.find(start)
    if begin < 0:
        raise AssertionError("%s: the opening marker %r is gone" % (what, start))
    stop = text.find(end, begin + len(start))
    if stop < 0:
        raise AssertionError("%s: the closing marker %r is gone" % (what, end))
    return flat(text[begin:stop])


def rule_five():
    """Routing rule 5, from its own number to the paragraph that follows the rules."""
    return region(read(MODULE2), "5. Linux →", "When a learner lands on Docker",
                  "Module 2 routing rule 5")


def detection_paragraph():
    """Step 2's detect-first paragraph, up to the pinned fallback question."""
    return region(read(MODULE2), "**Detect first, do not ask.**", "**Fallback only**",
                  "Module 2 Step 2's detection paragraph")


def step_two():
    """The whole of Step 2, for the question count."""
    return region(read(MODULE2), "## Step 2: Determine Platform", "## Step 3:",
                  "Module 2 Step 2")


def platform_bullet():
    """Bootcamp preparation's platform-detection bullet, up to the pinned question."""
    return region(read(PREP), "- **Detect the platform first (do not ask).**",
                  "\U0001f449 **Which operating system",
                  "Bootcamp preparation's platform-detection bullet")


def consolidated_write():
    """Bootcamp preparation's Step 6 prose, which lists every key it persists."""
    return region(read(PREP), "## 6. Consolidated preference write", "```yaml",
                  "Bootcamp preparation Step 6")


# --------------------------------------------------------------------------------------------
# The checks, written as functions of the passage so the negative controls can run the SAME
# code over the pre-#680 wording. A check returns a list of problems; empty means satisfied.
# --------------------------------------------------------------------------------------------

def names_the_call(passage):
    problems = []
    if "sdk_guide(topic='install')" not in passage:
        problems.append("rule 5 does not name `sdk_guide(topic='install')`, the route that owns "
                        "the `platform` enum and the choice between its values")
    if not re.search(r"with no `platform`", passage):
        problems.append("rule 5 does not say the call is made with no `platform`, which is what "
                        "returns the decision tree rather than an install")
    return problems


def says_what_to_extract(passage):
    problems = []
    for field in ("needs_input.decision_tree.question",
                  "needs_input.decision_tree.options[].value"):
        if field not in passage:
            problems.append("rule 5 does not say to read `%s` from the response" % field)
    return problems


def states_the_mapping(passage):
    problems = []
    if "/etc/os-release" not in passage:
        problems.append("rule 5 does not name `/etc/os-release`, the file the criterion reads")
    if not re.search(r"`ID`, then `ID_LIKE`", passage):
        problems.append("rule 5 does not say to take `ID`, then `ID_LIKE`")
    yum = ("`rhel`, `centos`, `rocky`, `almalinux`, `ol`, `fedora` or `amzn` → "
           "**`platform='linux_yum'`**")
    apt = "`debian` or `ubuntu` → **`platform='linux_apt'`**"
    if yum not in passage:
        problems.append("the linux_yum value list is not stated as the server gives it: %s" % yum)
    if apt not in passage:
        problems.append("the linux_apt value list is not stated as the server gives it: %s" % apt)
    return problems


def retires_the_plugin_owned_criterion(passage):
    problems = []
    if re.search(r"based on the package manager", passage):
        problems.append("rule 5 still asserts the package manager as its selection CRITERION; "
                        "the server states the criterion, and the package manager is now only "
                        "the fallback")
    if "does not show the distribution" not in passage:
        problems.append("rule 5 does not say `uname` cannot decide it, which is the half of the "
                        "server's answer a guide arriving from Step 2 most needs")
    if not re.search(r"1\.39\.1, 2026-10-16", passage):
        problems.append("the relayed server wording carries no server version and date, so a "
                        "later reader cannot tell how old the quoted criterion is (INV-080)")
    return problems


def states_the_fallback(passage):
    problems = []
    if "INV-125" not in passage:
        problems.append("the fallback cites no invariant; INV-125 governs what a fallback must "
                        "preserve when the MCP-first path fails")
    if "`apt`/`dpkg` → `linux_apt`" not in passage or \
            "`yum`/`dnf`/`rpm` → `linux_yum`" not in passage:
        problems.append("the fallback does not name today's behavior -- the package manager "
                        "actually present on the host, with the platform each resolves to")
    if "which route decided it" not in passage:
        problems.append("the fallback does not require saying WHICH route decided the platform, "
                        "so the deliverable does not say how it was made (INV-125)")
    if "\U0001f449" in passage:
        problems.append("rule 5 now carries a \U0001f449 question; this change adds a detection, "
                        "never a new gate (INV-012), and the pinned question is untouched "
                        "(INV-056)")
    return problems


def unames_limit_is_stated(passage):
    """Step 2's detection paragraph sends the guide to `uname`; it must say what that misses."""
    problems = []
    if "not the distribution" not in passage:
        problems.append("the detection paragraph does not say that what it detects is the OS and "
                        "the architecture and NOT the distribution")
    if "`uname` does not" not in passage:
        problems.append("the detection paragraph does not name `uname` as the route that cannot "
                        "answer it, which is the route this very paragraph sends the guide to")
    if "Rule 5 below makes its own read" not in passage:
        problems.append("the detection paragraph does not say that rule 5 makes its own read, so "
                        "the gap it names is left with no owner")
    if not ("INV-012" in passage and "INV-006" in passage):
        problems.append("the addition does not cite INV-012 and INV-006, the rules that make it "
                        "a detection rather than a new question")
    return problems


def cites_module_two(passage):
    """Bootcamp preparation points at rule 5 (INV-300) and carries no copy of its criterion."""
    problems = []
    if "../module-02-sdk-setup/SKILL.md" not in passage:
        problems.append("the bullet does not name the file that owns the rule, so the pointer "
                        "cannot be followed from where it is read (INV-300, INV-183)")
    if "Routing rules (apply in order)" not in passage:
        problems.append("the bullet does not name the list's own heading, so a reader must guess "
                        "which numbered list in that file is meant")
    if "rule 5" not in passage:
        problems.append("the bullet does not say which rule owns the choice")
    if "INV-300" not in passage:
        problems.append("the bullet claims the rule is stated elsewhere and cites no invariant "
                        "for that claim (INV-300)")
    if "INV-061" not in passage:
        problems.append("the bullet no longer cites INV-061 for the `os`/`arch` it does persist")
    # ⚠️ The two platform TOKENS are not the criterion: the bullet has to say what the choice is
    # between for the pointer to mean anything. The criterion is `ID`/`ID_LIKE` and the
    # distribution names it maps, and that is what must live in one place only.
    copied = [token for token in ("ID_LIKE", "rhel", "centos", "rocky", "almalinux", "amzn",
                                  "fedora", "debian", "ubuntu") if token in passage]
    if copied:
        problems.append("the pointing site carries a second copy of the criterion it points at "
                        "(%s); a copy that drifts is undetectable by construction (INV-300)"
                        % ", ".join(copied))
    return problems


class TheScanIsNotVacuous(unittest.TestCase):
    """Every region this guard reads is locatable, and none of them is empty."""

    def test_every_region_is_found(self):
        for what, passage in (("rule 5", rule_five()),
                              ("Step 2's detection paragraph", detection_paragraph()),
                              ("Step 2", step_two()),
                              ("the platform-detection bullet", platform_bullet()),
                              ("Step 6's consolidated write", consolidated_write())):
            with self.subTest(region=what):
                self.assertGreater(len(passage), 120,
                                   "%s was located but is too short to be the passage" % what)

    def test_the_rules_list_still_opens_where_the_other_guards_find_it(self):
        self.assertIn("**Routing rules (apply in order):**", read(MODULE2),
                      "the routing-rules heading moved; test_language_gate_names_the_cost.py "
                      "and test_rule_citations_name_their_file.py index it by that text")


class RuleFiveTakesTheCriterionFromTheServer(unittest.TestCase):
    def setUp(self):
        self.rule = rule_five()

    def test_it_names_the_call_that_carries_the_criterion(self):
        self.assertEqual([], names_the_call(self.rule), "\n".join(names_the_call(self.rule)))

    def test_it_says_which_fields_of_the_response_to_read(self):
        self.assertEqual([], says_what_to_extract(self.rule),
                         "\n".join(says_what_to_extract(self.rule)))

    def test_it_states_the_os_release_mapping_the_response_gives(self):
        self.assertEqual([], states_the_mapping(self.rule),
                         "\n".join(states_the_mapping(self.rule)))

    def test_it_no_longer_asserts_a_criterion_of_its_own(self):
        self.assertEqual([], retires_the_plugin_owned_criterion(self.rule),
                         "\n".join(retires_the_plugin_owned_criterion(self.rule)))

    def test_the_file_read_is_stated_as_installing_nothing(self):
        """A bootcamper must not read the new step as a package operation."""
        self.assertIn("reading it installs nothing", self.rule,
                      "rule 5 does not say that reading `/etc/os-release` installs nothing, so a "
                      "plain file read reads like a system change on the target host")

    def test_the_target_host_is_the_one_read(self):
        self.assertIn("on the **target** host", self.rule,
                      "rule 5 does not say WHICH host's `/etc/os-release` decides it; on the "
                      "docker and WSL2 routes the guide's host is not the install host")


class TheFallbackIsTodaysBehaviorAndNamesItsRoute(unittest.TestCase):
    def test_the_fallback_is_stated(self):
        rule = rule_five()
        self.assertEqual([], states_the_fallback(rule), "\n".join(states_the_fallback(rule)))

    def test_both_failure_modes_are_covered(self):
        rule = rule_five()
        for failure in ("the call cannot be reached", "`/etc/os-release` is absent"):
            with self.subTest(failure=failure):
                self.assertIn(failure, rule,
                              "the fallback does not cover this failure, so one of the two ways "
                              "the primary path can fail leaves rule 5 with no answer")

    def test_a_wrong_choice_is_said_to_surface_rather_than_pass_silently(self):
        self.assertIn("not silently", rule_five(),
                      "rule 5 does not say that a wrong fallback choice surfaces at once as an "
                      "install command the host rejects, which is why no question is added")


class StepTwoSaysUnameCannotAnswerIt(unittest.TestCase):
    def test_the_detection_paragraph_names_what_uname_misses(self):
        para = detection_paragraph()
        self.assertEqual([], unames_limit_is_stated(para),
                         "\n".join(unames_limit_is_stated(para)))

    def test_the_fallback_questions_linux_options_are_named_as_no_answer_either(self):
        self.assertIn("neither Linux option in the fallback question below", detection_paragraph(),
                      "the paragraph does not say that the pinned question's two Linux options "
                      "carry no distribution either, so the ask-instead reading survives")

    def test_step_two_still_asks_exactly_one_question(self):
        """INV-012 / INV-006: this change adds a detection, not a gate."""
        self.assertEqual(
            1, step_two().count("\U0001f449"),
            "Step 2 no longer carries exactly one \U0001f449 question. The pinned platform "
            "question is the only one it may ask (INV-056); rule 5's distribution read is a "
            "detection (INV-012) and asking again would repeat a question (INV-006)")

    def test_the_pinned_question_and_its_five_options_are_unchanged(self):
        step = step_two()
        self.assertIn("**Which operating system and processor architecture are you using? Reply "
                      "with a number:**", step, "the pinned question's wording changed (INV-056)")
        for option in ("1. Linux (x86-64)", "2. Linux (ARM64)", "3. macOS (Apple Silicon)",
                       "4. macOS (Intel)", "5. Windows (x86-64)"):
            with self.subTest(option=option):
                self.assertIn(option, step,
                              "an option of the pinned fallback question changed; this issue adds "
                              "no question and no option (INV-056, INV-284)")


class BootcampPreparationCitesModuleTwoRatherThanRestating(unittest.TestCase):
    def test_the_platform_bullet_points_at_rule_five(self):
        bullet = platform_bullet()
        self.assertEqual([], cites_module_two(bullet), "\n".join(cites_module_two(bullet)))

    def test_it_says_no_distribution_is_held_here(self):
        self.assertIn("nothing here detects or holds one", platform_bullet(),
                      "the bullet does not say that no distribution is detected or held, which "
                      "is what makes rule 5's own read necessary rather than redundant")


class NoDistributionValueIsPersisted(unittest.TestCase):
    """INV-061 is unchanged: `os`/`arch` is persisted, and no distribution beside it."""

    def test_the_consolidated_write_lists_no_distribution_key(self):
        prose = consolidated_write()
        self.assertIn("the detected `os`/`arch`", prose,
                      "Step 6 no longer names `os`/`arch` among the keys it writes (INV-061)")
        for token in ("distro", "distribution", "os_release", "os-release", "linux_apt",
                      "linux_yum"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, prose,
                    "Step 6's consolidated write now persists a distribution value (%r). It must "
                    "not: INV-061 covers the operating system and the architecture, the "
                    "distribution is neither, and rule 5 reads it at the moment it is needed "
                    "rather than from a file written modules earlier" % token)


class ModuleTwoIsTheOnlySiteThatStatesTheMapping(unittest.TestCase):
    """INV-300 from the other side: one owner, and no second copy anywhere in shipped text."""

    def test_only_rule_five_pairs_id_like_with_the_platform_tokens(self):
        owners = []
        for path in sorted(PLUGIN.rglob("*.md")):
            text = read(path)
            if "ID_LIKE" in text and ("linux_yum" in text or "linux_apt" in text):
                owners.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            ["plugins/senzing-bootcamp/skills/module-02-sdk-setup/SKILL.md"], owners,
            "more than one shipped file states the `/etc/os-release` criterion together with the "
            "platform tokens. Module 2's rule 5 owns it and every other site cites it (INV-300); "
            "a second copy that drifts is exactly what the duplication scan cannot see:\n  "
            + "\n  ".join(owners))

    def test_the_corpus_scanned_is_not_empty(self):
        self.assertGreater(len(list(PLUGIN.rglob("*.md"))), 20,
                           "the shipped Markdown sweep found almost nothing; the check above "
                           "would pass forever")


class EachCheckSeesTheTextItWasWrittenFor(unittest.TestCase):
    """Negative controls: the pre-#680 wording, and one targeted removal per check.

    ⛔ A check that cannot fail certifies what it never read. Each control is a mutation of the
    shipped passage, run through the SAME function the live assertion uses.
    """

    def test_the_pre_680_rule_is_reported_by_every_rule_five_check(self):
        control = flat(PRE_680_RULE_5)
        for name, check in (("names_the_call", names_the_call),
                            ("says_what_to_extract", says_what_to_extract),
                            ("states_the_mapping", states_the_mapping),
                            ("retires_the_plugin_owned_criterion",
                             retires_the_plugin_owned_criterion),
                            ("states_the_fallback", states_the_fallback)):
            with self.subTest(check=name):
                self.assertNotEqual([], check(control),
                                    "%s passes on rule 5's pre-#680 wording" % name)

    def test_restoring_the_package_manager_criterion_is_reported(self):
        mutated = rule_five().replace("and the install decision tree decides which, not this file",
                                      "based on the package manager")
        self.assertNotEqual([], retires_the_plugin_owned_criterion(mutated),
                            "the criterion check does not notice the old criterion put back")

    def test_dropping_the_decision_tree_fields_is_reported(self):
        mutated = rule_five().replace("needs_input.decision_tree.question", "the question")
        self.assertNotEqual([], says_what_to_extract(mutated),
                            "the extraction check does not notice the field name removed")

    def test_dropping_a_value_from_the_yum_list_is_reported(self):
        mutated = rule_five().replace("`almalinux`, ", "")
        self.assertNotEqual([], states_the_mapping(mutated),
                            "the mapping check does not notice a value list that no longer "
                            "matches the one the server returns")

    def test_dropping_the_route_disclosure_is_reported(self):
        mutated = rule_five().replace("which route decided it", "the outcome")
        self.assertNotEqual([], states_the_fallback(mutated),
                            "the fallback check does not notice that the route is no longer named")

    def test_adding_a_question_to_rule_five_is_reported(self):
        mutated = rule_five() + " \U0001f449 **Which Linux distribution are you on?**"
        self.assertNotEqual([], states_the_fallback(mutated),
                            "the fallback check does not notice a new gate question in rule 5")

    def test_a_pointer_that_restates_the_criterion_is_reported(self):
        mutated = platform_bullet() + " Take `ID`, then `ID_LIKE`: `debian` or `ubuntu` means "
        mutated += "linux_apt."
        self.assertNotEqual([], cites_module_two(mutated),
                            "the pointer check does not notice a second copy of the criterion at "
                            "the site that is supposed to point at it")

    def test_a_pointer_that_names_no_file_is_reported(self):
        mutated = platform_bullet().replace("`../module-02-sdk-setup/SKILL.md`", "Module 2")
        self.assertNotEqual([], cites_module_two(mutated),
                            "the pointer check does not notice that the owning file is no longer "
                            "named")

    def test_dropping_the_uname_caveat_is_reported(self):
        mutated = detection_paragraph().replace("`uname` does not", "the detection does not")
        self.assertNotEqual([], unames_limit_is_stated(mutated),
                            "the Step 2 check does not notice that `uname` is no longer named as "
                            "the route that cannot answer it")


class ReWrapping(unittest.TestCase):
    """INV-346: every clause is found whether or not the shipped Markdown is re-flowed."""

    def test_the_checks_survive_a_one_word_per_line_reflow(self):
        rule = flat(" \n".join(rule_five().split()))
        for name, check in (("names_the_call", names_the_call),
                            ("says_what_to_extract", says_what_to_extract),
                            ("states_the_mapping", states_the_mapping),
                            ("retires_the_plugin_owned_criterion",
                             retires_the_plugin_owned_criterion),
                            ("states_the_fallback", states_the_fallback)):
            with self.subTest(check=name):
                self.assertEqual([], check(rule),
                                 "%s stopped matching after a re-flow, so it is reading line "
                                 "layout rather than the rule" % name)


if __name__ == "__main__":
    unittest.main()
