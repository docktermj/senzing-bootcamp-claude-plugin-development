"""Every hook entry names a script, and the configured command runs it rather than its payload.

A bootcamper on plugin 0.5.1 saw this repeatedly in Module 1, non-blocking:

    Stop hook error: Failed with non-blocking status code: Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    NameError: name 'false' is not defined. Did you mean: 'False'?

Three facts compose into it: `python3` with **no script argument** reads its program from stdin; a
`type: command` hook's stdin is the event payload JSON; and a Stop payload carries
`stop_hook_active`, whose value is the JSON literal `false` — not a Python name. So the failing
process was the interpreter with the script path missing, parsing the payload it was handed as
source code. `stop-nudge.py` never ran, which is the invisible half: whatever the Stop hook was
for, it did not happen.

**Resolved 2026-08-21 (`/dry-run` phase 2): `args` is not part of the `type: command` schema, so the
launch was never going to work.** Anthropic's own `plugin-dev` plugin documents a command hook as
"Execute bash commands" with the script inside `command`
(`plugin-dev/skills/hook-development/SKILL.md:44-51`), and `args` appears nowhere in that skill.
Across seventeen `hooks.json` files in the official marketplaces, none uses `args` — including the
`every-marketplace` fixture that enumerates 15 events and every hook variant, and
`security-guidance`, which passes a second argument *inside* the command string. Every `"args"` key
on that machine belongs to an `.mcp.json`, where it genuinely is the schema. `hooks.json` now puts
each script inside `command`, quoted so a `${CLAUDE_PLUGIN_ROOT}` containing a space survives.

⛔ **What this file still does NOT test.** Claude Code has not been observed firing these hooks — that
needs the plugin in `enabledPlugins` and a live session. Windows is unverified from a Linux suite.
What IS guarded: the config regressions that would make the defect reachable again — an entry naming
a bare interpreter with no script, a script path that does not resolve, a script the interpreter
cannot run, and a **reintroduced `args` array**, which would silently move the script back out of the
channel the host reads.

This file is INV-052's named enforcer: it pins the corrected `command`-string form that invariant
now requires, and fails if an entry moves a script back into `args`.

⚠️ **Two of these tests were vacuous for one commit** and it is worth knowing why: they keyed off
`resolved_args()`, so moving the script into `command` emptied their input and they passed while
asserting nothing (the tell was a 0.000s run that spawned no subprocess). A guard that reads the
shape it was written against, rather than the shape in the file, certifies whatever it finds.

No phrase-level pattern (#438): its line reads are of a subprocess's stderr, as #424 recorded
(INV-346).

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"

# Bare interpreters: naming one in `command` with no script is the defect's precondition.
INTERPRETERS = {
    "python", "python3", "py", "node", "deno", "bun", "ruby", "perl",
    "sh", "bash", "zsh", "dash", "pwsh", "powershell",
}


def hook_entries():
    """(event, entry) for every hook declaration, derived from the file.

    ⛔ Derived, never listed: a hardcoded event list certifies the hooks someone remembered and is
    blind to the next one added, which is the only one that matters (INV-246).
    """
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    table = data.get("hooks", data)
    out = []
    for event, entries in table.items():
        for entry in (entries if isinstance(entries, list) else [entries]):
            if not isinstance(entry, dict):
                continue
            for hook in (entry.get("hooks") or [entry]):
                if isinstance(hook, dict):
                    out.append((event, hook))
    return out


def _expand(text):
    root = str(PLUGIN)
    return text.replace("${CLAUDE_PLUGIN_ROOT}", root).replace("$CLAUDE_PLUGIN_ROOT", root)


def resolved_args(hook):
    return [_expand(a) for a in (hook.get("args") or [])]


def resolved_command(hook):
    """The command string as the host would run it, with the plugin root expanded."""
    return _expand((hook.get("command") or "").strip())


def script_paths(hook):
    """Every script path the entry names, from EITHER channel.

    ⛔ Read both, always. Keying only on `args` is what made two tests here vacuous the moment the
    scripts moved into `command`: the input went empty and the assertions passed on nothing.
    """
    found = []
    for token in shlex.split(resolved_command(hook)) + resolved_args(hook):
        if token.endswith((".py", ".js", ".sh", ".mjs")):
            found.append(token)
    return found


class TheScanReachesTheHooks(unittest.TestCase):
    def test_hooks_json_parses_and_declares_hooks(self):
        self.assertTrue(HOOKS_JSON.is_file(), "hooks.json is missing: %s" % HOOKS_JSON)
        entries = hook_entries()
        self.assertGreaterEqual(
            len(entries), 5,
            "only %d hook entries found; the scan is near-vacuous and would pass while the file "
            "was gutted" % len(entries))


class NoEntryNamesAnInterpreterWithNoScript(unittest.TestCase):
    """The defect's precondition, made unreachable by construction."""

    def test_every_interpreter_command_carries_a_script_argument(self):
        offenders = []
        for event, hook in hook_entries():
            command = (hook.get("command") or "").strip()
            if not command:
                continue
            base = os.path.basename(command).lower()
            if base not in INTERPRETERS:
                continue          # the script path is inside `command`; nothing to drop
            if not resolved_args(hook):
                offenders.append("%s: command=%r with no args" % (event, command))
        self.assertEqual(
            [], offenders,
            "a hook names a bare interpreter and no script. The interpreter then reads its program "
            "from stdin — which for a hook is the event payload — and a payload's JSON `false` is "
            "not a Python name. That is the 2026-08-17 Stop-hook traceback, and the script never "
            "runs:\n  %s" % "\n  ".join(offenders))

    def test_every_named_script_exists(self):
        missing = []
        named = 0
        for event, hook in hook_entries():
            for path in script_paths(hook):
                named += 1
                if not Path(path).is_file():
                    missing.append("%s: %s" % (event, path))
        self.assertEqual([], missing,
                         "a hook names a script that does not exist, so the interpreter would "
                         "fail at launch:\n  %s" % "\n  ".join(missing))
        # Anti-vacuity: this test passed on an empty input set for one commit.
        self.assertGreaterEqual(named, 5,
                                "only %d script paths found across all hook entries; the scan is "
                                "vacuous and would pass while naming nothing" % named)

    def test_no_entry_relies_on_an_args_array(self):
        """`args` is not in the `type: command` schema — a hook using it runs a bare interpreter.

        Anthropic's `plugin-dev/skills/hook-development/SKILL.md` documents a command hook as a
        shell command string and never mentions `args`; no official plugin uses it. An entry that
        puts the script there launches `python3` with nothing to run, which then reads the event
        payload as its program — the 2026-08-17 bootcamper defect, silent on six of seven events.
        """
        offenders = ["%s: args=%r" % (event, hook["args"])
                     for event, hook in hook_entries() if hook.get("args")]
        self.assertEqual(
            [], offenders,
            "a hook entry carries an `args` array. The host reads `command` as a shell string and "
            "ignores `args`, so the script never runs and the interpreter parses the payload "
            "instead. Put the script inside `command`, quoted:\n  %s" % "\n  ".join(offenders))


