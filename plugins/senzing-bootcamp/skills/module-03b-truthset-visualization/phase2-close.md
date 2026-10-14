# Truth Set Visualization, Phase 2: Report and Close

Continues from Phase 1 (`phase1-visualization.md`). Follow `../bootcamp-onboarding/ground-rules.md`;
`🛑`/`⛔` are internal directives, never rendered.

> **Pre-advancement verification (agent self-check, internal directive):**
>
> Before offering to advance to the next module or marking this module complete, the agent MUST
> verify BOTH the checkpoints and the artifact on disk:
>
> - In `config/bootcamp_progress.json`: `truthset_visualization.checks.web_service.status` =
>   `"passed"` and `truthset_visualization.checks.web_page.status` = `"passed"`, or both
>   `"unavailable"` with a `reason` on `web_service`, as the no-live-server completion rule below
>   allows.
> - **The visualization artifact actually exists on disk:** the standalone snapshot written by the
>   visualization server (`docs/visualizations/truthset_verification.html`) is present and non-empty. This is
>   the hard guarantee that the visualization always happened; a checkpoint alone is not sufficient.
> - **The snapshot reflects the loaded Truth Set, not an empty template:** the visualization
>   server's build-only run (Phase 1, 2.2) MUST have built the entity model from a non-empty record
>   set (`records_total > 0`), consistent with the Truth Set record count loaded in Step 1
>   (1.2). A snapshot built from zero records is a blank page and does NOT satisfy INV-077.
>
> - **The snapshot agrees with the app the bootcamper saw:** its tab set matches the running
>   server's current tab set. Both are generated from the same source, so this is a cheap textual
>   comparison — count and compare the tab identifiers in the saved HTML against the server's.
>   ⛔ **Match on `id="tab-<name>"` — that is the marker the identifiers are written with**, and the
>   set is the six of INV-155 (`tab-graph`, `tab-stats`, `tab-matchkeys`, `tab-features`,
>   `tab-overlap`, `tab-probe`). ⛔ **A comparison that finds ZERO identifiers on both sides has not
>   passed — it has not run (INV-265).** On a dry run the first attempt matched `data-tab="…"`, found none in
>   either file, and reported "tab sets match: True"; `data-tab` appears **nowhere** in the
>   generated app. So assert a non-zero count on both sides before comparing them, and treat an
>   empty match as a broken check rather than agreement — a check that passes by comparing nothing
>   certifies exactly what it never looked at. A genuine
>   divergence means the visualization changed after the snapshot was built (Phase 1, 2.4b) and the
>   snapshot was never rebuilt. With no live server there is nothing to compare against; the
>   no-live-server completion rule below says what replaces this comparison.
>
> If the checkpoints are missing OR the snapshot file does not exist OR the snapshot was built from
> zero records, the agent MUST execute Steps 1–2 immediately (load `phase1-visualization.md`) and run
> the visualization server's build-only snapshot step (2.2) — whose `--records` file
> (`src/system_verification/truthset_data.jsonl`) matches the Truth Set loaded in Step 1
> (1.2) — so the artifact exists AND is non-empty. Do NOT offer advancement. Do NOT ask the
> module-transition question. Do NOT save progress. Produce the visualization first.
>
> If only the **tab sets diverge**, rebuild the snapshot via 2.2 while the data and server are still
> up, then re-verify. If the rebuild is not possible, warn the bootcamper that the saved copy shows
> an earlier version of the app and say how it differs — never let the recap claim a change the
> keepsake does not carry. This warning does not block module completion.
>
> <a id="no-live-server-completion"></a>
> **No-live-server completion.** This is the canonical statement of how this module completes
> when no live server ran. Step 3, Step 4 and the success indicator below, `SKILL.md`'s success
> indicator, and `phase1-visualization.md` (2.3's declined recreate, the checkpoint, its success
> indicator and its "Fallback" section) point here rather than restating it (INV-300).
>
> - **The no-live-server path** is one of two routes, each with its own `reason`:
>   `"recreate_declined"`, when the bootcamper declined to recreate a container that has no
>   published port (`phase1-visualization.md` 2.3); and `"server_failed"`, when the server could
>   not be made to serve after iterating with the MCP tools (`phase1-visualization.md` →
>   "Fallback: guarantee the snapshot if the live server cannot run").
> - **Record it as its own state, never as `passed`:** `web_service` is
>   `{"status": "unavailable", "reason": "recreate_declined"}` or
>   `{"status": "unavailable", "reason": "server_failed"}`, with no `pid`; `web_page` is
>   `{"status": "unavailable", "snapshot": "docs/visualizations/truthset_verification.html"}`,
>   with no `url`.
> - **The gate accepts** `web_service.status` = `"passed"`, or `"unavailable"` with one of the
>   two reasons, **and**, on either, the snapshot conditions above: present, non-empty, and built
>   from `records_total > 0`.
> - ⛔ **A missing, empty or zero-record snapshot blocks on every status (INV-077).** `unavailable`
>   excuses the server, never the snapshot: the STOP paragraph above applies unchanged, and routes
>   back to Phase 1.
> - **`failed` is not accepted.** It means the fallback has not finished: load
>   `phase1-visualization.md`, run its "Fallback" section, which ends by recording `unavailable`
>   with `reason: "server_failed"`, then re-verify. `unavailable` with no reason, or with any other
>   reason, is not accepted either: record which of the two routes led here first.
> - ⛔ **On `unavailable`, check the snapshot's own tab set instead (INV-130, INV-155, INV-265).**
>   There is no running server to compare against, so assert that the snapshot contains each of
>   INV-155's six identifiers, `id="tab-graph"`, `id="tab-stats"`, `id="tab-matchkeys"`,
>   `id="tab-features"`, `id="tab-overlap"` and `id="tab-probe"`, each with a non-zero count. A
>   zero count for any of them means the check did not run, not that it passed (INV-265): warn the
>   bootcamper which tab the saved copy lacks. As with the comparison, this warns and never blocks
>   module completion (INV-130).
> - **Show the snapshot before close.** On `unavailable`, tell the bootcamper there is no live
>   server and give them the snapshot by its file path,
>   `docs/visualizations/truthset_verification.html`, to open in a browser, before Step 5.
> - **Step 4 on `unavailable`:** run item 1 (rebuild the snapshot if it is stale) and item 4 (the
>   purge). Skip item 2, the live-server screenshots: there is no running engine to capture
>   Search / Probe from, and capture is best-effort anyway. Skip item 3, termination: no `pid` was
>   recorded and no server runs, so INV-223's kill-by-pid does not apply. **Still ask the
>   teardown question**, because the purge is irreversible; its disclosure says there is no live
>   server, so no URL goes dead and there is nothing to stop, and that the Truth Set records will
>   be removed from the database (exploring further means reloading them).
> - **Success** on this path is "the no-live-server state is recorded with its reason" in place
>   of "the live app served its endpoints", and the web service is terminated only when one ran.

