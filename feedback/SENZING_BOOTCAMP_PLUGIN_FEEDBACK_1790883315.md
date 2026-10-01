# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp.

**Started:** 2026-01-01

## Your Feedback

## Improvement: A precious entry that must survive graduation untouched

**Date:** 2026-01-01
**Module:** Data collection
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the banner did not appear
**Upstream:** not applicable

### What happened

If graduation's normalization pass rewrites, empties or deletes this file, INV-067 is
broken and this sentence will be missing.

## Improvement: SDK setup never records database_type, so every later SQLite check runs on a fallback

**Date:** 2026-10-01
**Module:** SDK setup
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the recording rule sits after the PostgreSQL branch, so the SQLite path skips it
**Upstream:** not applicable

### What happened

SQLite was chosen in SDK setup, but `database_type` never reached `config/bootcamp_preferences.yaml`. Data collection's load-time check, Data processing's loader concurrency and SQLite heads-up, and graduation's pre-check all found it absent and fell back.

### Why it matters

The fallbacks happened to be right for SQLite. A PostgreSQL bootcamper with the same gap would get a serialized loader and SQLite warnings without being told why.

### Suggested fix

Record `database_type` before the engine branch in SDK setup Step 7, so both paths write it.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** sdk_setup / 7
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** SDK setup Step 7; Data collection Step 8b; Data processing Phase A step 3
- **Observed problem:** database_type absent in preferences
- **Expected behavior:** SDK setup Step 7 writes database_type
- **Divergence:** the write sits on the PostgreSQL path only

## Improvement: The project environment script refuses to run until a file only Step 8 writes exists

**Date:** 2026-10-01
**Module:** SDK setup
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the guard checks for config/engine_config.json, which SDK setup creates later
**Upstream:** not applicable

### What happened

`src/scripts/senzing-env.sh` exits with a path-resolution error unless `config/engine_config.json` exists, but SDK setup only writes that file at Step 8, after earlier steps already need the environment.

### Why it matters

The error says 'path-resolution fault', which sends the reader looking at the wrong problem at the start of setup.

### Suggested fix

Guard only the configuration export on the file's presence, and let PYTHONPATH/LD_LIBRARY_PATH export before it exists.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** sdk_setup / 5
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** SDK setup environment script
- **Observed problem:** env script refuses to load
- **Expected behavior:** env script usable from the first SDK step
- **Divergence:** guard requires a file written later

## Improvement: Senzing's initialization anti-pattern article says SQLite is auto-created; on SDK 4.4.2 it is not

