"""The shipped example recap shows every recap element the #465 producing steps write.

Graduation (`graduation/SKILL.md`) and `module-completion.md` both point to
`docs/examples/bootcamp_recap.example.md` as the shape to follow, and graduation suggests showing
its PDF to the Bootcamper (INV-065). The #465 sub-issues each changed a producing step and left
the example behind, so it showed one of their elements (the headline entity) and none of the
others. This guard reads the example and fails, naming the element, unless it carries all five:

1. **The headline entity** (INV-355): a `**Headline entity:**` block in Query, Visualize and
   Discover's Information Shared.
2. **A `You directed:` line** (INV-354) in the End-of-Module Summary of each hands-on module, Data
   Quality, Mapping, and Transformation, Data processing, and Query, Visualize and Discover:
   exactly one, after `**Why it matters:**`.
3. **A prediction line** (INV-357) in some module's Questions & Responses, in the format
   `ground-rules.md` → "Predictions before results" gives:
   `- **{the 👉 question}** — {prediction} → {engine's call} (agreed)` or `(differed)`.
4. **The handover** (INV-358, INV-258): exactly one well-formed `BOOTCAMP-HANDOVER` fence, after
   the notes fence, with the four `###` subsections `Decisions you made`, `How you got it built`,
   `Your takeaway` and `Next time`.
5. **A worked steer** (INV-352): a `- Worked steer shown:` line in the Actions Taken of an Act 2
   module (Data collection through Query, Visualize and Discover), at most one per module and none
   anywhere else.

Every check is negative-controlled: each element is removed from a copy of the example, and the
guard must name that element.

Line-scoped by design (#518): every element is a recap line whose shape is fixed by its producing
step, a `**Label:**` line, a bullet, a `###` heading or a fence marker, each written on one line,
so the guard reads lines rather than wrapped phrases.

Source issue: #518.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_MD = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "docs" / "examples"
              / "bootcamp_recap.example.md")

NOTES_START = "<!-- BOOTCAMP-NOTES:START -->"
NOTES_END = "<!-- BOOTCAMP-NOTES:END -->"
HANDOVER_START = "<!-- BOOTCAMP-HANDOVER:START -->"
HANDOVER_END = "<!-- BOOTCAMP-HANDOVER:END -->"

QUERY_MODULE = "Query, Visualize and Discover"
HANDS_ON_MODULES = ("Data Quality, Mapping, and Transformation", "Data processing", QUERY_MODULE)
ACT_2_MODULES = ("Data collection",) + HANDS_ON_MODULES
HANDOVER_PARTS = ("Decisions you made", "How you got it built", "Your takeaway", "Next time")

PREDICTION_LINE = re.compile(r"^- \*\*.+?\*\* — .+ → .+ \((agreed|differed)\)$")
WORKED_STEER = "- Worked steer shown:"

HEADLINE = "the headline entity"
PREDICTION = "a prediction line"
HANDOVER = "the BOOTCAMP-HANDOVER block"
STEER = "a Worked steer shown line"


def directed(module):
    return f"the You directed line in {module}"


def _without_fences(text):
    """The text with the notes and handover fences removed, so neither is read as a module."""
    for start, end in ((NOTES_START, NOTES_END), (HANDOVER_START, HANDOVER_END)):
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
    return text


def modules(text):
    """``{module name: {subsection name: [lines]}}`` for every ``## `` section outside a fence."""
    found = {}
    current = None
    sub = None
    for line in _without_fences(text).splitlines():
        if line.startswith("## "):
            current = found.setdefault(line[3:].split(" — ")[0].strip(), {})
            sub = None
        elif line.startswith("### ") and current is not None:
            sub = current.setdefault(line[4:].strip(), [])
        elif sub is not None:
            sub.append(line)
    return found


def _handover_problems(text):
    starts, ends = text.count(HANDOVER_START), text.count(HANDOVER_END)
    if starts != 1 or ends != 1:
        return [f"{HANDOVER}: expected exactly one START and one END marker, found "
                f"{starts} and {ends}"]
    start, end = text.index(HANDOVER_START), text.index(HANDOVER_END)
    if end < start:
        return [f"{HANDOVER}: its END marker comes before its START marker"]
    if NOTES_END in text and start < text.index(NOTES_END):
        return [f"{HANDOVER}: it is not after the BOOTCAMP-NOTES block"]
    headings = re.findall(r"^### (.+?)\s*$", text[start:end], re.M)
    missing = [part for part in HANDOVER_PARTS if part not in headings]
    if missing:
        return [f"{HANDOVER}: missing the ### subsection(s) {', '.join(missing)}"]
    return []


