"""SDK setup Step 7 and Step 8a state what they do on a datastore that already exists (#684).

Enforces **INV-393**, registered by the maintainer 2026-10-20: a step whose precondition can
already be satisfied states the branch for that case rather than leaving it to the guide. ⚠️ It
reads the shipped step prose; it **cannot** establish that a live run takes the stated branch.

Both steps were written for a datastore that does not yet exist, and the module documents two
paths that re-enter them on one that does:

* a **resume**, because Step 7's instruction 2 holds the step-7 checkpoint back until the chosen
  branch's setup is finished, so a session interrupted between creating the datastore and the
  checkpoint runs the whole of Step 7 again; and
* the **`sdk_repair` detour**, whose row runs Step 1 through Step 9 and is offered from Data
  Quality, Mapping, and Transformation Phase 3 — after that module has already set the datastore
  up and registered its sources.

Neither step said anything about that state, while both of the MCP routes they use do. The
server's *Senzing Anti-Patterns: Database Initialization and Container Setup* article guards its
DDL behind a `sys_cfg` existence check and its `create_config_from_template()` behind
`get_default_config_id()`, and names "application code calls `create_config_from_template()` on
every startup, which fails when a config already exists" as a symptom. The seeding snippet Step 8a
sends the guide to fetch, `python/configuration/init_default_config.py`, carries the check as an
**interactive prompt** — "A configuration exists in the repository, replace it with a template
configuration? (y/n)", `sys.exit(1)` on anything else — which in an agent-driven run is a hang or
an exit 1 that reads as a failed step, while answering `y` replaces the registered default config
and drops every `DATA_SOURCE` code in it. (Re-verified on MCP server 1.39.1, 2026-10-17.)

So each branch is stated **once** (INV-300) and pointed at from everywhere else:

* Step 7's **instruction 3**, at the head of the step where both engines pass, owns the
  already-applied-schema branch; the SQLite branch's rung 2 and the PostgreSQL branch's DDL step
  point at it.
* **Step 8a**'s already-seeded block owns the already-registered-config branch, names the prompt,
  and forbids answering it blind.
* The **`sdk_repair` detour** cites both and restates neither, and states that it needs no
  `register-sources` step of its own — Data Quality, Mapping, and Transformation step 21a
  re-registers the `DATA_SOURCE` codes before the step 22 test load (INV-089), so a re-seed on the
  repair path is already covered — so the omission reads as a decision, not an oversight.

Each check is a function of the file text, and every negative control runs the SAME check over a
mutated copy that restores the pre-#684 shape (INV-265). Prose is matched wrap-aware (INV-346) and
shipped files are read as text, never imported (INV-108).

**Every other seeding site points at Step 8a's block (#804; INV-393's dated note of 2026-10-23,
applied 2026-10-26).** Data processing Phase A step 4a
and Data Quality, Mapping, and Transformation step 21a seeded "on a freshly schema-created
datastore" and "if this phase's sandbox database was created fresh" — a test of the container, not
of the end state (INV-393) — on steps a resume and a `database_switch` or `quality_iteration`
return re-enter. The block now carries the anchor `already-seeded`, and the guard finds the
seeding sites by **scanning** every shipped Markdown file rather than by naming files (INV-246):
each file is split into heading-delimited sections and each section into blocks (blank lines and
list items). A **hit** is an `sdk_guide(topic='configure'…)` call that passes no `data_sources` —
on the server, that call's primary snippet *is* the seeding snippet — or text naming the seeding
snippet or `init_default_config`. HTML comments are skipped: they are maintainer provenance, never
an instruction. A hit inside Module 2 Step 8a is the owner. Every other hit makes its section a
**seeding site**, which must link `#already-seeded` in Module 2, unless the hit's own block is on
``EXEMPT``, keyed by (file, section heading, a quote from that block) — text, never a line
number — with the reason it seeds nothing. An exemption that matches no hit is reported as stale.
Both pointers are also read clause by clause: the anchored block, INV-393 and INV-300, the
decision by the default config id, the `init_default_config` prompt that is never answered blind,
no freshness test in place of the id, and no copy of the block.

⚠️ **What these tests cannot establish:** that a live guide runs the probe, reads the id before
seeding, or skips rather than re-applies. They assert that the skill *states* the branches; only a
dry run against a real datastore can observe the behavior.

Enforces **INV-080**, **INV-089**, **INV-246** and **INV-300** at these sites.

Run:  python3 -m unittest discover -s tests
"""
import posixpath
import re
import unittest
from collections import namedtuple
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import match_lines as _match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
PHASE3 = SKILLS / "module-05-data-quality-mapping" / "phase3-test-load.md"