class TheConfiguredCommandRunsTheScript(unittest.TestCase):
    """Behavioral, not structural — and narrower than it looks; see the module docstring.

    Launches each hook exactly as configured, with a payload containing the JSON literal `false`,
    and asserts the interpreter did not parse that payload as source. This cannot fail from the
    host dropping an argument (the test supplies them), and it is not written as though it could.
    It fails when a script has a syntax error, an unresolvable path, or an interpreter that is not
    installed — the config regressions that would make the original defect reachable.
    """

    def test_no_hook_parses_its_payload_as_source(self):
        offenders = []
        launched = 0
        for event, hook in hook_entries():
            command = resolved_command(hook)
            args = resolved_args(hook)
            if not command:
                continue
            payload = json.dumps({
                "session_id": "test",
                "transcript_path": "/nonexistent/transcript.jsonl",
                "hook_event_name": event,
                # A JSON literal that is not a Python name — the tell for the whole defect.
                "stop_hook_active": False,
            })
            # A temp cwd with no config/bootcamp_progress.json, so every script takes its
            # "not a bootcamp — never touch unrelated projects" path and writes nothing.
            with tempfile.TemporaryDirectory() as cwd:
                try:
                    # Launched the way the host does: `command` as a shell string. `args` is
                    # appended only so a regression that puts the script back there is still
                    # exercised rather than skipped — it must not be how the script is found.
                    proc = subprocess.run(
                        " ".join([command] + [shlex.quote(a) for a in args]),
                        shell=True, input=payload, capture_output=True,
                        text=True, cwd=cwd, timeout=30)
                    launched += 1
                except subprocess.TimeoutExpired:
                    offenders.append("%s: %r did not exit within 30s" % (event, command))
                    continue
            if 'File "<stdin>"' in proc.stderr:
                offenders.append("%s: parsed its PAYLOAD as source — %s"
                                 % (event, proc.stderr.strip().splitlines()[-1]))
            elif proc.returncode not in (0, 2):
                offenders.append("%s: exited %d — %s"
                                 % (event, proc.returncode, proc.stderr.strip()[:160]))
        self.assertEqual(
            [], offenders,
            "a hook did not run its script cleanly when launched exactly as configured:\n  %s"
            % "\n  ".join(offenders))
        # Anti-vacuity: this test skipped every hook for one commit, passing in 0.000s.
        self.assertGreaterEqual(launched, 5,
                                "only %d hooks were actually launched; the behavioral test is "
                                "vacuous" % launched)


if __name__ == "__main__":
    unittest.main()
