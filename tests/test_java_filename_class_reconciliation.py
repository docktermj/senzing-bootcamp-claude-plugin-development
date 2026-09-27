"""A prescribed snake_case filename must not force an un-nameable Java class.

Java couples a **public** top-level class to its filename; Python does not couple anything.
Every `.[ext]` filename in this bootcamp is written in the Python idiom, so on the Java path
`public class MeridianCrmMapper` inside the prescribed `meridian_crm_mapper.java` fails:

    class MeridianCrmMapper is public, should be declared in a file named MeridianCrmMapper.java

Reproduced on javac 21.0.11, 2026-08-14. The reconciliation is to drop `public` from the
top-level class: a package-private top-level class may live in any filename, so the prescribed
path and the idiomatic class name both survive, and `java -cp <dir> <ClassName>` still launches
it. Verified the same day for a single mapper class — the package-private form compiles clean
under `javac -Xlint:all` and runs.

⚠️ **That holds for a prescribed standalone program file, not for a class other files use.**
`javac` resolves a class from the sourcepath by filename, so a package-private shared class in a
differently named file draws the auxiliary-class warning when every file compiles together, and
`cannot find symbol` when one program is rebuilt alone with `-sourcepath` (javac 21.0.12.1,
2026-09-25, #161). A shared class — the JSON reader Module 5 step 13 reuses, or the helper Module
7 step 2 anticipates — goes in a file named after the class. Such a helper has no prescribed
filename, so the no-rename rule below does not reach it.

Renaming is not available as a fix in either direction. The filenames are read by other
machinery (graduation's artifact mapping, Module 5's source-qualified names, Module 3's build
table, which its own tests pin), and renaming the class to `snake_case` satisfies `javac` while
breaking the same instruction's "idiomatic style for the chosen language".

C# is the quiet version and takes the opposite advice: the file/type correspondence is
conventional, not enforced (`public class MeridianCrmMapper` in `meridian_crm_mapper.cs` builds
with 0 warnings, 0 errors on .NET 8, verified 2026-08-14), so nothing is dropped there.

Enforces **INV-237** — the reconciliation is stated centrally, pointed at from every prescribing
site, and never resolved by renaming the file or the type.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
VERIFICATION = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"
MAPPING = PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
QUERY = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

#: The central statement, identified by the reconciliation it prescribes rather than by a
#: heading, so moving the section does not silently un-cover the sites.
PACKAGE_PRIVATE_RULE = re.compile(
    r"(?i)declare the (?:top-level )?class\s+package-private|Drop `public` from the top-level class"
)
#: A site prescribes a Java filename when it names one, or names the `[ext]`/`<ext>` pattern
#: alongside Java. Both forms appear in the plugin.
PRESCRIBES_JAVA_FILE = re.compile(r"\.java\b|\[ext\]|<ext>")
#: How a site discharges its obligation: point at the central statement.
POINTS_AT_CENTRAL = re.compile(
    r"(?i)ground-rules\.md.{0,60}File placement|INV-237"
)
#: Filenames other machinery reads, which this fix must not change.
PRESCRIBED_NAMES = ("verify_pipeline.java", "transform_[name].[ext]")


def read(path):
    return path.read_text(encoding="utf-8")


def squashed(path):
    return re.sub(r"\s+", " ", read(path))


def java_prescribing_sites():
    """Files that prescribe a Java source filename and so need the pointer.

    Deliberately the two the spec names plus anything that grows the same shape: a file that
    both mentions Java and prescribes a filename pattern. Module 2's `.java` mentions are
    *scaffold* filenames returned by the MCP server, not paths the plugin prescribes, so they
    are excluded by requiring a prescribed-path form.
    """
    return [VERIFICATION, MAPPING]


class TheReconciliationIsStatedCentrally(unittest.TestCase):
    """Criteria 1 and 3 — stated once, with its reason and the C# difference."""

    def test_ground_rules_prescribes_the_package_private_class(self):
        self.assertRegex(squashed(GROUND_RULES), PACKAGE_PRIVATE_RULE)

    def test_it_gives_the_reason(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)only a `public` top-level class is filename-bound",
            "without the reason the rule reads as a superstition and will be 'tidied' away",
        )

    def test_it_says_the_launcher_is_unaffected(self):
        self.assertRegex(squashed(GROUND_RULES), r"java -cp <dir> <ClassName>` still launches it")

    def test_it_quotes_the_compiler_error(self):
        # The error names class visibility while the cause is a filename convention, so the
        # searchable string is what connects the two for a reader who hits it.
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)should be declared in a file named MeridianCrmMapper\.java",
        )

    def test_it_carries_its_verification_provenance(self):
        text = squashed(GROUND_RULES)
        self.assertRegex(text, r"(?i)javac/java 21\.0\.11")
        self.assertRegex(text, r"(?i)-Xlint:all")

    def test_the_csharp_case_distinguishes_conventional_from_enforced(self):
        text = squashed(GROUND_RULES)
        self.assertRegex(text, r"(?i)conventional, not enforced")
        self.assertRegex(text, r"(?i)\.NET 8")
        self.assertRegex(
            text, r"(?i)keep the prescribed filename\s+and name the type idiomatically",
            "C# needs the opposite advice stated, not merely the Java rule scoped away",
        )

    def test_the_unaffected_languages_are_named(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)Python, Rust and TypeScript have no such coupling",
        )