#: Step 7's instruction 3 and the sites that point at it.
INSTRUCTION_3 = "3. ⛔ **(INV-393) When the datastore already exists"
HANDLING = "**Handling each answer (INV-284).**"
SQLITE_BRANCH = "**For SQLite**"
RUNG_2 = "2. **Apply the Senzing schema**"
RUNG_3 = "3. **Seed the Senzing configuration**"
PG_DDL = "4. Apply the Senzing PostgreSQL schema DDL"
PG_WIRE = "5. Wire the connection into the engine config"
#: Step 8a's already-seeded branch and the paragraph it sits in front of.
SEED_BRANCH = "⛔ **(INV-393) When a default configuration is already registered"
SEED_FETCH = "`sdk_guide(topic='configure')`'s primary `RegisterDataSources` snippet"
#: The detour section and the `sdk_repair` running notes inside it.
DETOUR_ANCHOR = '<a id="receiving-a-setup-detour"></a>'
SDK_REPAIR_NOTES = "For `sdk_repair`:"
DETOUR_FINISH = "**When every step is done,**"
#: Data Quality, Mapping, and Transformation's register-before-load step, which the detour cites
#: as its reason for having no `register-sources` step of its own.
STEP_21A_HEADING = "### 21a. Register the data source code (before the test load)"
STEP_21A_LINK = "../module-05-data-quality-mapping/phase3-test-load.md"
#: The one phrase that says which question the probe asks, on either engine.
SYS_CFG = "sys_cfg"
#: The prompt the fetched seeding snippet raises, as the server returns it.
PROMPT = "A configuration exists in the repository, replace it with a template configuration?"
#: A server version and a date, so a Senzing fact in shipped text carries its provenance.
PROVENANCE = r"MCP server 1\.\d+\.\d+, \d{4}-\d{2}-\d{2}"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def match(text, pattern):
    """Wrap-aware (INV-346): does `pattern` appear anywhere in `text`?"""
    return bool(_match_lines(text, re.compile(pattern)))


def missing(text, patterns, where):
    return [f"{where} does not say {p!r}" for p in patterns if not match(text, p)]


def step7(m2):
    return between(m2, "## Step 7:", "\n## Step 8:")


def step8a(m2):
    return between(m2, "## Step 8a:", "\n## Step 9:")


def instruction_3(m2):
    return between(step7(m2), INSTRUCTION_3, HANDLING)


def seed_branch(m2):
    return between(step8a(m2), SEED_BRANCH, SEED_FETCH)


def repair_notes(m2):
    return between(between(m2, DETOUR_ANCHOR, "\n## Step 1:"), SDK_REPAIR_NOTES, DETOUR_FINISH)


def anchor(heading):
    """The GitHub anchor a Markdown heading gets, so a link cannot drift from its target."""
    slug = heading.lstrip("#").strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"[\s]+", "-", slug)


# --- the seeding sites, found by scanning (#804) ---------------------------------------------

#: The anchor directly before Step 8a's already-seeded block, and the name every pointer links.
ALREADY_SEEDED = "already-seeded"
ALREADY_SEEDED_TAG = '<a id="already-seeded"></a>'
M02_REL = "plugins/senzing-bootcamp/skills/module-02-sdk-setup/SKILL.md"
PHASE_A_REL = "plugins/senzing-bootcamp/skills/module-06-data-processing/phaseA-build-loading.md"
PHASE3_REL = "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase3-test-load.md"
PHASE_A_4A = "4a. Register the data source codes (before loading)"
STEP_21A = STEP_21A_HEADING.lstrip("#").strip()
#: The two pointers #804 adds; the scan must find both, so an empty scan cannot pass (INV-265).
POINTER_SITES = ((PHASE_A_REL, PHASE_A_4A), (PHASE3_REL, STEP_21A))
#: A fetch of the seeding snippet: a configure call that passes no `data_sources`, whose primary
#: snippet on the server IS `init_default_config` (Step 8a's table) ...
CONFIGURE_CALL = re.compile(r"sdk_guide\(\s*topic=['\"]configure['\"][^)]*\)")
#: ... or text that names the seeding snippet.
SNIPPET_NAME = re.compile(r"(?i)init_default_config|seeding snippet")
#: A link to the anchor; the path before `#` is resolved against the linking file.
ANCHOR_LINK = re.compile(r"\]\(([^)\s#]*)#%s\)" % re.escape(ALREADY_SEEDED))
#: A seeding decision taken by whether the datastore is new, the pre-#804 shape of both pointers.
FRESHNESS = re.compile(r"(?i)\b(?:if|on|when|where)\b[^.;:]{0,80}\bfresh(?:ly)?\b[^.;:]{0,60}"
                       r"\b(?:seed|call it without)")

