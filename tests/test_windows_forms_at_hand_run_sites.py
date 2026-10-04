"""Hand-run commands at four sites carry a Windows PowerShell 5.1 form, and no redirection (#391).

INV-001 makes Windows a supported platform, and the ground rules say to assume Windows
PowerShell 5.1, where "`>` and `Out-File` are not equivalent to bash `>`". The 2026-10-02
production-readiness audit (finding C-F6) found four hand-run sites that no test executes on
Windows and that had no correct Windows form:

1. **Module 4 Step 8a sub-step 5 (apply a license key).** The Windows decode used
   `Set-Content … -AsByteStream`, which needs PowerShell 6+, and `-Encoding Byte` is no fix
   because PowerShell 7 rejects it. The decode is now `[System.IO.File]::WriteAllBytes` with an
   absolute path built from `Get-Location`: `WriteAllBytes` resolves a relative path against
   .NET's working directory, not PowerShell's current location. The binary check `file` does not
   exist on Windows; the Windows check is `Format-Hex`, and sub-step 7's limit detection is the
   authoritative check on every platform.
2. **Graduation Step 1b (render the recap PDF).** The venv render line and the venv creation
   line had no Windows form, while the pip line between them did.
3. **Graduation Step 6c (the return guide).** It said to re-source `senzing-env.sh` "(if
   present)", which silently drops the step on Windows. #419 replaced Module 2's
   `senzing-env.bat` with a dot-sourced `senzing-env.ps1`, so the Windows form is now
   `. .\\src\\scripts\\senzing-env.ps1`.
4. **`graduation/database-backup.md` (the PostgreSQL backup and restore).** The backup wrote the
   binary dump with `>`, which PowerShell 5.1 re-encodes as text, silently until a restore; the
   restore used `psql <`, which PowerShell 5.1 rejects as a parser error. The commands now name
   their files by argument (`pg_dump -f`, `pg_restore -d <db> <file>`, `psql -f`), and the
   container form copies the dump out with `docker cp`, because `-f` inside `docker exec` writes
   into the container's filesystem. The packaged `OPEN_ME_FIRST.md` restore step
   (`package_bootcamp.py`'s `PG_RESTORE`) is the same step and is held to the same rule.

5. **Graduation Step 1c (the Piper voice and the `imageio-ffmpeg` install), #420.** Step 1c
   created the same recap venv three more times with the POSIX form only, and in both code blocks
   the venv line sat above `# Linux/macOS`, shared by both platforms. Each block now creates it
   under `# Linux/macOS` and, as `py -3 -m venv data\\temp\\recap-venv`, under `# Windows:`;
   the list item names the Windows form in a parenthetical; and each block is followed by Step
   1b's "unverified on Windows" sentence. A scan of every `.md` under the plugin pairs each
   `python3 -m venv <path>` with `py -3 -m venv <path, / as \\>` in the same fenced code block,
   or, outside code blocks, the same paragraph or list item (text between blank lines), so a
   new venv site is caught without a line number (INV-246).

These tests pin the forms. They **cannot** establish that the Windows forms run on Windows: this
repo's CI runs on Linux, so each site says on its own text that its Windows form is unverified
there (INV-163), and a test pins that disclosure too.

Enforces INV-001, INV-166 and INV-167 at these sites.

Run:  python3 -m unittest discover -s tests
"""
import ast
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"
DATABASE_BACKUP = SKILLS / "graduation" / "database-backup.md"
PACKAGER = PLUGIN / "scripts" / "package_bootcamp.py"

DECODE = ("[System.IO.File]::WriteAllBytes((Join-Path (Get-Location) 'licenses\\g2.lic'), "
          "[System.Convert]::FromBase64String('<BASE64_STRING>'))")
WINDOWS_RENDER = ('data\\temp\\recap-venv\\Scripts\\python '
                  '"${CLAUDE_PLUGIN_ROOT}\\scripts\\generate_recap_pdf.py"')
