"""The candidate set is computed, not hand-counted — and it subtracts the declined set.

`implement-spec` Step 3 has always said to subtract `DECLINED.md`, and said why: "Omitting the
declined set re-offers a spec the maintainer has already ruled out, every run." On 2026-08-13 a
run did it by hand, subtracted only `IMPLEMENTED.md`, reported a **declined** spec as open,
recommended it to the maintainer, and implemented it. `tests/test_declined_ledger.py` caught the
contradiction after the fact; nothing caught the listing that produced it.

`list_specs.py` exists so the subtraction is not a thing anyone does by hand. This file tests the
script's arithmetic against synthetic fixtures rather than only against the live repo -- the live
repo currently has zero open specs, so "it agrees with the repo" is a claim about an empty set and
would pass on a script that returned nothing at all.

Enforces **INV-216**.

Run:  python3 -m unittest discover -s tests
"""

import importlib.util
import io
import contextlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "skills" / "implement-spec" / "list_specs.py"


def load():
    spec = importlib.util.spec_from_file_location("list_specs_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["list_specs_under_test"] = module
    spec.loader.exec_module(module)
    return module


ls = load()


def scratch(tmp, specs=(), implemented=(), declined=()):
    """A repo-shaped directory with the given spec files and ledger headings."""
    root = Path(tmp)
    (root / "specs").mkdir()
    for name in specs:
        (root / "specs" / f"{name}.md").write_text("# spec\n", encoding="utf-8")
    def ledger(fname, names):
        body = "# Ledger\n\n<!-- format:\n\n## <spec-name>\n\n-->\n\n"
        body += "".join(f"## {n}\n\n- **Implemented:** 2026-08-13\n\n" for n in names)
        (root / "specs" / fname).write_text(body, encoding="utf-8")
    ledger("IMPLEMENTED.md", implemented)
    ledger("DECLINED.md", declined)
    return str(root)


class TheDeclinedSetIsSubtracted(unittest.TestCase):
    def test_a_declined_spec_is_not_open(self):
        """The exact failure of 2026-08-13, as a fixture."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha", "beta"), implemented=("alpha",),
                           declined=("beta",))
            open_, impl, decl, both = ls.compute(root)
            self.assertEqual([], open_,
                             "beta is declined and alpha implemented, so nothing is open")
            self.assertEqual(["alpha"], impl)
            self.assertEqual(["beta"], decl)
            self.assertEqual([], both)

    def test_subtracting_only_implemented_would_have_reported_it_open(self):
        """Pins the arithmetic that went wrong, so the fix cannot silently regress.

        Without this, a script that dropped the DECLINED subtraction would still pass the test
        above only if the fixture happened to have no declined specs. Here the difference between
        the correct and incorrect computations is asserted directly.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha", "beta"), implemented=("alpha",),
                           declined=("beta",))
            correct, _impl, decl, _both = ls.compute(root)
            naive = sorted(ls.candidates(root) - ls._headings(root, "IMPLEMENTED.md"))
            self.assertEqual(["beta"], naive,
                             "the naive computation is what reported a declined spec as open")
            self.assertNotEqual(naive, correct,
                                "the script must differ from the naive computation")
            self.assertEqual(decl, naive,
                             "and the difference is exactly the declined set")

    def test_a_genuinely_open_spec_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha", "beta", "gamma"), implemented=("alpha",),
                           declined=("beta",))
            open_, _i, _d, _b = ls.compute(root)
            self.assertEqual(["gamma"], open_)


class ItSurfacesTheContradictoryCase(unittest.TestCase):
    def test_a_spec_in_both_ledgers_is_flagged_not_silently_subtracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha",), implemented=("alpha",), declined=("alpha",))
            open_, _i, _d, both = ls.compute(root)
            self.assertEqual(["alpha"], both,
                             "implemented AND declined means one record is wrong; it must be "
                             "reported rather than quietly subtracted twice")
            self.assertEqual([], open_)

    def test_check_exits_non_zero_when_a_spec_is_in_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha",), implemented=("alpha",), declined=("alpha",))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ls.main(["--repo", root, "--check"])
            self.assertEqual(2, rc, "--check must fail on the contradictory case")
            self.assertIn("IN BOTH LEDGERS", buf.getvalue())

    def test_listing_exits_zero_even_with_findings(self):
        """It informs a run; it does not gate one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha",), implemented=(), declined=())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ls.main(["--repo", root])
            self.assertEqual(0, rc)
            self.assertIn("alpha", buf.getvalue())


class TemplatePlaceholdersAreNotCounted(unittest.TestCase):
    def test_the_scaffold_heading_is_ignored(self):
        """Both ledgers carry a literal `## <spec-name>` example in their format comment."""
        self.assertEqual(set(), {h for h in ("<spec-name>",) if "<" not in h},
                         "sanity: the filter drops angle-bracketed headings")
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, specs=("alpha",), implemented=())
            self.assertNotIn("<spec-name>", ls._headings(root, "IMPLEMENTED.md"))


class TheLiveRepoAgreesAndTheOutputIsUsable(unittest.TestCase):
    def test_the_live_repo_has_no_spec_in_both_ledgers(self):
        _open, _impl, _decl, both = ls.compute(str(REPO_ROOT))
        self.assertEqual([], both, "a spec is both implemented and declined — resolve it")

    def test_the_live_counts_are_non_vacuous(self):
        """Guards against a script that reads nothing and reports a clean empty set."""
        _open, impl, decl, _both = ls.compute(str(REPO_ROOT))
        self.assertGreater(len(impl), 200, "implemented set came back suspiciously small")
        self.assertGreaterEqual(len(decl), 1, "the declined set should not be empty")

    def test_the_report_warns_about_reopening_a_declined_spec(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ls.report(str(REPO_ROOT))
        out = buf.getvalue()
        self.assertIn("DECLINED", out)
        self.assertRegex(
            out, r"(?i)revisit if",
            "the report must send the reader to the Revisit if: clause before reopening — the "
            "spec file argues FOR the change and only the ledger records the argument against",
        )


# ⛔ REMOVED 2026-09-16 (#60): `TheSkillNamesTheScript` asserted INV-216's SECOND and THIRD
# clauses -- that `implement-spec` names this script, and that its prose steps explain what the
# script computes and why. Both were **scoped to the archive** by a dated correction to INV-216
# on 2026-09-16, because `specs/` froze under INV-307 and the candidate set is permanently
# `open: 0`, so the prose they pinned documented a retired workflow. `/implement-spec` retired
# under the same issue and there is no command left that is required to name the script.
#
# ⚠️ **INV-216's FIRST clause is untouched and still binding**, which is why everything above
# stays: the candidate set MUST be computed rather than hand-counted, and MUST subtract BOTH
# terminal states. That is a property of `list_specs.py` itself, and this file still tests it
# against synthetic fixtures -- the live repo has zero open specs, so "it agrees with the repo"
# would pass on a script that returned nothing at all.


if __name__ == "__main__":
    unittest.main()
