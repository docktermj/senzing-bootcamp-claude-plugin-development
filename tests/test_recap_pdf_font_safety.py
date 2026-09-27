"""No text path may hand fpdf2's Latin-1 core font a character it cannot encode.

The recap PDF has two renderers: a designed fpdf2 one and a plainer stdlib fallback.
INV-048 wants the professional-looking artifact, so the fpdf2 path is the one bootcampers
should normally get; INV-111 requires *saying* when a fallback happens. Both worked. What
failed was subtler and only a dry run against a realistic recap exposed it.

`_clip()` truncated with a U+2026 "…" — and every call site is `_clip(_safe(x), n)`, so
`_safe` runs **first** and never sees the character `_clip` appends afterwards. fpdf2 then
raised `Character "…" … outside the range of characters supported by the font used`,
`render_with_fpdf2` caught it exactly as designed, and the only visible symptom was the
bootcamper quietly receiving the plainer PDF. `_UNICODE_MAP` already mapped "…" to "..." —
the defect was purely order of operations.

It fired on the cover's module chips, `_clip(..., 46)`. "Data Quality, Mapping, and
Transformation", the longest real module title, is 41 characters, and nothing a real recap
appends pushes it over: `parse_recap` splits a timestamp or the `— in progress` marker off
the title before the chip is built, and even a two-digit number prefix makes only 45. That
is why no realistic fixture caught it — every one sits under the threshold — and why the
chip clip is pinned here by unit test, with the width read from the generator's own call
site rather than restated.

What this pins:

* `_clip` introduces nothing outside Latin-1, at every width the source actually uses.
* The shipped composition order `_clip(_safe(x))` survives adversarial input.
* `_UNICODE_MAP` covers the non-ASCII characters the plugin's own recap templates use.
* The cover chip: `parse_recap` strips `— in progress`, the 41-character title is not
  clipped at the chip width, and a title over it is.
* End-to-end (skipped without fpdf2, which is not stdlib — INV-108): a recap whose title
  is long enough to clip still renders with **fpdf2**, not the fallback.

Enforces **INV-159** (no character of a Bootcamper-authored value is reduced to `?` -- the
name above all, which the certificate prints largest; an unprintable name warns and falls
back to the placeholder rather than being transliterated), which names this file.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"
)


def load_generator():
    """Import the generator by path.

    It must be registered in ``sys.modules`` before ``exec_module``: the generator
    defines dataclasses, and ``dataclasses._is_type`` resolves annotations through
    ``sys.modules[cls.__module__]``, which is ``None`` for an unregistered module.
    """
    import sys

    spec = importlib.util.spec_from_file_location("_recap_gen", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()

# Characters the plugin's own recap templates and module names actually contain.
TEMPLATE_CHARS = ("—", "…", "·", "→", "’", "“", "”", "✅", "👉", "⏱️")

# Characters the *bootcamper's own* deliverables carry, which the plugin's
# templates never emit — so scanning the templates could not find them. `↔` and
# `⚠️` shipped as `?` in both PDFs for exactly that reason: a source-pair table
# read "GLEIF ? OPEN-OWNERSHIP" and every caveat began "??". The variation
# selector that trails an emoji is its own character and needs its own entry.
#
# ⛔ This list is about what a *generated deliverable* can contain, not what the
# plugin writes. Add to it whenever a generator learns to render new content.
DELIVERABLE_CHARS = (
    "↔", "⚠️", "⚠", "️", "≈", "±", "×", "–", "•", "⛔",
    "≤", "≥", "≠", "∞", "€", "™", "⇒", "↑", "↓", "←",
    "‑",  # non-breaking hyphen — indistinguishable from "-" on sight
    "​",  # zero-width space — invisible, and it corrupted to "?" all the same
)

# The Bootcamper's own **name**, which INV-134 detects from `git config user.name` and the
# certificate prints in 34 pt. The inventory above is punctuation and symbols, so nothing
# covered a name in a non-Latin script and `_safe` reduced 李明 to "??" on the one page a
# Bootcamper frames — silently, at exit 0. A name is what a generated deliverable carries
# most certainly of all.
NAME_PROBES = (
    "李明",                 # Chinese
    "山田太郎",              # Japanese
    "김민준",                # Korean
    "Владимир Петров",      # Cyrillic
    "أحمد حسن",             # Arabic
    "Δημήτρης Παπαδόπουλος",  # Greek
    "אברהם לוי",            # Hebrew
    "李明 (Li Ming)",        # mixed: the Latin part must survive
)

# Latin-script names whose letters the core fonts lack. These MUST fold to readable ASCII
# rather than being dropped: "ukasz" is not a lesser rendering of "Łukasz", it is a
# different name.
FOLDING_NAMES = {
    "Łukasz Wiśniewski": "Lukasz Wisniewski",
    "Ngô Bảo Châu": "Ngo Bao Chau",
    "Đặng Thị Hương": "Dang Thi Huong",
    "Ólafur Ægisson": "Ólafur Ægisson",  # already Latin-1; must pass through untouched
}

# A title long enough to clip at every width the source uses, built from the longest
# real module name so the case stays realistic rather than synthetic.
LONG_TITLE = "Data Quality, Mapping, and Transformation for the Customer Domain"


def latin1_ok(s):
    try:
        s.encode("latin-1")
        return True
    except UnicodeEncodeError:
        return False


def clip_widths():
    """Every width `_clip` is called with in the generator.

    The one-line pattern cannot see a call whose first argument has its own parentheses,
    so on its own it found 46 only in the `_clip` docstring's prose (checked 2026-09-26).
    The chip width is added from its own call site, so the loops below keep testing it
    even if that prose is reworded.
    """
    src = GENERATOR.read_text(encoding="utf-8")
    widths = {int(n) for n in re.findall(r"_clip\([^)]*?,\s*(\d+)\s*\)", src, re.S)}
    return widths | {chip_width()}


# The cover chip's call site, matched on the label expression it clips so the width below
# is the chip's and no other call site's. If the label expression changes, this stops
# matching and `chip_width()` fails loudly rather than measuring the wrong thing.
CHIP_CALL_RE = re.compile(
    r'_clip\(\s*_safe\(\s*f"\{mod\.number\}\. \{mod\.title\}"\s*'
    r"if mod\.number is not None\s*else mod\.title\s*\)\s*,\s*(\d+)\s*,?\s*\)",
    re.S,
)

# The longest real module title (the Bootcamp preparation module table).
LONGEST_REAL_TITLE = "Data Quality, Mapping, and Transformation"


def chip_width():
    """The width the cover's module chips are clipped at, read from the generator."""
    found = CHIP_CALL_RE.findall(GENERATOR.read_text(encoding="utf-8"))
    if len(found) != 1:
        raise AssertionError(
            f"expected exactly one cover-chip _clip call site, parsed {len(found)}"
        )
    return int(found[0])