WINDOWS_VENV = "py -3 -m venv data\\temp\\recap-venv"
UNVERIFIED = "unverified on Windows"
#: Step 1b's whole disclosure sentence, which Step 1c repeats after each of its code blocks.
DISCLOSURE = ("The Windows lines are written for PowerShell 5.1 and 7 but are unverified on "
              "Windows: no test runs them there.")
POSIX_VENV_LINE = "python3 -m venv data/temp/recap-venv    # only if it does not exist yet"
WINDOWS_VENV_LINE = "py -3 -m venv data\\temp\\recap-venv    # only if it does not exist yet"

#: A POSIX venv creation and its path, which ends at whitespace or a closing backtick.
POSIX_VENV = re.compile(r"python3 -m venv ([^\s`]+)")
#: A code-fence line, read as `_wrapped_text` reads one.
FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")

#: A PostgreSQL client command, as the first word of a command or after `docker exec <c>`.
PG_COMMAND = re.compile(r"\b(?:pg_dump|pg_restore|psql)\s+-")
#: A placeholder such as `<user>` or `<BASE64_STRING>`; its brackets are not redirections.
PLACEHOLDER = re.compile(r"<[A-Za-z_][\w-]*>")
#: An inline code span. A span may wrap across a line break but not a blank line.
SPAN = re.compile(r"`([^`\n]+(?:\n[^`\n]+)*)`")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def license_substep(text):
    return between(text, "5. **Apply a Senzing License Key", "6. **Obtain a Senzing License Key")


def step_1b(text):
    return between(text, "### 1b. Render the PDF", "### 1c.")


def step_6c(text):
    return between(text, "### 6c. Return guide", "## Step 7:")


def step_1c(text):
    return between(text, "### 1c.", "## Step 2:")


def units(text):
    """The text's pairing units, in order: ``(kind, [(lineno, line), ...])``.

    ``kind`` is ``"fence"`` for the whole contents of one fenced code block and ``"prose"`` for
    one block between blank lines (a paragraph, or a list's lines). The cut is
    `_wrapped_text.blocks`; the only change is that the blocks inside one fence are joined, since
    a blank line inside a code block does not end the code block.
    """
    out, fence, current = [], None, None
    for block in blocks(text):
        opener = FENCE_LINE.match(block[0][1]) if len(block) == 1 else None
        if opener and (fence is None or opener.group(1)[0] == fence):
            if fence is None:
                fence, current = opener.group(1)[0], []
            else:
                out.append(("fence", current))
                fence, current = None, None
        elif fence:
            current.extend(block)
        else:
            out.append(("prose", block))
    if fence:
        out.append(("fence", current))
    return out


def flat_unit(block):
    """A unit's text with whitespace collapsed, and the line each word came from."""
    words = [(lineno, word) for lineno, line in block for word in line.split()]
    return " ".join(word for _, word in words), [lineno for lineno, _ in words]


def venv_sites(text):
    """``(lineno, path, paired)`` for every `python3 -m venv <path>` in ``text``.

    ``paired`` is whether `py -3 -m venv <path with / as \\>` is in the same unit (see `units`).
    The conversion is literal: `/` becomes `\\` and nothing else changes.
    """
    sites = []
    for _, block in units(text):
        flat_text, origin = flat_unit(block)
        for match in POSIX_VENV.finditer(flat_text):
            windows = "py -3 -m venv " + match.group(1).replace("/", "\\")
            paired = re.search(re.escape(windows) + r"(?![^\s`])", flat_text) is not None
            sites.append((origin[flat_text[:match.start()].count(" ")], match.group(1), paired))
    return sites


def unpaired_venvs(text):
    return [(lineno, path) for lineno, path, paired in venv_sites(text) if not paired]


