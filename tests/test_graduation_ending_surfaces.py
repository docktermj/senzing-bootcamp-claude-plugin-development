"""Every surface describing graduation's ending must describe the same ending.

INV-057 is precise about how the bootcamp stops: the terminal "END OF SENZING BOOTCAMP"
banner is presented exactly once, as the **final output**, after the Bootcamper declines
further exploration — and never while exploration continues. `graduation/SKILL.md`
implements that correctly.

`commands/graduate.md` did not. It said graduation should "end with the guaranteed-recap
announcement and the single closing question" — wording that predates INV-057, omits the
banner entirely, and describes the closing question as the last thing that happens. The
slash command is a first-class entry point, so a Bootcamper who typed `/graduate` was
driven from a description of the wrong ending. Nothing caught it because every test looked
at the skill, which was right.

The lesson is the one `test_tab_set_is_singular.py` already learned for tabs: agreement
between files is exactly what cannot be inferred from the file that was edited. Pinned
here for graduation's two ending surfaces, plus the graduation-offer question, which the
plugin itself asks to be kept "identical to module-completion.md" across two files — an
instruction with no enforcement until now.

#894 adds one plain line after the banner, pinned verbatim, so the last thing the
Bootcamper sees names `/package-bootcamp`: "Run `/package-bootcamp` anytime to bundle your
bootcamp results into one zip you can archive, move to another machine, or share with
others." That line, not the banner, is now the final output. It is a statement with no 👉
and no `?`, and names no archive path, because graduation runs no packager (INV-251).
`TheEndingNamesThePackager` pins it in graduation's item 4 and checks, on every discovered
ending surface, that `/package-bootcamp` is mentioned after the last banner mention.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

GRADUATION_SKILL = PLUGIN / "skills" / "graduation" / "SKILL.md"
GRADUATE_COMMAND = PLUGIN / "commands" / "graduate.md"
MODULE_COMPLETION = PLUGIN / "skills" / "bootcamp-onboarding" / "module-completion.md"
MODULE_07_PHASE1 = (
    PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
)

TERMINAL_BANNER = "END OF SENZING BOOTCAMP"

# The graduation offer, which must be worded identically wherever it is presented.
OFFER = re.compile(r"👉 \*\*Would you like to graduate now[^*]*\*\*")

#: Non-vacuity FLOORS, not site sets. The scans below decide what is checked (INV-246);
#: these only stop a broken pattern degrading a guard to silence.
KNOWN_ENDING_SURFACES = (GRADUATION_SKILL, GRADUATE_COMMAND)
KNOWN_OFFER_SITES = (MODULE_COMPLETION, MODULE_07_PHASE1)


def shipped_markdown():
    return sorted(PLUGIN.rglob("*.md"))


def ending_surfaces():
    """Every surface telling the reader how graduation finishes — discovered, not listed."""
    return tuple(p for p in shipped_markdown()
                 if TERMINAL_BANNER in p.read_text(encoding="utf-8"))


def offer_sites():
    """Every surface presenting the graduation offer — discovered, not listed.

    INV-246: the constants these replace encoded where the author noticed each pattern,
    under comments claiming "wherever it is presented". A third surface gaining either
    would have left this guard green.
    """
    return tuple(p for p in shipped_markdown()
                 if OFFER.search(p.read_text(encoding="utf-8")))

# The one line shown right after the banner's fence (#894), pinned verbatim.
PACKAGE_LINE = (
    "Run `/package-bootcamp` anytime to bundle your bootcamp results into one zip you can "
    "archive, move to another machine, or share with others."
)
PACKAGE_COMMAND = "/package-bootcamp"

# Graduation's closing step, item 4: from its numbered heading to the end of its section.
ITEM_4 = re.compile(r"^4\. \*\*Terminal banner\b.*?(?=^## |\Z)", re.S | re.M)

# The fenced banner block, wherever it is indented.
BANNER_FENCE = re.compile(r"^[ \t]*```text\n(?:(?!```).)*?" + re.escape(TERMINAL_BANNER)
                          + r"(?:(?!```).)*?^[ \t]*```[ \t]*$", re.S | re.M)

# Ordering language: the banner follows the Bootcamper declining, it is not the reply to
# the closing question itself.
DECLINE_CUES = ("declin", "done", "nothing else", "keep exploring")

# Prose distance, in characters, between the banner's render site and the condition that
# governs it. Generous because graduation/SKILL.md spells the decline branch out at
# length (the stand-down-the-Stop-hook step sits between the two).
CUE_WINDOW = 1600


def read(path):
    return path.read_text(encoding="utf-8")


class TheDerivedSiteSetsAreNotVacuous(unittest.TestCase):
    """INV-246: both sets are scanned, so a third surface is covered on sight."""

    def test_the_known_ending_surfaces_are_still_found(self):
        found = ending_surfaces()
        for known in KNOWN_ENDING_SURFACES:
            with self.subTest(file=known.name):
                self.assertIn(known, found,
                              "%s no longer carries the terminal banner, so the ending-surface "
                              "scan is inspecting a smaller set than it believes" % known.name)

    def test_the_known_offer_sites_are_still_found(self):
        found = offer_sites()
        for known in KNOWN_OFFER_SITES:
            with self.subTest(file=known.name):
                self.assertIn(known, found,
                              "%s no longer matches the graduation offer, so the offer scan is "
                              "inspecting a smaller set than it believes" % known.name)


class TestEndingSurfacesAgree(unittest.TestCase):

    def test_every_ending_surface_names_the_terminal_banner(self):
        missing = [
            str(p.relative_to(REPO_ROOT))
            for p in ending_surfaces()
            if TERMINAL_BANNER not in read(p)
        ]
        self.assertEqual(
            [],
            missing,
            f"surface(s) describing graduation's ending without naming the "
            f"'{TERMINAL_BANNER}' banner (INV-057): {missing}",
        )

    def test_every_ending_surface_conditions_the_banner_on_a_decline(self):
        """Naming the banner is not enough; it must not read as unconditional.

        Checks whether *any* mention carries the condition, not the first: both surfaces
        legitimately foreshadow the banner in their opening prose before specifying it.
        """
        offenders = []
        for path in ending_surfaces():
            text = read(path)
            conditioned = False
            for m in re.finditer(re.escape(TERMINAL_BANNER), text):
                window = text[
                    max(0, m.start() - CUE_WINDOW) : m.start() + CUE_WINDOW
                ].lower()
                if any(cue in window for cue in DECLINE_CUES):
                    conditioned = True
                    break
            if not conditioned:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            [],
            offenders,
            "surface(s) naming the terminal banner without tying it to the Bootcamper "
            f"declining further exploration (INV-057): {offenders}",
        )

    def test_the_banner_is_described_after_the_closing_question(self):
        """Structural, not prose-matching: order on the page encodes order in the flow.

        Prose matching cannot tell the correct "end the graduation *turn* on the closing
        question" from the defect's "end *with* the closing question" — both contain the
        same words. Position can: whatever a surface says, the banner has to come after
        the question it follows.

        Anchored on the LAST banner mention — its render site. Both surfaces foreshadow
        the banner in their opening prose, so the first mention says nothing about order.
        """
        for path in ending_surfaces():
            with self.subTest(path=path.name):
                text = read(path)
                question = text.find("anything else you would like to explore")
                banner = text.rfind(TERMINAL_BANNER)
                self.assertNotEqual(-1, question, "closing question not found")
                self.assertNotEqual(-1, banner, "terminal banner not found")
                self.assertGreater(
                    banner,
                    question,
                    "the terminal banner is described before the closing question it "
                    "must follow (INV-057)",
                )


def flat(text):
    """Collapse whitespace, so a pinned sentence still matches where a surface wraps it."""
    return " ".join(text.split())


def item_4(text):
    """Graduation's closing step, item 4, or None when the heading is not found."""
    m = ITEM_4.search(text)
    return m.group(0) if m else None