def chip_label(mod):
    """The label the cover builds for a module — the expression CHIP_CALL_RE matches."""
    return f"{mod.number}. {mod.title}" if mod.number is not None else mod.title


class TestClipStaysLatin1(unittest.TestCase):

    def test_clip_widths_were_found(self):
        """If the call sites stop parsing, the width loop below goes vacuous."""
        self.assertTrue(clip_widths(), "no _clip(x, n) call sites parsed from the source")

    def test_clip_introduces_nothing_outside_latin1(self):
        for width in sorted(clip_widths()):
            with self.subTest(width=width):
                out = GEN._clip(LONG_TITLE, width)
                self.assertLess(len(out), len(LONG_TITLE), "input must actually clip")
                self.assertTrue(
                    latin1_ok(out),
                    f"_clip(..., {width}) produced a non-Latin-1 character: {out!r}. "
                    "Every call site is _clip(_safe(x), n), so _safe cannot sanitize "
                    "what _clip appends — the suffix must be ASCII.",
                )

    def test_the_shipped_composition_order_survives(self):
        """_clip(_safe(x)) is the order in the source; it must be encodable."""
        for width in sorted(clip_widths()):
            for probe in (LONG_TITLE, LONG_TITLE + " — 2026-07-26T14:00:00-07:00"):
                with self.subTest(width=width, probe=probe[:30]):
                    self.assertTrue(latin1_ok(GEN._clip(GEN._safe(probe), width)))

    def test_safe_alone_handles_every_template_character(self):
        for ch in TEMPLATE_CHARS:
            with self.subTest(char=ch):
                self.assertTrue(
                    latin1_ok(GEN._safe(f"prefix {ch} suffix")),
                    f"_safe does not reduce {ch!r} to Latin-1; add it to _UNICODE_MAP",
                )

    def test_safe_handles_characters_the_deliverables_carry(self):
        """Latin-1-encodable is necessary but not sufficient — `?` is encodable."""
        for ch in DELIVERABLE_CHARS:
            with self.subTest(char=ch):
                out = GEN._safe(f"prefix {ch} suffix")
                self.assertTrue(
                    latin1_ok(out),
                    f"_safe does not reduce {ch!r} to Latin-1; add it to _UNICODE_MAP",
                )
                self.assertNotIn(
                    "?", out,
                    f"_safe replaced {ch!r} with '?' — encodable, but the reader sees "
                    "a corrupted glyph. Map it to an ASCII equivalent instead.",
                )


