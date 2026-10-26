"""Module 5 Phase 1: every worked quality score is its own operands run through the declared formula.

Step 6 of `phase1-quality-assessment.md` declares the score that routes a gate banded to the
percentage point:

    quality_score = 0.70 x completeness + 0.25 x format_consistency + 0.05 x (100 - duplicate_rate)

and then presents a worked assessment block printing each source's three inputs beside its total.
Two of those totals were not the formula applied to the inputs printed next to them (#677, from a
static production-readiness audit of the pinned child release):

* `CUSTOMERS_CRM` printed **82 / 90 / 3** and a total of **78%**, labeled
  `⚠ Acceptable — some gaps`. The formula gives `57.4 + 22.5 + 4.85` = **84.75 → 84.8** — the
  **≥80%** band, whose gate is a statement that continues into Phase 2 in the same turn and asks
  no 👉 question. The example therefore illustrated the non-yielding branch as the 70-79 warning
  gate that ends a turn on a choice.
* `VENDORS_LEGACY` printed **45 / 55 / 12** and a total of **42%**. The formula gives
  `31.5 + 13.75 + 4.4` = **49.65 → 49.7**. Its band — below 70 — and so its label were right by
  luck; the number was not.

⚠️ **Why a prose read does not catch this.** Each line is individually plausible: a quality score,
a band label, a gate. The defect is only visible by *doing the arithmetic the same file declares
two paragraphs earlier*, which is exactly the work a guide copying the example skips. The fix
keeps the formula and the bands as declared (no specification change was requested) and corrects
the worked outputs and the labels derived from them.

**What this file asserts**, all of it read off the shipped file rather than pinned here:

1. Every `w x operand + w x operand + w x (100 - operand) = ... = total` chain in the file uses the
   **declared** weights, multiplies correctly, sums correctly, and rounds half-up to one decimal
   where it shows a rounded figure.
2. Every source in the presented assessment block has a total equal to the formula applied to the
   three inputs printed beside it, rounded to one decimal.
3. Every such total carries the status label the file's own band declaration gives for the band
   that total lands in — and carries no other band's label.
4. A source in the ≥80% band is illustrated as the non-yielding branch: it is not labeled with a
   gating band's label, and the gate's ≥80% branch still carries no 👉 question.

Each check returns its problems, so the negative controls below can run the same code over a
mutated copy of the file and see the defect reported. Standard library only (INV-108).

**Every other shipped worked example, found by scanning (#796).** Until #796 this file read
Module 5 Step 6 only, while Module 4's gap-rate table printed **91.25** for a row the declared
rounding states as **91.3**. It now scans every Markdown file under `plugins/` (through
`tests/_corpus.py`) and reads each worked example of the formula it finds, with the weights and
bands read from Step 6, the one file that declares them (INV-174):

5. Every worked chain, in any file, computes as in check 1.
6. Every presented assessment block, in any file, computes as in check 2.
7. Every **worked table** (a Markdown table whose header names a completeness column and a score
   column) prints, on each row, the formula applied to that row's completeness, with the
   format-consistency and duplicate-rate operands read from their columns or, where the table
   has none, from what its lead-in states ("clean formatting" is 100, "distinct keys" a 0
   duplicate rate). A table that prints neither and states neither is reported. Each score is
   stated to one decimal, a range row reads both ends, and a row naming a band ("the 70-79 band")
   lands every score it prints in that band.
8. Every quality score stated in prose in such a file (`score **80.8**`) is stated to one decimal.
   Only its precision is read: prose does not print the other operands beside it.

INV-405 (a worked example of a computation the guidance declares is that computation applied to
its own printed operands, labeled by the band its value selects) names this file as its enforcer.
It does not establish that a worked example in a shape none of the four readers above parses
follows the formula, that a prose figure's value is right, nor that a live guide recomputes a
Bootcamper's totals, which only `dry-run` phase 3 observes.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of

REPO_ROOT = Path(__file__).resolve().parent.parent
#: The file that DECLARES the computation: its weights, bands and labels are read from here.
PHASE1 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping" / "phase1-quality-assessment.md")
#: The subtree whose Markdown is scanned for worked examples (#796): everything that ships.
SHIPPED = "plugins"

#: The declared formula, read for its weights rather than for its wording. The subtraction is
#: written with a true minus sign (U+2212) in the file; a hyphen is accepted so a later edit that
#: normalizes the glyph does not read as a missing formula.
FORMULA = re.compile(
    r"quality_score\s*=\s*([\d.]+)\s*×\s*completeness"
    r"\s*\+\s*([\d.]+)\s*×\s*format_consistency"
    r"\s*\+\s*([\d.]+)\s*×\s*\(\s*100\s*[−-]\s*duplicate_rate\s*\)")

#: One line of worked arithmetic, after backticks and bold markers are stripped: the three
#: weighted terms, their products, the raw total, and optionally the rounded total after an arrow.
CHAIN = re.compile(
    r"([\d.]+)\s*×\s*([\d.]+)\s*\+\s*([\d.]+)\s*×\s*([\d.]+)"
    r"\s*\+\s*([\d.]+)\s*×\s*\(\s*100\s*[−-]\s*([\d.]+)\s*\)"
    r"\s*=\s*([\d.]+)\s*\+\s*([\d.]+)\s*\+\s*([\d.]+)"
    r"\s*=\s*([\d.]+)(?:\s*→\s*([\d.]+))?")

#: The gate's three bands, as Step 6's threshold list states them.
BAND_PROCEED = re.compile(r"\*\*≥(\d+)% quality score\*\*")
BAND_WARN = re.compile(r"\*\*(\d+)-(\d+)% quality score\*\*")
BAND_FIX = re.compile(r"\*\*<(\d+)% quality score\*\*")

#: The status-label declaration: which label belongs to which band.
LABEL_PROCEED = re.compile(r"`([^`]+)` only at ≥(\d+)%")
LABEL_WARN = re.compile(r"`([^`]+)` *\n? *at (\d+)-(\d+)%")
LABEL_FIX = re.compile(r"`([^`]+)` below (\d+)%")

#: One source stanza inside the presented assessment block.
SOURCE = re.compile(r"^Source: (\S+)\s*$", re.M)
COMPLETENESS = re.compile(r"Field completeness:\s*([\d.]+)%")
CONSISTENCY = re.compile(r"Format consistency:\s*([\d.]+)%")
DUPLICATES = re.compile(r"Duplicate rate:\s*([\d.]+)%")
TOTAL = re.compile(r"Overall quality:\s*([\d.]+)%\s{2}(.+?)\s*$", re.M)

ONE_DP = Decimal("0.1")


def body():
    return PHASE1.read_text(encoding="utf-8")


def rounded(value):
    """One decimal, half-up — the rounding convention the file states beside the formula."""
    return Decimal(value).quantize(ONE_DP, rounding=ROUND_HALF_UP)


def plain(line):
    """A line with Markdown emphasis removed, so arithmetic reads the same in prose and in code."""
    return line.replace("`", "").replace("**", "").replace("*", "")


def weights(text):
    found = FORMULA.search(text)
    if not found:
        return None
    return tuple(Decimal(group) for group in found.groups())


def bands(text):
    """(proceed_floor, warn_low, warn_high) as the threshold list declares them, or None."""
    proceed, warn, fix = (BAND_PROCEED.search(text), BAND_WARN.search(text),
                          BAND_FIX.search(text))
    if not (proceed and warn and fix):
        return None
    return (Decimal(proceed.group(1)), Decimal(warn.group(1)), Decimal(warn.group(2)),
            Decimal(fix.group(1)))


def labels(text):
    """{band key: declared status label}, read off the file's own label declaration."""
    proceed, warn, fix = (LABEL_PROCEED.search(text), LABEL_WARN.search(text),
                          LABEL_FIX.search(text))
    if not (proceed and warn and fix):
        return None
    return {"proceed": proceed.group(1), "warn": warn.group(1), "fix": fix.group(1)}


