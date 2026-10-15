"""Every guide-run block declares its shell, and the schema DDL comes from the SDK container (#508, #597).

INV-001 makes Windows a supported platform. A **guide-run** block is one the guide runs itself with
its Bash tool, which on Windows is Git Bash. A **hand-run** block is one the Bootcamper types into
their own terminal, the case #391 gave PowerShell 5.1 forms (INV-167).

#508 found six guide-run blocks on SDK setup's container route that said nothing about which shell
runs them, and pinned those six in a fixed tuple with an exact count. #597 found the same gap at
every other guide-run block in the plugin, and found that the count blocked closing it: adding the
pointer anywhere else turned the suite red (INV-246). So the guard now derives its sites from the
fences.

The fix has three parts, and these tests pin each:

1. **One statement.** `ground-rules.md` → "Windows and PowerShell" holds the policy once, under the
   anchor `guide-run-blocks` (INV-300): guide-run blocks run in the guide's POSIX shell (Git Bash
   on Windows) and need no PowerShell form; hand-run blocks need a PowerShell 5.1 form (INV-167).
   Since #597 it also says how the guide runs a PowerShell-only guide-run block from that shell:
   one `powershell.exe -NoProfile -Command …` call, and blocks that share a variable in one call.
2. **One pointer line after every guide-run block.** Every ```` ```bash ````, ```` ```sh ```` and
   PowerShell fence under `plugins/` is guide-run, and the paragraph after it must be the pointer,
   unless `HAND_RUN` below names it as hand-run with a one-line reason. The pointer links the
   anchor and carries the INV-163 "unverified on Windows" disclosure in the #391 wording
   ("…unverified on Windows: no test runs it there."). A `HAND_RUN` entry is keyed on the file, the
   nearest heading above the fence and the fence's first non-comment line, never on a line number
   (INV-246). An entry that matches no fence fails, so the list cannot go stale, and a listed fence
   that carries the pointer fails, so a block is never both. No site or pointer count is asserted.
   - PowerShell fences are read too, because SDK setup's Scoop check and Step 8's `SUPPORTPATH`
     check are PowerShell-only guide-run blocks (#597). Module 4 Step 3 keeps only its POSIX form.
   - A fence nested in a longer ```` ````markdown ```` fence is the example's text, not a block
     anyone runs: the fence reader closes a fence only on a run at least as long as its opener,
     as #596's reader in `test_windows_powershell_guidance.py` does.
   - The pointer's words are the same at every site. Its link is relative to its file, so a skill
     links `../bootcamp-onboarding/ground-rules.md` and a command links
     `../skills/bootcamp-onboarding/ground-rules.md`. A sweep holds every link to the anchor,
     anywhere in the plugin, to that wording.
3. **The schema DDL.** On the container route the host has no `/opt/senzing`, so Option 1 step 4
   copies the DDL out of the SDK container into the project's `database/` with the SDK container's
   recorded runtime (`<runtime> cp`, INV-195, INV-200) and applies the project copy. The path is a
   placeholder taken from MCP at runtime (INV-080). The native route still applies the host file.
   The container-route block is run with `sh` against stub runtimes in a temporary project, so the
   test sees the DDL reach `psql`'s stdin from the project copy. Option 2 (a local PostgreSQL)
   applies the DDL "as above" with `psql -f`, so its sentence also says that on the container
   route the DDL comes from the SDK container, the way Option 1's container-route command takes it,
   never from a host path.

Each check is a function returning its problems, and a negative control mutates the real text and
sees the check report it.

It does **not** establish that any of these blocks runs under Git Bash on Windows (this repo's CI
runs on Linux, which is what the disclosure says), that `powershell.exe -NoProfile -Command`
receives a block intact from Git Bash, or that a real `docker cp` / `podman cp` copies out of a
real container: no Windows host and no container runs in this suite. Nor can it tell a guide-run
block from a hand-run one by reading it: that is the judgment each `HAND_RUN` reason records.

Prose is read wrap-aware (INV-346). Stdlib only (INV-108).

Enforces **INV-001**, **INV-163**, **INV-167**, **INV-195**, **INV-200** and **INV-300** at these
sites.

INV-167's 2026-10-12 note (#508, applied 2026-10-13) names this module as its enforcer. It reads
the skill text and runs the schema block against stub runtimes: it does not establish that a live
guide runs a guide-run block in its POSIX shell on Windows, which no test here can observe.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from collections import Counter, namedtuple
from pathlib import Path

from _wrapped_text import match_lines as _match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
PHASE1 = SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md"
CONTRACT = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"

ANCHOR_ID = "guide-run-blocks"
ANCHOR = f'<a id="{ANCHOR_ID}"></a>'
LINK = f"../bootcamp-onboarding/ground-rules.md#{ANCHOR_ID}"
#: The one pointer line, in the same wording at every site.
POINTER = ("Guide-run in the guide's POSIX shell (Git Bash on Windows); unverified on Windows: no "
           f"test runs it there ([guide-run blocks]({LINK})).")
#: The #391 disclosure's wording (`graduation/database-backup.md`), which the pointer reuses.
DISCLOSURE = "unverified on Windows: no test runs it there"

#: A hand-run fence: the file (relative to the plugin), the nearest heading above the fence, the
#: fence's first non-comment line, and why the Bootcamper runs it rather than the guide. It is
#: never keyed on a line number (INV-246).
HandRun = namedtuple("HandRun", "file heading first reason")

ENV_SCRIPT = "### Create the project-local environment script"

#: The hand-run fences under `plugins/` (#597). Every other bash, sh or PowerShell fence there is
#: guide-run and is followed by the pointer. A hand-run block still owes its PowerShell 5.1 form on
#: Windows (INV-167); this list does not relax that.
HAND_RUN = (
    HandRun("skills/module-02-sdk-setup/SKILL.md", ENV_SCRIPT, 'if [ -n "${ZSH_VERSION:-}" ]; then',
            "the body of src/scripts/senzing-env.sh, which the Bootcamper sources into their own "
            "bash or zsh; Windows gets senzing-env.ps1 instead (INV-166, INV-175)"),
    HandRun("skills/module-02-sdk-setup/SKILL.md", ENV_SCRIPT,
            "if ($MyInvocation.InvocationName -ne '.') {",
            "the body of src/scripts/senzing-env.ps1, which the Bootcamper dot-sources into their own "
            "PowerShell window: the env script's Windows form (INV-166, INV-167)"),
)

#: The fence languages a block is run in. PowerShell is read because some guide-run blocks exist
#: only in PowerShell (#597).
RUN_LANGS = {"bash", "sh", "powershell", "ps1", "pwsh"}
#: A fence line: its run of backticks or tildes, then the info string.
FENCE_MARK = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
#: An ATX heading line, outside any fence.
HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]")

#: A fenced block a guard reads: where it is, how it is keyed, and the lines after it.
Fence = namedtuple("Fence", "path lang heading first start close")

#: The PowerShell-only guide-run blocks #597 names, each found by one line of its own block.
POWERSHELL_GUIDE_RUN = (
    ("Scoop update check", MODULE_2, "scoop info senzingsdk/senzingsdk"),
    ("SUPPORTPATH: SENZING_DIR is set", MODULE_2, "if (-not $env:SENZING_DIR)"),
    ("SUPPORTPATH: expand the returned path", MODULE_2,
     "$supportPath = [System.IO.Path]::GetFullPath("),
    ("SUPPORTPATH: test the directory and its content", MODULE_2,
     "Test-Path -Path $supportPath -PathType Container"),
)
MODULE_4_STEP_3 = "### 3. Verify data was received"
MODULE_4_STEP_4 = "### 4. Document data source locations"

STEP_4 = "4. Apply the Senzing PostgreSQL schema DDL"
OPTION_2 = "**Option 2 — Install PostgreSQL locally:**"
OPTION_3 = "**Option 3 — Use an existing PostgreSQL server:**"
STEP_5 = "5. Wire the connection into the engine config"
CONTAINER_ROUTE = "**On SDK setup's container route**"
NATIVE_ROUTE = "**On a native route**"
FENCE = re.compile(r"^[ \t]*```")
HOST_OPT_REDIRECT = re.compile(r"<\s*\"?/opt/senzing")


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a pattern string."""
    return _match_lines(text, re.compile(pattern))


