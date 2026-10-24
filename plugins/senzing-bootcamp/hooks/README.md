# Bootcamp hooks

The plugin ships these hooks (registered in `hooks.json`). Following the bootcamp
convention, each hook's purpose is phrased beginning with the word "to", from the
bootcamper's point of view. In the Kiro Power these were named hook files
(e.g. "to review what you said"); in the Claude plugin they are `command`-type
hooks wired to small **Python** scripts under `../scripts/`, each invoked by a
`command` string naming the interpreter and the script, quoted
(`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py"`).

Every hook is gated, so the plugin never alters unrelated Claude Code sessions: each
script no-ops unless a `config/bootcamp_progress.json` file exists in the working
directory. The Gate column below says what each one tests beyond that, and the two gates
answer different questions:

- **`bootcamp_active()`** (in `scripts/recap_checkpoint.py`) asks *is a bootcamp in
  progress?* It is true only when the progress file **records a module**, the same rule
  session start uses (`../skills/bootcamp-onboarding/SKILL.md` → "Fresh start vs. resume —
  decided by the progress file's CONTENT, not its existence", INV-227). The four recap hooks
  use it, so they stay silent while the file exists but records no module.
- **Existence** asks *is this a bootcamp project?* The onboarding preface creates the file
  empty, and nothing records a module until Bootcamp preparation's final consolidated write.
  The preface and every preparation gate still ask pinned 👉 questions, write project files
  and take feedback, so the three hooks that serve them gate on existence on purpose, not on
  `bootcamp_active()` (INV-227, INV-010).

| Event | Script | Purpose | Gate |
|-------|--------|---------|------|
| `SessionStart` | `scripts/session-start.py` | to resume an in-progress bootcamp (offers to continue from the last recorded module, and folds any in-progress recap checkpoint into the recap). | `bootcamp_active()`: a resume needs a recorded module. |
| `UserPromptSubmit` | `scripts/feedback-capture.py` | to capture bootcamp feedback, bootcamper notes and verbosity changes at any time (routes "bootcamp feedback", "make a note" and "change verbosity" requests to the right workflow). | Existence: feedback (INV-010), notes (INV-254) and verbosity changes (INV-011) are taken from onboarding on, before any module is recorded. |
| `UserPromptSubmit` | `scripts/checkpoint-tick.py` | to keep the in-progress recap checkpoint durable (creates `docs/progress/recap_checkpoint.md` as an empty scaffold within a turn of the bootcamp starting, and reminds the guide once to keep it current). Runs per turn because a bootcamp becomes active *after* `SessionStart` has already run; silent on every turn after the file exists. | `bootcamp_active()`: there is no module recap to keep before a module is recorded. |
| `PreToolUse` (Write, Edit) | `scripts/write-gate.py` | to keep your files in the project (blocks writes whose resolved target is outside the project — system temp and Downloads get a more specific message — and obvious hardcoded secrets, during a bootcamp). | Existence: the onboarding preface and Bootcamp preparation write project files before any module is recorded, and those writes must stay in the project too. |
| `Stop` | `scripts/stop-nudge.py` | to review what you said and end each turn with one leading question (a loop-safe safety net for the closing 👉 question). | Existence: the preface and every Bootcamp preparation gate end on a pinned 👉 question before any module is recorded. |
| `PreCompact` | `scripts/precompact-recap.py` | to preserve your in-progress recap before the conversation is compacted (folds the module recap checkpoint into the recap). | `bootcamp_active()`: there is no module recap to fold before a module is recorded. |
| `SessionEnd` | `scripts/session-end.py` | to preserve your in-progress recap and stop the bootcamp's containers when the session ends (folds the module recap checkpoint into the recap, then stops each container the bootcamp started with the runtime CLI recorded for it, `<runtime> stop`, never removing it, so it can be restarted on resume; INV-101). | `bootcamp_active()`: there is no module recap to fold before a module is recorded. |

**Convention (INV-016 interpretation):** the "begin with the word 'to'" rule applies
to each hook's **documented purpose** — the Purpose column above — not to the runtime
text a hook emits (block reasons, injected context, resume notes), which is written
for clarity and is delivered to Claude rather than shown directly to the bootcamper.
Every hook MUST carry a "to …" purpose entry in this table, and new hooks follow the
same rule. This is the settled reading of INV-016 (whose own examples — "to process
your request", "to review what you said" — are purposes), resolving the earlier
ambiguity between the purpose-phrasing and emitted-message readings.

## Runtime prerequisites (per platform)

The hooks are **Python 3** scripts, invoked as `type: command` hooks whose `command`
string names both the interpreter and the script, with the plugin root **quoted**
(`{"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/<hook>.py\""}`). The quoting is
what keeps a plugin root containing a space working.

> ⚠️ **Corrected 2026-08-21.** This section previously described an *exec form*
> (`{"command": "python3", "args": [...]}`) and claimed it spawned the interpreter with
> no shell on any platform. That was wrong: `args` is not part of the `type: command`
> schema, so every hook launched a bare `python3`, which read the event payload as its
> program and never ran the script. A command hook is a shell command string by design,
> so there is no shell-free form to prefer. INV-052 carries the corrected form.

The only requirement is a `python3` on `PATH`, and it is **not a new dependency** —
the bootcamp already requires `python3` for the graduation recap PDF
(`scripts/generate_recap_pdf.py`, always run at graduation) and, when the chosen language is
Python, the Truth Set visualization server (`scripts/senzing_viz_server.py`, the reference per
INV-090), so any machine that can run the bootcamp can run the hooks.

| Platform | Requirement | Notes |
|----------|-------------|-------|
| Linux | `python3` on `PATH` | Already required by the bootcamp. |
| macOS | `python3` on `PATH` | Already required by the bootcamp. The per-user temp dir under `$TMPDIR` is handled by the write-gate. |
| Windows | `python3` on `PATH` | The command name must be `python3` (the name the rest of the plugin already uses); if only `python`/`py` is installed, add a `python3` entry to `PATH`. |

Environment-variable substitution (`${CLAUDE_PLUGIN_ROOT}`) is performed by Claude
Code identically on all three platforms. Keep it quoted inside the `command` string:
the expanded path can contain a space, and unquoted it would split into two arguments.

## Design notes

- **Deterministic gates, not model judgment.** The `Stop` and `PreToolUse` hooks
  are `command` scripts that decide behavior from the on-disk progress file's
  existence (the Gate column above), so they never fire in non-bootcamp sessions.
- **Non-blocking by default.** The write-gate can block a tool call (exit 2), and only
  for a target outside the project or an obvious secret, during a bootcamp. The `Stop` hook can block a turn
  from ending (`decision: block`) to request the one forgotten closing 👉 question, but
  only once: it returns success whenever `stop_hook_active` is true, so it can never loop
  on its own continuation, and it stays silent when the session is not a bootcamp, when
  the nudge is disabled (see [Disabling / quieting the Stop-hook nudge](#disabling--quieting-the-stop-hook-nudge)),
  or when the current turn already ends with a 👉 question. Detection scans the whole
  current turn and biases toward silence if the turn's text is not yet on disk, and the
  block reason tells the model to repeat nothing it has already asked — so a false block
  can never surface as a duplicate question. The `UserPromptSubmit` hook injects guidance via
  `additionalContext`; `SessionStart` emits resume context. Everything else emits nothing.
- **Hooks ship with the plugin.** There is no hook-install step (this replaces the
  Kiro `install_hooks.py` / `.kiro/hooks/` workflow).
- **Recap durability.** The recap (`docs/bootcamp_recap.md`) is finalized per
  module at completion, but an interrupted module (quit / compaction / new session) would
  otherwise lose its in-progress narrative. To close that gap the guide keeps an
  in-progress checkpoint at `docs/progress/recap_checkpoint.md` (refreshed at each step
  boundary, wrapped in `<!-- RECAP-CHECKPOINT:START -->` … `<!-- RECAP-CHECKPOINT:END -->`
  markers), and three hooks — `PreCompact`, `SessionEnd`, and `SessionStart` — fold it into
  `docs/bootcamp_recap.md`. The fold (in the shared, non-hook helper
  `scripts/recap_checkpoint.py`) is deterministic, idempotent, and append-only with respect
  to completed `## {module}` sections: it only ever replaces the marker-fenced block, so
  repeated folds never duplicate and a finalized section is never rewritten. Module
  completion appends the final section and clears the checkpoint.

## Disabling / quieting the Stop-hook nudge

The `Stop` hook (`scripts/stop-nudge.py`) is a safety net for the single closing
👉 question. It stays silent whenever the current turn already ends with a 👉
question, and it biases toward silence when the transcript cannot be read
decisively — a missed nudge is far cheaper than a duplicated question. If you still
want to turn it off, there are two documented, opt-out switches (either one works;
both are read cross-platform with no shell and no extra dependency):

| Switch | Where | Effect |
|--------|-------|--------|
| `SENZING_BOOTCAMP_DISABLE_STOP_NUDGE` | environment variable | Set to `1`/`true`/`yes`/`on` to disable the nudge for the session. |
| `disable_stop_nudge: true` | top-level key in `config/bootcamp_preferences.yaml` | Disables the nudge for the project. |

When either switch is on, the hook returns success immediately (exit 0, no block),
so a turn can never be re-opened to re-ask a closing question. Remove the env var or
set `disable_stop_nudge: false` to re-enable it.

## Administrative write noise (no harness suppression)

Every `Write`/`Edit` tool result renders its file content or diff inline in the
transcript — including the small administrative config writes the bootcamp makes
(`config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`). In a
prose-driven guided experience this is visual noise, and it runs against the spirit of
INV-012 (output that is not important to the bootcamper is suppressed).

A `claude-code-guide` investigation (2026-07-16) confirmed that **no harness mechanism
suppresses this today** — there is no `settings.json` setting, no output style, no
environment variable, no Claude Code CLI flag, and no keyboard shortcut that collapses or hides
Write/Edit tool-result output. Rendering is controlled by the harness, not the plugin,
so full suppression is **not achievable from the plugin**.

The one controllable lever is write **frequency and size**, so the plugin minimizes
administrative writes rather than trying to hide them:

- Progress/preference writes are **batched to step and module boundaries**, not made on
  every sub-step (`../skills/bootcamp-onboarding/ground-rules.md` → "Progress and state").
- The **Bootcamp preparation** module collects every setup choice (path, module selection,
  verbosity, programming language, detected platform/name, git status) and
  persists them in **one** consolidated write at the end, instead of one write per gate
  (there is no `model_guidance` key — that preference was retired by INV-137)
  (`../skills/bootcamp-preparation/SKILL.md` → Step 6). The onboarding preface itself writes
  **no** preferences at all (`../skills/bootcamp-onboarding/onboarding-flow.md` → step 4).
- Module completion applies its progress update as a **single** batched write
  (`../skills/bootcamp-onboarding/module-completion.md` → Step 1).
- Config files are kept small, and minimal edits are preferred over full-file rewrites.

If a harness-level way to collapse Write/Edit output would help, file a Claude Code
feature request via `/feedback` in the Claude Code CLI or at <https://claude.com/feedback>. This
finding is recorded here so it is not re-investigated.