def band_of(score, floors):
    """Which band a score lands in: 'proceed', 'warn' or 'fix'."""
    proceed_floor, warn_low, _warn_high, _fix_ceiling = floors
    if score >= proceed_floor:
        return "proceed"
    if score >= warn_low:
        return "warn"
    return "fix"


def assessment_block(text):
    """The presented assessment block — the fenced example the guide prints to the Bootcamper."""
    marker = "Data Quality Assessment:"
    if marker not in text:
        return None
    start = text.index(marker)
    end = text.find("```", start)
    return text[start:end if end != -1 else len(text)]


def presented_sources(text):
    """Each source stanza in the presented block, with its operands, total and label."""
    block = assessment_block(text)
    if block is None:
        return None
    out = []
    starts = [(m.start(), m.group(1)) for m in SOURCE.finditer(block)]
    for index, (offset, name) in enumerate(starts):
        stop = starts[index + 1][0] if index + 1 < len(starts) else len(block)
        stanza = block[offset:stop]
        operands = [pattern.search(stanza)
                    for pattern in (COMPLETENESS, CONSISTENCY, DUPLICATES)]
        total = TOTAL.search(stanza)
        if not all(operands) or not total:
            out.append({"name": name, "broken": True})
            continue
        out.append({
            "name": name,
            "completeness": Decimal(operands[0].group(1)),
            "consistency": Decimal(operands[1].group(1)),
            "duplicates": Decimal(operands[2].group(1)),
            "total": Decimal(total.group(1)),
            "printed_total": total.group(1),
            "label": total.group(2).strip(),
        })
    return out