def windows_section(text):
    return between(text, "## Windows and PowerShell", "\n## ")


def statement(text):
    """From the anchor to the next heading: the one canonical statement."""
    section = windows_section(text)
    begin = section.index(ANCHOR)
    return section[begin:]


def fenced_block_after(text, marker):
    """``(block_lines, rest)``: the fenced block holding the line ``marker``, and the text after it."""
    lines = text.splitlines()
    at = next((i for i, line in enumerate(lines) if marker in line), None)
    if at is None:
        raise LookupError(marker)
    start = max(i for i in range(at + 1) if FENCE.match(lines[i]))
    end = next(i for i in range(at + 1, len(lines)) if FENCE.match(lines[i]))
    return lines[start + 1:end], "\n".join(lines[end + 1:])


def paragraph_after(rest):
    """The first paragraph after a block, whitespace collapsed, so a wrapped line still reads."""
    para = rest.lstrip("\n").split("\n\n", 1)[0]
    return flat(para)


# --- checks: each returns a list of problems ------------------------------------------------


def ground_rules_problems(text):
    problems = []
    if "## Windows and PowerShell" not in text:
        return ["no 'Windows and PowerShell' section"]
    section = windows_section(text)
    if section.count(ANCHOR) != 1 or text.count(ANCHOR) != 1:
        return [f"{ANCHOR} must appear once, inside 'Windows and PowerShell'"]
    body = statement(text)
    for pattern in (r"This is the canonical statement of which command blocks need a\s+PowerShell form",
                    r"\(INV-300\)",
                    r"A guide-run block\*\* is one the guide runs itself with its Bash tool",
                    r"guide's\s+POSIX shell, which on Windows is Git Bash, so it needs no PowerShell form",
                    r"A hand-run block\*\* is one the Bootcamper types",
                    r"needs a\s+PowerShell 5\.1 form that meets the rules above \(INV-167\)",
                    r"\(INV-163\)",
                    r"A PowerShell-only guide-run block\*\* is a guide-run block written only in PowerShell",
                    r"runs it from its POSIX shell as one call, `powershell\.exe -NoProfile -Command …`",
                    r"blocks that share a variable\s+run in one call",
                    r"followed by the same line as any other guide-run block",
                    r"There is\s+no PowerShell fallback"):
        if not match_lines(body, pattern):
            problems.append(f"statement lacks {pattern!r}")
    if flat(POINTER.split(" ([")[0]) not in flat(body):
        problems.append("statement does not quote the pointer line's wording")
    return problems


