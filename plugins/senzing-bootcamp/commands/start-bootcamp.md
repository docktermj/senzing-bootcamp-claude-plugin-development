---
description: Start or resume the Senzing entity-resolution bootcamp.
---

The user wants to begin the Senzing bootcamp.

Invoke the `bootcamp-onboarding` skill and follow it. Whether this is a resume is decided by
what `config/bootcamp_progress.json` **contains**, not by whether it exists — three cases:

- **No file** -> start onboarding from the beginning.
- **A file recording no module** (empty, `{}`, malformed, not a JSON object, or `current_module`
  null/blank) -> also start onboarding from the beginning, and **silently**: this is the normal
  state between the preface's project setup and Bootcamp preparation's final write, not a
  corruption to report.
- **A file with a `current_module`** -> resume from that module.