class EveryPrescribingSitePointsAtIt(unittest.TestCase):
    """Criteria 2 and 5 — reachable from the site, and not restated there."""

    def test_each_site_points_at_the_central_statement(self):
        for path in java_prescribing_sites():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                text = squashed(path)
                self.assertRegex(text, PRESCRIBES_JAVA_FILE)
                self.assertRegex(
                    text, POINTS_AT_CENTRAL,
                    "this file prescribes a Java source filename with no route to the "
                    "reconciliation, so the bootcamper meets it at the compiler instead",
                )

    def test_each_site_names_the_reconciliation_without_restating_it(self):
        """INV-183's shape: named where needed, defined once."""
        for path in java_prescribing_sites():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                text = squashed(path)
                self.assertRegex(text, r"(?i)package-private")
                # The reason and the C# clause belong to the central statement only.
                self.assertNotRegex(
                    text, r"(?i)conventional, not enforced",
                    "the C# clause is restated here; it has one home (INV-183)",
                )
                self.assertNotRegex(
                    text, r"(?i)do not restate them here.{0,4}$",
                )

    def test_the_central_statement_is_what_makes_them_pass(self):
        """Negative control in assertion form: the pointer must name a real target.

        If the central statement were removed, `test_ground_rules_prescribes_the_package_private
        _class` fails; this asserts the *link target* exists as prose rather than as a path that
        happens to resolve, so a section rename cannot leave two live pointers aimed at nothing.
        """
        self.assertRegex(squashed(GROUND_RULES), r"(?i)## File placement")
        self.assertIn("INV-237", read(GROUND_RULES))


class NoPrescribedFilenameChanged(unittest.TestCase):
    """Criterion 4 — the fix must not ripple into machinery that reads these names."""

    def test_the_verification_build_table_still_names_verify_pipeline_java(self):
        self.assertIn(
            "| Java | `javac src/system_verification/verify_pipeline.java` |",
            read(VERIFICATION),
            "the build table's Java row moved; graduation and this module's own tests read it",
        )

    def test_the_transform_filename_pattern_survives(self):
        self.assertIn("src/transform/transform_[name].[ext]", read(MAPPING))

    def test_no_pascal_case_java_path_was_introduced(self):
        # The tempting fix is renaming to PascalCase.java per language. It ripples further
        # than the defect warrants, so its absence is asserted rather than assumed.
        for path in java_prescribing_sites():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertNotRegex(
                    read(path), r"src/\S*/[A-Z][A-Za-z0-9]*\.java",
                    "a PascalCase .java path appeared, changing a prescribed filename",
                )

    def test_the_prescribed_names_are_all_still_present(self):
        joined = read(VERIFICATION) + read(MAPPING)
        for name in PRESCRIBED_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, joined)


class TheOtherLanguagesAreUntouched(unittest.TestCase):
    """Criterion 6 — Python, Rust and TypeScript have no coupling, so no new instruction."""

    def test_the_build_table_rows_are_unchanged(self):
        text = read(VERIFICATION)
        for row in (
            "| Python | `python3 -m py_compile src/system_verification/verify_pipeline.py` |",
            "| C# | `dotnet build src/system_verification/` |",
            "| Rust | `cargo build --manifest-path src/system_verification/Cargo.toml` |",
            "| TypeScript | `tsc src/system_verification/verify_pipeline.ts --noEmit` |",
        ):
            with self.subTest(row=row.split("|")[1].strip()):
                self.assertIn(row, text)

    def test_no_package_private_advice_leaked_onto_a_language_without_the_coupling(self):
        """`package-private` is a Java word; finding it beside Rust or Python is a smell."""
        for path in java_prescribing_sites():
            block = squashed(path)
            for match in re.finditer(r"[^.]*package-private[^.]*\.", block):
                sentence = match.group(0)
                with self.subTest(file=str(path.relative_to(PLUGIN)),
                                  sentence=sentence[:80]):
                    for lang in ("Python", "Rust", "TypeScript"):
                        self.assertNotIn(lang, sentence)