class TestTheCoverChipClip(unittest.TestCase):
    """The chip clip no realistic recap reaches, pinned where a fixture cannot pin it.

    The dry-run scaffold's banner once gave a recipe for reaching this clip with its
    `— in progress` heading. Measured 2026-09-24, it did not: the parser strips the suffix,
    so the chip was the bare 41-character title. These assertions state what holds.
    Pure stdlib; they never skip.
    """

    def setUp(self):
        self.width = chip_width()

    def test_parse_recap_strips_the_in_progress_suffix(self):
        recap = GEN.parse_recap(
            f"# R\n\n## {LONGEST_REAL_TITLE} — in progress\n\n### Information Shared\n- x\n"
        )
        self.assertEqual([LONGEST_REAL_TITLE], [m.title for m in recap.modules])
        self.assertEqual("in progress", recap.modules[0].date)
        self.assertEqual(LONGEST_REAL_TITLE, chip_label(recap.modules[0]))

    def test_the_longest_real_title_is_not_clipped_at_the_chip_width(self):
        for label in (LONGEST_REAL_TITLE, f"10. {LONGEST_REAL_TITLE}"):
            with self.subTest(label=label):
                self.assertLessEqual(len(label), self.width)
                self.assertEqual(label, GEN._clip(GEN._safe(label), self.width))

    def test_a_title_over_the_chip_width_is_clipped(self):
        recap = GEN.parse_recap(
            f"# R\n\n## {LONG_TITLE} — in progress\n\n### Actions Taken\n- x\n"
        )
        label = chip_label(recap.modules[0])
        self.assertEqual(LONG_TITLE, label)
        self.assertGreater(len(label), self.width, "the probe must exceed the chip width")
        clipped = GEN._clip(GEN._safe(label), self.width)
        self.assertNotEqual(label, clipped)
        self.assertTrue(clipped.endswith("..."), clipped)
        self.assertTrue(label.startswith(clipped[:-3]), clipped)


