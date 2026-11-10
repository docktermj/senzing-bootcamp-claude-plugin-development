---
description: Start or resume the Senzing entity-resolution bootcamp.
---

The user wants to begin the Senzing bootcamp.

Invoke the `bootcamp-onboarding` skill and follow it. Whether this is a resume is decided by
what `config/bootcamp_progress.json` **contains**, not by whether it exists — four cases, the
first checked before the rest:

- **A finished bootcamp** (`bootcamp_complete: true` in `config/bootcamp_progress.json` or in
  `config/bootcamp_preferences.yaml`, whatever else the progress file holds or whether it
  exists) -> do not start onboarding and do not offer to resume a module. Say the bootcamp is
  complete, name `/package-bootcamp`, and ask with one open 👉 question what they would like to
  explore, in the form the skill's step 2 pins.
- **No file** -> start onboarding from the beginning.
- **A file recording no module** (empty, `{}`, malformed, not a JSON object, or `current_module`
  null/blank) -> also start onboarding from the beginning, and **silently**: this is the normal
  state between the preface's project setup and Bootcamp preparation's final write, not a
  corruption to report.
- **A file with a `current_module`** -> resume from that module.