def venv_blocks_out_of_layout(text):
    """Each fenced block creating the recap venv whose lines are not, in this order: a
    `# Linux/macOS` comment, the POSIX venv line, `# Windows:`, the Windows venv line."""
    bad = []
    for kind, block in units(text):
        lines = [line.strip() for _, line in block]
        if kind != "fence" or POSIX_VENV_LINE not in lines:
            continue
        posix = lines.index(POSIX_VENV_LINE)
        linux = next((i for i, l in enumerate(lines) if l.startswith("# Linux/macOS")), None)
        windows = lines.index("# Windows:") if "# Windows:" in lines else None
        py = lines.index(WINDOWS_VENV_LINE) if WINDOWS_VENV_LINE in lines else None
        if None in (linux, windows, py) or not linux < posix < windows < py:
            bad.append(block[0][0])
    return bad


def venv_blocks_without_disclosure(text):
    """Each fenced block creating a venv whose next unit does not carry `DISCLOSURE`."""
    found = units(text)
    bad = []
    for i, (kind, block) in enumerate(found):
        if kind != "fence" or not POSIX_VENV.search(flat_unit(block)[0]):
            continue
        after = found[i + 1] if i + 1 < len(found) else None
        if after is None or after[0] != "prose" or DISCLOSURE not in flat_unit(after[1])[0]:
            bad.append(block[0][0])
    return bad


def redirecting_pg_commands(text):
    """Every inline span running a PostgreSQL client with a `<` or `>` outside a placeholder."""
    out = []
    for match in SPAN.finditer(text):
        span = " ".join(match.group(1).split())
        if PG_COMMAND.search(span) and re.search(r"[<>]", PLACEHOLDER.sub("", span)):
            out.append(span)
    return out


def pg_commands(text):
    return [" ".join(m.group(1).split()) for m in SPAN.finditer(text)
            if PG_COMMAND.search(" ".join(m.group(1).split()))]