class TestNamesAreNeverCorrupted(unittest.TestCase):
    """The Bootcamper's name, which the certificate prints at 34 pt (INV-143/INV-113)."""

    def test_a_non_latin_name_never_becomes_question_marks(self):
        for name in NAME_PROBES:
            with self.subTest(name=name):
                out = GEN._safe(name)
                self.assertNotIn(
                    "?", out,
                    f"_safe turned {name!r} into {out!r} — '??' on a certificate is the "
                    "exact failure INV-143 forbids.",
                )
                self.assertTrue(latin1_ok(out))

    def test_the_latin_part_of_a_mixed_name_survives(self):
        """Dropping the unprintable half must not take the printable half with it."""
        self.assertIn("Li Ming", GEN._safe("李明 (Li Ming)"))

    def test_latin_script_names_fold_rather_than_lose_letters(self):
        for name, expected in FOLDING_NAMES.items():
            with self.subTest(name=name):
                self.assertEqual(expected, GEN._safe(name))

    def test_unprintable_characters_are_reported_not_just_dropped(self):
        self.assertEqual(["李", "明"], GEN._unrepresentable("李明"))
        self.assertEqual([], GEN._unrepresentable("Ada Lovelace"))
        self.assertEqual([], GEN._unrepresentable("Łukasz"), "a foldable letter is not lost")

    def test_an_unprintable_name_is_flagged_for_the_INV_113_question(self):
        recap = GEN.parse_recap("# R\n\n**Bootcamper:** 李明\n\n## M — 2026-07-20\n")
        name, lost = GEN.recap_certificate_name_unprintable(recap)
        self.assertEqual("李明", name)
        self.assertEqual(["李", "明"], lost)
        self.assertEqual(("", []), GEN.recap_certificate_name_unprintable(
            GEN.parse_recap("# R\n\n**Bootcamper:** Ada Lovelace\n\n## M — 2026-07-20\n")
        ))

    def test_the_certificate_falls_back_rather_than_printing_a_blank_name(self):
        recap = GEN.parse_recap("# R\n\n**Bootcamper:** 李明\n\n## M — 2026-07-20\n")
        printed, _date, _labels = GEN._cert_fields(recap)
        self.assertEqual(GEN.CERTIFICATE_NAME_PLACEHOLDER, printed)


class TestRealisticRecapUsesThePreferredRenderer(unittest.TestCase):
    """The end-to-end symptom: a clipping title must not force the fallback."""

    RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-26T09:00:00-07:00

---

## {title} — 2026-07-26T14:00:00-07:00

### Information Shared
- A line with an em dash — and an ellipsis … and a bullet ·

### Questions & Responses
- **Q:** Did the cover chip clip?
    - **R:** Yes — that is the point.

### Actions Taken
- Rendered the cover, whose module chip clips at 46 characters.

### End-of-Module Summary
**What you accomplished:**
- Proved the preferred renderer is still selected.

**Files produced:**
- `docs/bootcamp_recap.pdf` — the keepsake.

**Why it matters:** A silent downgrade to the plainer renderer defeats INV-048.

---
"""

    def setUp(self):
        if importlib.util.find_spec("fpdf") is None:
            self.skipTest("fpdf2 not installed (it is not stdlib — INV-108)")

    def test_a_clipping_title_still_renders_with_fpdf2(self):
        import tempfile

        recap = GEN.parse_recap(self.RECAP.format(title=LONG_TITLE))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "recap.pdf"
            ok = GEN.render_with_fpdf2(recap, out)
            self.assertTrue(
                ok,
                "the designed fpdf2 renderer refused a recap whose module title clips — "
                "the exact silent-downgrade defect this module exists to pin",
            )
            self.assertTrue(out.is_file() and out.stat().st_size > 0)

    def test_the_module_title_actually_clips(self):
        """Otherwise the test above passes without exercising the defect."""
        self.assertGreater(
            len(LONG_TITLE),
            min(clip_widths()),
            "LONG_TITLE no longer exceeds the narrowest clip width, so the "
            "end-to-end assertion would pass vacuously",
        )


# --------------------------------------------------------------------------------------
# Dropping a character the core fonts cannot encode is correct (INV-143 forbids `?`).
# Doing it SILENTLY is the defect. `_safe`'s own docstring already promised the generator
# "drops, warns" — but the warn existed for the certificate name only, so a Cyrillic
# organization name in a discoveries document rendered as `"- "` at exit 0 with
# `content retained: 96%`. Retention structurally cannot catch it: it is measured over
# parsed SOURCE characters, before `_safe` runs at render time.
# --------------------------------------------------------------------------------------

DISCOVERIES_GENERATOR = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_discoveries_pdf.py"
)

# A discoveries document needs all six findings sections to render (INV-110), so the
# fixture carries them; only one section holds the non-Latin-1 content under test.
DISCOVERIES_SECTIONS = (
    "Headline numbers",
    "Merges and match keys",
    "Review queue",
    "Why and how",
    "Relationship networks",
    "What was not found",
)

CYRILLIC_ORG = "Акционерное"
BOX_DRAWING = "│"          # the vertical connector an ASCII diagram reaches for
DOWN_TRIANGLE = "▼"        # and its arrowhead


def discoveries_doc(network_body):
    lines = ["# Data Discoveries", "", "**Prepared:** 2026-07-29", ""]
    for section in DISCOVERIES_SECTIONS:
        lines += [f"## {section}", ""]
        if section == "Relationship networks":
            lines += [network_body, ""]
        else:
            lines += [f"Plain ASCII finding text for {section}, long enough to count.", ""]
    return "\n".join(lines)


def run_generator(script, source_text, filename):
    """Render `source_text` through `script`; return (returncode, stdout, stderr)."""
    import subprocess
    import sys
    import tempfile

    workdir = Path(tempfile.mkdtemp())
    (workdir / "docs").mkdir(exist_ok=True)
    src = workdir / "docs" / filename
    src.write_text(source_text, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(script), "--input", str(src), "--output", str(workdir / "o.pdf")],
        capture_output=True,
        text=True,
        cwd=workdir,
    )
    return proc.returncode, proc.stdout, proc.stderr, workdir / "o.pdf"


RECAP_WITH = """# Bootcamp Recap

