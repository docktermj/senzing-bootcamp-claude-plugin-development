"""The maintainer operation set, derived in one place: every skill plus any command.

`/<name>` runs the project skill when a skill and a command share a name, with or without an
argument (measured 2026-09-29 on Claude Code 2.1.284, #241). So the maintainer surface is the
skills under `.claude/skills/`, together with any command under `.claude/commands/`, and #262
deleted the ten same-name command files that never ran. INV-302 (as narrowed 2026-09-30)
compares that set with `docs/development.md`, INV-316 (its 2026-09-30 note) resolves a name
against it and requires the register to list it, and INV-318 and INV-319 read "maintainer
command" as "command or skill".

⛔ **(INV-300) The "commands or skills" reading lives here once.** Every guard that asks "which
maintainer operations ship?" imports `operations()` rather than globbing a directory of its
own. A second copy of the reading is how one guard kept `.claude/commands/` as the whole
surface after the others moved on: while commands shipped the two readings agreed, and the
day the last command went, a guard globbing only `.claude/commands/` would have compared the
documentation with an empty set.

⚠️ **An operation is a name, not a file.** A skill is a directory holding a `SKILL.md`, since a
directory without one is not a skill (INV-302). A command is a `.md` file directly under
`.claude/commands/`. The directory may be absent altogether, which is the state #262 leaves,
and `commands()` then returns an empty set rather than raising.

⚠️ **INV-303 still binds any command added later**, an alias included, so its enforcer needs
commands to read when none ship. `command_files_under_test()` returns the shipped command files
when there are any, and otherwise the fixture commands under
`tests/fixtures/maintainer-commands/`, so that enforcer never passes over an empty set
(INV-265).

What a green run of a guard built on this means: the names on disk and the names in a
document agree. It does not establish that `/<name>` runs the skill on any given Claude Code
version; that is the #241 measurement, recorded on the issue and in the ledger.

Stdlib only; the directories are listed and nothing is imported (INV-108).

Source issue: #262.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = REPO_ROOT / ".claude"
COMMANDS_DIR = CLAUDE_DIR / "commands"
SKILLS_DIR = CLAUDE_DIR / "skills"
OVERLAYS_DIR = CLAUDE_DIR / "skill-overlays"

#: Commands the INV-303 enforcer reads when no command ships. Each names a real skill.
FIXTURE_COMMANDS_DIR = REPO_ROOT / "tests" / "fixtures" / "maintainer-commands"


def skills(skills_dir=SKILLS_DIR):
    """Names of the skills under `skills_dir`: directories holding a `SKILL.md`."""
    if not skills_dir.is_dir():
        return set()
    return {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}


def command_files(commands_dir=COMMANDS_DIR):
    """The command files directly under `commands_dir`, sorted; empty when it is absent."""
    if not commands_dir.is_dir():
        return []
    return sorted(p for p in commands_dir.glob("*.md") if p.is_file())


def commands(commands_dir=COMMANDS_DIR):
    """Names of the commands under `commands_dir`: the stems of its `.md` files."""
    return {p.stem for p in command_files(commands_dir)}


def operations(commands_dir=COMMANDS_DIR, skills_dir=SKILLS_DIR):
    """⛔ The maintainer operation set: every skill, together with any command."""
    return skills(skills_dir) | commands(commands_dir)


def ships(name, commands_dir=COMMANDS_DIR, skills_dir=SKILLS_DIR):
    """Whether `name` (a leading slash is ignored) is a shipped command or skill."""
    return name.lstrip("/") in operations(commands_dir, skills_dir)


def skill_file(name, skills_dir=SKILLS_DIR):
    """The `SKILL.md` that defines the operation `name`."""
    return skills_dir / name / "SKILL.md"


def command_files_under_test(commands_dir=COMMANDS_DIR, fixtures_dir=FIXTURE_COMMANDS_DIR):
    """(where, files) for the INV-303 enforcer: shipped commands, or the fixtures if none ship."""
    shipped = command_files(commands_dir)
    if shipped:
        return commands_dir, shipped
    return fixtures_dir, command_files(fixtures_dir)
