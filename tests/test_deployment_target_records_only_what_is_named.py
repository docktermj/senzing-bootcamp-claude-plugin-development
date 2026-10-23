"""The deployment answer records only what the Bootcamper named, and every reader says so (#785).

Module 1 Step 10a's deployment question offers four numbered options. Until #785, option 1
("A cloud hyperscaler (AWS/Azure/GCP)") recorded `aws`, `azure` or `gcp`, so a bare "1" forced
the guide to invent a provider, which graduation Step 3 then stamped into production files.
Options 2 and 3 had the same problem.

What this pins, each against the shipped text and each with a negative control on a mutated copy:

1. **Step 10a's mapping.** Each option's handling entry records the option's generic value
   (`cloud`, `container`, `local`) unless the Bootcamper names a specific one. Every sentence that
   records a specific value carries the naming condition, and the sentence for a bare number
   records the generic value and no specific one. Option 1 writes `cloud_provider` only when a
   provider is named, and a provider outside the three is recorded lowercased beside `cloud`. The
   write sentence lists the same value set the entries record, so the two cannot drift.
2. **No new question (INV-251).** The handling block asks nothing.
3. **Step 11's template** renders a generic value as its category with Platform "Not stated",
   and keeps its existing lines for the older values.
4. **Graduation** states the generic-value rendering once, in pre-check 1a, where each generic
   value's rendering says the platform was not stated; Step 3's header comment, Step 4's
   Deployment section and Step 5's report each link it rather than restating it (INV-300). The
   Deployment section gives each category its checkboxes, the container list naming no
   orchestrator. Every existing specific-value line is kept word for word.

These assert that the skill files *state* the mapping and the rendering. They **cannot** establish
that a live guide records `cloud` for a bare "1"; only `dry-run` phase 3 can observe that.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE1 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

#: option number → (generic value, specific values recorded only when named)
OPTIONS = {
    "1": ("cloud", ("aws", "azure", "gcp")),
    "2": ("container", ("kubernetes", "docker_swarm")),
    "3": ("local", ("on_premises",)),
}
UNDECIDED = "undecided"
ALL_VALUES = {UNDECIDED} | {v for g, s in OPTIONS.values() for v in (g, *s)}

#: The naming condition a sentence recording a specific value must carry.
NAMED = re.compile(r"\bnames?\b|\bnamed\b", re.I)

ANCHOR = "generic-deployment-target"


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def step10a(text):
    return section(text, "## 10a.", "## 11.")


def handling_block(text):
    """Step 10a's deployment handling: from its INV-284 marker to Step 11."""
    body = step10a(text)
    return body[body.index("**Handling each answer (INV-284).**"):]


def handling_entries(text):
    """{option number: flattened entry} for each `- **N, "…":**` item in the handling block."""
    entries = {}
    for m in re.finditer(r"^- \*\*(\d), \"[^\"]+\":\*\*(.*?)(?=^- \*\*|\Z)",
                         handling_block(text), re.M | re.S):
        entries[m.group(1)] = flat(m.group(2))
    return entries


def sentences(entry):
    return [s for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])", entry) if s]


def values_in(s):
    return set(re.findall(r"`([a-z_]+)`", s)) & ALL_VALUES


