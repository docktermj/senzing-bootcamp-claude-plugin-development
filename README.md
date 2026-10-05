# Senzing Bootcamp Claude Code Plugin

A guided bootcamp for learning [Senzing] entity resolution,
packaged as a Claude Code plugin.
Install it, then say **"start the bootcamp"** to be guided through
a hands-on, module-by-module tutorial.

## What the bootcamp covers

A guided sequence of hands-on modules takes you from zero
to working entity resolution:

- ***Bootcamp preparation:*** choose your curriculum, level of detail, and programming language
- ***Entity Resolution Concepts:*** a primer on how entity resolution works *(optional)*
- ***Discover the Business Problem:*** describe the problem you are trying to solve
- ***SDK setup:*** install and configure the Senzing SDK
- ***System verification:*** end-to-end checks that Senzing works on your machine *(optional)*
- ***Truth Set visualization:*** an interactive web app of the resolved Truth Set data *(optional)*
- ***Data collection:*** identify and collect your data sources
- ***Data Quality, Mapping, and Transformation:*** make your data "Senzing-ready"
- ***Data processing:*** ingest your Senzing-ready data
- ***Query, Visualize and Discover:*** see what Senzing can do for you
- ***Bootcamp graduation:*** wrap up your bootcamp with a bow

You finish with working Senzing code and data in your project, a professional
recap PDF you can keep and share, and a production starter. See
[What you finish with](#what-you-finish-with) for details.

## Requirements

- Network access to the [Senzing MCP server].
  The bootcamp cannot proceed without it.
  It generates SDK code,
  looks up Senzing facts,
  and provides working examples.
- Python 3, available as `python3` on the `PATH`.
  The bootcamp's hooks and its graduation recap run on it.
  On Windows, if only `python` or `py` is installed, add a `python3` entry to the `PATH`.
- Minimum of a [Claude Max 5x] plan.
  - *Note:* Multiple 5-hour windows of a [Claude Pro] plan will work, but you will not be able to complete the bootcamp in one session.
- *Recommended, but not mandatory:*
  A business problem requiring Entity Resolution
  and 5,000 to 20,000 records that illustrate the problem.

## Install and start

This is a Claude Code plugin, and it works wherever Claude Code runs.
This walkthrough covers the two interfaces it has step-by-step instructions for:

- **Claude Desktop** — Claude Code inside the desktop application; the step-by-step
  walkthrough below.
- **Claude Code CLI** — Claude Code in a terminal; see [Using the Claude Code CLI].

Claude Code also runs in the **Claude web app** and in **Claude IDE extensions** (VS Code,
JetBrains). The bootcamp itself supports those — it adapts its model and reasoning-effort
guidance to whichever interface you are in — but this walkthrough has no verified install
steps for them, so install the plugin the way your client installs plugins and then start the
bootcamp as below.

### Using Claude Desktop

In this section are instructions for
installing Claude Desktop,
installing the Senzing Bootcamp plugin,
and starting the Bootcamp.

1. Download and install [Claude Desktop].
1. Start Claude Desktop.
    1. If asked, install `git`.
1. In Claude Desktop,
    1. In the left-hand pane, choose "**</> Code**".
    1. In the *Code* pane, click "**New**".
1. In Claude Desktop, near the bottom, choose the "Working directory" (it might say "Select folder...")
    1. Create and use a new folder for the Senzing Bootcamp.
1. In Claude Desktop, on the bottom, click the "Add" icon (**+**) > **Plugins** > **Manage plugins**.
    > **Note:** These instructions may change depending on version of Claude App.
    1. Select the "Yours" tab.
    1. In the upper-right of the *Plugins* pane, click **Add** > **Add Marketplace**.
        1. If the plus sign is missing, see [Troubleshooting: Claude Desktop inoperative](#claude-desktop-inoperative)
    1. In the *Add marketplace* pane, enter "**URL:**"

        ```console
        https://github.com/Senzing/senzing-bootcamp-claude-plugin
        ```

    1. Click the "**Sync**" button.
    1. To the right of *Senzing bootcamp*, **Add** > "install for project (personal)".
    1. Close *Plugins* dialog.
1. In Claude Desktop, on the bottom,
    1. Choose the Mode: "**auto**" for a smooth ride.
    1. Choose the Model "**Sonnet 5.5**".
    1. Choose the Effort: "**medium**".
1. In Claude Desktop, near the bottom, in the agentic chat, enter:

    ```console
    Start the bootcamp
    ```

    (Or use the `/start-bootcamp` command. See [Bootcamp commands] for the rest.)

## What you finish with

The bootcamp is a guided, module-by-module tutorial.
You end with working Senzing code and data in your project (`src/`, `data/`, `database/`),
a professional recap PDF you can keep and share (e.g. [bootcamp_recap.pdf], but yours will differ),
and a `production/` starter project.

## Troubleshooting

### Claude Desktop inoperative

If you are unable to enter and process prompts in Claude Desktop
or if you are unable to add a Claude Marketplace or Claude plugin,
the issue may be with an incomplete installation of Claude Desktop.

- Claude Desktop requires `git` to be installed.

[Bootcamp commands]: docs/README.md#bootcamp-commands
[bootcamp_recap.pdf]: https://raw.githubusercontent.com/Senzing/senzing-bootcamp-claude-plugin/refs/heads/main/plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.pdf
[Claude Desktop]: https://claude.ai/download
[Claude Max 5x]: https://claude.com/pricing
[Claude Pro]: https://claude.com/pricing
[Senzing MCP server]: https://mcp.senzing.com/mcp
[Senzing]: https://senzing.com
[Using the Claude Code CLI]: docs/README.md#using-the-claude-code-cli
