# Tests

Dev-only tests for the Senzing Bootcamp plugin. They live here at the repo top
level — **not** under `plugins/` — so `propagate.sh` (which mirrors `plugins/`
into the public repo) never ships them to bootcampers.

Standard library only; no third-party dependency (INV-108). Availability of the
optional `fpdf2` renderer is probed with `importlib.util.find_spec`, never by
importing it in a test.

Run everything:

```bash
python3 -m unittest discover -s tests
```

Install `fpdf2` first, or the tests that measure the fpdf2-rendered PDF will skip:

```bash
python3 -m pip install -r requirements-dev.txt
```

That is a dependency of the *renderer under test*, not of the tests. The shipped
generators fall back to a stdlib renderer without it, and that fallback path ships
and is tested — so the suite stays green either way, but a run without `fpdf2`
leaves the fpdf2 renderer unmeasured. `tests/_fpdf2_support.py` prints one notice
when it is absent and supplies the `@requires_fpdf2` guard; see `docs/development.md`.

- `test_write_gate.py` — exercises the PreToolUse write-gate security control
  (`plugins/senzing-bootcamp/scripts/write-gate.py`): location allow/block,
  `..`-traversal, home-relative and `$TMPDIR`/`%TEMP%` temp paths, the
  case-folded in-project exemption, and secret detection (PEM / AWS / Senzing
  `AQAAAD` license blobs). Invoked as a subprocess because the gate reads stdin
  at import time.
- `test_brand_sync.py` — asserts the inlined fallback palettes in
  `senzing_viz_server.py` and `generate_recap_pdf.py` stay equal to
  `brand_tokens.py`, so the hand-maintained copies cannot drift silently.
- `test_recap_pdf_guard.py` — pins the recap PDF generator's two outcome classes
  apart (`generate_recap_pdf.py`): a recognizable-but-incomplete recap warns,
  renders, and exits 0 (graduation is non-blocking), while a non-recap input or
  catastrophic content loss writes no PDF, prints no `PDF generated:` line, and
  exits non-zero. Also covers the content-retention figure, the
  never-silent `fpdf2` downgrade, the stdlib fallback's landscape certificate
  (INV-066/INV-100), and `--check`'s exit semantics.