def mapping_problems(text):
    """Every way Step 10a's handling can record a value the answer did not determine."""
    problems = []
    entries = handling_entries(text)
    if sorted(entries) != ["1", "2", "3", "4"]:
        return [f"handling entries found for options {sorted(entries)}, expected 1-4"]
    for n, (generic, specifics) in OPTIONS.items():
        entry = entries[n]
        recorded = values_in(entry)
        if recorded != {generic, *specifics}:
            problems.append(f"option {n} records {sorted(recorded)}, expected "
                            f"{sorted({generic, *specifics})}")
        for s in sentences(entry):
            if values_in(s) & set(specifics) and not NAMED.search(s):
                problems.append(f"option {n} records a specific value with no naming "
                                f"condition: {s!r}")
        bare = [s for s in sentences(entry) if f'a bare "{n}"' in s]
        if not bare:
            problems.append(f'option {n} says nothing about a bare "{n}"')
        for s in bare:
            if generic not in values_in(s):
                problems.append(f'a bare "{n}" does not record `{generic}`: {s!r}')
            if values_in(s) & set(specifics):
                problems.append(f'a bare "{n}" records a specific value: {s!r}')
    one = entries["1"]
    bare_one = [s for s in sentences(one) if 'a bare "1"' in s]
    if not any("no `cloud_provider`" in s for s in bare_one):
        problems.append('a bare "1" must record no `cloud_provider`')
    other = [s for s in sentences(one) if "lowercased" in s]
    if not any("`cloud`" in s and "`cloud_provider`" in s for s in other):
        problems.append("a provider outside AWS/Azure/GCP must record `cloud` with "
                        "`cloud_provider` lowercased")
    if values_in(entries["4"]) != {UNDECIDED}:
        problems.append(f"option 4 records {sorted(values_in(entries['4']))}, expected undecided")
    return problems


def write_sentence(text):
    body = step10a(text)
    return flat(section(body, "**Now write both answers together**", "**Handling each answer"))


def question_problems(text):
    """The handling block asks nothing: no follow-up 👉 for a provider or platform (INV-251)."""
    return ["the deployment handling asks a 👉 question"] if "👉" in handling_block(text) else []


def template_deployment(text):
    return flat(section(text, "## Deployment Target", "## Timeline"))


def template_problems(text):
    problems = []
    t = template_deployment(text)
    m = re.search(r"If a generic value \(([^)]*)\): (.*?)\]", t)
    if not m:
        return ["Step 11's Deployment Target template has no generic-value case"]
    if values_in(m.group(1)) != {g for g, _ in OPTIONS.values()}:
        problems.append(f"the generic-value case names {sorted(values_in(m.group(1)))}")
    if 'Platform "Not stated"' not in m.group(2):
        problems.append('the generic-value case must give Platform "Not stated"')
    if not all(c in m.group(2) for c in ("Cloud", "Container", "Local")):
        problems.append("the generic-value case must give Category Cloud, Container or Local")
    if "bare" in t:
        problems.append("Step 11's template restates Step 10a's mapping (INV-300)")
    return problems


def rendering_paragraph(text):
    i = text.index(f'<a id="{ANCHOR}"></a>')
    return flat(text[i:text.index("\n\n", i)])


def graduation_problems(text):
    """Graduation's generic-value rendering: stated once in pre-check 1a, linked by each reader."""
    problems = []
    if text.count(f'<a id="{ANCHOR}"></a>') != 1:
        return [f"graduation must carry the `{ANCHOR}` anchor exactly once"]
    prechecks = section(text, "## Pre-checks", "## Step 0")
    if f'<a id="{ANCHOR}"></a>' not in prechecks:
        problems.append("the generic-value rendering must sit in pre-check 1a")
    para = rendering_paragraph(text)
    renderings = {}
    for generic, _ in OPTIONS.values():
        m = re.search(r"`%s` → \"([^\"]+)\"" % generic, para)
        if not m:
            problems.append(f"pre-check 1a gives no rendering for `{generic}`")
            continue
        renderings[generic] = m.group(1)
        if "not stated" not in m.group(1):
            problems.append(f"`{generic}`'s rendering does not say the platform was not stated: "
                            f"{m.group(1)!r}")
        if re.search(r"\b(AWS|Azure|GCP|Kubernetes|Docker Swarm)\b", m.group(1), re.I):
            problems.append(f"`{generic}`'s rendering names a platform: {m.group(1)!r}")
    if "Step 10a" not in para or "INV-300" not in para:
        problems.append("pre-check 1a must point at Step 10a for the mapping, citing INV-300")
    if "never guesses" not in para:
        problems.append("pre-check 1a must say a generic value never becomes a guessed platform")
    whole = flat(text)
    for generic, r in renderings.items():
        if whole.count(r) != 1:
            problems.append(f"`{generic}`'s rendering {r!r} is stated {whole.count(r)} times; "
                            "state it once and link it (INV-300)")
    if re.search(r'a bare "\d"', text, re.I):
        problems.append("graduation restates Step 10a's answer mapping (INV-300)")
    readers = {
        "Step 3's header comment": flat(section(
            text, "**Where `deployment_target`/`cloud_provider` is known", "\n\n")),
        "Step 4's Deployment section": flat(section(
            text, "**The Deployment section is where", "\n\n")),
        "Step 5's report": flat(section(
            text, "Record the Module 1 answers too", "\n\n")),
    }
    for name, body in readers.items():
        if f"](#{ANCHOR})" not in body:
            problems.append(f"{name} does not link pre-check 1a's generic-value rendering")
    deployment = readers["Step 4's Deployment section"]
    for want in ("`cloud` the cloud list", "`container` a container list naming no "
                 "orchestrator-specific tooling", "`local` the on-premises list"):
        if want not in deployment:
            problems.append(f"Step 4's Deployment section lacks the category checkboxes: {want!r}")
    if "stated" not in readers["Step 5's report"]:
        problems.append("Step 5's report must say when the platform was not stated")
    return problems


