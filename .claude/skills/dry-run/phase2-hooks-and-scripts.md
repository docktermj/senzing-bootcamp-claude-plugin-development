# Phase 2 — Hooks and bundled scripts

Execute **every hook entry** in `plugins/senzing-bootcamp/hooks/hooks.json` and every
bundled script against a **realistic** bootcamp project. The realism is the whole point: an
empty directory exercises the gating branch and nothing else, and most of these scripts only
misbehave when the state they read is mid-flight.

⛔ **Iterate hook ENTRIES, not events — one event carries a second hook.** A reader who
walks the event names runs one script per event and never reaches the second entry under
`UserPromptSubmit`, which is `checkpoint-tick.py` — the script driving the durability
checkpoint the fold hooks depend on. This phase's whole value is executing *every* hook, and
under-covering it reports phase 2 complete having skipped one.

⛔ **Do not state a hook count in this file.** Ask the manifest, so the instruction cannot
disagree with it — a literal was wrong here for exactly as long as it took someone to add a
second `UserPromptSubmit` entry:

```bash
python3 -c "
import json
d = json.load(open('plugins/senzing-bootcamp/hooks/hooks.json'))['hooks']
n = 0
for event, groups in d.items():
    for group in groups:
        for hook in group['hooks']:
            n += 1
            print('%-18s %s' % (event, hook['command']))
print()
print('%d hook entries across %d events' % (n, len(d)))
"
```

Every line it prints is a script this phase must run.

## Build the project first

```bash
python3 .claude/skills/dry-run/scaffold_project.py "$HOME/senzing-bootcamp-dryrun"
```

The scaffold prints which fixture exercises which invariant **for the mode it built**, and
names the ones that mode omits. The list below is the default mid-bootcamp set, which is what
phase 2 wants — `--fresh` and `--seeded` create only the two config files plus the feedback
file, so they carry none of the recap/checkpoint/Markdown/records fixtures and their banners say
so. Use `--explain` (with `--fresh`/`--seeded` if you mean those) to see a mode's list without
writing anything. Each fixture is there because a naive one hid a defect:

- **A mid-module recap** with a completed section and all four subsections — an empty
  recap never exercises the parser.
- **An unfinalized `<!-- RECAP-CHECKPOINT -->` block** — the state the durability
  hooks produce and module-completion is supposed to clear (INV-059).
- **A feedback file with a precious entry** — graduation must never touch it (INV-067).
- **Deliberately messy Markdown** — the normalizer needs something to normalize.
- **A `docker_containers` list** naming a container that does not exist — the
  warn-and-continue path (INV-101).
- **Not the cover-chip clip.** The recap generator's cover chips clip at 46 characters,
  and the realistic scaffold sits *under* that threshold: its longest module title,
  "Data Quality, Mapping, and Transformation", is 41, and the parser strips the
  `— in progress` suffix before the chip is built. That under-threshold fixture is how a
  renderer crash hid, so the clip path is covered by unit test
  (`tests/test_recap_pdf_font_safety.py`), not by this walk.

## Order of operations

### 1. Hooks outside a bootcamp (the gating claim)

`hooks/README.md` claims every hook "no-ops unless a `config/bootcamp_progress.json`
file exists". Test that first, from a directory with no such file: every entry the command
above listed must exit 0 and emit nothing. A hook that fires in an unrelated session is a serious defect —
the plugin is installed globally.

### 2. Hooks inside the bootcamp

Feed each its real stdin shape (`{"prompt": …}` for `UserPromptSubmit`,
`{"tool_name","tool_input"}` for `PreToolUse`, `{"stop_hook_active","transcript_path"}`
for `Stop`) and assert on behavior, not just exit status:

- **write-gate** — must block `/tmp/…`, `~/Downloads/…`, `C:\Windows\Temp\…`, a
  relocated `%TEMP%`, a PEM key, an AWS key id and an `AQAAAD…` license blob, while
  **allowing** project-relative writes (INV-109, INV-001). Include a project whose
  own path contains `tmp` — it must not trip.
- **feedback-capture** — must inject guidance for a feedback prompt and stay
  **silent** on an unrelated one.
- **stop-nudge** — must stay silent when the transcript is unreadable *and* when
  `stop_hook_active` is true (INV-054: a missed nudge is far cheaper than a duplicate
  question), and must honor both documented opt-outs (INV-055).
- **The three fold hooks** — run `precompact-recap` **three times** and assert the
  recap has one checkpoint block, one section per module, and an untouched completed
  section. Idempotency is the invariant (INV-059); one run cannot show it.

### 3. Bundled scripts

Drive each and **inspect the artifact, not the exit code** (INV-129):

- `normalize_docs_markdown.py` — the feedback file must be **byte-identical** after
  (hash it before and after), and the recap's non-whitespace word count must not drop.
- `generate_recap_pdf.py` — check which renderer it reports. A `PDF generated:` line
  with `renderer: stdlib` when `fpdf2` is installed means something crashed the
  preferred path and was caught; that is a defect, not a fallback. Then `--check
  --expect-modules "…"` with **semicolons** (two module names contain commas).
- `generate_discoveries_pdf.py` — feed it junk and confirm it writes **no** PDF
  (INV-110).
- `capture_screenshots.py` — pass a tab that is not in the page; it must skip it with
  a message on stderr rather than saving the default tab under that name (INV-122),
  and name files by tab slug.
- `senzing_viz_server.py --no-serve --snapshot …` — without `libSz.so` it must fail
  loudly and write **no** snapshot; a blank page would satisfy the file-exists check
  while failing INV-077. ⛔ **TWO gates fail this way and they are not interchangeable —
  read the exit code, not just "it failed and wrote nothing".**
  - **exit 2** — the config-completeness pre-flight rejected `engine_config.json`
    (`PIPELINE` missing `CONFIGPATH`/`RESOURCEPATH`/`SUPPORTPATH`). The SDK was never
    touched. `config/engine_config_incomplete.json` is the fixture for this gate.
  - **exit 1** — the pre-flight passed and the SDK could not be loaded
    (`failed to load the Senzing library` / `libSz.so: cannot open shared object file`).
    This is the gate this bullet is about, and `config/engine_config.json` is the fixture
    that reaches it.

  ⚠️ Reporting the SDK branch as checked after hitting the config branch is not
  hypothetical: until 2026-09-02 the scaffold shipped `{"PIPELINE": {}}`, so **every**
  prior phase-2 run that listed this as verified had exercised the config gate instead.
  It went unnoticed because those runs had no `libSz.so` either, which makes the two
  outcomes indistinguishable unless the exit code is read
  (`specs/scaffold-engine-config-never-reaches-the-sdk-path.md`).
- `brand_tokens.color_for_sources()` — pass sources that are **not** the Truth Set's
  names, which is every real bootcamper's case (INV-127). Assert distinct encodings,
  including more sources than palette entries (it must vary a second channel, not
  reuse a color), and that the result is order-independent.

## Interpreting a caught exception

Several scripts catch broadly and degrade on purpose — that is INV-066/INV-111
behavior and it is correct. The trap is that **a correct fallback hides an incorrect
cause**. When you see a fallback message, ask why the preferred path failed rather
than accepting the degradation. The `_clip` ellipsis defect was found exactly this
way: the renderer reported its own failure honestly, and the reported *reason* was
the bug.

## Do not

⛔ Trust `grep -c` on a restored file without clearing `__pycache__` first — see the
SKILL's absolute rules.

⛔ Leave the scratch project behind. `rm -rf "$HOME/senzing-bootcamp-dryrun"`.