## Step 3: Visualization completeness check

Confirm that `config/bootcamp_progress.json` contains BOTH `web_service` and `web_page` checkpoint
entries under `truthset_visualization.checks` (this module's own checks). If either entry is missing
or has a status other than `"passed"`:

- If missing: STOP. Do not close the module. Return to Phase 1 and execute Steps 1–2 fully by loading
  `phase1-visualization.md`.
- If `"failed"` or `"unavailable"`: apply the
  [no-live-server completion rule](#no-live-server-completion), stated once at the gate above
  (INV-300). It says which of the two the gate accepts and what to do about the other.

## Step 4: Cleanup

Terminate the web service and purge the Truth Set data from the database.

**When `web_service.status` is `"unavailable"`,** skip item 2 (the live-server screenshots) and
item 3 (server termination) below: no server ran, so there is nothing to capture from or to stop.
The reasons, and what the disclosure before the teardown question says, follow the
[no-live-server completion rule](#no-live-server-completion), stated once at the gate above
(INV-300).

⛔ **Ask the teardown gate first — do not proceed to the steps below until the bootcamper says
yes.** Per the server-lifetime contract in `visualization-api-reference.md` → "Server lifetime",
present this pinned question verbatim (INV-056) and end the turn on it:

⛔ **State what they are agreeing to FIRST, in the same turn but above the question, so the yes is
informed:** the live URL goes dead, the Truth Set records are removed from the database (exploring
further means reloading them), and the saved snapshot at
`docs/visualizations/truthset_verification.html` keeps every tab that renders from embedded data but
**not** the live `why`/`how`/`search` actions. This precedes the 👉 because nothing may follow it —
the question ends the turn — and because a disclosure arriving after the answer cannot inform it
(`../bootcamp-onboarding/ground-rules.md` → the 👉 protocol). The teardown is irreversible, so an
uninformed yes here is the costliest kind.

> 👉 **Ready for me to stop the visualization server and clean up the Truth Set data?**

*(Internal: end the turn on this question and wait.)*

**On "no" or "not yet":** leave the server running and the data in place, tell the bootcamper it is
still at its URL, and wait for their go-ahead. Do not re-ask on a loop.

⛔ **The Step 2.5 tour question does not authorize this.** "Are you ready to continue?" asks whether
the bootcamper is done with the guided tour; this asks whether an irreversible teardown may proceed.
They are different questions, so asking this one is **not** an INV-006 violation — INV-006 forbids
re-asking the same question, not asking a different one about a consequence the first never
mentioned. Do not reintroduce a "no separate confirmation gate" shortcut here.

⛔ **Order matters: everything that needs the data or the server happens BEFORE the purge, and the
purge is the LAST action of this module.** Once the Truth Set records are gone the snapshot cannot be
rebuilt and the live server cannot be re-served, so a missed rebuild or a missed capture becomes
permanent. Work through 1–4 in order; do not hoist the purge.

1. **Rebuild the snapshot if it is stale.** If the visualization changed after the snapshot was built
   (Phase 1, 2.4b) — or if Step 3's tab-set comparison flagged a divergence — re-run the build-only
   snapshot step **now**, while the records are still loaded. This is the last moment it is possible.

2. **Capture any missing screenshots from the live server.** Per
   `../bootcamp-onboarding/module-completion.md` → "Capturing visualization screenshots", the
   Search / Probe tab can only show real results against the running engine, so capture it here
   rather than from the static snapshot. Best-effort and non-blocking.

3. **Terminate the web service** — by process id, per `visualization-api-reference.md` → "Server
   lifetime" → "Identifying the server process":
   - Send a termination signal to the **pid recorded in Phase 1 (2.3)**, in
     `truthset_visualization.checks.web_service.pid`.
   - **Fall back to the port whenever the pid does not stop the server — a missing pid is only
     one of the two cases.** The other is a pid that *is* recorded, whose kill **exits 0**, and
     whose port stays bound: the recorded value was a subshell rather than the server (see
     `phase1-visualization.md` 2.3). Treat "the recorded pid is gone but the port still answers"
     exactly like "no pid was recorded" — the same port lookup resolves both, and this is the case
     that actually occurred on a dry run. Find the listener by
     the recorded port: `lsof -ti:<port>` on Linux/macOS,
     `Get-NetTCPConnection -LocalPort <port> | Select-Object -ExpandProperty OwningProcess` in
     PowerShell.
   - ⛔ **On the `docker` path both of those are host-shell routes and the container has neither
     tool (INV-223 still governs: terminate by pid, confirm the port)** — no `procps`, no `lsof`. Signal through the shell builtin
     (`docker exec <container> sh -c 'kill <pid>'`) using the pid INV-223 required the launch to
     record, and probe the port with `python3`, never with `lsof`, at the address the server bound
     (`visualization-api-reference.md` → "Serving from the SDK container", item 4). **The kill's exit status is not evidence the server stopped; the port is.** Full rule
     and the reason, stated once (INV-300):
     `visualization-api-reference.md` → "Server lifetime" → "Identifying the server process".
   - ⛔ **Never `pkill -f <script name>`** (or any other command-line pattern match). The pattern
     appears in the matching command's own command line, so it signals the invoking shell: on a dry
     run this killed the shell mid-teardown with exit code 144, leaving the records loaded, the
     purge below unrun, and the failure looking like the purge had crashed. The server is also
     built in the bootcamper's chosen language (INV-090), so in general there is no script name to
     match.
   - **Confirm the port is free** rather than assuming it: poll it for up to 5 seconds and stop as
     soon as nothing is listening. If it is still bound after 5 seconds, force-stop the process,
     re-check, and if it is *still* bound warn the bootcamper that the port may need manual release.
   - ⛔ Do not start step 4 until the port is confirmed free or the bootcamper has been warned — the
     purge is irreversible, and running it on the assumption that teardown succeeded is how a failed
     kill gets attributed to the purge.

4. **Purge the Truth Set data from the database** (the module's final action):
   - Remove the Truth Set records loaded in Phase 1 (CUSTOMERS/REFERENCE/WATCHLIST, or the CORD
     substitute's codes) from the Senzing database, using generated Senzing SDK code (via
     `get_sdk_reference` + `sdk_guide`); never direct SQL against `database/G2C.db`. Save it as
     the program `cleanup_truthset` in `src/system_verification`, at the path and with the project
     that `../bootcamp-onboarding/ground-rules.md` → "Building and running a program" gives, and
     build and run it with that section's commands.
   - After purge, verify zero Truth Set entities remain while preserving any other database state.
   - If the purge fails: report a fail status identifying which records could not be removed, with a
     Fix_Instruction advising the bootcamper to re-run cleanup or manually reset the database.

5. **Retain visualization artifacts:** the standalone snapshot
   (`docs/visualizations/truthset_verification.html`), the program `truthset_server` in
   `src/server` (when the chosen language is not Python), and the program
   `register_truthset_sources` in `src/system_verification`, the program `load_truthset` in
   `src/system_verification` and the program `cleanup_truthset` in `src/system_verification` remain
   in place for reference.

**Checkpoint:** write to `config/bootcamp_progress.json`.

## Step 5: Module Close

Complete this module using the standard **Module Completion** process in
`../bootcamp-onboarding/module-completion.md`. Record it as a first-class module in the order the
bootcamper experienced it (immediately after System verification), so it does not depend on
graduation's reconcile backfill (INV-085/INV-086/INV-087):

1. **Update progress state.** Add `truthset_visualization` to `modules_completed` (a module name
   token, not a number), placed after `system_verification`. Set `current_module` to the next module
   in `selected_modules` and `current_step` to `null`. All idempotent (do not duplicate).
2. **Append the recap section** to `docs/bootcamp_recap.md`, name-based and append-only (INV-085):
   `## Truth Set visualization — {timestamp}` with the four subsections (Information Shared,
   Questions & Responses, Actions Taken, End-of-Module Summary): capture the Truth Set acquisition/load, the
   interactive visualization and standalone snapshot, and — if screenshots were captured — the
   embedded `![…](visualizations/…png)` image(s) in Actions Taken — the path is relative to
   `docs/bootcamp_recap.md`, so `visualizations/…` and never `docs/visualizations/…` (INV-161;
   the recap already lives in `docs/`, so a `docs/`-prefixed path resolves to `docs/docs/…` and
   embeds nothing). Then save this module's B-roll entry under `truthset_visualization`, per
   `module-completion.md` 2e, listing the same screenshots by their project-relative
   `docs/visualizations/…` paths.
3. **Present the completion line + end-of-module summary** (INV-032):
   `✅ Module complete: Truth Set visualization` and its four-part summary, per `module-completion.md`
   Step 3. (This module's module-start banner/journey/before-after/step-overview were already shown at
   its module start in Phase 1, so only its close is presented here.)
4. **Transition to the next module.** First say the **curtain line**, a statement immediately
   before the transition 👉 and never a second question
   (`../bootcamp-onboarding/module-completion.md`: one 👉 ends the turn, INV-251). It names the
   Truth Set as practice data built to contain matches and points to the Bootcamper's own problem,
   named in one clause taken from the "Problem Description" in `docs/business_problem.md`:

   > That was practice data, built to contain matches. Next comes your own data, and the problem
   > you brought to the bootcamp: {one clause from `docs/business_problem.md`}.

   When `docs/business_problem.md` is missing, it says "your own data" and names no problem:

   > That was practice data, built to contain matches. Next comes your own data.

   Then ask the single transition question (once), and on an
   affirmative reply **(INV-272) acknowledge it in one short visible line naming that module before invoking
   its skill** (the ground rules' acknowledge clause and
   `../bootcamp-onboarding/module-completion.md` Step 4 own the ordering — a skill invocation and its
   file reads emit nothing the bootcamper can see), then produce the next module's start banner,
   journey map, before/after framing, and step overview per the ground rules.

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)*

**Checkpoint:** write to `config/bootcamp_progress.json`.

**Success indicator:** ✅ The standalone snapshot exists (built from a non-empty Truth Set) + the
live app served its endpoints, **or** the no-live-server state is recorded with its reason
([no-live-server completion rule](#no-live-server-completion), INV-300) + the web service is
terminated when one ran + the Truth Set data is purged + `truthset_visualization` is recorded in
`modules_completed` with its own recap section.