def between(path, start, end):
    """The squashed text of `path` from heading `start` to heading `end` (or the file's end).

    Empty when `start` is missing, which the callers assert against so a renamed heading fails
    loudly instead of passing vacuously (INV-265).
    """
    text = read(path)
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i + len(start):]
    j = rest.find(end)
    return re.sub(r"\s+", " ", rest if j < 0 else rest[:j])


def plain(path):
    """Squashed text with `**` emphasis removed, so a bolding change does not break a match."""
    return squashed(path).replace("**", "")


#: The pointer the two shared-code sites carry: it names the shared-class case and the owner.
POINTS_AT_SHARED_CLASS_RULE = re.compile(
    r"(?i)shared class.{0,80}ground-rules\.md.{0,40}File placement.{0,20}INV-237"
)


class TheSharedClassCaseIsDistinguished(unittest.TestCase):
    """#161 — the package-private form covers standalone programs; a shared class needs its own
    file. Removing the shared-class sentence, the scoping, either stamp, or a pointer fails here.
    """

    def test_the_package_private_form_is_scoped_to_standalone_programs(self):
        self.assertRegex(
            plain(GROUND_RULES),
            r"(?i)This form is for prescribed standalone program files \(mappers, loaders, "
            r"verification programs\)",
            "the package-private form reads as universal again; it breaks for a shared class",
        )

    def test_a_shared_class_goes_in_a_file_named_after_the_class(self):
        text = plain(GROUND_RULES)
        self.assertRegex(
            text,
            r"(?i)A shared class — one that other files reference — goes in a file named after "
            r"the class",
        )
        # A bare filename, so the PascalCase-path guard above stays as it is.
        self.assertRegex(text, r"such as `CounterpartyApi\.java`, `public` or not")

    def test_it_gives_the_sourcepath_reason_and_both_symptoms(self):
        text = plain(GROUND_RULES)
        self.assertRegex(text, r"(?i)resolves a class from the sourcepath by filename")
        self.assertRegex(text, r"(?i)auxiliary class CounterpartyApi")
        self.assertRegex(text, r"(?i)error: cannot find symbol")

    def test_the_no_rename_rule_does_not_reach_a_shared_helper(self):
        self.assertRegex(
            plain(GROUND_RULES),
            r"(?i)Such a helper has no prescribed filename, so \"do not rename the file\"",
            "without this, INV-237's no-rename rule reads as forbidding the fix",
        )

    def test_the_xlint_claim_is_scoped_to_the_single_class_case(self):
        self.assertRegex(
            plain(GROUND_RULES),
            r"(?i)Verified for a single mapper class on javac/java 21\.0\.11, 2026-08-14: "
            r".{0,120}package-private form compiles clean under `javac -Xlint:all`",
            "the -Xlint:all claim lost its scope; it was verified on one standalone class only",
        )

    def test_the_shared_class_case_carries_its_own_stamp(self):
        self.assertRegex(
            plain(GROUND_RULES),
            r"(?i)Verified on javac 21\.0\.12\.1, 2026-09-25, with `CounterpartyApi` in "
            r"`counterparty_api\.java`: both failures reproduce, and the same class in "
            r"`CounterpartyApi\.java` compiles clean under `-Xlint:all -sourcepath`",
        )

    def test_module_5_step_13_points_at_the_clause(self):
        step = between(MAPPING, "### 13. Build the transformation program", "\n### 14.")
        self.assertIn("reuse this same reader", step, "step 13 was not located")
        self.assertRegex(
            step, POINTS_AT_SHARED_CLASS_RULE,
            "step 13 asks for a reader reused across modules with no route to the shared-class "
            "filename rule",
        )

    def test_module_7_step_2_points_at_the_clause(self):
        step = between(QUERY, "## 2. Create query programs", "\n## ")
        self.assertIn("INV-152", step, "step 2 was not located")
        self.assertRegex(
            step, POINTS_AT_SHARED_CLASS_RULE,
            "step 2 invites a shared helper with no route to the shared-class filename rule",
        )

    def test_the_pointers_do_not_restate_the_rule(self):
        """INV-300: the reason and the symptoms have one home, ground-rules.md."""
        for name, step in (
            ("module 5 step 13",
             between(MAPPING, "### 13. Build the transformation program", "\n### 14.")),
            ("module 7 step 2", between(QUERY, "## 2. Create query programs", "\n## ")),
        ):
            with self.subTest(site=name):
                self.assertTrue(step, "%s was not located" % name)
                for phrase in ("by filename", "auxiliary class", "cannot find symbol",
                               "CounterpartyApi"):
                    self.assertNotIn(phrase, step.replace("**", ""))


if __name__ == "__main__":
    unittest.main()
