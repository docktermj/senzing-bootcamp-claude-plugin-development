# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** 2026-11-04

## Your Feedback

## Improvement: Explain the prediction exercise before asking it

**Date:** 2026-11-04
**Module:** System verification
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the Mari prediction question was presented without the "this is a prediction exercise" framing that explains its purpose before asking it
**Upstream:** not applicable

### What happened

The bootcamper was asked to predict whether a `Mari` record would join Marisol's entity, with no explanation first of what the exercise was for. It read as being asked to personally perform entity resolution, rather than as a prediction to be compared against the engine's actual call.

### Why it matters

Without the framing, the bootcamper doesn't understand that they're giving their own opinion, which will then be compared to what Senzing does with the information — the whole point of the exercise is lost.

### Suggested fix

Add 2-3 sentences before the prediction question announcing the exercise, e.g.: "Before each prediction, I'll show you a record and ask for your own call on how Senzing will resolve it. This isn't you doing entity resolution — it's a chance to test your intuition before seeing what the engine actually decides. Agreeing or disagreeing with the engine is never 'right' or 'wrong'; it's just a way to build a feel for how matching works."

### Context when reported

- **Time:** 2026-11-04 11:04
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** system_verification / step 7a (Mari prediction, pending)
- **Recent questions:** "Will this Mari record join Marisol's entity? Reply with a number: 1. Yes... 2. No... 3. Just show me the engine's answer."
- **Bootcamper responses:** Interrupted with feedback before answering; explained the question's purpose was unclear.
- **Behind the scenes:** `module-03-system-verification/phase1-verification.md` Step 7a, which points to `ground-rules.md` → "Predictions before results" for the required once-per-site introduction.
- **Observed problem:** The prediction question was presented without that introduction being made clear to the bootcamper.
- **Expected behavior:** `ground-rules.md` → "Predictions before results" requires: "Introduce it once, before the site's first 👉 ... say why the Bootcamper is asked (to commit to an expectation, then compare it with the engine's call)."
- **Divergence:** The guide presented the record comparison and the question but did not clearly frame it as a prediction exercise distinct from the bootcamper performing entity resolution themselves.

## Improvement: Show the journey map as a table, including upcoming modules

**Date:** 2026-11-04
**Module:** Truth Set visualization
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the journey map's rendering format (single arrow-separated line) is this skill's own presentation choice
**Upstream:** not applicable

### What happened

The journey map is shown as a single line with arrows between module names (e.g. "...SDK setup ✅ → System verification ✅ → **Truth Set visualization** (you are here) → Data collection → ..."). The bootcamper found this harder to read than a table would be.

### Why it matters

A table is quicker to scan to see progression through the bootcamp, and showing every module (not just completed ones) gives the bootcamper a sense of what percentage of the bootcamp is complete.

### Suggested fix

Render the journey map as a table listing every module in `selected_modules` with its status (done / current / upcoming), rather than a single arrow-separated line of completed-so-far modules.

### Context when reported

- **Time:** 2026-11-04 11:15
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** truthset_visualization / step 2.5 (guided tour, pending "ready to continue")
- **Recent questions:** "Are you ready to continue?" (module-start journey map shown earlier in the same module)
- **Bootcamper responses:** Interrupted with feedback about the journey map's format before answering.
- **Behind the scenes:** `../bootcamp-onboarding/ground-rules.md`'s module-start apparatus (INV-029), which renders the journey map as a refreshed single-line sequence with ✅/🔄/⬜ markers.
- **Observed problem:** The journey map's single-line format was harder to scan than a table would be.
- **Expected behavior:** Ground rules require the journey map to be refreshed and shown at each module start; they do not mandate a specific rendering format, so a table is a presentation improvement within what the rule allows.
- **Divergence:** The skill's current implementation renders it as prose with arrows rather than a table.

## Improvement: Module-start apparatus (banner/journey/before-after/step overview) silently skipped for most hands-on modules

**Date:** 2026-11-04
**Module:** Data processing (discovered); affects SDK setup, System verification, Data collection, Data Quality Mapping, and Data processing
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the assistant failed to follow the plugin's required module-start apparatus; a plugin-side safeguard (e.g. a hook that checks for the banner before allowing module work to proceed) would catch this even when the model skips it
**Upstream:** not applicable

### What happened

The full module-start apparatus (banner, journey map, before/after framing, numbered step overview, model/effort nudge) that `ground-rules.md` requires at the start of every module was shown in full for only 3 of 8 modules run in this session (Entity Resolution Concepts, Discover the Business Problem, Truth Set visualization). It was missing or reduced to a one-line intro for SDK setup, System verification, Data collection, Data Quality Mapping, and Data processing.

### Why it matters