#: Every hit outside Step 8a that seeds nothing, keyed (file, section heading, a quote from the
#: hit's own block) — text, never a line number — with the reason. Module 2's canonical
#: statements and existing pointers sit here as they stand; a hit in a section that links the
#: anchor needs no entry.
EXEMPT = {
    (M02_REL, "Receiving a `setup_detour` (from a later module)",
     "Step 8a's already-seeded branch is the one statement"):
        "an existing pointer: the `sdk_repair` note names Step 8a's already-seeded branch and "
        "restates none of it (pinned by `detour_problems`)",
    (M02_REL, "Step 3: Install Senzing SDK",
     "`sdk_guide(topic='configure', platform='linux_apt', language='python')` returns "
     "`environment.env_vars`"):
        "provenance for an environment-variable fact; no snippet is fetched to run",
    (M02_REL, "Step 5: License (record capacity)",
     "took the silence of `sdk_guide(topic='configure')`"):
        "history of a retracted absence claim; names the call, fetches nothing",
    (M02_REL, "Step 7: Configure Database",
     "Generate the engine config with `sdk_guide(topic='configure', ...)`"):
        "an engine-configuration fetch, before Step 8a seeds",
    (M02_REL, "Step 7: Configure Database",
     "Generate the full engine config via `sdk_guide(topic='configure', ...)`"):
        "an engine-configuration fetch, before Step 8a seeds",
    (M02_REL, "Step 7: Configure Database",
     "wire the `postgresql://` connection via `sdk_guide(topic='configure', ...)`"):
        "an engine-configuration fetch, before Step 8a seeds",
    (M02_REL, "Step 8: Create Engine Configuration",
     "the connection-string form all come from `sdk_guide(topic='configure',"):
        "an engine-configuration fetch (path values), before Step 8a seeds",
    (M02_REL, "Step 8: Create Engine Configuration",
     "Take `config_path`, `resource_path` and `support_path` from the"):
        "reads the engine-configuration response above, before Step 8a seeds",
    (M02_REL, "Agent Behavior",
     "the connection-string form from `sdk_guide(topic='configure',"):
        "an engine-configuration rule, restating Step 8's values",
    (M02_REL, "Troubleshooting", "seed one per Step 8a"):
        "an existing pointer: SENZ7221 sends the guide to Step 8a, which opens on the "
        "already-seeded block",
    ("plugins/senzing-bootcamp/skills/module-03-system-verification/phase1-verification.md",
     "Step 5a: Register the Synthetic Data Source Code",
     "**Generate the registration code from the MCP server**"):
        "a registration fetch on the datastore SDK setup seeded; it asks for the registration "
        "code and seeds nothing",
    ("plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/phase1-visualization.md",
     "1.2 Register the Truth Set data source codes and load",
     "Generate the registration code from the MCP server"):
        "a registration fetch on the datastore SDK setup seeded; it asks for the registration "
        "code and seeds nothing",
    ("plugins/senzing-bootcamp/skills/module-04-data-collection/SKILL.md",
     "8a. Senzing License Key gate (single, volume-gated — INV-093)",
     "Confirm the SDK facts via `sdk_guide(topic='configure',"):
        "a license-fact lookup (`recordLimit`); no snippet is fetched to run",
    ("plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase1-quality-assessment.md",
     "5a. Senzing-readiness check and fast-path offer (CORD sources only)",
     "taking the registration code from `sdk_guide(topic='configure')`"):
        "a registration fetch before the preview; it asks for the registration code and seeds "
        "nothing",
}

Block = namedtuple("Block", "file section heading h2 flat")


def squash(text):
    return " ".join(re.sub(r"(?m)^[ \t]*(?:>[ \t]?)*", "", text).split())


def shipped_corpus():
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in corpus_files("plugins", suffixes={".md"})}


def blocks_of(relpath, text):
    """Every paragraph-level block of a Markdown file, with its section heading and its `##`.

    HTML comments are dropped first (line count kept). A heading starts a section; a blank line
    (a bare ``>`` counts as blank) ends a block, and so does a list item, which starts the next.
    Lines inside a fenced code block are never headings and never end a block.
    """
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out, section, heading, h2, current, fenced = [], 0, "", "", [], False

    def flush():
        if current:
            out.append(Block(relpath, section, heading, h2, squash("\n".join(current))))

    for line in text.split("\n"):
        bare = re.sub(r"^[ \t]*(?:>[ \t]?)*", "", line)
        if bare.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if not fenced and re.match(r"#{1,6}\s", line):
            flush()
            current, heading, section = [], line.lstrip("#").strip(), section + 1
            if line.startswith("## "):
                h2 = heading
            continue
        if not fenced and not bare.strip():
            flush()
            current = []
            continue
        if not fenced and re.match(r"\s*(?:[-*+]|\d+\.)\s", bare):
            flush()
            current = []
        current.append(line)
    flush()
    return out