def score(operands, weight):
    """The declared formula, applied."""
    completeness, consistency, duplicates = operands
    return (weight[0] * completeness + weight[1] * consistency
            + weight[2] * (Decimal(100) - duplicates))


def strong_branch(text):
    """The gate's ≥80% bullet, which must stay a statement rather than a question."""
    opening = "**Quality ≥80%:**"
    if opening not in text:
        return None
    start = text.index(opening)
    end = text.find("**Quality 70-79%", start)
    return text[start:end if end != -1 else len(text)]


# --- the checks, each returning its problems so a negative control can run them on a mutant ---


def problems_with_the_arithmetic(text, declared=None):
    """Every worked chain in the file uses the declared weights and computes correctly.

    ``declared`` is the text that declares the formula; by default ``text`` itself. A file
    other than the declaring one may carry no chain at all, so the empty case is reported only
    for the declaring file.
    """
    weight = weights(text if declared is None else declared)
    if weight is None:
        return ["the declared quality_score formula is gone — re-point this guard"]
    out = []
    chains = 0
    for line in text.splitlines():
        found = CHAIN.search(plain(line))
        if not found:
            continue
        chains += 1
        parts = found.groups()
        used = (Decimal(parts[0]), Decimal(parts[2]), Decimal(parts[4]))
        operands = (Decimal(parts[1]), Decimal(parts[3]), Decimal(parts[5]))
        products = (Decimal(parts[6]), Decimal(parts[7]), Decimal(parts[8]))
        raw, shown = Decimal(parts[9]), parts[10]
        if used != weight:
            out.append("a worked chain uses weights %s where the formula declares %s: %r"
                       % (used, weight, line.strip()))
            continue
        expected = (used[0] * operands[0], used[1] * operands[1],
                    used[2] * (Decimal(100) - operands[2]))
        for index, (got, want) in enumerate(zip(products, expected)):
            if got != want:
                out.append("term %d of a worked chain is %s, not %s: %r"
                           % (index + 1, got, want, line.strip()))
        total = sum(expected, Decimal(0))
        if raw != total:
            out.append("a worked chain totals %s where its own terms sum to %s: %r"
                       % (raw, total, line.strip()))
        if shown is None:
            if raw != rounded(total):
                out.append("a worked chain shows %s, which is not %s rounded to one decimal: %r"
                           % (raw, total, line.strip()))
        elif Decimal(shown) != rounded(total):
            out.append("a worked chain rounds %s to %s, not to %s: %r"
                       % (total, shown, rounded(total), line.strip()))
    if not chains and declared is None:
        out.append("no worked arithmetic chain was found in the file — re-point this guard")
    return out