def site_problems(text, marker):
    try:
        _, rest = fenced_block_after(text, marker)
    except (LookupError, ValueError, StopIteration):
        return [f"site not found by {marker!r}"]
    following = paragraph_after(rest)
    if following != POINTER:
        return [f"line after the block is {following[:120]!r}, not the pointer"]
    return []


def pointer_for(path):
    """The pointer as ``path`` writes it: the one wording, its link relative to that file."""
    path = Path(path).resolve()
    if SKILLS.resolve() in path.parents:
        return POINTER
    target = Path(os.path.relpath(GROUND_RULES.resolve(), path.parent)).as_posix()
    return POINTER.replace(LINK, f"{target}#{ANCHOR_ID}")


def plugin_files():
    return sorted(PLUGIN.rglob("*.md"))


def fences(path, text=None):
    """Each bash, sh or PowerShell fence in ``path`` (or in ``text``, read as ``path``), in order.

    A fence closes only on a run of its own character at least as long as its opener, with no
    info string, so a ```` ```bash ```` inside a ```` ````markdown ```` example is that example's
    text. ``heading`` is the nearest heading line above the fence, outside any fence; ``first``
    is the fence's first line that is neither blank nor a ``#`` comment; ``start`` and ``close``
    are the indexes of its opening and closing fence lines in ``text.split("\\n")``.
    """
    lines = (read(path) if text is None else text).split("\n")
    out, heading, i = [], None, 0
    while i < len(lines):
        mark = FENCE_MARK.match(lines[i])
        if not mark:
            if HEADING.match(lines[i]):
                heading = lines[i].strip()
            i += 1
            continue
        opener = mark.group(1)
        lang = (mark.group(2).split() or [""])[0].lower()
        j = i + 1
        while j < len(lines):
            end = FENCE_MARK.match(lines[j])
            if (end and end.group(1)[0] == opener[0] and len(end.group(1)) >= len(opener)
                    and not end.group(2).strip()):
                break
            j += 1
        if lang in RUN_LANGS:
            body = [line.strip() for line in lines[i + 1:j]]
            first = next((line for line in body if line and not line.startswith("#")), "")
            out.append(Fence(Path(path), lang, heading, first, i, j))
        i = j + 1
    return out


def fence_key(fence):
    return (fence.path.resolve().relative_to(PLUGIN.resolve()).as_posix(), fence.heading, fence.first)


def after(text, fence):
    """The text after ``fence``'s closing line."""
    return "\n".join(text.split("\n")[fence.close + 1:])