def hits(block):
    """The seeding-snippet fetches and names in one block."""
    return ([c for c in CONFIGURE_CALL.findall(block.flat) if "data_sources" not in c]
            + SNIPPET_NAME.findall(block.flat))


def is_owner(block):
    """Module 2 Step 8a, sub-steps included, which states the branch."""
    return block.file == M02_REL and block.h2.startswith("Step 8a:")


def links_already_seeded(block):
    """True when the block links the anchor in Module 2, resolved from its own file."""
    for target in ANCHOR_LINK.findall(block.flat):
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(block.file), target)) \
            if target else block.file
        if resolved == M02_REL:
            return True
    return False


def exemption_for(block, exempt):
    for (file, heading, quote) in exempt:
        if block.file == file and block.heading == heading and quote in block.flat:
            return (file, heading, quote)
    return None


def scan(corpus, exempt=None):
    """Read every hit; return (problems, seeding sites, hit count)."""
    exempt = EXEMPT if exempt is None else exempt
    problems, sites, count, used = [], set(), 0, set()
    for relpath in sorted(corpus):
        blocks = blocks_of(relpath, corpus[relpath])
        linked = {b.section for b in blocks if links_already_seeded(b)}
        for block in blocks:
            found = hits(block)
            if not found or is_owner(block):
                continue
            count += len(found)
            key = exemption_for(block, exempt)
            if key is not None:
                used.add(key)
                continue
            sites.add((relpath, block.heading))
            if block.section not in linked:
                problems.append("a seeding site does not link Module 2 Step 8a's already-seeded "
                                "block (#%s): %s › %s › %r"
                                % (ALREADY_SEEDED, relpath, block.heading, found[0]))
    for key in sorted(set(exempt) - used):
        problems.append("an exemption matches no hit (stale): %s › %s › %r" % key)
    return problems, sites, count


def anchor_problems(m2):
    """The anchor sits once, directly before Step 8a's already-seeded block."""
    if m2.count(ALREADY_SEEDED_TAG) != 1:
        return ["Module 2 carries %d `already-seeded` anchors; it needs one"
                % m2.count(ALREADY_SEEDED_TAG)]
    after = m2[m2.index(ALREADY_SEEDED_TAG) + len(ALREADY_SEEDED_TAG):].lstrip()
    if not after.startswith(SEED_BRANCH):
        return ["the `already-seeded` anchor is not directly before Step 8a's already-seeded "
                "block"]
    if not step8a(m2).count(ALREADY_SEEDED_TAG):
        return ["the `already-seeded` anchor is outside Step 8a"]
    return []


def seeding_pointer_problems(corpus, relpath, heading):
    """One #804 pointer, clause by clause: it points at the block and restates none of it."""
    where = "%s › %s" % (relpath, heading)
    pointer = [b for b in blocks_of(relpath, corpus[relpath])
               if b.heading == heading and links_already_seeded(b)]
    if len(pointer) != 1:
        return ["%s has %d blocks linking #%s; it needs one"
                % (where, len(pointer), ALREADY_SEEDED)]
    text = pointer[0].flat
    problems = missing(text, (
        r"INV-393",
        r"INV-300",
        r"(?i)read the default config id",
        r"(?i)keep a present, non-zero id",
        r"(?i)seed only on `0` or no id",
        r"`init_default_config` prompt",
        r"(?i)never answered blind",
    ), where)
    if FRESHNESS.search(text):
        problems.append("%s decides seeding by whether the datastore is new, not by the default "
                        "config id" % where)
    for copy in (re.escape(PROMPT[:40]), r"(?i)exiting `1`", r"(?i)\bhangs\b"):
        if match(text, copy):
            problems.append("%s restates Step 8a's block (%r) instead of pointing at it (INV-300)"
                            % (where, copy))
    return problems


def step_21a_keeps_problems(phase3):
    """Step 21a keeps its error evidence and its sandbox sentence (#804 scope)."""
    return missing(squash(between(phase3, STEP_21A_HEADING, "### 22.")), (
        r"explain_error_code",
        r"(?i)No default config has EVER been registered on this datastore",
        r"(?i)where `mapping_workflow` step 6 creates and initializes the sandbox database itself",
        r"(?i)confirm rather than assume",
    ), "step 21a")


