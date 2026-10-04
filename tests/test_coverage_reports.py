"""The maintainer coverage reports run, and report the two gaps they exist for.

MCP-NEGATIVE-SCAN: ignore-file — the marker strings below are scratch-tree fixtures for the
scan surface, not claims about the current server.

`deep-dive-audit-2026-07-29-minor-fixes` item 4 added
`.claude/skills/dry-run/coverage_reports.py` because two blind spots let an invariant stand
unimplemented for weeks while `IMPLEMENTED.md` recorded its spec as done: an invariant no
test cites, and a spec file a ledger entry never records changing.

Neither gap can be a failing test — a hit in either is usually legitimate — so both are
reports. That makes them exactly the kind of apparatus that rots unnoticed: nothing fails
when a report stops reporting. So it is *executed* here rather than asserted present, the
discipline INV-175 settled for shipped snippets.

Three properties, one per way it could rot:

1. **It runs at all**, from a working directory that is not the repo root (the audit
   workflows run from a scratch project — see `dry-run/SKILL.md`), and exits 0 whatever it
   finds, because a report that gates is a report nobody runs.
2. **The invariants report's own property holds** — everything it calls uncited is defined
   in INVARIANTS.md and appears in no `tests/*.py`. Naming specific IDs here cannot work:
   writing an ID into this file makes this file cite it, so the report correctly stops
   listing it and the assertion destroys itself. The first version of this test did
   exactly that with INV-060 and INV-097.
3. **The affected report finds a known gap** and does not crash on the audit entries that
   have no spec file at all.

No phrase-level pattern (#438): its line reads are of the index lines of `specs/INVARIANTS.md`,
which is outside the in-scope corpora, as #424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "skills" / "dry-run" / "coverage_reports.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reports = load(SCRIPT, "coverage_reports_surface")


def run(report, cwd):
    """Run the report from `cwd`, returning (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), report, "--repo", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestReportsRun(unittest.TestCase):
    def test_the_script_ships(self):
        self.assertTrue(SCRIPT.is_file(), f"missing: {SCRIPT}")

    def test_both_reports_run_from_an_unrelated_directory_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            for report in ("invariants", "affected", "both"):
                code, out, err = run(report, tmp)
                self.assertEqual(
                    0, code, f"{report} exited {code}; stderr:\n{err}"
                )
                self.assertTrue(out.strip(), f"{report} produced no output")

    def test_a_missing_repo_is_reported_not_crashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "invariants", "--repo", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, proc.returncode)
            self.assertIn("no specs/", proc.stderr)


class TestInvariantsReport(unittest.TestCase):
    def test_it_counts_the_invariants_it_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _ = run("invariants", tmp)
        m = re.search(r"defined: (\d+)\s+cited by a test: (\d+)\s+uncited: (\d+)", out)
        self.assertIsNotNone(m, f"the summary line is gone:\n{out[:400]}")
        defined, cited, uncited = (int(g) for g in m.groups())
        self.assertGreater(defined, 150, "far fewer invariants parsed than exist")
        self.assertEqual(defined, cited + uncited, "the counts do not add up")

    def test_every_reported_invariant_is_real_and_genuinely_uncited(self):
        """The report's own property, checked independently of it.

        Naming specific IDs here does not work: writing `INV-060` into this file makes
        this file cite it, so the report correctly stops listing it and the assertion
        destroys itself. (That is exactly what the first version of this test did.) So
        assert the property instead — every ID reported is defined in INVARIANTS.md and
        appears in no `tests/*.py` — which stays true however the corpus moves.
        """
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _ = run("invariants", tmp)
        reported = set(re.findall(r"\bINV-(\d{3})\b", out.split("uncited:")[-1]))
        self.assertTrue(reported, "the report listed no uncited invariant at all")

        invariants = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        defined = set(re.findall(r"\*\*INV-(\d{3})\*\*", invariants))
        self.assertEqual(
            set(),
            reported - defined,
            "the report named an invariant that INVARIANTS.md does not define",
        )

        cited_anywhere = set()
        for test_file in (REPO_ROOT / "tests").glob("*.py"):
            cited_anywhere |= set(
                re.findall(r"INV-(\d{3})", test_file.read_text(encoding="utf-8"))
            )
        leaked = sorted(reported & cited_anywhere)
        self.assertEqual(
            [],
            leaked,
            "the report called these uncited while a test file cites them: "
            + ", ".join("INV-" + n for n in leaked),
        )


