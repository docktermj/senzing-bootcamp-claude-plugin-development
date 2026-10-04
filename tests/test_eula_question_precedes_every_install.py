"""Module 2 asks the pinned EULA question before it installs anything, on every path.

Step 3 opened with "**Phase 1: Install the SDK package (execute without stopping):**" (add the
repository, install the package) and only then, in Phase 2, asked "👉 **Do you accept the
Senzing End User License Agreement (EULA)?**". So a Bootcamper following Step 3 had the SDK
installed before consenting, and the install ran without the per-platform EULA variable,
which Step 1b says makes it do nothing and report success. The `docker` path had the same
defect, since it follows the `linux_apt` steps inside a plain Linux container. The update path
in Step 1b already had the order right ("Ask the EULA question before any package installs")
and pointed at the Step 3 wording, so the file disagreed with itself.

The server puts the question first. `sdk_guide(topic='install', platform=<p>,
language='java')` for `linux_apt`, `linux_yum`, `macos_arm` and `windows` (MCP server 1.37.14,
2026-09-28) each carries "EULA acceptance — BEFORE running this command, ASK the user … Only
proceed if they confirm." ahead of the SDK package install. The plugin asks earlier still,
before adding the repository, which is stricter than the server and does not contradict it.

What these tests pin, within the Step 3 section:

* the pinned question precedes the repository add, the package install and the `docker`
  path's in-container `linux_apt` install
* the phases are labeled Phase 1 (EULA acceptance), Phase 2 (install the SDK package) and
  Phase 3 (install language bindings), in that order, and the anti-pattern lookup still
  heads the step
* the accept branch routes to Phase 2, then Phase 3; the decline branch installs nothing and
  writes no checkpoint
* Phase 2 sets the per-platform EULA variable from Step 1b's table before the package install
* Step 1b's pointer names "Step 3 Phase 1", and the question exists once in the file

A negative control runs the order check against the pre-fix order and requires it to fail.

#284 added the sites its `DEFERRED INVARIANT` block names that nothing above covered: Step 3's
opening sentence, Phase 1's list of what counts as an install, the existing-install path's
"Do not re-ask the EULA" exclusion, Step 1b's rule sentence, and each row of Step 1b's
per-platform variable table (with a negative control on a swapped value).

Enforces **INV-338** (the EULA question precedes every Senzing install, an update included; what counts
as an install; the per-platform variable from Step 1b's table; the existing-install path is not asked).
It asserts that Module 2 *states* the rule at each site, and does **not** establish that a live run asks
before installing, which only `dry-run` phase 3 can observe.

Source issues: #192, #284.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE2 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-02-sdk-setup", "SKILL.md"
)

QUESTION = "👉 **Do you accept the Senzing End User License Agreement (EULA)?**"
REPO_ADD = "1. Add the Senzing package repository."
PACKAGE_INSTALL = "2. Install the Senzing SDK package."
DOCKER_INSTALL = "follow the `linux_apt` steps inside it"
ANTI_PATTERNS = "call `search_docs` with `category='anti_patterns'`"

PHASE_1 = "**Phase 1: EULA acceptance"
PHASE_2 = "**Phase 2: Install the SDK package"
PHASE_3 = "**Phase 3: Install language bindings"


def read():
    with open(MODULE2, encoding="utf-8") as handle:
        return handle.read()


def step_3(text):
    start = text.index("## Step 3: Install Senzing SDK")
    return text[start : text.index("\n## Step 4:", start)]


def between(section, start_marker, end_marker):
    start = section.index(start_marker)
    return section[start : section.index(end_marker, start)]


def order_problems(section):
    """Every install instruction that the pinned question does not precede."""
    out = []
    if QUESTION not in section:
        return ["the pinned EULA question is not in Step 3"]
    asked = section.index(QUESTION)
    for label, marker in (
        ("the repository add", REPO_ADD),
        ("the SDK package install", PACKAGE_INSTALL),
        ("the docker path's in-container linux_apt install", DOCKER_INSTALL),
    ):
        if marker not in section:
            out.append(f"{label} ({marker!r}) is not in Step 3")
        elif section.index(marker) < asked:
            out.append(f"{label} comes before the EULA question")
    return out


class TheEulaQuestionPrecedesEveryInstall(unittest.TestCase):
    def setUp(self):
        self.text = read()
        self.section = step_3(self.text)

    def test_the_question_precedes_every_install_instruction(self):
        self.assertEqual(order_problems(self.section), [])

    def test_the_phases_are_labeled_in_the_new_order(self):
        positions = [self.section.index(h) for h in (PHASE_1, PHASE_2, PHASE_3)]
        self.assertEqual(positions, sorted(positions))
        phase_1 = between(self.section, PHASE_1, PHASE_2)
        self.assertIn(QUESTION, phase_1)

    def test_the_anti_pattern_lookup_still_heads_the_step(self):
        self.assertLess(
            self.section.index(ANTI_PATTERNS), self.section.index(QUESTION),
            "the anti-pattern lookup is not an install; it stays ahead of the question",
        )

    def test_the_question_ends_the_turn(self):
        phase_1 = re.sub(r"\s+", " ", between(self.section, PHASE_1, PHASE_2))
        self.assertIn("end the turn on this question and wait", phase_1)

    def test_the_accept_branch_routes_to_phase_2_then_phase_3(self):
        phase_1 = re.sub(r"\s+", " ", between(self.section, PHASE_1, PHASE_2))
        self.assertRegex(
            phase_1,
            r"\*\*If they accept the EULA:\*\* proceed to Phase 2 to install the SDK package, "
            r"then Phase 3",
        )

    def test_the_decline_branch_installs_nothing(self):
        phase_1 = re.sub(r"\s+", " ", between(self.section, PHASE_1, PHASE_2))
        decline = phase_1[phase_1.index("**(INV-338) If they decline the EULA:**") :]
        self.assertRegex(decline, r"^\*\*\(INV-338\) If they decline the EULA:\*\* install nothing")
        for item in ("no package repository", "no SDK package", "no language bindings"):
            self.assertIn(item, decline)
        self.assertIn("Do not write the checkpoint", decline)

    def test_the_eula_variable_is_set_before_the_package_install(self):
        phase_2 = between(self.section, PHASE_2, PHASE_3)
        flat = re.sub(r"\s+", " ", phase_2)
        self.assertRegex(flat, r"set the EULA variable for the bootcamper's platform")
        self.assertIn('the table in Step 1b ("The EULA variable differs per platform")', flat)
        self.assertLess(
            flat.index("set the EULA variable"), flat.index(PACKAGE_INSTALL),
        )
        self.assertRegex(flat, r"On the `docker` path, set the `linux_apt` variable")

    def test_the_referenced_table_still_exists_in_step_1b(self):
        self.assertIn("**(INV-338) The EULA variable differs per platform", self.text)

    def test_the_update_path_points_at_step_3_phase_1(self):
        flat = re.sub(r"\s+", " ", self.text)
        self.assertIn("reuse the existing wording in Step 3 Phase 1", flat)
        self.assertNotIn("reuse the existing wording in Step 3 Phase 2", flat)

    def test_the_question_exists_once(self):
        self.assertEqual(self.text.count(QUESTION), 1)

    def test_no_pointer_names_the_docker_bullets_under_phase_1(self):
        self.assertNotIn("Phase 1 `docker` bullets", self.text)


#: Step 1b's per-platform EULA variable table, row by row. Re-verified against
#: `sdk_guide(topic='install', platform=<p>, language='java')` for each platform (server 1.37.16,
#: 2026-09-30): the apt and yum commands export `SENZING_ACCEPT_EULA=I_ACCEPT_THE_SENZING_EULA`,
#: the Homebrew cask reads `HOMEBREW_SENZING_ACCEPT_EULA` with the lowercase value, and the Scoop
#: manifest reads `SENZING_ACCEPT_EULA` with the uppercase value.
EULA_VARIABLES = {
    "`linux_apt`, `linux_yum`": ("`SENZING_ACCEPT_EULA`", "`I_ACCEPT_THE_SENZING_EULA`"),
    "`macos_arm`": ("`HOMEBREW_SENZING_ACCEPT_EULA`", "`i_accept_the_senzing_eula`"),
    "`windows`": ("`SENZING_ACCEPT_EULA`", "`I_ACCEPT_THE_SENZING_EULA`"),
}


def eula_table_rows(text):
    """{platform cell: (variable, value)} for the table under Step 1b's EULA-variable rule.

    Line-scoped by design (#424): a table row is one line.
    """
    start = text.index("**(INV-338) The EULA variable differs per platform")
    rows = {}
    for line in text[start:].splitlines()[1:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Platform", "---") or set(cells[0]) <= {"-"}:
            continue
        value = cells[2].split(" (")[0].strip()
        rows[cells[0]] = (cells[1], value)
    return rows


class TheEulaRuleHoldsAtEverySiteTheDeferralNames(unittest.TestCase):
    """The sites #284's `DEFERRED INVARIANT` block names that no assertion above covered.

    The block drafts the EULA-before-install rule for `/review-invariants`. Each test here pins
    one site the block lists, so the rule the maintainer is asked to register is the rule that
    ships at every one of them.
    """

    def setUp(self):
        self.text = read()
        self.flat = re.sub(r"\s+", " ", self.text)
        self.section = re.sub(r"\s+", " ", step_3(self.text))

    def test_step_3_opens_by_saying_nothing_installs_before_the_answer(self):
        self.assertIn(
            "the EULA question comes first: nothing is installed until the bootcamper accepts it",
            self.section,
        )

    def test_phase_1_scopes_an_install_as_every_install_command(self):
        """The scope the drafted wording takes over: repository, package, docker install."""
        phase_1 = re.sub(r"\s+", " ", between(step_3(self.text), PHASE_1, PHASE_2))
        self.assertIn(
            "this question comes before **every** install command on **every** path: adding "
            "the Senzing package repository (the apt or yum `senzingrepo` package, the Homebrew "
            "tap, the Scoop bucket), installing the SDK package, and the `docker` path's "
            "in-container `linux_apt` install",
            phase_1,
        )

    def test_the_existing_install_path_is_excluded_and_an_accepted_update_is_not(self):
        self.assertIn(
            "**(INV-338) Do not re-ask the EULA.** Phase 1 gates installing the SDK, and this path "
            "installs no SDK. Only an update the bootcamper accepts in Step 1b asks it, because "
            "an update is an install.",
            self.flat,
        )

    def test_the_update_path_states_the_rule_and_that_an_update_is_an_install(self):
        self.assertIn(
            "⛔ **(INV-338) Ask the EULA question before any package installs** — reuse the existing "
            "wording in Step 3 Phase 1 rather than writing a second copy. An update is an "
            "install.",
            self.flat,
        )

    def test_the_variable_rule_says_a_wrong_one_is_silently_ignored(self):
        self.assertIn(
            "⛔ **(INV-338) The EULA variable differs per platform, and a wrong one is silently ignored:**",
            self.text,
        )

    def test_each_platform_row_names_its_own_variable_and_value(self):
        self.assertEqual(eula_table_rows(self.text), EULA_VARIABLES)

    def test_the_row_check_sees_a_swapped_value(self):
        """Negative control: the macOS row with the uppercase value must fail."""
        mutant = self.text.replace(
            "| `macos_arm` | `HOMEBREW_SENZING_ACCEPT_EULA` | `i_accept_the_senzing_eula`",
            "| `macos_arm` | `HOMEBREW_SENZING_ACCEPT_EULA` | `I_ACCEPT_THE_SENZING_EULA`",
        )
        self.assertNotEqual(mutant, self.text)
        self.assertNotEqual(eula_table_rows(mutant), EULA_VARIABLES)


class TheOrderCheckCatchesThePreFixOrder(unittest.TestCase):
    """Negative control: the order the file shipped before #192 must fail the check."""

    def test_the_install_first_order_is_reported(self):
        section = step_3(read())
        phase_1 = between(section, PHASE_1, PHASE_2)
        phase_2 = between(section, PHASE_2, PHASE_3)
        mutant = section.replace(phase_1 + phase_2, phase_2 + phase_1)
        self.assertNotEqual(mutant, section)
        problems = order_problems(mutant)
        self.assertEqual(len(problems), 3, problems)


if __name__ == "__main__":
    unittest.main()
