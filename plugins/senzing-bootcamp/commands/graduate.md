---
description: 'Graduate the Senzing bootcamp: generate the recap PDF and a production-ready project.'
---

The bootcamper wants to graduate the Senzing bootcamp.

First, decide whether there is a bootcamp to graduate by what
`config/bootcamp_progress.json` in the working directory records, never by whether it
exists: follow `../skills/bootcamp-onboarding/SKILL.md` → "Fresh start vs. resume — decided
by the progress file's CONTENT, not its existence" (INV-227, INV-300). Where that rule reads a
fresh start, whether the file is missing or records no module, tell the bootcamper there is no
bootcamp to graduate and offer to start one with `/start-bootcamp`, instead of graduating.

Invoke the `graduation` skill and follow it: show the BOOTCAMP GRADUATION banner, present
the graduation preface (journey map, before/after, step overview, estimated time), show the
decisions the bootcamper made and how they got it built, ask for their one-line takeaway and their
"Next time" request, finalize
`docs/bootcamp_recap.md` and render `docs/bootcamp_recap.pdf`, offer the optional graduation
video (`docs/bootcamp_recap.mp4`), build the `production/`
project, create the revisit/resume bundle, then emit the guaranteed-recap announcement
and the single closing 👉 question ("Is there anything else you would like to explore?").

Only after the bootcamper declines further exploration, render the terminal
`END OF SENZING BOOTCAMP` banner as the final output, exactly once (INV-057). Never show
that banner while exploration is still continuing, and never end graduation on the closing
question when the bootcamper has said they are done.

The bundled recap PDF generator is available at
`${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_pdf.py`; pass that path when the
graduation skill renders the PDF.