#: Lines for values recorded before #785, which must render as they did (word for word).
KEPT_MODULE1 = (
    'If "not sure yet": Platform "To be determined", Category "Undecided".',
    'If absent: "Not applicable: deployment target not captured for this bootcamp."',
    "Platform / Category (Cloud/Container/Local/ Undecided)",
)
KEPT_GRADUATION = (
    "`# Target: AWS (ECS/Fargate)`, `# Target: Kubernetes`, `# Target: on-premises`",
    "a cloud target → managed database, secret storage, image registry, network egress to "
    "nothing external; Kubernetes → manifests/Helm, resource limits, liveness probes; "
    "on-premises → host provisioning, backup schedule",
    "Absent → the generic six-section list exactly as before.",
    "omit either line when absent.",
    "⛔ Stay declarative: name the target and stop.",
    "When the value is absent the files are exactly as they were before this paragraph.",
)


class TestStep10aRecordsOnlyWhatIsNamed(unittest.TestCase):
    def setUp(self):
        self.text = MODULE1.read_text(encoding="utf-8")

    def test_each_answer_maps_to_one_value_without_a_guess(self):
        self.assertEqual([], mapping_problems(self.text))

    def test_the_write_lists_every_value_the_entries_record(self):
        listed = values_in(write_sentence(self.text))
        recorded = set().union(*(values_in(e) for e in handling_entries(self.text).values()))
        self.assertEqual(ALL_VALUES, listed)
        self.assertEqual(listed, recorded)
        self.assertIn("`cloud_provider` when a provider is named", write_sentence(self.text))

    def test_no_follow_up_question(self):
        self.assertEqual([], question_problems(self.text))