def where(fence):
    file, heading, first = fence_key(fence)
    return f"{file} under {heading!r}, the block starting {first[:60]!r}"


def guide_run_problems(path, text=None, hand_run=HAND_RUN):
    """Each fence in ``path`` is followed by the pointer, unless ``hand_run`` names it."""
    text = read(path) if text is None else text
    listed = {(h.file, h.heading, h.first) for h in hand_run}
    expected = pointer_for(path)
    problems = []
    for fence in fences(path, text):
        following = paragraph_after(after(text, fence))
        if fence_key(fence) in listed:
            if following == expected:
                problems.append(f"{where(fence)}: listed in HAND_RUN, but followed by the guide-run "
                                "pointer")
        elif following != expected:
            problems.append(f"{where(fence)}: guide-run, so the line after it must be the pointer, not "
                            f"{following[:100]!r}; or list it in HAND_RUN with its reason")
    return problems


def hand_run_problems(fence_list, hand_run=HAND_RUN):
    """Each ``hand_run`` entry names exactly one fence in ``fence_list`` and gives one reason line."""
    found = Counter(fence_key(fence) for fence in fence_list)
    problems = []
    for entry, n in Counter(hand_run).items():
        if n > 1:
            problems.append(f"HAND_RUN lists {entry.first!r} {n} times")
    for entry in hand_run:
        key = (entry.file, entry.heading, entry.first)
        if not found[key]:
            problems.append(f"stale HAND_RUN entry, it matches no fence: {key!r}")
        elif found[key] > 1:
            problems.append(f"HAND_RUN entry matches {found[key]} fences, so it names none: {key!r}")
        if not entry.reason.strip() or "\n" in entry.reason:
            problems.append(f"HAND_RUN entry {key!r} needs a one-line reason")
    return problems


def module_4_step_3_problems(text):
    """Module 4 Step 3 keeps only its POSIX form, followed by the pointer (#597)."""
    try:
        step = between(text, MODULE_4_STEP_3, MODULE_4_STEP_4)
    except ValueError:
        return ["Module 4 Step 3 not found"]
    found = fences(MODULE_4, step)
    problems = [f"Step 3 keeps a {f.lang} twin: {f.first!r}" for f in found if f.lang != "bash"]
    posix = [f for f in found if f.lang == "bash"]
    if [f.first for f in posix] != ["ls -lh data/raw/"]:
        problems.append(f"Step 3's POSIX block is not the one `ls -lh data/raw/` block: {posix!r}")
    for fence in posix:
        if paragraph_after(after(step, fence)) != POINTER:
            problems.append("Step 3's POSIX block is not followed by the pointer")
    return problems


def pointer_sweep_problems(files):
    """Every paragraph in the plugin that links the anchor is the pointer, word for word."""
    problems = []
    for path in files:
        for para in re.split(r"\n[ \t]*\n", read(path)):
            if f"#{ANCHOR_ID})" in para and flat(para) != pointer_for(path):
                problems.append(f"{path.name}: {flat(para)[:100]!r}")
    return problems


def schema_step_problems(text):
    problems = []
    try:
        step = between(text, STEP_4, STEP_5)
        container = between(step, CONTAINER_ROUTE, NATIVE_ROUTE)
        native = step[step.index(NATIVE_ROUTE):]
    except ValueError:
        return ["step 4 or its two routes not found"]
    for line in step.splitlines():
        if HOST_OPT_REDIRECT.search(line):
            problems.append(f"redirects from a host /opt/senzing path: {line.strip()!r}")
    block, _ = fenced_block_after(container, "psql")
    code = "\n".join(block)
    if not re.search(r'^\s*<runtime> cp "<sdk-container>:<schema path from MCP>" database/\S+\.sql &&$',
                     code, re.M):
        problems.append("container route does not `<runtime> cp` the MCP path into database/")
    if re.search(r"^\s*docker cp\b", code, re.M):
        problems.append("container route hardcodes `docker cp` (INV-195)")
    if not re.search(r"psql -U senzing -d G2 < database/\S+\.sql$", code, re.M):
        problems.append("container route's psql does not read the project copy")
    if not match_lines(container, r"recorded `runtime` as `<runtime>` \(INV-195\)"):
        problems.append("container route does not dispatch on the recorded runtime")
    if not match_lines(container, r"\(INV-200\)"):
        problems.append("container route does not keep the copy in the project (INV-200)")
    if not match_lines(container, r"A failed copy\s+stops the step"):
        problems.append("container route has no failed-copy rule")
    if not match_lines(step, r"`<schema path from MCP>`.*at runtime \(INV-080\)"):
        problems.append("the path is not taken from MCP at runtime")
    native_block, _ = fenced_block_after(native, "psql")
    if not re.search(r'psql -U senzing -d G2 < "<schema path from MCP>"$', "\n".join(native_block),
                     re.M):
        problems.append("native route no longer applies the host file")
    return problems