def problems_with_the_presented_scores(text, declared=None):
    """Every presented total is the formula applied to the operands printed beside it."""
    weight = weights(text if declared is None else declared)
    if weight is None:
        return ["the declared quality_score formula is gone — re-point this guard"]
    sources = presented_sources(text)
    if sources is None:
        return ["the presented assessment block is gone — re-point this guard"]
    if len(sources) < 2:
        return ["the presented assessment block shows fewer than two sources — re-point "
                "this guard; the example exists to exercise more than one band"]
    out = []
    for source in sources:
        if source.get("broken"):
            out.append("source %s does not print all three inputs and a total" % source["name"])
            continue
        operands = (source["completeness"], source["consistency"], source["duplicates"])
        expected = rounded(score(operands, weight))
        if source["total"] != expected:
            out.append(
                "source %s prints %s%% from %s / %s / %s, where the declared formula gives %s%%"
                % (source["name"], source["printed_total"], operands[0], operands[1],
                   operands[2], expected))
        if Decimal(source["printed_total"]) != rounded(source["printed_total"]):
            out.append("source %s prints %s%%, which is not stated to one decimal"
                       % (source["name"], source["printed_total"]))
    return out


def problems_with_the_presented_labels(text):
    """Every presented label is the one the file declares for that total's band."""
    weight, floors, declared = weights(text), bands(text), labels(text)
    if weight is None or floors is None or declared is None:
        return ["the formula, the band list or the label declaration is gone — re-point "
                "this guard"]
    sources = presented_sources(text)
    if not sources:
        return ["the presented assessment block is gone — re-point this guard"]
    out = []
    for source in sources:
        if source.get("broken"):
            continue
        operands = (source["completeness"], source["consistency"], source["duplicates"])
        computed = rounded(score(operands, weight))
        band = band_of(computed, floors)
        want = declared[band]
        if want not in source["label"]:
            out.append("source %s scores %s%% (%s band) and is labeled %r, which does not "
                       "carry the declared label %r"
                       % (source["name"], computed, band, source["label"], want))
        for other, label in declared.items():
            if other != band and label in source["label"]:
                out.append("source %s scores %s%% (%s band) and carries the %s band's label %r"
                           % (source["name"], computed, band, other, label))
    return out


def problems_with_the_strong_branch(text):
    """A ≥80% example is the non-yielding branch, not the 70-79 warning gate."""
    weight, floors, declared = weights(text), bands(text), labels(text)
    if weight is None or floors is None or declared is None:
        return ["the formula, the band list or the label declaration is gone — re-point "
                "this guard"]
    out = []
    branch = strong_branch(text)
    if branch is None:
        out.append("the gate's ≥80% branch is gone — re-point this guard")
    elif re.search(r"\U0001f449\s*\*\*", branch):
        out.append("the gate's ≥80% branch now carries a 👉 question; a ≥80% example cannot "
                   "illustrate a branch that ends the turn on a choice")
    strong = [s for s in presented_sources(text) or []
              if not s.get("broken")
              and band_of(rounded(score((s["completeness"], s["consistency"], s["duplicates"]),
                                        weight)), floors) == "proceed"]
    if not strong:
        out.append("no presented source lands in the ≥80% band — the band most runs take is "
                   "no longer illustrated")
    for source in strong:
        if declared["warn"] in source["label"] or declared["fix"] in source["label"]:
            out.append("source %s is in the ≥80%% band and carries a gating band's label %r"
                       % (source["name"], source["label"]))
        if "?" in source["label"]:
            out.append("source %s is in the ≥80%% band and its label poses a question: %r"
                       % (source["name"], source["label"]))
    return out


# --- every other shipped worked example, found by scanning (#796, INV-246) ---

#: A Markdown table row, and the delimiter row under a table's header.
TABLE_ROW = re.compile(r"^[ \t>]*\|(.*)\|[ \t]*$")
TABLE_RULE = re.compile(r"^[ \t>]*\|[\s:|-]+\|[ \t]*$")
#: A worked table's score column: "score", "quality score", "quality_score", "overall quality".
SCORE_HEADER = re.compile(r"(?:quality[ _])?score|overall quality")
#: A number in a cell, after emphasis, code marks and the percent sign are dropped. A range
#: ("70.0% – 57.1%") is two numbers joined by a spaced dash; a band row reads both ends.
RANGE = re.compile(r"\s+[–-]\s+")
#: What a worked table's lead-in states when it prints neither a format nor a duplicate operand.
CLEAN_FORMAT = re.compile(r"(?i)\bclean formatting\b|\bformatting (?:is|as) clean\b")
NO_DUPLICATES = re.compile(r"(?i)\bdistinct keys\b|\bno duplicates\b")
#: A band named in a row's first cell ("the 70-79 band").
ROW_BAND = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s+band")
#: A quality score stated in prose: the word, then a bold figure. Only its precision is read,
#: because prose does not print the other operands beside it.
PROSE_SCORE = re.compile(r"(?i)\bscores?\s+\*\*(\d+(?:\.\d+)?)%?\*\*")