class TestStep10aNegativeControls(unittest.TestCase):
    """Each mutation is a way the mapping can guess; each must be reported."""

    def setUp(self):
        self.text = MODULE1.read_text(encoding="utf-8")
        self.entry1 = re.search(r'^- \*\*1, "A cloud hyperscaler":\*\*.*?(?=^- \*\*2)',
                                self.text, re.M | re.S).group(0)

    def mutate_entry1(self, new):
        return self.text.replace(self.entry1, new)

    def test_a_bare_1_recording_aws_is_caught(self):
        for value in ("aws", "azure", "gcp"):
            mutated = self.mutate_entry1(
                f'- **1, "A cloud hyperscaler":** `aws`, `azure` or `gcp` when the Bootcamper '
                f'names it. Otherwise `cloud`. Named none (a bare "1") → `{value}`, and no '
                "`cloud_provider`. Named another (\"1, Oracle Cloud\") → `cloud`, with "
                "`cloud_provider` lowercased.\n")
            self.assertTrue(any('a bare "1" records a specific value' in p
                                for p in mapping_problems(mutated)), value)

    def test_the_pre_785_entry_is_caught(self):
        mutated = self.mutate_entry1(
            '- **1, "A cloud hyperscaler":** `aws`, `azure` or `gcp`, also as '
            "`cloud_provider`.\n")
        problems = mapping_problems(mutated)
        self.assertTrue(any("no naming condition" in p for p in problems), problems)
        self.assertTrue(any('nothing about a bare "1"' in p for p in problems), problems)

    def test_a_specific_value_without_the_naming_condition_is_caught(self):
        mutated = self.text.replace(
            "`kubernetes` or `docker_swarm` when the Bootcamper names it.",
            "`kubernetes` or `docker_swarm` by default.")
        self.assertNotEqual(self.text, mutated)
        self.assertTrue(any("option 2" in p and "no naming condition" in p
                            for p in mapping_problems(mutated)))

    def test_a_bare_1_writing_cloud_provider_is_caught(self):
        mutated = self.text.replace("→ `cloud`, and no\n  `cloud_provider`.",
                                    "→ `cloud`, and `cloud_provider: aws`.")
        self.assertNotEqual(self.text, mutated)
        self.assertIn('a bare "1" must record no `cloud_provider`', mapping_problems(mutated))

    def test_a_bare_3_recording_on_premises_is_caught(self):
        mutated = self.text.replace('(a bare "3", or "3, my laptop") → `local`',
                                    '(a bare "3", or "3, my laptop") → `on_premises`')
        self.assertNotEqual(self.text, mutated)
        self.assertTrue(any('a bare "3"' in p for p in mapping_problems(mutated)))

    def test_a_follow_up_question_is_caught(self):
        mutated = self.text.replace(
            "- **4, \"Not sure yet\":** `undecided`.",
            "- **4, \"Not sure yet\":** `undecided`.\n\n👉 **Which cloud provider?**")
        self.assertNotEqual(self.text, mutated)
        self.assertTrue(question_problems(mutated))


class TestStep11TemplateRendersAGenericValue(unittest.TestCase):
    def setUp(self):
        self.text = MODULE1.read_text(encoding="utf-8")

    def test_generic_value_case(self):
        self.assertEqual([], template_problems(self.text))

    def test_older_values_render_as_before(self):
        t = template_deployment(self.text)
        for line in KEPT_MODULE1:
            self.assertIn(line, t)

    def test_negative_controls(self):
        no_case = re.sub(r" If a generic value \(.*?\]", "]", self.text, flags=re.S)
        self.assertIn("no generic-value case", template_problems(no_case)[0])
        guessed = self.text.replace('Platform "Not stated" (or', 'Platform "AWS" (or')
        self.assertNotEqual(self.text, guessed)
        self.assertTrue(any("Not stated" in p for p in template_problems(guessed)))


class TestGraduationRendersAGenericValue(unittest.TestCase):
    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")

    def test_rendering_stated_once_and_linked_by_each_reader(self):
        self.assertEqual([], graduation_problems(self.text))

    def test_older_values_render_as_before(self):
        whole = flat(self.text)
        for line in KEPT_GRADUATION:
            self.assertIn(line, whole)

    def test_negative_controls(self):
        cases = {
            "a guessed provider": (
                '`cloud` → "cloud (provider not stated)"', '`cloud` → "AWS"',
                "does not say the platform was not stated"),
            "a reader's link removed": (
                "Record the value as stored; for a generic value, add its\n"
                "[pre-check 1a rendering](#generic-deployment-target)",
                "Record the value as stored; for a generic value, add its rendering",
                "Step 5's report does not link"),
            "the rendering repeated in a reader": (
                "`local` the on-premises list.",
                '`local` the on-premises list, rendered "container platform (not stated)".',
                "is stated 2 times"),
            "the mapping restated": (
                "Every other value renders as that step already says.",
                'Every other value renders as that step already says. A bare "1" is `cloud`.',
                "restates Step 10a"),
            "the container list naming an orchestrator": (
                "naming no orchestrator-specific tooling",
                "naming Helm charts",
                "category checkboxes"),
        }
        for name, (old, new, want) in cases.items():
            with self.subTest(name):
                self.assertEqual(1, self.text.count(old), old)
                problems = graduation_problems(self.text.replace(old, new))
                self.assertTrue(any(want in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