def option_2_problems(text):
    """Option 2's "as above" sentence takes the DDL from the SDK container on the container route."""
    try:
        option = between(text, OPTION_2, OPTION_3)
    except ValueError:
        return ["Option 2 not found"]
    problems = []
    for pattern, what in (
            (r"On SDK setup's container route the DDL is taken from the SDK container",
             "does not take the DDL from the SDK container on the container route"),
            (r"as Option 1's container-route command takes it, never from a host path",
             "does not point at Option 1's container-route command, or allows a host path"),
            (r"copy it into `database/` with that command's `<runtime> cp`",
             "does not copy the DDL into database/ with the recorded runtime's cp"),
            (r"apply the copy with `psql -f database/szcore-schema-postgresql-create\.sql`",
             "does not apply the project copy")):
        if not match_lines(option, pattern):
            problems.append(f"Option 2 {what}")
    for line in option.splitlines():
        if HOST_OPT_REDIRECT.search(line) or re.search(r"psql -f \"?/opt/senzing", line):
            problems.append(f"Option 2 reads a host /opt/senzing path: {line.strip()!r}")
    return problems


# --- tests -----------------------------------------------------------------------------------


class GroundRulesHoldTheOneStatement(unittest.TestCase):
    def test_statement_is_present(self):
        self.assertEqual(ground_rules_problems(read(GROUND_RULES)), [])

    def test_negative_control_removing_the_anchor(self):
        self.assertTrue(ground_rules_problems(read(GROUND_RULES).replace(ANCHOR, "")))

    def test_negative_control_dropping_the_hand_run_clause(self):
        text = read(GROUND_RULES).replace("PowerShell 5.1 form that meets the rules above (INV-167)",
                                          "form")
        self.assertTrue(ground_rules_problems(text))

    def test_negative_control_dropping_git_bash(self):
        text = read(GROUND_RULES).replace("which on Windows is Git Bash", "which varies")
        self.assertTrue(ground_rules_problems(text))

    def test_negative_control_dropping_the_powershell_runner(self):
        text = read(GROUND_RULES).replace("`powershell.exe -NoProfile -Command …`", "PowerShell")
        self.assertTrue(ground_rules_problems(text))

    def test_negative_control_anchor_outside_the_section(self):
        text = read(GROUND_RULES).replace(ANCHOR, "")
        text = text.replace("## Markdown files", ANCHOR + "\n\n## Markdown files")
        self.assertTrue(ground_rules_problems(text))