def item_4_problems(text):
    """What item 4 gets wrong about the package line; empty when it is right.

    A function of the text, not of the file, so the controls below can feed it a mutant.
    """
    item = item_4(text)
    if item is None:
        return ["graduation's item 4 ('4. **Terminal banner') was not found"]
    fence = BANNER_FENCE.search(item)
    if fence is None:
        return ["item 4 has no ```text fence holding the terminal banner"]
    problems = []
    if PACKAGE_COMMAND in fence.group(0):
        problems.append("the package line sits inside the banner's fence")
    after = item[fence.end():]
    following = [line.strip() for line in after.splitlines() if line.strip()]
    if not following or following[0] != PACKAGE_LINE:
        problems.append("the first line after the banner's fence is not the pinned package "
                        "line: %r" % (following[0] if following else None))
    if item.count(PACKAGE_LINE) != 1:
        problems.append("item 4 carries the pinned line %d times, not once"
                        % item.count(PACKAGE_LINE))
    if "That line is the final output." not in after:
        problems.append("item 4 does not say the package line is the final output")
    if "No 👉 question follows it" not in after:
        problems.append("item 4 does not say that no 👉 question follows the package line")
    return problems


class TheEndingNamesThePackager(unittest.TestCase):
    """#894: the last thing the Bootcamper sees reminds them `/package-bootcamp` exists."""

    def test_the_pinned_line_has_no_question_and_no_path(self):
        self.assertNotIn("👉", PACKAGE_LINE)
        self.assertNotIn("?", PACKAGE_LINE)
        for path_shape in ("backups/", ".zip", "\\"):
            self.assertNotIn(path_shape, PACKAGE_LINE,
                             "the package line names an archive path, and graduation runs no "
                             "packager, so none exists yet (INV-251)")

    def test_item_4_shows_the_pinned_line_right_after_the_banner(self):
        self.assertEqual([], item_4_problems(read(GRADUATION_SKILL)))

    def test_the_pinned_line_appears_once_in_graduation(self):
        self.assertEqual(1, read(GRADUATION_SKILL).count(PACKAGE_LINE),
                         "the pinned package line must appear exactly once in graduation, "
                         "together with the banner")

    def test_item_4_shows_it_on_every_path_and_preset(self):
        item = item_4(read(GRADUATION_SKILL))
        self.assertIsNotNone(item)
        after = item[item.index(PACKAGE_LINE):]
        self.assertIn("after Step 2's Abort", after)
        self.assertIn("under every verbosity preset, including `minimal`", after)

    def test_the_command_surface_gives_the_same_order(self):
        text = flat(read(GRADUATE_COMMAND))
        line = text.find(PACKAGE_LINE)
        self.assertNotEqual(-1, line,
                            "commands/graduate.md does not carry the pinned package line")
        self.assertGreater(line, text.rfind(TERMINAL_BANNER),
                           "commands/graduate.md puts the package line before the banner")
        self.assertIn("That line is the final output (INV-057): no 👉 question follows it.",
                      text)

    def test_graduation_says_it_ends_on_the_banner_and_its_line(self):
        text = flat(read(GRADUATION_SKILL))
        ends = re.findall(r"ends on the (?:terminal )?END OF SENZING BOOTCAMP banner and its "
                          r"one `/package-bootcamp` line \(INV-057\)", text)
        self.assertEqual(2, len(ends),
                         "the overview and the preface's closing sentence must both say "
                         "graduation ends on the banner and its one /package-bootcamp line")
        self.assertNotRegex(text, r"ends on the (?:terminal )?END OF SENZING BOOTCAMP banner "
                                  r"\(INV-057\)")

    def test_the_packager_is_named_after_the_banner_on_every_ending_surface(self):
        """Structural, in the style of `test_the_banner_is_described_after_the_closing_question`.

        Anchored on the LAST banner mention, its render site: the opening prose of both
        surfaces names the packager before the banner's render site, which says nothing
        about what the Bootcamper sees last.
        """
        for path in ending_surfaces():
            with self.subTest(path=path.name):
                text = read(path)
                banner = text.rfind(TERMINAL_BANNER)
                self.assertNotEqual(-1, banner, "terminal banner not found")
                self.assertGreater(
                    text.rfind(PACKAGE_COMMAND),
                    banner,
                    "%s does not mention /package-bootcamp after its last mention of the "
                    "terminal banner (#894)" % path.name,
                )