#: Fixture ids for the scratch trees below, assembled at runtime. Written as literals they
#: read as citations of UNDEFINED invariants and fail `citations.py verify` — which is exactly
#: what happened on this test's first run, turning the suite red for five dangling references.
#: `test_citation_census.py` takes the file-level `citations.py: ignore-file` route instead;
#: that is right for the file which tests the scanner and wrong here, because this file carries
#: eight REAL invariant citations that must stay verified.
_I = "INV-"
FIX_A, FIX_B, FIX_C = _I + "800", _I + "801", _I + "802"
FIX_DEV, FIX_OTHER = _I + "900", _I + "999"


class TestShippedReport(unittest.TestCase):
    """`shipped` — the mirror of `invariants`, looking at plugins/ instead of tests/.

    The gap it fills: `conformance.py rules` is satisfied by ANY `INV-NNN` in a section, so it
    reported 0 uncited hard rules on 2026-08-13 while INV-212 was named nowhere near the step
    it had been registered from. Nothing asked the simpler question — which invariants does
    shipped text never mention at all.

    Built with a scratch tree rather than the live repo wherever the property is about the
    *rule*, because the live answer legitimately changes as citations are added. The live repo
    is used only for the two things that must hold whatever it contains: the report runs, and
    the exemption comes from the data.
    """

    #: The module table the artifact filter composes display names from. Two rows are enough
    #: to prove the property, and keeping it here rather than in the live file is what lets a
    #: scratch tree exercise the display-name case at all.
    MODULE_TABLE = "\n".join((
        "| # | Module | Rule | State token | Maps to |",
        "|---|---|---|---|---|",
        "| 1 | Bootcamp preparation | Required | `bootcamp_preparation` | this module |",
        "| 2 | System verification | Optional — Requires \"SDK setup\" | `system_verification` "
        "| `module-03-system-verification` |",
        "| 3 | Truth Set visualization | Optional | `truthset_visualization` | `module-03b` |",
    )) + "\n"

    def _tree(self, root, invariants_md, plugin_files=(), test_files=()):
        (root / "specs").mkdir(exist_ok=True)
        (root / "plugins").mkdir(exist_ok=True)
        (root / "tests").mkdir(exist_ok=True)
        (root / "specs" / "INVARIANTS.md").write_text(invariants_md, encoding="utf-8")
        # The filter reads its display names from the shipped module table, so a tree without
        # one is not a valid repo — `module_display_names` raises rather than narrowing itself
        # in silence, which is the behavior `test_a_tree_with_no_module_table_raises` pins.
        prep = root / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-preparation"
        prep.mkdir(parents=True, exist_ok=True)
        (prep / "SKILL.md").write_text(self.MODULE_TABLE, encoding="utf-8")
        for name, body in plugin_files:
            (root / "plugins" / name).write_text(body, encoding="utf-8")
        for name, body in test_files:
            (root / "tests" / name).write_text(body, encoding="utf-8")

    @staticmethod
    def _invariants(*entries, dev_group=(FIX_DEV,)):
        """An INVARIANTS.md with a subject index, in the live file's shape."""
        body = ["# Invariants", ""]
        body += ["- **%s** — %s" % (i, t) for i, t in entries]
        body += ["", "### Index by subject", ""]
        body += ["- **Everything else** — the rest.  ",
                 "  " + ", ".join(i for i, _ in entries if i not in dev_group)]
        body += ["- **The development record itself** — rules governing specs.  ",
                 "  " + ", ".join(dev_group)]
        return "\n".join(body) + "\n"

    def test_an_invariant_naming_a_shipped_artifact_and_cited_nowhere_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Module 5's `SKILL.md` MUST do the thing."),
                (FIX_B, "Module 6's `SKILL.md` MUST do the other thing."),
            ), plugin_files=[("m6.md", "governed by %s here" % FIX_B)])
            hits, ungrouped = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_A], [h[0] for h in hits],
                             "exactly the uncited one must be reported; got %r" % (hits,))
            self.assertEqual([], ungrouped)

    def test_an_invariant_cited_only_by_a_test_is_still_reported(self):
        """The INV-212 case, and the whole reason this is not the `invariants` report.

        `coverage_reports.py invariants` scores an invariant covered when a test names it —
        which is exactly what made INV-212 invisible: guarded, and unreachable from the step.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Module 5's `SKILL.md` MUST do the thing."),
            ), test_files=[("test_it.py", "# enforces %s\n" % FIX_A)])
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_A], [h[0] for h in hits],
                             "a test citation must NOT count as shipped coverage")

    def test_the_development_group_is_exempt_and_read_from_the_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_DEV, "A spec's `SKILL.md` entry MUST be recorded."),
                dev_group=(FIX_DEV,),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([], hits, "a member of the development group must be exempt")

    def test_moving_an_invariant_out_of_the_development_group_un_exempts_it(self):
        """Proves the exemption tracks the DATA, not a list hardcoded in the script."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_DEV, "A spec's `SKILL.md` entry MUST be recorded."),
                dev_group=(FIX_OTHER,),          # the dev entry now sits in the other group
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_DEV], [h[0] for h in hits],
                             "re-filing must change the outcome, or the rule is not in the data")

    def test_an_invariant_in_no_group_is_surfaced_not_silently_exempted(self):
        """A missing index entry must not become a way to vanish from this report."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = ("# Invariants\n\n"
                    "- **%s** — Module 5's `SKILL.md` MUST do the thing.\n\n"
                    "### Index by subject\n\n"
                    "- **The development record itself** — rules governing specs.  \n"
                    "  %s\n" % (FIX_A, FIX_DEV))
            self._tree(root, body)
            _hits, ungrouped = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_A], ungrouped)

    def test_an_invariant_naming_no_shipped_artifact_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "A value the Bootcamper was asked for MUST outrank a detected one."),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([], hits,
                             "a general property with no artifact is honored by behavior; "
                             "reporting it is the noise that gets a report ignored")

    def test_an_invariant_naming_a_module_by_its_DISPLAY_name_is_reported(self):
        """The 2026-08-14 blind spot: seven of eight new invariants were invisible here.

        The filter matched paths, `module-NN` directories and `Module N` catalog labels — the
        spellings the plugin is told NOT to render — and no display name. So INV-223 ("Truth
        Set visualization"), INV-225 ("System verification"), INV-227 ("Bootcamp preparation")
        and INV-229 ("System-verification checks") all passed straight through, and only
        INV-226 surfaced, because its text happens to say "Module 0". INV-079 requires the very
        vocabulary this report could not read.
        """
        cases = (
            ("Truth Set visualization", "the spaced display name"),
            ("System verification", "a second spaced display name"),
            ("System-verification", "the hyphenated adjectival form"),
            ("Bootcamp preparation", "a skill named in prose, not as a directory"),
        )
        for name, why in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self._tree(root, self._invariants(
                        (FIX_A, "%s's close MUST record the module." % name),
                    ))
                    hits, _ = reports.find_uncited_in_shipped(str(root))
                    self.assertEqual(
                        [FIX_A], [h[0] for h in hits],
                        "%s (%s) is not recognized as naming a shipped artifact, so an "
                        "uncited invariant about it is invisible" % (name, why))

    def test_a_skill_named_in_prose_with_a_space_is_reported(self):
        """Onboarding is the case the module table cannot cover — it is not a module row.

        ⚠️ Written after a negative control escaped: the "Bootcamp preparation" case above
        passes on the table-derived name alone, so it proved nothing about the spaced form in
        `STATIC_ARTIFACT`. Onboarding is the only skill named in invariant prose that the table
        does not supply, which makes it the one case that actually pins that half.

        ⛔ The fixture text must name NOTHING else the filter matches. The first attempt said
        "MUST create the progress file" and passed on `the progress file` alone — a fixture that
        defeats its own assertion, which the negative control caught by escaping twice.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Bootcamp onboarding's preface MUST run silently."),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_A], [h[0] for h in hits],
                             "a skill named in prose with a space is unmatched, so the "
                             "hyphenated directory spelling is the only one that counts")

    def test_the_display_names_come_from_the_module_table_not_a_second_list(self):
        """Rename a module in the table and the filter follows — no hand-listed copy to drift."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Wildly Renamed Module's close MUST record the module."),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([], hits, "a name absent from the table must not match")

            prep = root / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-preparation"
            (prep / "SKILL.md").write_text(
                self.MODULE_TABLE
                + "| 4 | Wildly Renamed Module | Required | `wrm` | `module-99` |\n",
                encoding="utf-8")
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_A], [h[0] for h in hits],
                             "adding the row to the module table did not widen the filter, so "
                             "the names are hand-listed somewhere and will drift")

    def test_a_tree_with_no_module_table_raises(self):
        """⛔ A silent fallback here re-creates the blind spot, invisibly and totally.

        An empty display-name list makes the report keep printing and keep looking
        authoritative while it stops seeing every display-name invariant — which is exactly
        the failure mode that let eight of them through. So this raises instead.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()
            (root / "specs" / "INVARIANTS.md").write_text("# Invariants\n", encoding="utf-8")
            with self.assertRaises(Exception):
                reports.module_display_names(str(root))

    def test_the_live_module_table_parses_to_every_module(self):
        """The one live-repo assertion: the real table must actually yield its rows."""
        names = reports.module_display_names(str(REPO_ROOT))
        self.assertGreaterEqual(len(names), 11,
                                "the live module table parsed to %d rows; the filter's "
                                "display-name half is nearly empty" % len(names))
        for expected in ("Bootcamp preparation", "System verification",
                         "Truth Set visualization", "Bootcamp graduation"):
            with self.subTest(module=expected):
                self.assertIn(expected, names, "a known module is missing from the parse")

    def test_a_superseded_invariant_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Module 5's `SKILL.md` MUST do it. (Superseded by %s.)" % FIX_B),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([], hits, "a retired rule is not a coverage gap")

    def test_bootcamp_outcome_invariants_are_out_of_scope(self):
        """INV-001–050 are outcomes the flow satisfies, and are deliberately unindexed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                ("INV-013", "All shipped modules are performed in order: Module 1 -> 2."),
            ))
            hits, ungrouped = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([], hits)
            self.assertEqual([], ungrouped, "an unindexed outcome invariant is not a gap")

    def test_hits_are_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, self._invariants(
                (FIX_A, "Module 5's `SKILL.md` MUST a."),
                (FIX_C, "Module 6's `SKILL.md` MUST b."),
                (FIX_B, "Module 7's `SKILL.md` MUST c."),
            ))
            hits, _ = reports.find_uncited_in_shipped(str(root))
            self.assertEqual([FIX_C, FIX_B, FIX_A], [h[0] for h in hits],
                             "a newly registered invariant is the most likely oversight and "
                             "must lead")

    def test_the_report_runs_on_the_live_repo_and_exits_zero(self):
        code, out, err = run("shipped", REPO_ROOT)
        self.assertEqual(0, code, err)
        self.assertIn("plugins/", out)

    def test_the_preamble_says_a_hit_is_a_lead_not_a_defect(self):
        _code, out, _err = run("shipped", REPO_ROOT)
        self.assertIn("not a defect", out,
                      "without this the report reads as a bug list and its first run, which "
                      "is always the longest, gets it ignored")

    def test_the_live_index_declares_the_group_the_script_depends_on(self):
        """The script reads an exemption out of prose; the prose must say it is one.

        ⚠️ Negative control found this by ruling a mutation *invalid* rather than missed:
        re-filing an ID out of the development group changes nothing in the suite, and should
        not — the maintainer chose "the group IS the rule" (2026-08-13), so re-filing is a
        permitted edit, not a regression. What a test can protect is the coupling itself: a
        future editor tidying the index could drop the sentence naming this group as the
        exemption, and `coverage_reports.py shipped` would keep matching on `DEV_GROUP`
        with nothing left to tell them why.
        """
        body = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        groups = reports._index_groups(body)
        dev = [name for name in groups if reports.DEV_GROUP in name.lower()]
        self.assertEqual(
            1, len(dev),
            "exactly one index group must match coverage_reports.DEV_GROUP (%r); found %r. "
            "Zero means the exemption silently applies to nothing and every development rule "
            "floods the report; two means it is ambiguous."
            % (reports.DEV_GROUP, dev),
        )
        block = next(m.group(0) for m in reports.INDEX_GROUP.finditer(body)
                     if reports.DEV_GROUP in m.group("name").lower())
        self.assertIn(
            "exemption", block.lower(),
            "the development-record group must state IN THE INDEX that it is the exemption "
            "`coverage_reports.py shipped` uses, so an author filing a new invariant there "
            "knows what it turns off",
        )

    def test_both_still_runs_every_report_including_this_one(self):
        code, out, err = run("both", REPO_ROOT)
        self.assertEqual(0, code, err)
        for heading in ("cited by no test file", "NO file under plugins/ cites",
                        "Predicted-but-unrecorded", "Dated MCP negatives"):
            with self.subTest(heading=heading):
                self.assertIn(heading, out)


class TestSupersededFilter(unittest.TestCase):
    """`invariants` filters FULLY superseded entries — and only those.

    ⛔ The naive implementation greps each invariant for "superseded by INV" and is wrong.
    `INVARIANTS.md` draws a two-way distinction on purpose: "**Fully superseded:** the whole
    invariant is retired… Skip it" versus "**Partly superseded, or superseded then restored:**
    one clause was replaced while the rest still binds. **Read it**". Dropping a partly
    superseded invariant hides a live rule, which is the one way this filter can do harm.
    """

    def test_it_reads_the_index_lists_not_each_invariants_prose(self):
        body = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        retired = reports.fully_superseded(body)
        self.assertTrue(retired, "no fully-superseded ids parsed — the index format moved")
        # Every id claimed retired must actually sit on a "Fully superseded" index line.
        for line in body.split("\n"):
            if "Partly superseded" in line or "since restored" in line:
                for n in re.findall(r"INV-(\d{3})", line):
                    with self.subTest(inv="INV-" + n):
                        self.assertNotIn(
                            int(n), retired,
                            "INV-%s is listed as PARTLY superseded and must not be filtered; "
                            "it still binds and dropping it hides a live rule" % n,
                        )

    def test_a_partly_superseded_invariant_survives_the_filter(self):
        """INV-040 is the live counter-example, not a hypothetical.

        Its CORD parenthetical is superseded by INV-198 while its main clause is what INV-198
        *strengthens*. A grep-based filter drops it; the index-based one keeps it.
        """
        body = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        inv040 = next(l for l in body.split("\n") if l.startswith("- **INV-040**"))
        self.assertIn("superseded", inv040.lower(),
                      "INV-040 no longer reads as superseded; pick another counter-example")
        self.assertNotIn(40, reports.fully_superseded(body),
                         "INV-040 is only PARTLY superseded and must survive the filter")

    def test_the_report_separates_filtered_outcome_and_residue(self):
        _code, out, _err = run("invariants", REPO_ROOT)
        for marker in ("fully superseded", "OUTCOME invariants",
                       "development rules with no citing test"):
            with self.subTest(marker=marker):
                self.assertIn(marker, out)

    def test_the_three_sections_account_for_every_uncited_invariant(self):
        _code, out, _err = run("invariants", REPO_ROOT)
        total = int(re.search(r"uncited: (\d+)", out).group(1))
        got = (int(re.search(r"filtered: (\d+)", out).group(1))
               + int(re.search(r"OUTCOME invariants \([^)]*\): (\d+)", out).group(1))
               + int(re.search(r"development rules with no citing test: (\d+)", out).group(1)))
        self.assertEqual(total, got,
                         "the sections must partition the uncited set, or one is being lost")


class TestAffectedClassification(unittest.TestCase):
    """`affected` classifies each gap row instead of printing 53 undifferentiated paths."""

    def test_classify_gap_sorts_each_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "plugins").mkdir()
            (root / "plugins" / "real.md").write_text("x", encoding="utf-8")
            self.assertEqual("glob", reports.classify_gap(str(root), "plugins/*.py"))
            self.assertEqual("bare", reports.classify_gap(str(root), "brand_tokens.py"))
            self.assertEqual("real", reports.classify_gap(str(root), "plugins/real.md"))
            self.assertEqual("moved", reports.classify_gap(str(root), "plugins/gone.md"))

    def test_criteria_named_files_are_distinguished_from_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()
            (root / "specs" / "s.md").write_text(
                "## Acceptance criteria\n\n- [ ] `a.md` is updated.\n\n"
                "## Affected files\n\n- `b.md` — maybe.\n", encoding="utf-8")
            self.assertTrue(reports.criteria_name_the_file(str(root), "s", "x/a.md"),
                            "a file named in the criteria is the INV-097 shape")
            self.assertFalse(reports.criteria_name_the_file(str(root), "s", "x/b.md"),
                             "an Affected-files entry alone is only a prediction")

    def test_the_report_prints_the_classes_and_the_marker(self):
        _code, out, _err = run("affected", REPO_ROOT)
        for marker in ("names a real current file", "bare filename",
                       "glob — the scan cannot match", "★"):
            with self.subTest(marker=marker):
                self.assertIn(marker, out)


class TestNegativesScanSurface(unittest.TestCase):
    """`specs/DECLINED.md` is in the negatives scan; the rest of `specs/` stays out.

    The exclusion of `specs/` is right for a spec body — `implement-spec` Step 3.3 re-verifies
    a spec's Senzing facts at implementation time — and wrong for `DECLINED.md`, which no
    implementation ever reaches. So it is added as a named FILE rather than by opening the
    directory, and both halves are asserted: one file in, everything else still out.
    """

    def scanned(self):
        return [Path(p).resolve() for p in reports._scan_files(str(REPO_ROOT))]

    def test_declined_md_is_in_the_scan_surface(self):
        self.assertIn((REPO_ROOT / "specs" / "DECLINED.md").resolve(), self.scanned())

    def test_no_other_file_under_specs_is_scanned(self):
        specs = (REPO_ROOT / "specs").resolve()
        leaked = sorted(p.name for p in self.scanned()
                        if p.parent == specs and p.name != "DECLINED.md")
        self.assertEqual(
            [], leaked,
            "adding one file must not open specs/ — a spec body's negatives are re-verified "
            "by implement-spec Step 3.3 and an IMPLEMENTED.md entry is a point-in-time "
            "record, so both would be noise on the worklist: %s" % leaked,
        )

    def test_the_exclusion_it_asserts_is_not_vacuous(self):
        """Other files under `specs/` really do contain the marker text.

        Without this, `test_no_other_file_under_specs_is_scanned` would pass just as well on a
        corpus where no spec body mentions a negative at all, and would stop meaning anything
        the moment the scan surface widened.
        """
        others = [p.name for p in (REPO_ROOT / "specs").glob("*.md")
                  if p.name != "DECLINED.md" and "MCP-NEGATIVE:" in p.read_text(encoding="utf-8")]
        self.assertTrue(others, "no other specs/ file carries marker text — the exclusion test "
                                "above is asserting nothing")

    def test_the_comment_says_why_declined_md_is_the_exception(self):
        """A bare constant invites the next reader to 'tidy' it into NEGATIVE_ROOTS."""
        src = SCRIPT.read_text(encoding="utf-8")
        m = re.search(r"((?:^#:.*\n)+)NEGATIVE_EXTRA_FILES", src, re.M)
        self.assertIsNotNone(m, "NEGATIVE_EXTRA_FILES carries no explanatory comment")
        why = m.group(1)
        self.assertIn("Step 3.3", why, "the comment must say what does NOT re-verify this file")
        self.assertRegex(why, r"(?i)never implemented|declined spec is never")

    def test_the_surface_distinguishes_declined_from_the_rest_of_specs(self):
        """Exercised on a scratch tree, so it holds however the real corpus moves.

        A live-repo assertion alone cannot notice the file-level scan being replaced by a
        directory walk that happens to find the same markers today.
        """
        stamp = "— server 1.32.9, 2026-08-13"
        good = ("MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list "
                "— owner: get_capabilities carries it " + stamp)
        clauseless = "MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list " + stamp
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()
            (root / "plugins").mkdir()
            (root / "plugins" / "shipped.md").write_text(good, encoding="utf-8")
            (root / "specs" / "DECLINED.md").write_text(good + "\n" + clauseless, encoding="utf-8")
            (root / "specs" / "a-spec.md").write_text(good, encoding="utf-8")
            (root / "specs" / "IMPLEMENTED.md").write_text(good, encoding="utf-8")
            found = sorted(Path(r[5]).name for r in reports.find_negatives(str(root)))
            malformed = sorted(Path(r[0]).name for r in reports.find_malformed_negatives(str(root)))
        self.assertEqual(
            ["DECLINED.md", "shipped.md"], found,
            "the worklist must carry the shipped claim and DECLINED.md's, and neither the "
            "spec body's nor IMPLEMENTED.md's; got %r" % (found,),
        )
        self.assertEqual(
            ["DECLINED.md"], malformed,
            "an `owner:`-less marker in DECLINED.md must be reported as malformed exactly as "
            "one in plugins/ is — that is the whole point of adding the file; got %r"
            % (malformed,),
        )


class TestUnmarkedReport(unittest.TestCase):
    """`unmarked` finds dated tool-absence prose that carries no marker.

    It is the complement of `negatives`, which can only list what is already tagged. Every design
    decision below was made by measuring against the real corpus on 2026-08-13, and each is pinned
    here because the tuning is what makes the report readable:

    * A bare `never` matched "never from training data", "never `exit 1`", "never re-read" — 23 hits
      with it, 8 without. Excluded.
    * A contiguous bullet list read as one unit produced a false positive on `ground-rules.md`'s
      tool-routing list, where a tool name, an absence phrase and a date sat in three *different*
      bullets. Units are per-bullet.
    * A fenced block stays whole, because a claim there is routinely split across two comment
      lines — the tool on one, the date on the next.
    * The **date** is the discriminator: undated prose about tool behavior is not a re-checkable
      claim, so it is not reported.
    """

    def report(self, root):
        return reports.find_unmarked_negatives(str(root))

    def test_it_runs_from_an_unrelated_directory_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = run("unmarked", tmp)
        self.assertEqual(0, code, "a report informs an audit; it never gates one. stderr:\n%s" % err)
        self.assertIn("NO marker", out)

    def test_the_live_corpus_is_clean(self):
        """⚠️ Was `assertGreaterEqual(len(found), 1)` until 2026-08-13, and the change is the point.

        The report was built with 6 live hits, so non-vacuity on the real corpus was then the
        useful assertion. `verify-and-mark-the-six-unmarked-prose-negatives` re-asked all five
        genuine claims against server 1.32.9, marked them, and triaged the sixth as not-a-tool-claim
        — so the live count is now 0 and the old assertion would fail on a **clean** repo.

        Rewritten rather than deleted: the expectation flipped, and the detector's non-vacuity is
        now proven on scratch trees below, which is where it belonged all along. A live-corpus
        count is a fact about today's corpus, not about whether the detector works.
        """
        found = self.report(REPO_ROOT)
        self.assertEqual(
            [], found,
            "shipped prose carries a dated tool-absence claim with no marker. Re-ask its owning "
            "route, then mark it — never stamp today's date on an unverified claim. If it is not "
            "a claim about a tool's content, declare that with the not-a-tool-claim escape:\n  "
            + "\n  ".join("%s:%d  %s" % (r[1], r[2], r[4]) for r in found),
        )

    def test_the_live_hits_carry_the_five_fields_the_report_prints(self):
        for row in self.report(REPO_ROOT):
            stamp, relpath, lineno, phrase, excerpt = row
            with self.subTest(where="%s:%d" % (relpath, lineno)):
                self.assertRegex(stamp, r"^(20\d\d-\d\d-\d\d|server \d)")
                self.assertTrue(relpath.startswith("plugins"), "prose scan is plugin-only")
                self.assertGreater(lineno, 0)
                self.assertTrue(phrase.strip() and excerpt.strip())

    def _tree(self, tmp, body):
        root = pathlib.Path(tmp)
        (root / "specs").mkdir(exist_ok=True)
        d = root / "plugins" / "senzing-bootcamp" / "skills" / "m"
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(body, encoding="utf-8")
        return root

    def test_a_dated_absence_with_no_marker_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, "- `sdk_guide` returns no upgrade topic (verified 2026-07-31).\n")
            self.assertEqual(1, len(self.report(root)))

    def test_the_same_claim_with_a_marker_is_not_reported(self):
        marker = ("<!-- MCP-NEGATIVE: sdk_guide(topic='install') — returns no upgrade topic "
                  "— owner: sdk_guide is the route that would carry it — server 1.32.9, "
                  "2026-08-13 -->")
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(
                tmp,
                "- `sdk_guide` returns no upgrade topic (verified 2026-07-31).\n" + marker + "\n")
            self.assertEqual([], self.report(root))

    def test_an_undated_absence_is_not_reported(self):
        """The discriminator. INV-192's 'empty by design' sentence must never need a marker."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "- A `needs_input` response is a gate, not an answer. Never report a topic as "
                "having no guidance on the strength of a gated response: the payload of a gate "
                "is empty by design, not because the topic is undocumented.\n"))
            self.assertEqual([], self.report(root),
                             "undated prose explaining how a tool behaves is not a claim that "
                             "expires, and requiring a marker for it would push authors to "
                             "weaken correct writing")

    def test_signals_split_across_separate_bullets_are_not_one_claim(self):
        """The `ground-rules.md` false positive, pinned so the granularity cannot regress."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "- Tool routing: SDK code -> `sdk_guide`; docs -> `search_docs`.\n"
                "- Some other rule that returns no value here.\n"
                "- Verified on 2026-07-31 against the live server.\n"))
            self.assertEqual([], self.report(root))

    def test_a_fenced_claim_split_across_two_comment_lines_is_one_unit(self):
        """The module-02 shape: tool on one comment line, date on the next."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "```bash\n"
                "# plugin-owned — sdk_guide documents no version-management command:\n"
                "# never outdated or upgrade (checked across its whole response, 2026-08-13)\n"
                "brew outdated --cask senzingsdk\n"
                "```\n"))
            self.assertEqual(1, len(self.report(root)),
                             "a fence must be one unit, or a claim whose tool and date sit on "
                             "different comment lines is invisible")

    def test_quoted_history_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "- It once said `sdk_guide` returns no upgrade topic (verified 2026-07-31).\n"
                "  <!-- MCP-NEGATIVE-SCAN: quoted-history — retracted claim, kept verbatim -->\n"))
            self.assertEqual([], self.report(root))

    def test_the_file_level_opt_out_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "MCP-NEGATIVE-SCAN: ignore-file — fixtures below.\n\n"
                "- `sdk_guide` returns no upgrade topic (verified 2026-07-31).\n"))
            self.assertEqual([], self.report(root))

    def test_a_bare_never_does_not_trigger_it(self):
        """15 of 23 measured hits were this. Pinned so the vocabulary cannot be re-loosened."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp, (
                "- ALL Senzing facts come from `search_docs` and friends, never from training "
                "data. Re-assessed 2026-07-26.\n"))
            self.assertEqual([], self.report(root))

    def test_specs_and_tests_are_out_of_scope(self):
        """They have their own mechanisms: Step 3.3, INV-217, and the assertion-line guard."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "specs").mkdir()
            (root / "tests").mkdir()
            claim = "- `sdk_guide` returns no upgrade topic (verified 2026-07-31).\n"
            (root / "specs" / "a-spec.md").write_text(claim, encoding="utf-8")
            (root / "tests" / "t.md").write_text(claim, encoding="utf-8")
            self.assertEqual([], self.report(root))


class TestAffectedReport(unittest.TestCase):
    def test_it_reports_gaps_without_choking_on_specless_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _ = run("affected", tmp)
        m = re.search(r"ledgered specs examined: (\d+)\s+with a gap: (\d+)", out)
        self.assertIsNotNone(m, f"the summary line is gone:\n{out[:400]}")
        examined, gaps = (int(g) for g in m.groups())
        self.assertGreater(examined, 150, "far fewer ledger entries parsed than exist")
        self.assertGreater(
            gaps, 0, "no gaps at all — the corpus had 38 when this report was written"
        )
        self.assertLess(gaps, examined, "every entry flagged; the matcher is broken")