def _cell_numbers(cell):
    """The numbers one cell prints, as strings, or None when it is not numeric."""
    plain_cell = cell.replace("*", "").replace("`", "").replace("%", "").strip()
    parts = RANGE.split(plain_cell)
    try:
        [Decimal(x) for x in parts]
    except InvalidOperation:
        return None
    return parts


def _lead_in(lines, start):
    """The paragraph directly above the table that starts at index ``start``, collapsed."""
    k = start - 1
    while k >= 0 and not lines[k].strip().lstrip(">").strip():
        k -= 1
    para = []
    while k >= 0 and lines[k].strip().lstrip(">").strip():
        para.insert(0, lines[k].strip())
        k -= 1
    return " ".join(" ".join(para).split())


def worked_tables(text):
    """Each table whose header names a completeness column and a score column.

    Yields ``(line, header, rows, lead_in)``: ``line`` is the header's 1-based line, ``rows``
    is ``[(line, cells)]`` and ``lead_in`` the paragraph above it.
    """
    lines = text.split("\n")
    i = 0
    while i < len(lines) - 1:
        head = TABLE_ROW.match(lines[i])
        if not (head and TABLE_RULE.match(lines[i + 1])):
            i += 1
            continue
        header = [norm_cell(c) for c in head.group(1).split("|")]
        rows, k = [], i + 2
        while k < len(lines) and TABLE_ROW.match(lines[k]):
            cells = TABLE_ROW.match(lines[k]).group(1).split("|")
            rows.append((k + 1, [c.strip() for c in cells]))
            k += 1
        if (any("completeness" in h for h in header)
                and any(SCORE_HEADER.fullmatch(h) for h in header)):
            yield i + 1, header, rows, _lead_in(lines, i)
        i = k


def norm_cell(cell):
    return " ".join(cell.replace("*", "").replace("`", "").split()).lower()


def problems_with_the_worked_tables(text, declared, name="text"):
    """Every score a worked table prints is the declared formula applied to its own row.

    The completeness operand is the row's own cell. A format-consistency or duplicate-rate
    column is read where the table has one; where it has none, the lead-in must state the
    value (clean formatting is 100, distinct keys a 0 duplicate rate), or that is a problem.
    A row naming a band ("the 70-79 band") must land every score it prints in that band.
    """
    weight, floors = weights(declared), bands(declared)
    if weight is None or floors is None:
        return ["the declared formula or its bands are gone — re-point this guard"]
    out = []
    for line, header, rows, lead_in in worked_tables(text):
        col = {"completeness": next(i for i, h in enumerate(header) if "completeness" in h),
               "score": next(i for i, h in enumerate(header) if SCORE_HEADER.fullmatch(h))}
        for key, word in (("format", "format"), ("duplicates", "duplicate")):
            found = [i for i, h in enumerate(header) if word in h]
            if found:
                col[key] = found[0]
        fixed = {}
        if "format" not in col:
            if not CLEAN_FORMAT.search(lead_in):
                out.append("%s:%d: a worked table prints no format_consistency operand and its "
                           "lead-in states none" % (name, line))
                continue
            fixed["format"] = Decimal(100)
        if "duplicates" not in col:
            if not NO_DUPLICATES.search(lead_in):
                out.append("%s:%d: a worked table prints no duplicate_rate operand and its "
                           "lead-in states none" % (name, line))
                continue
            fixed["duplicates"] = Decimal(0)
        for row_line, cells in rows:
            if len(cells) < len(header):
                continue
            read = {key: _cell_numbers(cells[i]) for key, i in col.items()}
            if read["completeness"] is None or read["score"] is None:
                continue
            ends = len(read["score"])
            if any(v is not None and len(v) != ends for v in read.values()):
                out.append("%s:%d: a worked row prints %d score(s) beside a different number of "
                           "operands" % (name, row_line, ends))
                continue
            band = ROW_BAND.search(norm_cell(cells[0]))
            for end in range(ends):
                operands = (Decimal(read["completeness"][end]),
                            Decimal(read["format"][end]) if "format" in read else fixed["format"],
                            Decimal(read["duplicates"][end]) if "duplicates" in read
                            else fixed["duplicates"])
                printed = read["score"][end]
                want = rounded(score(operands, weight))
                if Decimal(printed) != rounded(printed):
                    out.append("%s:%d: a worked score %s is not stated to one decimal; the "
                               "declared formula gives %s" % (name, row_line, printed, want))
                elif Decimal(printed) != want:
                    out.append("%s:%d: a worked score %s is not the formula applied to its row "
                               "(%s / %s / %s), which gives %s"
                               % (name, row_line, printed, *operands, want))
                if band and band_of(want, floors) != band_of(Decimal(band.group(2)), floors):
                    out.append("%s:%d: the row names the %s-%s band, and its score %s lands in "
                               "another" % (name, row_line, band.group(1), band.group(2), want))
    return out