**Date:** 2026-10-01
**Module:** SDK setup
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** mcp-server — the article contradicts sdk_guide and the measured SDK; nothing in the bootcamp needs to change
**Upstream:** submission blocked: maintainer /dry-run session (no-send rule; the bootcamper's yes was not acted on)

### What happened

The `search_docs` anti-pattern article 'Database Initialization and Container Setup' says the SDK creates and populates the SQLite file during config registration. On SDK 4.4.2 config seeding against a path with no file failed with SENZ1001 and created nothing; it worked once the schema was applied, exactly as `sdk_guide`'s notes say.

### Why it matters

Two routes on the same server give opposite instructions; a guide that follows the article skips the schema step and hits SENZ1001.

### Suggested fix

Correct the article's SQLite note to match sdk_guide.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** sdk_setup / 7
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** search_docs anti_patterns vs sdk_guide engine_config_notes
- **Observed problem:** SENZ1001 with no schema
- **Expected behavior:** SQLite auto-created per the article
- **Divergence:** the SDK does not auto-create it

## Improvement: The results app's relationship-mode note reports the capped subset as the whole population

**Date:** 2026-10-01
**Module:** Query, Visualize and Discover
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the note in senzing_viz_server.py counts linked nodes inside the 1,500-node cap
**Upstream:** not applicable

### What happened

On 7,084 customers the Entity Graph said 'Showing the 286 entities that have relationships, of 7084 total ... Uncheck the toggle to show them all', while at least 4,551 customers have a link and unchecking shows 1,500.

### Why it matters

The sentence is in a recap screenshot the bootcamper is encouraged to share, understating the links about 16 times.

### Suggested fix

Name both numbers when the graph is capped, and do not say 'all' when the cap applies.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3c
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** Module 7 step 3c, bundled visualization server
- **Observed problem:** note understates linked customers
- **Expected behavior:** note describes the shown subset as a subset
- **Divergence:** nodeCount is counted after capping

## Improvement: Module 5 puts sample files in data/senzing-ready/, which Module 6 counts as loadable

**Date:** 2026-10-01
**Module:** Data Quality, Mapping, and Transformation
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — two modules disagree on what data/senzing-ready/ holds
**Upstream:** not applicable

### What happened

Each source's `_sample.jsonl` sits beside its full output, so 'every file there' totals 10,045 rather than 10,000, and Module 5's own mapper-doc gate asks for a document per sample file.

### Why it matters

The double count can push a load across the SQLite heads-up threshold, and the gate cannot be met literally.

### Suggested fix

Write samples elsewhere, or define both checks from each source's registry file_path.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** data_processing / Phase A
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** Module 5 step 18; Module 6 Phase A item 1
- **Observed problem:** loadable total includes samples
- **Expected behavior:** loadable total = mapped outputs
- **Divergence:** samples share the directory

## Improvement: The generated scenario gives different invented people the same name and email

**Date:** 2026-10-01
**Module:** Data collection
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the synthesis guidance does not ask for identifiers that are unique per person
**Upstream:** not applicable

### What happened

The Harborline generator built emails from first name, last name and a number 1-99, so 53 pairs of different invented people share name and email; Senzing merged them on that evidence, and they show up as false merges in validation and in the how-analysis example.

### Why it matters

It makes a correct engine look wrong in the bootcamper's own accuracy figures and keepsake.

### Suggested fix

Ask generated scenarios to make each person's email and phone unique unless a shared one is deliberate.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** data_collection / 2
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** Data collection Step 2 generator
- **Observed problem:** 53 false merges from identifier collisions
- **Expected behavior:** distinct people get distinct identifiers
- **Divergence:** the generator reused identifiers

## Improvement: Module 7 forbids a CDN fallback that INV-091 and the bundled server both require

**Date:** 2026-10-01
**Module:** Query, Visualize and Discover
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the step, the invariant and the reference server disagree
**Upstream:** not applicable

### What happened

Step 3c says to keep the refusal-to-render when D3 is missing; the bundled server instead emits a d3js.org script tag, as INV-091 prescribes.

### Why it matters

The step cannot be followed while copying the reference it points to, and a silent CDN fetch defeats the offline guarantee.

### Suggested fix

Pick one behavior (refusal matches the offline rationale) and align the invariant, the server and the step.

### Context when reported

- **Time:** 2026-10-01 13:59
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3c
- **Recent questions:** What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** a display name
- **Behind the scenes:** Module 7 step 3c
- **Observed problem:** contradictory D3 rule
- **Expected behavior:** one rule
- **Divergence:** three sources disagree

## Improvement: Tell the bootcamper what to install so the graduation video has audio

**Date:** 2026-10-01
**Module:** Bootcamp graduation
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the renderer knows which speech engine each platform needs, but graduation never tells the bootcamper; a perfect MCP server would not change that
**Upstream:** not applicable

### What happened

The graduation video came out with no audio because the speech software was not installed, and nothing said so; I had to ask why there was no sound.

### Why it matters

The video should be a shareable keepsake, and silence looks broken.

### Suggested fix

Let the bootcamper know what needs to be installed for the video to have audio, with different information for Mac, Linux and Windows, and hints on how to install it (for example with apt or brew).

### Context when reported

- **Time:** 2026-10-01 14:16
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** graduation / closing
- **Recent questions:** Is there anything else you would like to explore?; Why does it matter to you?; What priority would you give this?
- **Bootcamper responses:** "What is the full path to the mp4 file?"; "Why is there no sound in the audio?"; the keepsake reason above; 1 (High)
- **Behind the scenes:** graduation Step 1c rendered docs/bootcamp_recap.mp4 with generate_recap_video.py; it reported "Audio track: no (captions carry the narration)"; no say, System.Speech, espeak-ng or espeak on this machine
- **Observed problem:** a 2:00 video with captions and no audio stream, and no explanation until asked
- **Expected behavior:** when the renderer reports no audio, graduation names the missing engine for this platform, how to install it, and how to re-render from the kept storyboard
- **Divergence:** Step 1c treats "Audio track: no" as not a failure and gives the guide nothing to tell the bootcamper

## Improvement: Add light, upbeat background music to the graduation video

**Date:** 2026-10-01
**Module:** Bootcamp graduation
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the bundled video renderer mixes narration only and ships no music; a perfect MCP server would not change that
**Upstream:** not applicable

### What happened

The graduation video's audio has no background music.

### Why it matters

It gives the video a better "feeling".

### Suggested fix

In the video's audio, there should be some light, but upbeat music.

### Context when reported

- **Time:** 2026-10-01 14:17
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** graduation / closing
- **Recent questions:** Is there anything else you would like to explore?; Why does it matter to you?; What priority would you give this?
- **Bootcamper responses:** the music request; the "feeling" reason above; 2 (Medium)
- **Behind the scenes:** graduation Step 1c; generate_recap_video.py renders narration audio only when a speech engine exists and has no music track or storyboard field for one
- **Observed problem:** a video with no music bed
- **Expected behavior:** a keepsake video with a light music bed under the narration
- **Divergence:** the renderer and storyboard schema have no music support

## Improvement: Make the graduation video's voice-over sound professional, not robotic

**Date:** 2026-10-01
**Module:** Bootcamp graduation
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — on Linux the bundled video renderer uses only espeak, a basic synthesizer; a perfect MCP server would not change that
**Upstream:** not applicable

### What happened

After espeak-ng was installed and the video was re-rendered, the narration played, but it sounds too robotic.

### Why it matters

Currently it sounds unprofessional.

### Suggested fix

Learn from the senzing-claude-video project, which has a better audio track: a natural-sounding neural voice (Piper) running locally, per-line pronunciation and speed tuning, a loudness-normalized stereo mix, and a synthesized music bed lowered under the voice.

### Context when reported

- **Time:** 2026-10-01 14:34
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** graduation / closing
- **Recent questions:** Why does it matter to you?; Do you have a suggested fix?; What priority would you give this?
- **Bootcamper responses:** "Currently it sounds unprofessional."; the senzing-claude-video suggestion; 1 (High)
- **Behind the scenes:** docs/bootcamp_recap.mp4 re-rendered with the espeak-ng voice-over (18 of 18 scenes, 2:02, mono AAC 44.1 kHz)
- **Observed problem:** a mechanical-sounding voice in a keepsake video
- **Expected behavior:** a natural-sounding narration suitable for sharing
- **Divergence:** the renderer's Linux speech engines are espeak-ng and espeak only

## Improvement: Build the accepted Piper voice-over and music bed into the graduation video

**Date:** 2026-10-01
**Module:** Bootcamp graduation
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the bundled video renderer needs a Piper voice engine, a music bed and a loudness-normalized mix; a perfect MCP server would not change that
**Upstream:** not applicable

### What happened

The graduation video was re-voiced with a local Piper neural voice (en_US-ryan-high) and an original synthesized music bed, ducked under the voice and normalized to about -16 LUFS. That version of the mp4 is acceptable.

### Why it matters

The video is a shareable keepsake; silence, or a robotic voice, looks broken and unprofessional (from the bootcamper's earlier feedback on the same video).

### Suggested fix

Capture what was done to make that mp4 and use it to update the plugin, so every graduation video gets the same audio by default.

### Context when reported

- **Time:** 2026-10-01 14:41
- **Plugin version:** 0.5.3
- **Workstation:** Linux 7.0.0-34-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5[1m] / high
- **Context size:** Unknown
- **Module / step:** graduation / closing
- **Recent questions:** Is there anything else you would like to explore?; What priority would you give this?
- **Bootcamper responses:** "Can you recreate the mp4 using the better audio technique?"; this feedback; 1 (High)
- **Behind the scenes:** re-voice done outside the bundled renderer: piper-tts in the project venv, per-scene clips placed on the rendered timeline, a numpy music bed, sidechaincompress ducking, loudnorm I=-16, audio muxed onto the existing picture
- **Observed problem:** the bundled renderer cannot produce this audio itself
- **Expected behavior:** the bundled renderer produces a natural voice-over and music bed by default
- **Divergence:** the renderer's speech engines are say, System.Speech and espeak only, and it has no music or loudness step