class EveryGuideRunBlockCarriesThePointer(unittest.TestCase):
    """Every bash, sh and PowerShell fence under `plugins/` is guide-run unless HAND_RUN says (#597)."""

    def test_pointer_links_the_anchor_and_discloses(self):
        self.assertIn(f"]({LINK})", POINTER)
        self.assertIn(DISCLOSURE, POINTER)

    def test_every_fence_is_guide_run_with_the_pointer_or_listed_as_hand_run(self):
        for path in plugin_files():
            with self.subTest(file=path.relative_to(PLUGIN).as_posix()):
                self.assertEqual(guide_run_problems(path), [])

    def test_every_hand_run_entry_names_one_fence_with_a_reason(self):
        every = [fence for path in plugin_files() for fence in fences(path)]
        self.assertEqual(hand_run_problems(every), [])

    def test_hand_run_entries_are_keyed_on_text_never_a_line_number(self):
        self.assertEqual(HandRun._fields, ("file", "heading", "first", "reason"))
        for entry in HAND_RUN:
            with self.subTest(entry=entry.first):
                self.assertTrue(all(isinstance(field, str) for field in entry))
                self.assertTrue((PLUGIN / entry.file).is_file(), entry.file)
                self.assertTrue(HEADING.match(entry.heading), entry.heading)

    def test_the_scan_reads_both_shells_and_every_top_level_directory(self):
        """A liveness check, not a count: an empty scan would pass every test above."""
        every = [fence for path in plugin_files() for fence in fences(path)]
        self.assertTrue({"bash", "powershell"} <= {fence.lang for fence in every})
        self.assertTrue({"commands", "skills"} <= {fence_key(fence)[0].split("/")[0] for fence in every})

    def test_each_link_resolves_to_the_anchor(self):
        for path in plugin_files():
            if not fences(path):
                continue
            with self.subTest(file=path.relative_to(PLUGIN).as_posix()):
                link = re.search(r"\]\(([^)#]+)#", pointer_for(path)).group(1)
                self.assertEqual((path.parent / link).resolve(), GROUND_RULES.resolve())
                self.assertIn(ANCHOR, read(GROUND_RULES))

    def test_every_link_to_the_anchor_uses_the_one_wording(self):
        self.assertEqual(pointer_sweep_problems(plugin_files()), [])

    def test_negative_control_a_removed_pointer(self):
        for path in plugin_files():
            text = read(path)
            listed = {(h.file, h.heading, h.first) for h in HAND_RUN}
            for fence in fences(path, text):
                if fence_key(fence) in listed:
                    continue
                with self.subTest(site=where(fence)):
                    lines = text.split("\n")
                    k = fence.close + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    end = k
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    self.assertEqual(flat(" ".join(lines[k:end])), pointer_for(path))
                    stripped = "\n".join(lines[:k] + lines[end:])
                    self.assertTrue(guide_run_problems(path, stripped))

    def test_negative_control_a_reworded_pointer(self):
        text = read(MODULE_2).replace("no test runs it there", "nobody checked")
        self.assertTrue(guide_run_problems(MODULE_2, text))

    def test_negative_control_a_new_unlisted_fence(self):
        for lang in ("bash", "sh", "powershell"):
            with self.subTest(lang=lang):
                text = read(PHASE1) + f"\n## A new step\n\n```{lang}\necho new\n```\n\nIt prints.\n"
                problems = guide_run_problems(PHASE1, text)
                self.assertTrue(any("'echo new'" in p for p in problems), problems)

    def test_negative_control_a_new_fence_with_the_pointer_passes(self):
        text = read(PHASE1) + f"\n## A new step\n\n```bash\necho new\n```\n\n{POINTER}\n"
        self.assertEqual(guide_run_problems(PHASE1, text), [])

    def test_negative_control_a_stale_hand_run_entry(self):
        every = [fence for path in plugin_files() for fence in fences(path)]
        stale = HAND_RUN + (HandRun("skills/module-02-sdk-setup/SKILL.md", ENV_SCRIPT, "echo gone",
                                    "a block that was deleted"),)
        problems = hand_run_problems(every, stale)
        self.assertTrue(any("stale" in p and "echo gone" in p for p in problems), problems)

    def test_negative_control_a_hand_run_block_whose_first_line_changed(self):
        """Its entry goes stale and the block becomes an unlisted guide-run block: both report."""
        text = read(MODULE_2).replace('if [ -n "${ZSH_VERSION:-}" ]; then',
                                      'if [ -n "${ZSH_VERSION-}" ]; then', 1)
        self.assertTrue(hand_run_problems(fences(MODULE_2, text)))
        self.assertTrue(guide_run_problems(MODULE_2, text))

    def test_negative_control_an_entry_under_the_wrong_heading(self):
        moved = tuple(entry._replace(heading="## Step 3: Install Senzing SDK") for entry in HAND_RUN)
        self.assertTrue(hand_run_problems(fences(MODULE_2), moved))

    def test_negative_control_a_hand_run_block_with_the_pointer(self):
        text = read(MODULE_2)
        fence = next(f for f in fences(MODULE_2, text) if f.first == HAND_RUN[0].first)
        lines = text.split("\n")
        lines[fence.close + 1:fence.close + 1] = ["", POINTER]
        problems = guide_run_problems(MODULE_2, "\n".join(lines))
        self.assertTrue(any("listed in HAND_RUN" in p for p in problems), problems)

    def test_negative_control_a_hand_run_entry_with_no_reason(self):
        blank = (HAND_RUN[0]._replace(reason=" "),) + HAND_RUN[1:]
        self.assertTrue(hand_run_problems(fences(MODULE_2), blank))

    def test_a_fence_nested_in_a_markdown_example_is_its_text(self):
        text = ("## Doc\n\n````markdown\n## Inside\n\n```bash\necho example\n```\n````\n\n"
                "```bash\necho real\n```\n\nIt prints.\n")
        self.assertEqual([(f.heading, f.first) for f in fences(PHASE1, text)],
                         [("## Doc", "echo real")])

    def test_negative_control_the_sweep_catches_a_drifted_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            drifted = Path(tmp) / "x.md"
            drifted.write_text(f"Runs in Git Bash ([guide-run blocks]({LINK})).\n", encoding="utf-8")
            self.assertTrue(pointer_sweep_problems([drifted]))

    def test_negative_control_a_command_using_the_skill_link(self):
        command = PLUGIN / "commands" / "package-bootcamp.md"
        self.assertNotEqual(pointer_for(command), POINTER)
        text = read(command).replace(pointer_for(command), POINTER)
        self.assertTrue(guide_run_problems(command, text))