# --- checks: each returns a list of problems -------------------------------------------------


def instruction_3_problems(m2):
    """Step 7 states the already-applied branch once, at the head, for both engines."""
    step = step7(m2)
    if step.count(INSTRUCTION_3) != 1:
        return [f"Step 7 carries {step.count(INSTRUCTION_3)} copies of instruction 3; it needs one"]
    if step.index(INSTRUCTION_3) > step.index(SQLITE_BRANCH):
        return ["instruction 3 sits after the branches, where a guide on one path never reads it"]
    text = instruction_3(m2)
    problems = missing(text, (
        r"(?i)when the datastore already exists",
        r"(?i)skip it and say so",
        r"(?i)for \*\*both\*\* engines",
        r"(?i)resume",
        r"(?i)`sdk_repair` detour",
        r"(?i)whether the Senzing schema is applied",
        SYS_CFG,
        r"(?i)\*\*Not applied:\*\* apply it",
        r"(?i)could not be run",
        PROVENANCE,
        r"INV-300",
    ), "Step 7's instruction 3")
    if not match(text, r"(?i)not whether a file or a database exists"):
        problems.append("instruction 3 does not say the question is the schema, not the file: a "
                        "datastore can exist with no schema in it, and the two answers differ")
    return problems


def pointer_problems(m2):
    """Both engines' schema steps point at instruction 3 and carry no second copy of it."""
    step = step7(m2)
    problems = []
    for label, text in (("the SQLite branch's rung 2", between(step, RUNG_2, RUNG_3)),
                        ("the PostgreSQL branch's DDL step", between(step, PG_DDL, PG_WIRE))):
        problems += missing(text, (r"instruction 3 at the head of Step 7", r"INV-300"), label)
        for copy in (SYS_CFG, r"(?i)skip it and say so"):
            if match(text, copy):
                problems.append(f"{label} carries a second copy of the branch ({copy!r}); it must "
                                "point at instruction 3, not restate it (INV-300)")
    return problems


def seed_branch_problems(m2):
    """Step 8a states the already-seeded branch, and names the prompt in the fetched snippet."""
    step = step8a(m2)
    if step.count(SEED_BRANCH) != 1:
        return [f"Step 8a carries {step.count(SEED_BRANCH)} copies of the already-seeded branch; "
                "it needs one"]
    if step.index(SEED_BRANCH) > step.index(SEED_FETCH):
        return ["the already-seeded branch sits after the seeding instructions, so a guide reads "
                "it only once it has already re-seeded"]
    problems = missing(seed_branch(m2), (
        r"(?i)do not re-seed",
        r"get_default_config_id\(\)",
        r"(?i)before anything else",
        r"(?i)already seeded",
        r"(?i)without seeding",
    ), "Step 8a's already-seeded branch")
    prompt = between(step, SEED_BRANCH, SEED_FETCH)
    problems += missing(prompt, (
        r"init_default_config",
        re.escape(PROMPT),
        r"(?i)must\s+not answer it blind",
        r"(?i)exiting `1`",
        r"(?i)hangs",
        PROVENANCE,
        r"INV-300",
    ), "Step 8a's note on the fetched snippet")
    return problems


def detour_problems(m2):
    """The `sdk_repair` detour cites both branches, restates neither, and owns its omission."""
    notes = repair_notes(m2)
    problems = missing(notes, (
        r"Step 7's instruction 3",
        r"(?i)Step 8a's already-seeded branch",
        r"(?i)does not restate it \(INV-300\)",
        r"(?i)No `register-sources` step",
        r"(?i)a decision rather than an omission",
        r"\[step 21a\]\(" + re.escape(STEP_21A_LINK),
        r"(?i)before the step 22 test load",
        r"INV-089",
    ), "the `sdk_repair` running notes")
    for copy in (SYS_CFG, re.escape(PROMPT)):
        if match(notes, copy):
            problems.append(f"the `sdk_repair` notes restate the branch ({copy!r}) instead of "
                            "pointing at it (INV-300)")
    row = [line for line in m2.splitlines() if line.startswith("| `sdk_repair` |")]
    if len(row) != 1:
        problems.append("the detour table has no single `sdk_repair` row")
    elif "register-sources" in row[0]:
        problems.append("the `sdk_repair` row carries a `register-sources` step, which #684 "
                        "decided against; the notes say why it has none")
    return problems


