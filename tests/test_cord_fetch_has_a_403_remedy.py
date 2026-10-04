"""A 403 on a CORD fetch has a documented way forward, and it is not a retry.

Module 4's "CORD fetch integrity" section was written from a **429** incident and gave a
remedy only for that status: retry with a short backoff. A **403** is reachable on the
bootcamp's most likely path and had no remedy at all, so collection simply stopped.

Measured 2026-09-01, Ubuntu 24.04 / Python 3.12.3 — reproducing 2026-08-31 exactly:

    source_download_url (senzing.com), default UA Python-urllib/3.12 -> HTTP 403
    source_download_url, User-Agent curl/8.5.0                       -> HTTP 200
    source_download_url, User-Agent Mozilla/5.0                      -> HTTP 403
    download_url (mcp.senzing.com), default UA                       -> HTTP 200

Python is the bootcamp's most likely language, the module tells the guide to fetch "in
whatever language the Bootcamper chose", and ``urllib.request`` is the zero-dependency
choice a guide reaches for first. A working route was in the same response the whole time.

⛔ The fix must never be a spoofed User-Agent: it is the wrong thing to teach, and
``Mozilla/5.0`` measured **403** on the same host in the same run, so it does not even work.

⚠️ This is an observation of a web host from one machine, not an MCP-reported fact
(INV-080/INV-149), so the guard asserts it is dated and scoped -- never that it is timeless.

Enforces **INV-292** — where a provider supplies more than one URL for the same content,
the programmatic route is preferred and every non-2xx has a next step distinguishing a
throttle from a refusal.

⚠️ It asserts the rule at BOTH fetch steps. module-03b documented only the throttle while
instructing a fallback to the URL measured to 403, and it runs first — so asserting only
Module 4 would have certified the half that was never the problem.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"


def flat(s):
    return re.sub(r"\s+", " ", s)


def fetch_integrity_section():
    """The CORD fetch integrity block -- from its anchor to the end of check 3."""
    text = MODULE_4.read_text(encoding="utf-8")
    start = text.find("**⛔ CORD fetch integrity")
    assert start != -1, "the CORD fetch integrity section was not found -- renamed?"
    nxt = text.find("\n## ", start)
    return text[start: nxt if nxt != -1 else len(text)]


class ThePreferredRouteIsStatedWithItsReason(unittest.TestCase):
    def setUp(self):
        self.section = flat(fetch_integrity_section())

    def test_download_url_is_preferred(self):
        self.assertRegex(
            self.section,
            r"(?i)prefer `?download_url`?[^.]{0,80}over[^.]{0,60}source_download_url",
            "Module 4 must state a preference for the MCP-hosted `download_url`. Both URLs "
            "arrive in the same citation and look equally available; one of them is refused "
            "to programmatic clients.",
        )

    def test_the_reason_is_given_not_just_the_rule(self):
        """A bare preference is followed until it is inconvenient; a reason survives."""
        self.assertRegex(
            self.section, r"(?i)restricted[- ]egress|only `?mcp\.senzing\.com`? (?:reachable|allowed)",
            "The preference must carry its reason -- the MCP endpoint is served to "
            "programmatic clients and is what keeps working when egress is restricted. "
            "Without it the next editor reads the preference as arbitrary and drops it.",
        )


class ForbiddenStatusHasItsOwnBranch(unittest.TestCase):
    def setUp(self):
        self.section = flat(fetch_integrity_section())

    def test_403_is_named(self):
        self.assertIn(
            "403", self.section,
            "403 must appear in the fetch-integrity guidance. It was reachable on the most "
            "likely path with no documented next step, so collection terminated.",
        )

    def test_403_routes_to_the_other_url_rather_than_retrying(self):
        """⚠️ Asserts the INSTRUCTION -- switch URLs -- not merely that '403' appears."""
        self.assertRegex(
            self.section,
            r"(?i)403[^.]{0,60}(?:do not retry|not a throttle)|"
            r"(?:do not retry|not a throttle)[^.]{0,60}403",
            "The 403 branch must say retrying does not help. A 403 is a refusal; a backoff "
            "burns the Bootcamper's time and fails anyway.",
        )
        self.assertRegex(
            self.section,
            r"(?i)(?:re-?fetch|switch)[^.]{0,120}(?:other URL|`?download_url`?)",
            "The 403 branch must route to the alternate URL from the same response. Naming "
            "the failure without the remedy is the gap this fix exists to close.",
        )

    def test_the_429_backoff_survives(self):
        for phrase in ("429", "backoff"):
            self.assertIn(
                phrase, self.section,
                "Adding the 403 branch must not disturb the 429 guidance, which was itself "
                "verified live against a four-source fetch that lost two sources.",
            )

    def test_all_three_checks_survive(self):
        for check in ("Check the HTTP status", "Compare the record count",
                      "Never write an unverified fetch"):
            self.assertIn(
                check, self.section,
                "All three integrity checks must remain -- they behaved correctly and are "
                "not what this fix changes.",
            )


class TheObservationIsDatedAndScoped(unittest.TestCase):
    """INV-080/INV-149: a web-host behavior is not an MCP fact and may not read as one."""

    def setUp(self):
        self.section = flat(fetch_integrity_section())

    def test_it_is_marked_observation_only(self):
        self.assertRegex(
            self.section, r"(?i)observation, not an MCP-sourced fact|observation-only",
            "The 403 finding must be marked as an observation rather than a Senzing-reported "
            "fact. No MCP route reports this, and a reader must be able to tell the "
            "difference between what the server said and what one machine saw.",
        )

    def test_it_carries_a_date_and_the_client_it_was_measured_with(self):
        self.assertRegex(self.section, r"20\d\d-\d\d-\d\d",
                         "The observation must carry the date it was measured.")
        self.assertRegex(
            self.section, r"(?i)Python-urllib|urllib\.request",
            "The observation must name the client it was measured with -- the split is by "
            "User-Agent, so 'senzing.com returns 403' without the client is not reproducible.",
        )


#: An instruction to disguise the client. Matched by ``match_lines`` across line wraps (#424):
#: "set a custom\nUser-Agent" is one instruction however the column falls.
INSTRUCTS_A_USER_AGENT = re.compile(
    r"(?i)(?:set|send|pass|use|supply|spoof)\s+(?:an?\s+|the\s+)?"
    r"(?:custom\s+|different\s+|browser\s+)?user[- ]agent")
#: The wording of a line that FORBIDS it, which must quote it to be followable.
FORBIDS = re.compile(r"(?i)never set|do not set|never send|not a working")


def user_agent_instructions(text):
    """1-based lines where an instruction to set a User-Agent starts, minus forbidding lines.

    ⚠️ The exemption still reads the line the match starts on, as before #424: a forbidding
    phrase that wraps away from that line is not seen, so the guard flags rather than exempts.
    """
    lines = text.split("\n")
    return [n for n in match_lines(text, INSTRUCTS_A_USER_AGENT)
            if not FORBIDS.search(lines[n - 1])]


class NothingInstructsASpoofedUserAgent(unittest.TestCase):
    """Derived by scanning all shipped markdown, not by checking the file just edited."""

    def test_no_shipped_file_instructs_setting_a_user_agent(self):
        offenders = []
        for md in sorted(SKILLS.rglob("*.md")):
            for lineno in user_agent_instructions(md.read_text(encoding="utf-8")):
                offenders.append("%s:%d" % (md.relative_to(REPO), lineno))
        self.assertEqual(
            [], offenders,
            "No shipped guidance may instruct disguising the client. It teaches the wrong "
            "habit, and `Mozilla/5.0` measured 403 on the same host anyway. Offenders: %s"
            % offenders,
        )

    def test_a_wrapped_instruction_is_caught_at_its_first_line(self):
        """Negative control (#424): "a custom" ends line 1 and "User-Agent" begins line 2."""
        wrapped = "If the host refuses the fetch, set a custom\nUser-Agent header and retry.\n"
        self.assertEqual([1], user_agent_instructions(wrapped))
        # The old line-at-a-time scan, kept only to show the fixture is the hard case.
        self.assertFalse(any(INSTRUCTS_A_USER_AGENT.search(l) for l in wrapped.split("\n")))

    def test_the_forbidding_line_is_not_an_instruction(self):
        """Must-not-flag (INV-282): the prohibition quotes what it forbids."""
        self.assertEqual([], user_agent_instructions(
            "Never set a custom User-Agent to get past a 403; it is not a working remedy.\n"))

    def test_the_prohibition_is_stated_where_the_temptation_is(self):
        self.assertRegex(
            flat(fetch_integrity_section()), r"(?i)never set a misleading user-agent",
            "The prohibition belongs in the fetch section itself. A reader hitting the 403 "
            "reaches for the User-Agent workaround precisely here, and a rule stated "
            "elsewhere is one they will not be reading at that moment.",
        )


if __name__ == "__main__":
    unittest.main()


class EveryFetchStepDistinguishesRefusalFromThrottle(unittest.TestCase):
    """INV-292 binds every step that fetches from the two-URL provider, not only Module 4.

    module-03b instructs falling back to `citation.source_download_url` — the URL measured
    to 403 against the Python stdlib client — and documented only the THROTTLE case (retry
    with backoff on HTTP 429). It runs BEFORE Module 4, so a Bootcamper taking that fallback
    met the refusal with no remedy and Module 4's contract had not been read yet.

    ⚠️ Found while registering the invariant, by sweeping for the rule rather than reading
    the deferral's file list (INV-246). A non-2xx rule that covers one status is the half
    that fails silently.
    """

    M04 = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
           "module-04-data-collection" / "SKILL.md")
    M03B = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
            "module-03b-truthset-visualization" / "phase1-visualization.md")

    def flat(self, path):
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    def refusal_block(self):
        """module-03b's INV-292 sub-bullet ONLY.

        ⚠️ Checked against the whole file, the before-Module-4 assertion passed with that
        clause deleted — satisfied by a pre-existing parenthetical 11 lines away that also
        says "it runs before Module 4", about the egress host. An assertion a neighboring
        sentence can satisfy is not an assertion about the clause it names.
        """
        text = self.M03B.read_text(encoding="utf-8")
        start = text.index("(INV-292) A 403 on that fallback")
        return re.sub(r"\s+", " ", text[start:text.index("\n   2.", start)])

    def test_module_4_states_the_refusal_rule(self):
        self.assertRegex(
            self.flat(self.M04), r"(?i)On 403, do not retry — switch URLs",
            "Module 4 must keep the refusal branch — it is where the 403 was measured.",
        )

    def test_module_3b_also_states_it(self):
        """The half that was missing, asserted by CLAIM rather than by one phrasing."""
        self.assertRegex(
            self.flat(self.M03B), r"(?i)403.{0,60}REFUSAL, not a throttle",
            "module-03b instructs a fallback to source_download_url, the URL measured to "
            "403. Documenting only HTTP 429 leaves the refusal case unhandled at the step "
            "that reaches it first (INV-292).",
        )

    def test_module_3b_says_what_to_do_instead_of_retrying(self):
        self.assertRegex(
            self.flat(self.M03B), r"(?i)switch back to `?citation\.download_url",
            "naming the failure without naming the recovery leaves the guide knowing a "
            "retry is wrong and not knowing what is right.",
        )

    def test_module_3b_says_why_module_4s_contract_does_not_cover_it(self):
        """⚠️ The ordering is the reason this must be stated twice rather than once."""
        self.assertRegex(
            self.refusal_block(), r"(?i)runs \*\*before\*\* Module 4",
            "the reason 3b states the remedy itself — rather than pointing at Module 4 — is "
            "that 3b runs first. Delete that and a later editor merges the two and "
            "reintroduces the gap.",
        )

    def test_neither_step_teaches_a_user_agent_workaround(self):
        for path in (self.M04, self.M03B):
            with self.subTest(file=path.name):
                self.assertRegex(
                    self.flat(path), r"(?i)[Nn]ever set a misleading User-Agent",
                    "a client-identity workaround must be forbidden wherever the 403 is "
                    "reachable, not only where it was first measured.",
                )