class PowerShellOnlyGuideRunBlocks(unittest.TestCase):
    """SDK setup's Scoop and SUPPORTPATH checks are guide-run; Module 4 Step 3 has one POSIX form (#597)."""

    def test_each_powershell_only_block_is_followed_by_the_pointer(self):
        for label, path, marker in POWERSHELL_GUIDE_RUN:
            with self.subTest(site=label):
                self.assertEqual(site_problems(read(path), marker), [])

    def test_none_of_them_is_listed_as_hand_run(self):
        listed = {(h.file, h.heading, h.first) for h in HAND_RUN}
        for label, path, marker in POWERSHELL_GUIDE_RUN:
            with self.subTest(site=label):
                lines = read(path).split("\n")
                holding = [f for f in fences(path) if f.lang == "powershell"
                           and any(marker in line for line in lines[f.start + 1:f.close])]
                self.assertEqual(len(holding), 1, holding)
                self.assertNotIn(fence_key(holding[0]), listed)

    def test_step_8_runs_the_blocks_that_share_a_variable_in_one_call(self):
        step = between(read(MODULE_2), "**On Windows, verify the `SUPPORTPATH`", "**On macOS, the same check")
        for pattern in (r"Each block below is a PowerShell-only guide-run block",
                        r"items 2 and 3's blocks in one call:\s+`\$supportPath` does not survive"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(step, pattern))

    def test_module_4_step_3_keeps_only_its_posix_form(self):
        self.assertEqual(module_4_step_3_problems(read(MODULE_4)), [])

    def test_negative_control_the_powershell_twin_restored(self):
        text = read(MODULE_4).replace(
            f"{POINTER}\n",
            f"{POINTER}\n\n```powershell\nGet-ChildItem data\\raw\\ | Format-Table Name, Length\n```\n", 1)
        self.assertNotEqual(text, read(MODULE_4))
        self.assertTrue(module_4_step_3_problems(text))

    def test_negative_control_a_powershell_only_block_without_the_pointer(self):
        text = read(MODULE_2)
        _, rest = fenced_block_after(text, "scoop info senzingsdk/senzingsdk")
        stripped = text[:len(text) - len(rest)] + rest.replace(POINTER, "", 1)
        self.assertTrue(site_problems(stripped, "scoop info senzingsdk/senzingsdk"))
        self.assertTrue(guide_run_problems(MODULE_2, stripped))


class SchemaDdlComesFromTheSdkContainer(unittest.TestCase):
    def test_step_4(self):
        self.assertEqual(schema_step_problems(read(MODULE_2)), [])

    def test_negative_control_the_old_host_redirect(self):
        text = read(MODULE_2).replace(
            "psql -U senzing -d G2 < database/szcore-schema-postgresql-create.sql",
            "psql -U senzing -d G2 < /opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql")
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_hardcoded_docker_cp(self):
        text = read(MODULE_2).replace('<runtime> cp "<sdk-container>:', 'docker cp "<sdk-container>:')
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_a_literal_path(self):
        text = read(MODULE_2).replace(
            '"<sdk-container>:<schema path from MCP>"',
            '"<sdk-container>:/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql"')
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_native_route_removed(self):
        text = read(MODULE_2).replace('< "<schema path from MCP>"', "< schema.sql")
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_copy_outside_the_project(self):
        text = read(MODULE_2).replace("database/szcore-schema-postgresql-create.sql &&",
                                      "/tmp/szcore-schema-postgresql-create.sql &&")
        self.assertTrue(schema_step_problems(text))