class TheItem4CheckIsNotVacuous(unittest.TestCase):
    """The checker fails each defect it exists to catch, on a mutant of the shipped text."""

    def setUp(self):
        self.text = read(GRADUATION_SKILL)
        self.assertEqual([], item_4_problems(self.text))

    def test_a_missing_line_fails(self):
        self.assertTrue(item_4_problems(self.text.replace(PACKAGE_LINE, "")))

    def test_a_line_inside_the_fence_fails(self):
        mutant = self.text.replace(TERMINAL_BANNER + "  🎓🎓🎓",
                                   TERMINAL_BANNER + "  🎓🎓🎓\n" + PACKAGE_LINE)
        mutant = mutant.replace("```\n\n     " + PACKAGE_LINE + "\n", "```\n", 1)
        self.assertNotEqual(self.text, mutant)
        self.assertTrue(item_4_problems(mutant))

    def test_a_reworded_line_fails(self):
        mutant = self.text.replace(PACKAGE_LINE, PACKAGE_LINE.replace("anytime", "now"))
        self.assertTrue(item_4_problems(mutant))

    def test_a_dropped_final_output_sentence_fails(self):
        mutant = self.text.replace("That line is the final output.", "")
        self.assertTrue(item_4_problems(mutant))


class TestGraduationOfferIsWordedOnce(unittest.TestCase):
    """module-completion.md asks Module 7 to keep this wording identical to its own."""

    def test_the_offer_appears_in_both_surfaces(self):
        for path in offer_sites():
            with self.subTest(path=path.name):
                self.assertTrue(
                    OFFER.search(read(path)),
                    f"{path.relative_to(REPO_ROOT)} no longer presents the graduation "
                    "offer in the expected pinned form",
                )

    def test_the_offer_is_identical_in_both_surfaces(self):
        found = {p.name: OFFER.findall(read(p)) for p in offer_sites()}
        wordings = {w for hits in found.values() for w in hits}
        self.assertEqual(
            1,
            len(wordings),
            "the graduation offer is worded differently across its two surfaces, which "
            f"module-completion.md explicitly forbids: {sorted(wordings)}",
        )


if __name__ == "__main__":
    unittest.main()
