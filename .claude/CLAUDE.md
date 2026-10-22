# Working in this repository

Maintainer context for Claude Code sessions in this repository. The auto mode classifier
reads this file too. Auto mode does not read `autoMode` from project settings, so the
context lives here, and the actions that must always prompt are `permissions.ask` rules
in `.claude/settings.json`.

## Outward-facing actions

- **This repository is public.** Any push to it is publishing. Only this repository's own
  work belongs in it. Secrets, credentials and bootcamper personal data never belong in
  it, whatever its visibility.
- **Filing a GitHub issue here is outward-facing.** The repository's skills create an
  issue only after an explicit yes from the maintainer for that issue.
- **Sending feedback upstream is irreversible.** The Senzing MCP server's
  `submit_feedback` tool sends each message to Senzing. It needs the maintainer's
  explicit yes for each message, and the maintainer tooling never calls it on its own.

## Trusted services

- `mcp.senzing.com` is the Senzing MCP server, the plugin's hard runtime dependency.
  Calling its read-only tools for documentation, references and examples is routine.

## Files that handle credentials

These files define secret detection or credential hardening. Never put a real secret,
credential or personal record in them, including as a test fixture:

- `plugins/senzing-bootcamp/scripts/secret_patterns.py`
- `specs/module02-postgres-credentials-hardening.md`
- `specs/the-packager-secret-scan-skips-the-files-most-likely-to-be-secrets.md`
- `tests/test_screenshot_retention_and_order.py`
- `tests/test_secret_patterns_are_shared.py`