**Bootcamper:** Alex Rivera

## Data processing — 2026-07-29T09:00:00-07:00

### Information Shared

- The counterparty {org} appears in the network summary for this module.

### Questions & Responses

- **Q:** Which source led?
  - **A:** GLEIF.

### Actions Taken

- Built the loader and drained the redo queue.

### End-of-Module Summary

**What you accomplished:**
- Loaded every source.

**Files produced:**
- `src/load.py` — the loader.

**Why it matters:** The resolved entities are the basis of the next module's work.

---
"""

WARNING_MARK = "cannot be rendered by this"


class TheDropIsNeverSilent(unittest.TestCase):
    """Both generators must report characters they dropped, and neither may cry wolf."""

    def test_recap_warns_and_still_ships_the_pdf(self):
        code, _out, err, pdf = run_generator(
            GENERATOR, RECAP_WITH.format(org=CYRILLIC_ORG), "bootcamp_recap.md"
        )
        self.assertEqual(0, code, err)
        self.assertTrue(pdf.is_file() and pdf.stat().st_size > 0, "no PDF was written")
        self.assertIn(
            WARNING_MARK,
            err,
            "the recap generator dropped Cyrillic body text without saying so:\n" + err,
        )
        self.assertIn("CYRILLIC", err, err)

    def test_recap_is_silent_on_latin1_only_content(self):
        """No false positives: an ordinary recap must not grow a scary warning."""
        code, _out, err, _pdf = run_generator(
            GENERATOR, RECAP_WITH.format(org="Gazprom Media Holding"), "bootcamp_recap.md"
        )
        self.assertEqual(0, code, err)
        self.assertNotIn(WARNING_MARK, err, err)

    def test_discoveries_warns_inside_a_fenced_block(self):
        """A fenced ASCII diagram is exactly where the reported loss happened."""
        fenced = "```\n[GLEIF] {bar}\n   {tri}\n{org}\n```".format(
            bar=BOX_DRAWING, tri=DOWN_TRIANGLE, org=CYRILLIC_ORG
        )
        code, out, err, pdf = run_generator(
            DISCOVERIES_GENERATOR,
            discoveries_doc(fenced),
            "bootcamp_data_discoveries.md",
        )
        self.assertEqual(0, code, err)
        self.assertIn("PDF generated:", out, out + err)
        self.assertTrue(pdf.is_file() and pdf.stat().st_size > 0)
        self.assertIn(WARNING_MARK, err, "fenced-block loss went unreported:\n" + err)
        for expected in ("CYRILLIC", "BOX DRAWINGS", "TRIANGLE"):
            with self.subTest(expected=expected):
                self.assertIn(expected, err, err)

    def test_discoveries_warns_inside_a_table_cell(self):
        table = (
            "| Entity | Name |\n|---|---|\n"
            f"| 1042 | {CYRILLIC_ORG} |\n"
        )
        _code, _out, err, _pdf = run_generator(
            DISCOVERIES_GENERATOR, discoveries_doc(table), "bootcamp_data_discoveries.md"
        )
        self.assertIn(WARNING_MARK, err, "table-cell loss went unreported:\n" + err)

    def test_discoveries_is_silent_on_latin1_only_content(self):
        code, _out, err, _pdf = run_generator(
            DISCOVERIES_GENERATOR,
            discoveries_doc("The network centers on Gazprom Media Holding and affiliates."),
            "bootcamp_data_discoveries.md",
        )
        self.assertEqual(0, code, err)
        self.assertNotIn(WARNING_MARK, err, err)

    def test_the_shipped_example_recap_reports_no_loss(self):
        """The reference artifact must render clean, or every run looks broken."""
        example = (
            REPO_ROOT / "plugins" / "senzing-bootcamp" / "docs" / "examples"
            / "bootcamp_recap.example.md"
        )
        code, _out, err, _pdf = run_generator(
            GENERATOR, example.read_text(encoding="utf-8"), "bootcamp_recap.md"
        )
        self.assertEqual(0, code, err)
        self.assertNotIn(WARNING_MARK, err, err)


class TheWarningSurvivesAnyConsole(unittest.TestCase):
    """The warning must not become the mojibake it exists to report.

    A Windows console in a legacy code page cannot display the very characters that were
    dropped (`ground-rules.md` -> "Windows and PowerShell"), so the report names them by
    Unicode NAME and backslash-escapes the locating excerpt rather than echoing either.
    """

    def setUp(self):
        GEN.reset_dropped_characters()

    def tearDown(self):
        GEN.reset_dropped_characters()

    def test_the_warning_is_pure_ascii(self):
        GEN._safe(f"{CYRILLIC_ORG} {BOX_DRAWING}{DOWN_TRIANGLE} 李明")
        warning = GEN.dropped_character_warning()
        self.assertIsNotNone(warning)
        self.assertTrue(
            warning.isascii(),
            "the drop warning carries non-ASCII text, so a legacy Windows code page can "
            f"corrupt the warning itself: {warning!r}",
        )

    def test_no_dropped_character_is_echoed_raw(self):
        GEN._safe(CYRILLIC_ORG)
        warning = GEN.dropped_character_warning()
        for ch in CYRILLIC_ORG:
            with self.subTest(ch=ch):
                self.assertNotIn(ch, warning)

    def test_an_accented_latin_name_is_not_reported_as_a_loss(self):
        """`ā`->`a` is the readable approximation INV-143 asks for, not a dropped value.

        Reporting it would fire on ordinary European names and bury the real losses.
        """
        folded = GEN._safe("José Mařík āōş Zoë")
        self.assertEqual("Jose Marik aos Zoe", folded)
        self.assertIsNone(
            GEN.dropped_character_warning(),
            "an accented Latin name was reported as dropped content",
        )

    def test_the_record_is_idempotent_across_render_passes(self):
        """fpdf2 renders in two passes and may then fall back to the stdlib writer.

        Counting occurrences would report two or three times the real loss, so the count
        must not move when the same content is sanitized again.
        """
        GEN._safe(CYRILLIC_ORG)
        first = GEN.dropped_character_warning()
        for _ in range(3):
            GEN._safe(CYRILLIC_ORG)
        self.assertEqual(first, GEN.dropped_character_warning())

    def test_it_names_a_locating_passage(self):
        GEN._safe(f"The network centers on {CYRILLIC_ORG} and its affiliates.")
        warning = GEN.dropped_character_warning()
        self.assertIn("First affected passage", warning)
        self.assertIn("The network centers on", warning)


if __name__ == "__main__":
    unittest.main()