def problems_with_the_prose_scores(text, name="text"):
    """Every quality score stated in prose is stated to one decimal, the declared precision."""
    out = []
    for flat, origin in collapsed_blocks(text):
        for m in PROSE_SCORE.finditer(flat):
            if Decimal(m.group(1)) != rounded(m.group(1)):
                out.append("%s:%d: the score %s is not stated to one decimal"
                           % (name, line_of(origin, m.start()), m.group(1)))
    return out


def carries_a_worked_example(text):
    """True when ``text`` holds a worked chain, a presented assessment block or a worked table."""
    return bool(any(CHAIN.search(plain(line)) for line in text.splitlines())
                or assessment_block(text) is not None
                or next(worked_tables(text), None))


def worked_files():
    """Every shipped Markdown file carrying a worked example — scanned, never listed (INV-246)."""
    out = []
    for path in corpus_files(SHIPPED, suffixes={".md"}):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if carries_a_worked_example(text):
            out.append(path)
    return out


def problems_in_a_worked_file(text, declared, name="text"):
    """The checks every scanned file takes; the declaring file's own gate checks run apart."""
    out = ["%s: %s" % (name, p) for p in problems_with_the_arithmetic(text, declared)]
    if assessment_block(text) is not None:
        out += ["%s: %s" % (name, p) for p in problems_with_the_presented_scores(text, declared)]
    out += problems_with_the_worked_tables(text, declared, name)
    out += problems_with_the_prose_scores(text, name)
    return out


ALL_CHECKS = (problems_with_the_arithmetic, problems_with_the_presented_scores,
              problems_with_the_presented_labels, problems_with_the_strong_branch)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_file_is_there(self):
        self.assertTrue(PHASE1.is_file(), "phase1-quality-assessment.md moved")

    def test_the_declared_formula_is_found(self):
        self.assertIsNotNone(weights(body()),
                             "the quality_score formula no longer parses; every check here "
                             "reads its weights off the file rather than pinning them")

    def test_the_bands_and_their_labels_are_found(self):
        self.assertIsNotNone(bands(body()), "the ≥80 / 70-79 / <70 threshold list is gone")
        self.assertIsNotNone(labels(body()), "the status-label declaration is gone")

    def test_the_rounding_convention_is_stated(self):
        flat = re.sub(r"\s+", " ", body())
        self.assertRegex(flat, r"(?i)round to one decimal",
                         "the rounding convention the worked totals follow is no longer "
                         "stated, so 84.75 and 49.65 have no declared presentation")

    def test_the_presented_block_is_found_with_its_sources(self):
        sources = presented_sources(body())
        self.assertIsNotNone(sources, "the presented assessment block is gone")
        self.assertGreaterEqual(len(sources), 2, "the presented block lost a source")