def packaged_pg_restore():
    """`package_bootcamp.py`'s `PG_RESTORE`, read as a literal without importing the script."""
    tree = ast.parse(PACKAGER.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", None) == "PG_RESTORE"):
            return ast.literal_eval(node.value)
    raise AssertionError("package_bootcamp.py has no PG_RESTORE assignment")


class TheLicenseDecodeWorksOnPowerShell5And7(unittest.TestCase):
    def setUp(self):
        self.module = MODULE_4.read_text(encoding="utf-8")
        self.step = flat(license_substep(self.module))

    def test_no_as_byte_stream_remains_in_module_4(self):
        self.assertNotIn("-AsByteStream", self.module,
                         "`Set-Content -AsByteStream` needs PowerShell 6+; 5.1 is the default")

    def test_no_encoding_byte_form_either(self):
        self.assertNotIn("-Encoding Byte", self.module, "PowerShell 7 rejects `-Encoding Byte`")

    def test_the_decode_uses_write_all_bytes_with_an_absolute_path(self):
        self.assertIn(DECODE, self.step)
        self.assertRegex(self.step, r"(?i)path must be absolute.*\.NET's working directory")

    def test_the_lic_copy_has_a_windows_form(self):
        self.assertIn("`cp <path-to>/g2.lic licenses/g2.lic`", self.step)
        self.assertIn("`Copy-Item <path-to>\\g2.lic licenses\\g2.lic`", self.step)

    def test_the_binary_check_has_a_windows_form_and_defers_to_sub_step_7(self):
        self.assertIn("`file licenses/g2.lic`", self.step)
        self.assertIn("`Format-Hex licenses\\g2.lic | Select-Object -First 1`", self.step)
        self.assertIn("Sub-step 7's limit detection is the authoritative check on every platform",
                      self.step)

    def test_the_binary_check_claims_no_byte_signature(self):
        self.assertIn("is non-empty and is not Base64 text", self.step)

    def test_the_windows_forms_are_disclosed_as_unverified(self):
        self.assertIn(UNVERIFIED, self.step)


class TheRecapRenderHasAWindowsForm(unittest.TestCase):
    """Line-scoped by design (#424): each form asserted here is one command line."""

    def setUp(self):
        self.step = step_1b(GRADUATION.read_text(encoding="utf-8"))

    def test_the_windows_render_line_is_present(self):
        self.assertIn(WINDOWS_RENDER, [line.strip() for line in self.step.splitlines()])

    def test_the_windows_venv_creation_line_is_present(self):
        self.assertIn(WINDOWS_VENV, [line.strip() for line in self.step.splitlines()])

    def test_the_posix_lines_are_kept(self):
        lines = [line.strip() for line in self.step.splitlines()]
        self.assertIn("python3 -m venv data/temp/recap-venv", lines)
        self.assertIn('data/temp/recap-venv/bin/python '
                      '"${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_pdf.py"', lines)

    def test_the_windows_lines_are_disclosed_as_unverified(self):
        self.assertIn(UNVERIFIED, flat(self.step))


class EveryVenvCreationHasAWindowsForm(unittest.TestCase):
    """#420: every `python3 -m venv <path>` under the plugin has its `py -3` form beside it."""

    def setUp(self):
        self.graduation = GRADUATION.read_text(encoding="utf-8")

    def test_every_site_under_the_plugin_is_paired(self):
        problems = []
        for path in sorted(PLUGIN.rglob("*.md")):
            for lineno, venv in unpaired_venvs(path.read_text(encoding="utf-8")):
                problems.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: python3 -m venv {venv}")
        self.assertEqual([], problems,
                         "pair each with `py -3 -m venv <path, / as \\>` in the same fenced code "
                         "block, or the same paragraph or list item")

    def test_the_scan_finds_the_graduation_sites(self):
        """Guard the guard: Step 1b's site and Step 1c's three are found, and found paired."""
        self.assertEqual(1, len(venv_sites(step_1b(self.graduation))))
        sites = venv_sites(step_1c(self.graduation))
        self.assertEqual(3, len(sites), sites)
        self.assertTrue(all(paired for _, _, paired in sites), sites)
        self.assertGreaterEqual(len(venv_sites(self.graduation)), 4)

    def test_the_step_1c_list_item_names_the_windows_form(self):
        self.assertIn("(Windows: `py -3 -m venv data\\temp\\recap-venv`)",
                      flat(step_1c(self.graduation)))

    def test_step_1c_blocks_split_the_venv_line_per_platform(self):
        step = step_1c(self.graduation)
        fenced = [b for kind, b in units(step) if kind == "fence"
                  and POSIX_VENV_LINE in [line.strip() for _, line in b]]
        self.assertEqual(2, len(fenced))
        self.assertEqual([], venv_blocks_out_of_layout(step))

    def test_step_1c_blocks_are_disclosed_as_unverified(self):
        self.assertEqual([], venv_blocks_without_disclosure(step_1c(self.graduation)))


class TheReturnGuideNamesBothEnvScripts(unittest.TestCase):
    def setUp(self):
        self.step = flat(step_6c(GRADUATION.read_text(encoding="utf-8")))

    def test_it_dot_sources_the_ps1_for_windows(self):
        """#419: a `.bat` run from PowerShell sets nothing in the session; the `.ps1` does."""
        self.assertIn("`. .\\src\\scripts\\senzing-env.ps1` on Windows", self.step)
        self.assertNotIn("senzing-env.bat", self.step)
        self.assertIn("unverified on Windows PowerShell 5.1", self.step)
        self.assertIn("`source src/scripts/senzing-env.sh` on Linux/macOS", self.step)

    def test_if_present_no_longer_drops_the_step(self):
        self.assertNotIn("senzing-env.sh` (if present)", self.step)

    def test_no_restore_command_redirects(self):
        self.assertEqual([], redirecting_pg_commands(self.step))
        self.assertNotIn("psql <", self.step)


class ThePostgresBackupAndRestoreUseNoRedirection(unittest.TestCase):
    def setUp(self):
        self.text = DATABASE_BACKUP.read_text(encoding="utf-8")

    def test_no_postgres_command_redirects(self):
        self.assertEqual([], redirecting_pg_commands(self.text),
                         "a `>` re-encodes the binary dump on PowerShell 5.1, and `<` is a parser "
                         "error there; name the file by argument (`-f`, `-d <db> <file>`)")

    def test_the_sweep_sees_the_commands(self):
        """Guard the guard: the sweep must find the backup and both restore commands."""
        commands = pg_commands(self.text)
        self.assertTrue(any(c.startswith("pg_dump ") for c in commands), commands)
        self.assertTrue(any("pg_restore -U" in c for c in commands), commands)
        self.assertTrue(any("psql -U" in c and " -f " in c for c in commands), commands)

    def test_the_host_backup_writes_with_dash_f(self):
        self.assertIn("`pg_dump -U <user> -d <db> -Fc -f backups/revisit/database/senzing.dump`",
                      self.text)

    def test_the_container_backup_copies_the_dump_out(self):
        flat_text = flat(self.text)
        dump = "`docker exec <container> pg_dump -U <user> -d <db> -Fc -f /tmp/senzing.dump`"
        copy = "`docker cp <container>:/tmp/senzing.dump backups/revisit/database/senzing.dump`"
        cleanup = "`docker exec <container> rm /tmp/senzing.dump`"
        for piece in (dump, copy, cleanup):
            with self.subTest(piece=piece):
                self.assertIn(piece, flat_text)
        self.assertLess(flat_text.index(dump), flat_text.index(copy))
        self.assertLess(flat_text.index(copy), flat_text.index(cleanup))

    def test_a_backup_that_never_reached_the_host_is_not_a_backup(self):
        self.assertIn("a failed `docker cp`, or a missing or empty file, means the backup could "
                      "not be produced", flat(self.text))

    def test_the_restore_names_its_file_by_argument(self):
        restore = flat(self.text[self.text.index("## Restore"):])
        self.assertIn("`pg_restore -U <user> -d <db> <file>`", restore)
        self.assertIn("`psql -U <user> -d <db> -f <file>`", restore)
        self.assertIn("`docker cp <file> <container>:/tmp/senzing.dump`", restore)
        self.assertNotIn("psql <", restore)

    def test_the_forms_are_disclosed_as_unverified(self):
        self.assertIn(UNVERIFIED, flat(self.text))


class ThePackagedRestoreStepFollowsTheSameRule(unittest.TestCase):
    """`OPEN_ME_FIRST.md` carries database-backup.md's restore step when no guide was packaged."""

    def test_it_names_the_file_by_argument(self):
        step = packaged_pg_restore()
        self.assertIn("`pg_restore -U <user> -d <db> <file>`", step)
        self.assertIn("`psql -U <user> -d <db> -f <file>`", step)
        self.assertNotIn("psql <", step)
        self.assertEqual([], redirecting_pg_commands(step))


class NegativeControls(unittest.TestCase):
    """Each check fails on the text it replaced."""

    OLD_DECODE = ("     `[System.Convert]::FromBase64String('<BASE64_STRING>') | "
                  "Set-Content -Path licenses\\g2.lic -AsByteStream`.")
    OLD_BACKUP = ("  `docker exec <container> pg_dump -U <user> -d <db> -Fc > "
                  "backups/revisit/database/senzing.dump`).")
    OLD_RESTORE = "- **PostgreSQL** — `pg_restore` (or `psql <` for a plain dump) into a fresh database."

    def test_the_old_decode_is_caught(self):
        self.assertIn("-AsByteStream", self.OLD_DECODE)
        self.assertNotIn(DECODE, self.OLD_DECODE)

    def test_the_old_backup_redirection_is_caught(self):
        self.assertEqual(1, len(redirecting_pg_commands(self.OLD_BACKUP)))

    def test_a_wrapped_redirecting_span_is_caught(self):
        wrapped = "  `docker exec <container> pg_restore -U <user>\n  -d <db> < /tmp/senzing.dump`"
        self.assertEqual(1, len(redirecting_pg_commands(wrapped)))

    def test_the_old_restore_is_caught(self):
        self.assertIn("psql <", flat(self.OLD_RESTORE))

    def test_placeholders_alone_are_not_redirections(self):
        self.assertEqual([], redirecting_pg_commands("`pg_restore -U <user> -d <db> <file>`"))

    OLD_1C_BLOCK = ("```bash\n"
                    "python3 -m venv data/temp/recap-venv    # only if it does not exist yet\n"
                    "# Linux/macOS (add Pillow when it is missing):\n"
                    "data/temp/recap-venv/bin/python -m pip install imageio-ffmpeg\n"
                    "# Windows:\n"
                    "data\\temp\\recap-venv\\Scripts\\python -m pip install imageio-ffmpeg\n"
                    "```\n")
    OLD_1C_ITEM = ("1. Create `data/temp/recap-venv/` with `python3 -m venv data/temp/recap-venv` "
                   "if it does not exist.\n"
                   "2. Run **one** `python -m pip install` with the venv's Python.\n")

    def test_the_old_shared_venv_block_is_caught(self):
        self.assertEqual(1, len(unpaired_venvs(self.OLD_1C_BLOCK)))
        self.assertEqual(1, len(venv_blocks_out_of_layout(self.OLD_1C_BLOCK)))

    def test_a_windows_line_above_the_posix_comment_is_out_of_layout(self):
        shared = self.OLD_1C_BLOCK.replace(
            "# Linux/macOS", "py -3 -m venv data\\temp\\recap-venv    # only if it does not "
            "exist yet\n# Linux/macOS")
        self.assertEqual([], unpaired_venvs(shared))
        self.assertEqual(1, len(venv_blocks_out_of_layout(shared)))

    def test_the_old_list_item_is_caught(self):
        self.assertEqual([(1, "data/temp/recap-venv")], unpaired_venvs(self.OLD_1C_ITEM))

    def test_a_step_1c_block_without_the_disclosure_is_caught(self):
        step = step_1c(GRADUATION.read_text(encoding="utf-8"))
        wrapped = ("The Windows lines are written for PowerShell 5.1 and 7 but are unverified on "
                   "Windows: no test\nruns them there.")
        self.assertEqual(2, step.count(wrapped))
        self.assertEqual(1, len(venv_blocks_without_disclosure(step.replace(wrapped, "", 1))))

    def test_a_windows_form_in_another_block_is_not_paired(self):
        apart = self.OLD_1C_ITEM + "\nOn Windows, `py -3 -m venv data\\temp\\recap-venv`.\n"
        self.assertEqual(1, len(unpaired_venvs(apart)))
        fenced = "```\npython3 -m venv a/b\n```\n```\npy -3 -m venv a\\b\n```\n"
        self.assertEqual(1, len(unpaired_venvs(fenced)))

    def test_the_path_conversion_is_literal(self):
        self.assertEqual(1, len(unpaired_venvs("`python3 -m venv a/b` or `py -3 -m venv a/b`")))
        self.assertEqual(1, len(unpaired_venvs("`python3 -m venv a/b` or `py -3 -m venv a\\bc`")))
        self.assertEqual([], unpaired_venvs("`python3 -m venv a/b` or\n`py -3 -m venv a\\b`"))

    def test_a_blank_line_inside_a_fence_does_not_split_the_code_block(self):
        self.assertEqual([], unpaired_venvs("```\npython3 -m venv a/b\n\npy -3 -m venv a\\b\n```"))

    def test_the_old_packaged_restore_is_caught(self):
        old = ("a `pg_dump` file; restore it with `pg_restore` (or `psql <` for a plain dump) "
               "into a fresh database")
        self.assertIn("psql <", old)


if __name__ == "__main__":
    unittest.main()