class OptionTwoTakesTheDdlFromTheSdkContainer(unittest.TestCase):
    """Option 2 (a local PostgreSQL) applies the DDL "as above"; on the container route it must say
    the DDL comes from the SDK container as Option 1's container-route command takes it (#508)."""

    def test_option_2(self):
        self.assertEqual(option_2_problems(read(MODULE_2)), [])

    def test_negative_control_the_container_route_sentence_removed(self):
        text = read(MODULE_2)
        option = between(text, OPTION_2, OPTION_3)
        cut = option[:option.index("On SDK setup's")].rstrip() + "\n\n"
        self.assertTrue(option_2_problems(text.replace(option, cut)))

    def test_negative_control_a_host_path(self):
        text = read(MODULE_2)
        option = between(text, OPTION_2, OPTION_3)
        hosted = option.replace(
            "psql -f database/szcore-schema-postgresql-create.sql",
            "psql -f /opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql")
        problems = option_2_problems(text.replace(option, hosted))
        self.assertTrue(any("host /opt/senzing" in p for p in problems), problems)

    def test_negative_control_option_2_gone(self):
        self.assertTrue(option_2_problems(read(MODULE_2).replace(OPTION_2, "**Option 2:**")))


def _stub(path, body):
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@unittest.skipUnless(shutil.which("sh") and os.name == "posix",
                     "needs a POSIX sh to run the container-route block against stub runtimes")
class TheContainerRouteBlockRuns(unittest.TestCase):
    """Run step 4's own container-route block, with stub `<runtime>` and `<pg-runtime>`, in a temp project.

    The stub runtime's `cp` reads `<container>:<path>` from a fake container root, so the test
    sees the copy come from the container and land in the project; the stub `<pg-runtime>`, the
    PostgreSQL container's recorded runtime (INV-195, #613), records what `psql` receives on stdin.
    """

    DDL = "CREATE TABLE sys_cfg (x INT);\n"
    IN_CONTAINER = "/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "project"
        (self.project / "database").mkdir(parents=True)
        self.container_root = root / "sdk-container-fs"
        ddl = self.container_root / self.IN_CONTAINER.lstrip("/")
        ddl.parent.mkdir(parents=True)
        ddl.write_text(self.DDL, encoding="utf-8")
        self.bin = root / "bin"
        self.bin.mkdir()
        self.stdin_log = root / "psql-stdin.sql"
        _stub(self.bin / "stubrt",
              'test "$1" = cp || exit 9\n'
              'src="${2#*:}"\n'
              f'cp "{self.container_root}$src" "$3"\n')
        _stub(self.bin / "stubpgrt", f'test "$1" = exec || exit 9\ncat > "{self.stdin_log}"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def block(self):
        step = between(read(MODULE_2), STEP_4, STEP_5)
        lines, _ = fenced_block_after(between(step, CONTAINER_ROUTE, NATIVE_ROUTE), "psql")
        code = "\n".join(line.strip() for line in lines)
        return (code.replace("<pg-runtime>", "stubpgrt")
                    .replace("<runtime>", "stubrt")
                    .replace("<sdk-container>", "senzing-bootcamp-demo-1a2b3c")
                    .replace("<schema path from MCP>", self.IN_CONTAINER)
                    .replace("<pg-container>", "bootcamp-postgres-demo-1a2b3c"))

    def run_block(self, code):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}")
        return subprocess.run(["sh", "-c", code], cwd=self.project, env=env,
                              capture_output=True, text=True, timeout=30)

    def test_the_ddl_reaches_psql_from_the_project_copy(self):
        result = self.run_block(self.block())
        self.assertEqual(result.returncode, 0, result.stderr)
        copy = self.project / "database" / "szcore-schema-postgresql-create.sql"
        self.assertEqual(copy.read_text(encoding="utf-8"), self.DDL)
        self.assertEqual(self.stdin_log.read_text(encoding="utf-8"), self.DDL)

    def test_negative_control_a_failed_copy_fails_the_block(self):
        (self.container_root / self.IN_CONTAINER.lstrip("/")).unlink()
        result = self.run_block(self.block())
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.stdin_log.exists(), "psql must not run after a failed copy")

    def test_negative_control_without_the_chain_a_stale_copy_is_applied(self):
        """Why the block chains with `&&`: unchained, a failed copy still applies an older copy."""
        (self.container_root / self.IN_CONTAINER.lstrip("/")).unlink()
        stale = self.project / "database" / "szcore-schema-postgresql-create.sql"
        stale.write_text("-- stale\n", encoding="utf-8")
        result = self.run_block(self.block().replace(" &&\n", "\n"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.stdin_log.read_text(encoding="utf-8"), "-- stale\n")


if __name__ == "__main__":
    unittest.main()