def citation_problems(m2, phase3):
    """The step the detour's reason rests on exists, under the heading the link resolves to."""
    problems = []
    if STEP_21A_HEADING not in phase3:
        return [f"{STEP_21A_HEADING!r} is not in phase3-test-load.md; the detour's reason for "
                "having no `register-sources` step rests on it"]
    expected = f"{STEP_21A_LINK}#{anchor(STEP_21A_HEADING)}"
    if expected not in m2:
        problems.append(f"the detour does not link {expected!r}; the anchor has drifted from the "
                        "heading it points at")
    step = between(phase3, STEP_21A_HEADING, "### 22.")
    problems += missing(step, (r"(?i)registered in the Senzing\s+engine config", r"INV-089"),
                        "step 21a")
    if not match(phase3, r"### 22\. Test data loading"):
        problems.append("phase3-test-load.md has no step 22, so 'before the test load' is stale")
    return problems


class TheExistingDatastoreBranchIsStated(unittest.TestCase):

    def setUp(self):
        self.m2 = read(MODULE_02)
        self.phase3 = read(PHASE3)

    def test_step_7_states_it_once_for_both_engines(self):
        self.assertEqual(instruction_3_problems(self.m2), [])

    def test_both_schema_steps_point_at_it(self):
        self.assertEqual(pointer_problems(self.m2), [])

    def test_step_8a_states_the_already_seeded_branch_and_names_the_prompt(self):
        self.assertEqual(seed_branch_problems(self.m2), [])

    def test_the_sdk_repair_detour_cites_both_and_owns_its_omission(self):
        self.assertEqual(detour_problems(self.m2), [])

    def test_the_reason_the_detour_rests_on_still_exists(self):
        self.assertEqual(citation_problems(self.m2, self.phase3), [])


class NegativeControls(unittest.TestCase):
    """Each mutation restores the pre-#684 shape, which every check must report."""

    def setUp(self):
        self.m2 = read(MODULE_02)
        self.phase3 = read(PHASE3)

    def drop(self, start, end):
        """The module with the passage from `start` up to `end` removed."""
        cut = between(self.m2, start, end)
        mutated = self.m2.replace(cut, "", 1)
        self.assertNotEqual(mutated, self.m2, "control did not apply")
        return mutated

    def test_step_7_with_no_instruction_3_fails(self):
        self.assertTrue(instruction_3_problems(self.drop(INSTRUCTION_3, HANDLING)))

    def test_instruction_3_placed_after_the_branches_fails(self):
        passage = between(self.m2, INSTRUCTION_3, HANDLING)
        moved = self.m2.replace(passage, "", 1).replace(
            "SQLite remains the default recommendation", passage + "SQLite remains the default "
            "recommendation", 1)
        self.assertNotEqual(moved, self.m2, "control did not apply")
        self.assertTrue(any("sits after the branches" in p
                            for p in instruction_3_problems(moved)))

    def test_a_probe_on_the_file_rather_than_the_schema_fails(self):
        broken = self.m2.replace("not whether a file or a database exists",
                                 "which is whether the file is there", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("not the file" in p for p in instruction_3_problems(broken)))

    def test_a_schema_step_that_does_not_point_at_it_fails(self):
        broken = self.m2.replace(
            """2. **Apply the Senzing schema** to `database/G2C.db` — **unless it is already applied**, which
   instruction 3 at the head of Step 7 decides, for both engines (INV-300); this rung is its
   "not applied" path.""",
            "2. **Apply the Senzing schema** to `database/G2C.db`.", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("rung 2" in p for p in pointer_problems(broken)))

    def test_a_schema_step_that_restates_the_branch_fails(self):
        broken = self.m2.replace(
            "3. **Seed the Senzing configuration**",
            "   Check for a `sys_cfg` table first and skip it and say so when it is there.\n"
            "3. **Seed the Senzing configuration**", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("second copy" in p for p in pointer_problems(broken)))

    def test_step_8a_with_no_already_seeded_branch_fails(self):
        self.assertTrue(seed_branch_problems(self.drop(SEED_BRANCH, SEED_FETCH)))

    def test_step_8a_that_does_not_name_the_prompt_fails(self):
        # The quoted prompt wraps in the file, so the mutation takes the part on one line.
        broken = self.m2.replace("A configuration exists in the repository, replace it with a template",
                                 "whether to replace the configuration", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("fetched snippet" in p for p in seed_branch_problems(broken)))

    def test_a_detour_that_restates_a_branch_fails(self):
        broken = self.m2.replace(
            "- **`8a`.** Likewise for the configuration:",
            "- **`8a`.** Read the default config id and skip the seed when a `sys_cfg` row holds "
            "one:", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("restate" in p for p in detour_problems(broken)))

    def test_a_detour_that_does_not_own_its_omission_fails(self):
        self.assertTrue(detour_problems(self.drop(
            "- **No `register-sources` step", "\n**When every step is done,**")))

    def test_a_register_sources_step_added_to_the_row_fails(self):
        row = next(r for r in self.m2.splitlines() if r.startswith("| `sdk_repair` |"))
        broken = self.m2.replace(row, row.replace(
            "`9`: [Step 9]", "`register-sources`: every code registered again. `9`: [Step 9]", 1), 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("decided against" in p for p in detour_problems(broken)))

    def test_a_drifted_anchor_fails(self):
        broken = self.m2.replace("#21a-register-the-data-source-code-before-the-test-load",
                                 "#21a-register-the-data-source-code", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("anchor has drifted" in p
                            for p in citation_problems(broken, self.phase3)))


