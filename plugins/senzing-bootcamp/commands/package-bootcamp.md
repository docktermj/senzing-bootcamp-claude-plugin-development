---
description: Package the bootcamp into one transferable zip archive under backups/packages/ (nothing is sent anywhere).
---

The bootcamper wants to archive their bootcamp, move it to another machine, or hand the
results to someone else.

Follow the packaging workflow in the `bootcamp-onboarding` skill's `packaging.md`: run the
dry run FIRST so the question quotes a measured size rather than an estimate, ask the one
pinned numbered 👉 question about what should travel, then write the archive with

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile <share|transfer>
```

Guide-run in the guide's POSIX shell (Git Bash on Windows); unverified on Windows: no test runs it there ([guide-run blocks](../skills/bootcamp-onboarding/ground-rules.md#guide-run-blocks)).

Two profiles: `share` carries the results — recap PDF, keepsake documents, visualizations
and `production/`, with no database, no source data and no credentials. `transfer` adds the
revisit bundle, config and mappings, so the bootcamp can be resumed elsewhere.

If this command was invoked **with** a profile as its argument (`share` or `transfer`),
still run the dry run and still ask the question — the size and the exclusions are what the
bootcamper is consenting to, and an argument is not consent for what leaves in the archive.

The archive is written **inside the project** and the plugin does not transmit it anywhere:
moving it is the bootcamper's action. Report the path, size and digest from the script's own
output, name anything excluded that they might expect to find, and return the bootcamper to
exactly where they left off.
