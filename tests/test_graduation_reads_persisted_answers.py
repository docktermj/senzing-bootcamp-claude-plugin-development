"""Graduation reads the keys that are actually written, and uses the answers it reads.

Three defects from the 2026-07-29 deep-dive audit, all in `graduation/SKILL.md`, all invisible
to the 1015-test suite that ran the day they were found:

1. **Three preference keys nothing writes** (`graduation-prechecks-read-the-keys-that-are-written`).
   Pre-checks read `language`, `database` and `data_sources`. The writers use
   `programming_language` (Bootcamp preparation), `database_type` (SDK setup Step 7) and
   `config/data_sources.yaml` (its own file, INV-050). The keys resolved to nothing, and because
   the fallback fires on a missing *file* rather than a missing *key*, nothing asked and nothing
   warned — six consumers degraded silently, including Step 6a's backup branch, which chooses
   file-copy vs `pg_dump` off that read. SDK setup had predicted it in its own words: "a different
   key name is the same failure as no key at all."

2. **INV-097's second half unbuilt** (`graduation-reads-integration-and-deployment-answers`).
   The invariant says the Module 1 integration/deployment answers are "read by the Module 1 problem
   statement **and by graduation**". Graduation contained zero references to them, so two pinned
   👉 questions changed nothing in the `production/` project — the artifact whose entire purpose is
   the thing being deployed.

3. **INV-060's second half unbuilt** (`normalize-production-markdown-at-graduation`).
   The invariant requires the CommonMark pass over `docs/*.md` **and the generated
   `production/*.md`**. Only `docs/` shipped; `production/` was hand-formatted, which
   `ground-rules.md` explicitly says not to rely on.

**Why the key contract is declared here rather than inferred.** Inferring "is this key written
somewhere?" was measured and rejected: `language:` and `database:` both appear in prose in other
skill files (so an inferred rule *passes* the two broken keys), while `deployment_target`, `os`,
`arch` and `data_sources` appear in no `key: value` form anywhere (so it *fails* four legitimate
ones). A rule that both false-passes and false-fails is worse than no rule — the shape INV-144 and
INV-173 forbid. So WRITERS below is a small maintained fact, and both directions are asserted
against it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

# Every `config/bootcamp_preferences.yaml` key graduation is allowed to read, mapped to the
# skill file that writes it. A reader naming anything else is the defect this pins.
WRITERS = {
    "name": "bootcamp-preparation/SKILL.md",
    "programming_language": "bootcamp-preparation/SKILL.md",
    "path": "bootcamp-preparation/SKILL.md",
    "selected_modules": "bootcamp-preparation/SKILL.md",
    "database_type": "module-02-sdk-setup/SKILL.md",
    "integration_targets": "module-01-business-problem/phase2-document-confirm.md",
    "deployment_target": "module-01-business-problem/phase2-document-confirm.md",
    "cloud_provider": "module-01-business-problem/phase2-document-confirm.md",
}

# Names that were read but never written. Kept as a regression list: a rename that reintroduces
# one of these is the original defect, not a new one.
NEVER_WRITTEN = ("language", "database", "data_sources")


#: A pinned question ``👉 **…?**`` whose bold run asks about deployment or integration. Matched
#: by ``match_lines`` on whitespace-collapsed blocks (#424), so a bold run that wraps is read
#: whole; one line at a time, ``(.+?)\*\*`` never closed on such a line and the question passed.
DEPLOYMENT_QUESTION = re.compile(
    r"👉\s*\*\*(?=(?:(?!\*\*).)*\?)(?=(?:(?!\*\*).)*(?i:deploy|integrat))")


def graduation_text():
    return GRADUATION.read_text(encoding="utf-8")


def prechecks_section():
    """The Pre-checks section, where the preference read is declared."""
    text = graduation_text()
    start = text.index("## Pre-checks")
    end = text.index("## Step 0", start)
    return text[start:end]


def declared_keys():
    """Keys in the first column of Pre-checks' key table — what it says it extracts.

    Scoped to the table on purpose. An earlier version of these tests asked only whether the
    key appeared *somewhere* in Pre-checks, and mutation-testing caught it: deleting the
    `integration_targets` table row still passed, because the prose below it mentions the key
    too. "Declared as a key to read" is the property; "mentioned nearby" is not.

    Line-scoped by design (#424): a table row is one line.
    """
    keys = set()
    for line in prechecks_section().splitlines():
        m = re.match(r"\s*\|\s*`([a-z_]+)`(\s*/\s*`([a-z_]+)`)?\s*\|", line)
        if m:
            keys.add(m.group(1))
            if m.group(3):
                keys.add(m.group(3))
    return keys


class TestPreferenceKeysHaveWriters(unittest.TestCase):
    def test_every_declared_writer_actually_mentions_its_key(self):
        """The map is only useful if its right-hand side is true."""
        missing = []
        for key, writer in WRITERS.items():
            path = SKILLS / writer
            if not path.is_file():
                missing.append(f"{writer} does not exist (writer for `{key}`)")
                continue
            if key not in path.read_text(encoding="utf-8"):
                missing.append(f"{writer} never mentions `{key}`")
        self.assertEqual([], missing, "WRITERS is stale:\n  " + "\n  ".join(missing))

    def test_prechecks_declare_the_written_key_for_language_and_database(self):
        declared = declared_keys()
        for key in ("programming_language", "database_type"):
            self.assertIn(
                key,
                declared,
                f"graduation's Pre-checks must DECLARE `{key}` as a key it reads — the key its "
                f"writer actually writes. Declared: {sorted(declared)}",
            )

    def test_prechecks_do_not_read_a_key_nobody_writes(self):
        """`language` / `database` / `data_sources` as *preference keys* are the defect.

        A line that frames one as retired is allowed and wanted — the same carve-out
        INV-158 makes for retired vocabulary, and the reason Pre-checks can say "this step
        used to read `language`". Only an unframed mention reads as an instruction.
        """
        # Flattened, because the framing phrase and the mention routinely land on different
        # source lines once the prose wraps — the trap `flatten()` exists for in
        # test_spec_ledger_invariants.py. Framing is looked for in a window around the mention.
        section = re.sub(r"\s+", " ", prechecks_section())
        framed = ("**not**", "nothing has ever written", "not a preferences key")
        offenders = []
        for key in NEVER_WRITTEN:
            # Only a backticked bare key counts: the words appear legitimately in prose, and
            # `data_sources.yaml` / `database_type` must not trip this.
            for m in re.finditer(r"`%s`(?!\.)" % re.escape(key), section):
                window = section[max(0, m.start() - 160):m.end() + 160]
                if not any(f in window for f in framed):
                    offenders.append(key)
                    break
        self.assertEqual(
            [],
            offenders,
            "graduation's Pre-checks read preference key(s) that nothing writes: "
            + ", ".join(offenders)
            + " — see SDK setup Step 7: a different key name is the same failure as no key at all",
        )

    def test_the_registry_is_read_from_its_own_file(self):
        self.assertIn(
            "`config/data_sources.yaml`",
            prechecks_section(),
            "the data-source registry is its own file (INV-050), not a preferences key",
        )

    def test_a_missing_key_is_distinguished_from_a_missing_file(self):
        section = prechecks_section()
        flat = re.sub(r"\s+", " ", section).lower()
        self.assertIn(
            "a file is present but a key is absent",
            flat,
            "Pre-checks must distinguish an absent key from an absent file — the fallback fired "
            "only on a missing file, so a wrong key name asked nothing and warned nothing",
        )


class TestModule1AnswersReachGraduation(unittest.TestCase):
    """INV-097: the integration/deployment answers are read by graduation, and used."""

    KEYS = ("integration_targets", "deployment_target", "cloud_provider")

    def test_prechecks_declare_all_three_keys(self):
        declared = declared_keys()
        for key in self.KEYS:
            self.assertIn(
                key,
                declared,
                f"Pre-checks must DECLARE `{key}` as a key it reads (INV-097). "
                f"Declared: {sorted(declared)}",
            )

    def test_each_consuming_step_references_them(self):
        """Reading them and not using them is the same defect one layer in."""
        text = graduation_text()
        steps = {
            "Step 3": (text.index("## Step 3:"), text.index("## Step 4:")),
            "Step 4": (text.index("## Step 4:"), text.index("## Step 5:")),
            "Step 5": (text.index("## Step 5:"), text.index("## Step 5a:")),
        }
        for step, (start, end) in steps.items():
            body = text[start:end]
            self.assertTrue(
                any(k in body for k in self.KEYS),
                f"{step} generates a production deliverable but never references the "
                "deployment/integration answers (INV-097)",
            )

    def test_graduation_never_asks_for_them(self):
        """They are asked once, in Module 1 (INV-006/INV-097).

        Matches the *pinned question* form `👉 **…?**` only. Prose that refers to Module 1's
        questions ("the answers to two pinned 👉 questions asked in Module 1") is not
        graduation asking one, and a keyword-anywhere-near-👉 rule flags it.
        """
        text = graduation_text()
        asked = match_lines(text, DEPLOYMENT_QUESTION)
        self.assertEqual(
            [], asked,
            "graduation must not ask a 👉 question about deployment or integration — asked "
            "once in Module 1 (INV-006/INV-097): %r"
            % [text.split("\n")[n - 1].strip()[:110] for n in asked])

    def test_a_wrapped_deployment_question_is_caught(self):
        """Negative control (#424): the bold run opens on line 1 and closes on line 2."""
        wrapped = "👉 **Where do you plan to\ndeploy this?**\n"
        self.assertEqual([1], match_lines(wrapped, DEPLOYMENT_QUESTION))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        for line in wrapped.split("\n"):
            m = re.search(r"👉\s*\*\*(.+?)\*\*", line)
            self.assertFalse(m and "?" in m.group(1)
                             and re.search(r"deploy|integrat", m.group(1), re.I))

    def test_prose_about_module_1s_questions_is_not_a_question(self):
        """Must-not-flag (INV-282): naming Module 1's pinned questions asks nothing."""
        self.assertEqual([], match_lines(
            "Use the answers to two pinned 👉 questions asked in Module 1 about where they\n"
            "will deploy and what they integrate with.\n", DEPLOYMENT_QUESTION))

    def test_absence_is_explicitly_harmless(self):
        flat = re.sub(r"\s+", " ", graduation_text()).lower()
        self.assertIn(
            "absent is normal",
            flat,
            "an absent value must be documented as normal and silent — Module 1 may not have "
            "run under a Customized path (INV-076)",
        )


class TestProductionMarkdownIsNormalized(unittest.TestCase):
    """INV-060: the pass runs over `docs/*.md` AND the generated `production/*.md`."""

    def test_both_normalizer_invocations_exist(self):
        text = graduation_text()
        self.assertIn(
            'normalize_docs_markdown.py"\n',
            text.replace("'", '"'),
            "the docs/*.md pass is missing",
        )
        self.assertRegex(
            text,
            r"normalize_docs_markdown\.py[^\n]*--docs-dir production",
            "no normalization pass over the generated `production/*.md` (INV-060's second half)",
        )

    def test_the_production_pass_runs_after_the_production_files_exist(self):
        text = graduation_text()
        step5 = text.index("## Step 5: Graduation report")
        production_pass = text.index("--docs-dir production")
        self.assertGreater(
            production_pass,
            step5,
            "the production pass must run after Step 5 writes GRADUATION_REPORT.md — "
            "`production/` does not exist at Step 1a",
        )

    def test_production_deliverables_are_not_hand_formatted(self):
        """Hand-formatting is what INV-060 exists to replace."""
        text = graduation_text()
        start = text.index("## Step 4:")
        end = text.index("## Step 5:")
        flat = re.sub(r"\s+", " ", text[start:end]).lower()
        self.assertIn(
            "plain, functional markdown",
            flat,
            "Step 4 must ask for plain Markdown and point at the pass, not ask the guide to "
            "hand-apply the house rules (ground-rules.md → Markdown files)",
        )

    def test_the_revisit_guide_states_which_pass_covers_it(self):
        """Written at 6c, after both passes — so it must say what it does instead."""
        text = graduation_text()
        start = text.index("### 6c. Return guide")
        flat = re.sub(r"\s+", " ", text[start:start + 1600]).lower()
        self.assertIn(
            "hand-format",
            flat,
            "REVISIT_BOOTCAMP.md is written after both normalization passes, so 6c must state "
            "its own formatting rule rather than pointing at a pass that cannot reach it",
        )