class EverySeedingSitePointsAtStep8a(unittest.TestCase):
    """#804: the seeding sites are found by scanning, and each one links the anchored block."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = shipped_corpus()

    def test_the_anchor_sits_directly_before_the_block(self):
        self.assertEqual(anchor_problems(self.corpus[M02_REL]), [])

    def test_every_seeding_site_links_it(self):
        problems, _, count = scan(self.corpus)
        self.assertGreater(count, 0, "the scan found no hit, so it checked nothing (INV-265)")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_the_scan_finds_both_pointers(self):
        _, sites, _ = scan(self.corpus)
        for site in POINTER_SITES:
            self.assertIn(site, sites, "the scan does not reach %s › %s" % site)

    def test_both_pointers_name_the_decision_and_the_prompt(self):
        for relpath, heading in POINTER_SITES:
            self.assertEqual(seeding_pointer_problems(self.corpus, relpath, heading), [])

    def test_step_21a_keeps_its_evidence(self):
        self.assertEqual(step_21a_keeps_problems(self.corpus[PHASE3_REL]), [])

    def test_every_exemption_has_a_reason(self):
        for key, reason in EXEMPT.items():
            self.assertTrue(reason.strip(), "exemption %r has no reason" % (key,))

    def test_the_scan_survives_a_reflow(self):
        """INV-346: one word per line inside every block changes no verdict."""
        corpus = {}
        for relpath, text in self.corpus.items():
            lines, fenced = [], False
            for line in text.split("\n"):
                bare = re.sub(r"^[ \t]*(?:>[ \t]?)*", "", line)
                if bare.lstrip().startswith(("```", "~~~")):
                    fenced = not fenced
                if fenced or not bare.strip() or re.match(r"#{1,6}\s|[ \t]*<", line):
                    lines.append(line)
                    continue
                prefix = line[:len(line) - len(bare)]
                words = bare.split()
                if re.match(r"\s*(?:[-*+]|\d+\.)\s", bare) and len(words) > 1:
                    words[:2] = [" ".join(words[:2])]
                lines.extend(prefix + word for word in words)
            corpus[relpath] = "\n".join(lines)
        problems, sites, count = scan(corpus)
        self.assertEqual(problems, [], "\n".join(problems))
        self.assertEqual((sites, count), scan(self.corpus)[1:])


class SeedingSiteNegativeControls(unittest.TestCase):
    """Each mutation restores a pre-#804 shape or adds an unguarded site; each is reported."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = shipped_corpus()

    def mutated(self, relpath, old, new):
        corpus = dict(self.corpus)
        corpus[relpath] = corpus[relpath].replace(old, new, 1)
        self.assertNotEqual(corpus[relpath], self.corpus[relpath], "control did not apply")
        return corpus

    def unlinked(self, relpath):
        """The file with its link to the anchor turned into plain text."""
        return self.mutated(relpath, "](../module-02-sdk-setup/SKILL.md#already-seeded)", "")

    def test_phase_a_pointer_removed_fails(self):
        problems, _, _ = scan(self.unlinked(PHASE_A_REL))
        self.assertTrue(any(PHASE_A_4A in p for p in problems), problems)

    def test_step_21a_pointer_removed_fails(self):
        problems, _, _ = scan(self.unlinked(PHASE3_REL))
        self.assertTrue(any(STEP_21A in p for p in problems), problems)

    def test_a_new_seeding_fetch_without_the_pointer_fails(self):
        corpus = self.mutated(PHASE_A_REL, "## 4a. Register the data source codes (before loading)",
                              "## 3z. Prepare the datastore\n\nSeed the configuration: call "
                              "`sdk_guide(topic='configure', language=<from "
                              "`programming_language`>)` and run its primary snippet.\n\n"
                              "## 4a. Register the data source codes (before loading)")
        problems, _, _ = scan(corpus)
        self.assertTrue(any("3z. Prepare the datastore" in p for p in problems), problems)

    def test_a_new_seeding_fetch_inside_an_exempt_section_fails(self):
        relpath = ("plugins/senzing-bootcamp/skills/module-03-system-verification/"
                   "phase1-verification.md")
        corpus = self.mutated(relpath, "1. **Determine the source codes to register.**",
                              "0. Run the `init_default_config` snippet to seed the "
                              "datastore.\n1. **Determine the source codes to register.**")
        problems, _, _ = scan(corpus)
        self.assertTrue(any("Step 5a" in p and "init_default_config" in p for p in problems),
                        problems)

    def test_the_anchor_removed_fails(self):
        m2 = self.corpus[M02_REL].replace(ALREADY_SEEDED_TAG + "\n\n", "", 1)
        self.assertNotEqual(m2, self.corpus[M02_REL], "control did not apply")
        self.assertTrue(anchor_problems(m2))

    def test_the_anchor_moved_off_the_block_fails(self):
        m2 = self.corpus[M02_REL].replace(ALREADY_SEEDED_TAG + "\n\n", "", 1).replace(
            "⚠️ **\"Schema-created\" is true of BOTH", ALREADY_SEEDED_TAG + "\n\n⚠️ "
            "**\"Schema-created\" is true of BOTH", 1)
        self.assertNotEqual(m2, self.corpus[M02_REL], "control did not apply")
        self.assertTrue(any("not directly before" in p for p in anchor_problems(m2)))

    def test_a_pointer_that_tests_freshness_fails(self):
        corpus = self.mutated(PHASE3_REL, "Before seeding this phase's datastore, test whether a "
                              "default configuration is already\nregistered, not whether the "
                              "datastore is new:",
                              "If this phase's sandbox database was created fresh, seed its "
                              "default configuration first, per")
        problems = seeding_pointer_problems(corpus, PHASE3_REL, STEP_21A)
        self.assertTrue(any("whether the datastore is new" in p for p in problems), problems)

    def test_the_pre_804_phase_a_wording_fails(self):
        corpus = self.mutated(PHASE_A_REL, "Before seeding, test whether a default configuration "
                              "is already registered, not\n   whether the datastore is new:",
                              "On a freshly schema-created datastore, call it WITHOUT "
                              "`data_sources` first, per")
        problems = seeding_pointer_problems(corpus, PHASE_A_REL, PHASE_A_4A)
        self.assertTrue(any("whether the datastore is new" in p for p in problems), problems)

    def test_a_pointer_without_the_decision_fails(self):
        corpus = self.mutated(PHASE_A_REL, " — read the default\n   config id; keep a present, "
                              "non-zero id; seed only on `0` or no id —", " —")
        problems = seeding_pointer_problems(corpus, PHASE_A_REL, PHASE_A_4A)
        self.assertTrue(any("read the default config id" in p for p in problems), problems)

    def test_a_pointer_that_does_not_name_the_prompt_fails(self):
        corpus = self.mutated(PHASE3_REL, "and its paragraph on the\n`init_default_config` "
                              "prompt is why that prompt is never answered blind.", "")
        problems = seeding_pointer_problems(corpus, PHASE3_REL, STEP_21A)
        self.assertTrue(any("never answered blind" in p for p in problems), problems)

    def test_a_pointer_that_restates_the_block_fails(self):
        corpus = self.mutated(PHASE_A_REL, "never answered blind.**",
                              "never answered blind: it asks `%s (y/n)`, exiting `1` on any "
                              "other answer.**" % PROMPT)
        problems = seeding_pointer_problems(corpus, PHASE_A_REL, PHASE_A_4A)
        self.assertTrue(any("restates" in p for p in problems), problems)

    def test_step_21a_without_its_evidence_fails(self):
        phase3 = self.corpus[PHASE3_REL].replace("confirm rather than assume", "assume so", 1)
        self.assertNotEqual(phase3, self.corpus[PHASE3_REL], "control did not apply")
        self.assertTrue(step_21a_keeps_problems(phase3))

    def test_a_stale_exemption_fails(self):
        exempt = dict(EXEMPT)
        exempt[(M02_REL, "Troubleshooting", "a quote that is not there")] = "drifted"
        problems, _, _ = scan(self.corpus, exempt)
        self.assertTrue(any("stale" in p for p in problems), problems)

    def test_an_empty_corpus_finds_no_site(self):
        _, sites, count = scan({}, {})
        self.assertEqual(count, 0)
        self.assertFalse(set(POINTER_SITES) <= sites)


if __name__ == "__main__":
    unittest.main()