class TheWorkedScoresFollowTheDeclaredFormula(unittest.TestCase):
    def test_every_worked_chain_computes(self):
        self.assertEqual([], problems_with_the_arithmetic(body()))

    def test_every_presented_total_is_its_own_operands(self):
        self.assertEqual([], problems_with_the_presented_scores(body()))

    def test_the_two_reported_examples_are_the_ones_fixed(self):
        """#677's two cases, named, so a later edit cannot silently drop them."""
        found = {s["name"]: s for s in presented_sources(body()) if not s.get("broken")}
        for name, operands, total in (
                ("CUSTOMERS_CRM", (82, 90, 3), "84.8"),
                ("VENDORS_LEGACY", (45, 55, 12), "49.7")):
            with self.subTest(source=name):
                self.assertIn(name, found, "the %s example is gone — if it was renamed, "
                                           "re-point this guard" % name)
                source = found[name]
                self.assertEqual(
                    [Decimal(x) for x in operands],
                    [source["completeness"], source["consistency"], source["duplicates"]],
                    "%s's operands changed; the issue settles that the operands stay and "
                    "the outputs follow them" % name)
                self.assertEqual(total, source["printed_total"])


class TheLabelsFollowTheBands(unittest.TestCase):
    def test_every_presented_label_matches_its_band(self):
        self.assertEqual([], problems_with_the_presented_labels(body()))

    def test_the_strong_example_illustrates_the_non_yielding_branch(self):
        self.assertEqual([], problems_with_the_strong_branch(body()))

    def test_the_canonical_formula_and_bands_are_unchanged(self):
        """The issue fixes the examples; the specification stays exactly as declared."""
        self.assertEqual((Decimal("0.70"), Decimal("0.25"), Decimal("0.05")), weights(body()),
                         "the declared weights changed. Correcting the worked examples was "
                         "the whole scope (#677); changing the weights is a specification "
                         "change nobody requested")
        self.assertEqual((Decimal(80), Decimal(70), Decimal(79), Decimal(70)), bands(body()),
                         "the gate boundaries changed; they are fixed as declared (#677)")


def table_file():
    """The first scanned file carrying a worked table, found by the scan rather than named."""
    for path in worked_files():
        if next(worked_tables(path.read_text(encoding="utf-8")), None):
            return path
    return None