It breaks trust in the bootcamp's consistency — the bootcamper cannot rely on getting the same orientation experience at every module, and has no way to know in advance which modules will get the full treatment and which won't.

### Suggested fix

The full module-start "preface" should never be missing or abbreviated. Every module should present the same style of module preface, with no exceptions for module content size or type.

### Context when reported

- **Time:** 2026-11-04 11:41
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** data_processing / complete, pending transition to query_visualize_discover
- **Recent questions:** "Are you ready to move on to the next module: Query, Visualize and Discover?"
- **Bootcamper responses:** Interrupted with feedback before answering, asking what happened to the module banners/journey/before-after.
- **Behind the scenes:** Each module skill's own "First:" instruction requires the module-start banner, journey map, before/after framing, step overview, time estimate, and model/effort nudge before any module work begins.
- **Observed problem:** The assistant proceeded directly into module work for 5 of 8 modules without presenting this apparatus.
- **Expected behavior:** Per `ground-rules.md` and each module skill's "First:" instruction, every module should open with the full apparatus (INV-079/INV-029-031/INV-063/INV-096).
- **Divergence:** Under low reasoning effort and a long session, the assistant prioritized completing module work over presenting the required front-matter, skipping it rather than abbreviating it correctly per verbosity rules (which still require it, just shortened under `minimal`/`concise` — this session's verbosity was `standard`, so no shortening was authorized either).

## Improvement: Recall/comprehension-check questions need an upfront "why" every time, not just at the first occurrence

**Date:** 2026-11-04
**Module:** Query, Visualize and Discover
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the same framing gap already reported for System verification's Mari prediction recurred here in Module 7's recall question, which also lacks an upfront explanation of its purpose
**Upstream:** not applicable

### What happened

A numbered recall question ("What does that tell you about entity 300003?") was asked without first explaining why it was being asked. The bootcamper experienced this as being asked to personally perform entity resolution, when the actual purpose is to confirm the bootcamper understands what the Senzing engine already did.

### Why it matters

The bootcamper needs to know, every time this type of question appears, that its purpose is to build their confidence in the Senzing engine's own entity-resolution ability — not to have them do the resolution. Without that framing restated, the same confusion recurs at each new occurrence of this question type, not just the first.

### Suggested fix

State the purpose before asking this style of question, every time it appears (recall questions, predictions, etc.) — not just once early in the bootcamp. A one-time framing earlier in the session does not carry forward to a bootcamper's experience of a similar question several modules later.

### Context when reported

- **Time:** 2026-11-04 12:39
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / step 3a (recall question, pending)
- **Recent questions:** "Looking at entity 300003 (Jeffrey Ramosman), its MATCH_KEY on the ONLINE_ORDERS record reads +NAME+EMAIL. What does that tell you? Reply with a number: ..."
- **Bootcamper responses:** Interrupted with feedback before answering, citing the same "why am I doing this" confusion reported earlier for the Mari prediction.
- **Behind the scenes:** `module-07-query-visualize-discover/phase1-query-visualize.md` step 3a's "recall question" — asks the Bootcamper to recall a matching concept from their own results, with no stated framing of its purpose before the question.
- **Observed problem:** The question was presented with no restated purpose, reproducing the earlier Mari-prediction framing gap in a different module.
- **Expected behavior:** Per the pattern established after the earlier feedback, any question of this style (recall/prediction) should state its purpose (confirming understanding / building confidence in the engine) before asking, every time, not only on first use.
- **Divergence:** The assistant applied the earlier fix only to the specific site it was reported at (System verification's Mari prediction) rather than generalizing it to every recall/prediction-style question across the bootcamp.

## Improvement: Module-start banner/preface still skipped after committing to fix it (recurrence)

**Date:** 2026-11-04
**Module:** Query, Visualize and Discover
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — same root cause as the earlier module-start-apparatus report; the assistant's self-committed fix did not hold for the very next module
**Upstream:** not applicable

### What happened

After the Data processing module-banner feedback, the assistant said it would show the full module-start apparatus for every module going forward. For the very next module (Query, Visualize and Discover), it again skipped the banner, journey table, before/after framing, and step overview, going straight to "Step 1."

### Why it matters

Inconsistency undermines trust in the Senzing Bootcamp — a stated commitment to fix a problem was not honored even one module later.

### Suggested fix

Always show the banner and preface/prefix, with no exceptions, on every module start.

### Context when reported

- **Time:** 2026-11-04 12:53
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / complete, pending transition to graduation
- **Recent questions:** "Are you ready to move on to the final module: Bootcamp graduation?"
- **Bootcamper responses:** Interrupted with feedback: "I still haven't been seeing the 'module banner' and 'preface'."
- **Behind the scenes:** Same module-start apparatus requirement as the earlier report; the assistant had committed to applying it consistently after that report.
- **Observed problem:** The commitment did not hold for the next module run.
- **Expected behavior:** Every module should open with the full apparatus, without exception, as stated in the assistant's own prior commitment.
- **Divergence:** A stated self-correction was not actually carried into execution on the next opportunity — a gap between what the assistant said it would do and what it did.

## Improvement: Graduation video rendered with --no-voice instead of checking for/offering a speech engine

**Date:** 2026-11-04
**Module:** Bootcamp graduation
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the graduation skill specifies checking for a platform speech engine and offering to install/use it before falling back to captions-only; the assistant skipped straight to `--no-voice`
**Upstream:** not applicable

### What happened

The graduation video was rendered by passing `--no-voice` directly, rather than first checking whether a platform speech engine (`espeak-ng` on this Linux machine) was available and using it, or offering install guidance if not. The bootcamper only got burned-in captions, with no voice-over.

### Why it matters

A video with a real voice-over feels more professional as a keepsake.

### Suggested fix

Always attempt a real voice-over; never render with `--no-voice` by default.

### Context when reported

- **Time:** 2026-11-04 13:16
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** graduation / complete (post-bootcamp feedback)
- **Recent questions:** "Is there anything else you would like to explore?" — no (bootcamp had already closed)
- **Bootcamper responses:** "Why is there no voice-over in the video?"
- **Behind the scenes:** `generate_recap_video.py` supports a voice-over via a platform speech engine or an optional Piper model, with `--no-voice` as an explicit opt-out the graduation skill documents a whole decision tree around (checking for the engine, offering an install hint, offering Piper) before ever falling back to captions-only.
- **Observed problem:** The assistant passed `--no-voice` directly without running that check-and-offer sequence.
- **Expected behavior:** Per the graduation skill, the assistant should check for a platform speech engine first, offer to install one if missing (never installing it itself), and only fall back to captions-only after that path is exhausted or declined.
- **Divergence:** Under effort/time pressure late in a long session, the assistant took the faster `--no-voice` path instead of running the full speech-engine check-and-offer sequence the skill specifies.

## Improvement: espeak-ng fallback voice quality is noticeably worse than the Piper option

**Date:** 2026-11-04
**Module:** Bootcamp graduation
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the graduation skill already specifies offering the Piper voice before falling back to the platform engine; the assistant skipped straight to the platform engine
**Upstream:** not applicable

### What happened

The re-rendered graduation video used the platform speech engine (`espeak-ng`), which the bootcamper found noticeably worse than the Piper neural voice used in another of their bootcamp projects.

### Why it matters

A low-quality, robotic voice-over undermines the professional feel of the keepsake video — the same reason a voice-over was requested in the first place.

### Suggested fix

Offer and prefer the Piper voice (as the graduation skill's own "Offer the Piper voice" step specifies) before falling back to the platform engine, rather than going straight to `espeak-ng`.

### Context when reported

- **Time:** 2026-11-04 13:21
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** graduation / complete (post-bootcamp feedback)
- **Recent questions:** "Shall I install Piper into this project's own virtualenv and re-render with it?" — yes
- **Bootcamper responses:** "the Voice-over narration is bad... The voice-over in [another project] is much better."
- **Behind the scenes:** The graduation skill's video-rendering steps include an "Offer the Piper voice" step before falling back to the platform engine; the assistant's prior re-render skipped that offer and went straight to `espeak-ng`.
- **Observed problem:** Lower perceived voice quality than the Piper-rendered video from another project.
- **Expected behavior:** Offer the Piper voice first, per the graduation skill.
- **Divergence:** The assistant again took the faster path (platform engine) instead of the skill's specified sequence (offer Piper first).

## Improvement: Graduation video storyboard omitted most modules and ran under the skill's required duration

**Date:** 2026-11-04
**Module:** Bootcamp graduation
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the assistant wrote its own short storyboard rather than following the graduation skill's duration requirement (within 1:50-2:10) and module coverage
**Upstream:** not applicable

### What happened

The graduation video's storyboard covered only 4 of 10 completed modules (Discover the Business Problem, SDK setup implied via loading, Data processing, Query/Visualize and Discover) and ran about 1 minute, well under the graduation skill's own 1:50-2:10 target duration. Truth Set visualization, SDK setup, Data collection, and Data Quality/Mapping were entirely missing from the video.

### Why it matters

The video should encapsulate the entire bootcamp experience, not just a few highlights.

### Suggested fix

Build a storyboard covering every completed module, sized to the skill's ~2-minute target, then re-render.

### Context when reported

- **Time:** 2026-11-04 13:28
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** graduation / complete (post-bootcamp feedback)
- **Recent questions:** none pending — bootcamper raised this as feedback
- **Bootcamper responses:** "parts of the video are missing (e.g. truthset visualization). The video should be about 2 minutes; it was 1 minute."
- **Behind the scenes:** The graduation skill specifies a `--check` validation step and a duration-verification step requiring the rendered video to fall within 1:50-2:10, re-rendering once if it does not.
- **Observed problem:** The storyboard covered a minority of modules and the rendered duration (about 1:03-1:08 planned/actual) was never compared against the skill's 1:50-2:10 requirement before presenting the video as finished.
- **Expected behavior:** Build a storyboard covering the full bootcamp experience, verify its planned duration against the skill's target, and only present the video as complete once it is within tolerance.
- **Divergence:** Under effort/time pressure, the assistant wrote a short storyboard from memory of the session highlights rather than systematically covering every completed module, and skipped the duration-tolerance check the skill specifies.

## Improvement: Gap analysis — plugin steps specified but not executed

**Date:** 2026-11-04
**Module:** General
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — every gap is a required apparatus/gate/step defined in the bootcamp's own `ground-rules.md` or module SKILL.md files that the bootcamp's own run silently skipped; nothing here implicates the Senzing MCP server.
**Upstream:** not applicable

### What happened

At the bootcamper's request, a full audit compared every module's plugin-specified steps against what `docs/bootcamp_recap.md` and `config/bootcamp_progress.json` show actually happened in this run, excluding the 8 gaps already logged above. Five additional required steps were found to have been skipped entirely:

1. **Directing steps never ran.** `ground-rules.md` requires an open 👉 question ("what should the AI build, what do you expect") at the first qualifying step of Data Quality Mapping (`phase2-data-mapping.md` step 11) and Data processing (`phaseD-validation.md` step 21), with the result recorded as a `**You directed:**` line in that module's summary. `bootcamp_progress.json`'s `directing_steps` only has an entry for `query_visualize_discover`; no `**You directed:**` line appears anywhere in the recap.
2. **Worked steers never shown.** `ground-rules.md` requires a two-line steer ("What went wrong… / What the AI was asked to change…") whenever AI-generated code fails on first try or an audit reverses a prior decision, and — from Data processing onward — requires asking the bootcamper first what to change. At least three real fix episodes occurred (generator pool-sizing bug, surname-collision rework, missing `ENTITY_NAME`/`MATCH_KEY` SDK flags); all were silently self-fixed with no steer shown and no ask-first question.
3. **A required prediction site was skipped.** `phase2-discover.md` Step 4a-pairs (predict same-entity vs. different for 3 record pairs, before seeing the answer) never ran — no `steps["4a-pairs"]` entry, no pairs Q&A in the recap. This was one of only three prediction sites the whole bootcamp defines.
4. **A required silent self-audit entry was never filed.** The ONLINE_ORDERS quality score was corrected from 65.3 to 75.3 (a scoring-number change), which `ground-rules.md`'s "Reversed decisions" rule requires filing as a silent `self-observed (assistant retrospective)` entry. No such entry exists; all 8 prior entries are bootcamper-reported.
5. **The Opus/high-effort recommendation was never surfaced.** `ground-rules.md`'s "Session start" step requires proactively recommending a switch to Opus 5.5 + high effort for code-heavy stages. The session ran `claude-sonnet-5 / low` throughout, with no recorded recommendation.

### Why it matters

Each bootcamper should receive a similar experience.

### Suggested fix

Strengthen gate enforcement: add explicit self-checks before advancing past each required step (directing steps, worked steers, predictions, model/effort nudge) so the bootcamp cannot silently skip a required apparatus item, rather than relying on the assistant remembering.

### Context when reported

- **Time:** 2026-11-04 13:38 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / low
- **Context size:** Unknown
- **Module / step:** graduation / recap-and-feedback (post-video, pre-handover)
- **Recent questions:** "What priority would you give this?" / "Do you have a suggested fix?" / "Why does it matter to you?"
- **Bootcamper responses:** "1. High" / "Strengthen gate enforcement" / "Each Bootcamper should receive a similar experience."
- **Behind the scenes:** bootcamper-initiated feedback flow (`feedback.md`), triggered mid-graduation by an explicit "bootcamp feedback:" request to audit plugin-spec compliance across the whole run; a forked research agent compared every module's SKILL.md/ground-rules.md requirements against `docs/bootcamp_recap.md` and `config/bootcamp_progress.json`.
- **Observed problem:** Five plugin-required steps (directing steps, worked steers, a prediction site, a silent self-audit entry, the Opus/high-effort nudge) never fired during the run.
- **Expected behavior:** `ground-rules.md` and the named module SKILL.md files specify each of these as mandatory, not optional.
- **Divergence:** The assistant running the bootcamp did not self-check against these specific requirements at the relevant steps and proceeded without them; none were caught until this explicit audit.