def missing_elements(text):
    """One problem per element the example lacks, each naming the element."""
    problems = []
    parsed = modules(text)

    shared = parsed.get(QUERY_MODULE, {}).get("Information Shared", [])
    if not any(line.startswith("**Headline entity:**") for line in shared):
        problems.append(f"{HEADLINE}: no **Headline entity:** block in {QUERY_MODULE}'s "
                        "Information Shared")

    for module in HANDS_ON_MODULES:
        summary = parsed.get(module, {}).get("End-of-Module Summary", [])
        lines = [i for i, line in enumerate(summary) if line.startswith("**You directed:**")]
        why = [i for i, line in enumerate(summary) if line.startswith("**Why it matters:**")]
        if len(lines) != 1:
            problems.append(f"{directed(module)}: expected one **You directed:** line in its "
                            f"End-of-Module Summary, found {len(lines)}")
        elif not why or lines[0] < why[0]:
            problems.append(f"{directed(module)}: it is not after **Why it matters:**")

    if not any(PREDICTION_LINE.match(line)
               for subsections in parsed.values()
               for line in subsections.get("Questions & Responses", [])):
        problems.append(f"{PREDICTION}: no Questions & Responses line ends in (agreed) or "
                        "(differed) in the format of ground-rules.md → Predictions before results")

    problems.extend(_handover_problems(text))

    in_act_2 = 0
    for module, subsections in parsed.items():
        for name, lines in subsections.items():
            steers = sum(1 for line in lines if line.startswith(WORKED_STEER))
            if not steers:
                continue
            if module not in ACT_2_MODULES or name != "Actions Taken":
                problems.append(f"{STEER}: found in {module} → {name}, which is not an Act 2 "
                                "module's Actions Taken")
            elif steers > 1:
                problems.append(f"{STEER}: {module} carries {steers}; a module shows at most one")
            else:
                in_act_2 += 1
    if not in_act_2:
        problems.append(f"{STEER}: none in the Actions Taken of an Act 2 module "
                        f"({', '.join(ACT_2_MODULES)})")
    return problems


EXAMPLE = EXAMPLE_MD.read_text(encoding="utf-8")


def _drop_lines(text, predicate):
    return "\n".join(line for line in text.split("\n") if not predicate(line))


class TheExampleShowsEveryElement(unittest.TestCase):

    def test_the_example_parses_into_its_modules(self):
        parsed = modules(EXAMPLE)
        for module in ACT_2_MODULES:
            with self.subTest(module=module):
                self.assertIn(module, parsed)
                self.assertIn("Actions Taken", parsed[module])

    def test_the_example_carries_all_five(self):
        self.assertEqual(
            [], missing_elements(EXAMPLE),
            "bootcamp_recap.example.md lacks recap elements the producing steps write. Add each "
            "in the shape its producing step gives, then re-render the PDF "
            "(tests/test_example_recap_sync.py gives the command).")


class EachRemovalIsNamed(unittest.TestCase):
    """Negative controls: removing one element from a copy fails, naming that element."""

    def assertNamed(self, text, element):
        problems = missing_elements(text)
        self.assertTrue(any(p.startswith(element) for p in problems),
                        f"removing {element!r} was not reported: {problems}")

    def test_the_headline_entity(self):
        self.assertNamed(_drop_lines(EXAMPLE, lambda l: l.startswith("**Headline entity:**")),
                         HEADLINE)

    def test_each_you_directed_line(self):
        for module in HANDS_ON_MODULES:
            with self.subTest(module=module):
                section_start = EXAMPLE.index(f"\n## {module} — ")
                line_start = EXAMPLE.index("\n**You directed:**", section_start)
                line_end = EXAMPLE.index("\n", line_start + 1)
                self.assertNamed(EXAMPLE[:line_start] + EXAMPLE[line_end:], directed(module))

    def test_a_you_directed_line_before_why_it_matters(self):
        section_start = EXAMPLE.index("\n## Data processing — ")
        why = EXAMPLE.index("\n**Why it matters:**", section_start)
        line_start = EXAMPLE.index("\n**You directed:**", section_start)
        line_end = EXAMPLE.index("\n", line_start + 1)
        moved = (EXAMPLE[:why] + EXAMPLE[line_start:line_end] + EXAMPLE[why:line_start]
                 + EXAMPLE[line_end:])
        self.assertNamed(moved, directed("Data processing"))

    def test_the_prediction_lines(self):
        self.assertNamed(_drop_lines(EXAMPLE, lambda l: bool(PREDICTION_LINE.match(l))),
                         PREDICTION)

    def test_the_handover_block(self):
        without = re.sub(re.escape(HANDOVER_START) + r".*?" + re.escape(HANDOVER_END), "",
                         EXAMPLE, flags=re.S)
        self.assertNamed(without, HANDOVER)

    def test_a_second_handover_block(self):
        block = EXAMPLE[EXAMPLE.index(HANDOVER_START):EXAMPLE.index(HANDOVER_END)
                        + len(HANDOVER_END)]
        self.assertNamed(EXAMPLE + "\n" + block + "\n", HANDOVER)

    def test_each_handover_subsection(self):
        for part in HANDOVER_PARTS:
            with self.subTest(part=part):
                self.assertNamed(EXAMPLE.replace(f"### {part}\n", ""), HANDOVER)

    def test_a_handover_before_the_notes(self):
        start = EXAMPLE.index(HANDOVER_START)
        block = EXAMPLE[start:EXAMPLE.index(HANDOVER_END) + len(HANDOVER_END)]
        moved = EXAMPLE.replace(block, "").replace(NOTES_START, block + "\n\n" + NOTES_START)
        self.assertNamed(moved, HANDOVER)

    def test_the_worked_steer(self):
        self.assertNamed(_drop_lines(EXAMPLE, lambda l: l.startswith(WORKED_STEER)), STEER)

    def test_a_worked_steer_outside_act_2(self):
        steer = next(l for l in EXAMPLE.split("\n") if l.startswith(WORKED_STEER))
        moved = EXAMPLE.replace(
            "- No project files are created by this preamble module.",
            "- No project files are created by this preamble module.\n" + steer)
        self.assertNamed(moved, STEER)


if __name__ == "__main__":
    unittest.main()