class EveryShippedWorkedExampleFollowsTheFormula(unittest.TestCase):
    """#796: the scan reads every worked example under `plugins/`, not Step 6 alone."""

    def test_the_scan_finds_more_than_the_declaring_file(self):
        """⛔ (INV-265) A scan that finds only Step 6 has not widened anything."""
        found = worked_files()
        self.assertIn(PHASE1, found, "the declaring file is no longer found by the scan")
        self.assertTrue([p for p in found if p != PHASE1],
                        "the scan finds no worked example outside Step 6")
        self.assertIsNotNone(table_file(), "the scan finds no worked table anywhere")

    def test_every_scanned_file_follows_the_formula(self):
        declared, problems = body(), []
        for path in worked_files():
            problems += problems_in_a_worked_file(
                path.read_text(encoding="utf-8"), declared,
                path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_every_worked_table_row_is_read(self):
        """Each numeric row of each worked table is recomputed: a parser that skips rows is
        caught here rather than passing on the rows it never read."""
        path = table_file()
        self.assertIsNotNone(path)
        for _line, _header, rows, _lead in worked_tables(path.read_text(encoding="utf-8")):
            numeric = [r for r in rows if _cell_numbers(r[1][-1]) is not None]
            self.assertGreaterEqual(len(numeric), 3, "the worked table lost its rows")


class TheScanSeesTheDefectsOf796(unittest.TestCase):
    """Negative controls on the scanned table's shipped text, each beside its passing form."""

    def setUp(self):
        self.path = table_file()
        self.assertIsNotNone(self.path, "no worked table is found by the scan")
        self.text = self.path.read_text(encoding="utf-8")
        self.declared = body()

    def reported(self, text):
        return problems_in_a_worked_file(text, self.declared, "scanned.md")

    def mutated(self, old, new):
        self.assertIn(old, self.text, "the text this control mutates is gone: %r" % old)
        return self.text.replace(old, new, 1)

    def test_the_shipped_table_passes(self):
        self.assertEqual([], self.reported(self.text))

    def test_the_figure_as_it_shipped_is_reported(self):
        """The #796 defect: 91.25 where the declared rounding states 91.3."""
        problems = self.reported(self.mutated("| **91.3** |", "| **91.25** |"))
        self.assertTrue(any("91.25" in p and "one decimal" in p for p in problems), problems)

    def test_a_rounding_slip_in_the_table_is_reported(self):
        problems = self.reported(self.mutated("| **91.3** |", "| **91.2** |"))
        self.assertTrue(any("91.2 " in p and "91.3" in p for p in problems), problems)

    def test_a_range_end_off_the_formula_is_reported(self):
        problems = self.reported(self.mutated("**79 – 70**", "**79 – 69**"))
        self.assertTrue(any("69" in p for p in problems), problems)

    def test_a_lead_in_that_states_no_format_is_reported(self):
        problems = self.reported(self.mutated("clean formatting", "some formatting"))
        self.assertTrue(any("format_consistency" in p for p in problems), problems)

    def test_a_prose_score_past_one_decimal_is_reported(self):
        problems = self.reported(self.mutated("score **80.8**", "score **80.75**"))
        self.assertTrue(any("80.75" in p for p in problems), problems)

    def test_a_worked_table_in_any_file_is_found(self):
        """The site set is scanned: a new file carrying a worked table is read with no edit here."""
        fixture = ("Clean formatting and distinct keys:\n\n| case | completeness | score |\n"
                   "|---|---|---|\n| one gap | 87.5% | **91.25** |\n")
        self.assertTrue(carries_a_worked_example(fixture))
        self.assertEqual(1, len(problems_with_the_worked_tables(fixture, self.declared)))


class TheGuardsSeeTheDefectTheyWereWrittenFor(unittest.TestCase):
    """Negative controls — each mutation is the shipped defect, or its neighbor."""

    def mutated(self, old, new):
        text = body()
        self.assertIn(old, text, "the text this control mutates is gone: %r" % old)
        return text.replace(old, new, 1)

    def reported(self, text):
        return [problem for check in ALL_CHECKS for problem in check(text)]

    def test_the_original_total_is_reported(self):
        """The shipped defect: 82 / 90 / 3 printed as 78%."""
        problems = self.reported(self.mutated("     84.8%", "       78%"))
        self.assertTrue(any("CUSTOMERS_CRM" in p and "84.8" in p for p in problems),
                        "a total that is not its own operands was not reported: %s" % problems)

    def test_the_second_original_total_is_reported(self):
        problems = self.reported(self.mutated("     49.7%", "       42%"))
        self.assertTrue(any("VENDORS_LEGACY" in p for p in problems),
                        "a total that is not its own operands was not reported: %s" % problems)

    def test_the_mislabeled_band_is_reported(self):
        """The other half of the defect: a ≥80% score wearing the 70-79 warning label."""
        problems = self.reported(
            self.mutated("✅ Strong — continue to mapping",
                         "⚠ Acceptable — some gaps"))
        self.assertTrue(any("CUSTOMERS_CRM" in p for p in problems),
                        "a ≥80%% source labeled with the 70-79 gate was not reported: %s"
                        % problems)

    def test_a_rounding_slip_is_reported(self):
        """84.75 truncated rather than rounded half-up."""
        problems = self.reported(self.mutated("     84.8%", "     84.7%"))
        self.assertTrue(any("CUSTOMERS_CRM" in p for p in problems),
                        "a total rounded the wrong way was not reported: %s" % problems)

    def test_a_weight_that_drifts_from_the_formula_is_reported(self):
        """A worked chain that stops using the declared weights."""
        problems = self.reported(self.mutated("`0.70 × 82", "`0.60 × 82"))
        self.assertTrue(any("weights" in p for p in problems),
                        "a chain using undeclared weights was not reported: %s" % problems)

    def test_an_arithmetic_slip_inside_a_chain_is_reported(self):
        problems = self.reported(self.mutated("`57.4 + 22.5 + 4.85`", "`57.4 + 22.5 + 4.95`"))
        self.assertTrue(problems, "a mis-multiplied term was not reported")

    def test_a_question_in_the_strong_branch_is_reported(self):
        branch = strong_branch(body())
        self.assertIsNotNone(branch, "the gate's ≥80% branch is gone — re-point this guard")
        problems = problems_with_the_strong_branch(
            body().replace(branch, branch + "\n\n  \U0001f449 **Shall we continue?**\n"))
        self.assertTrue(any("👉" in p for p in problems),
                        "a 👉 question added to the ≥80%% branch was not reported: %s"
                        % problems)


if __name__ == "__main__":
    unittest.main()
