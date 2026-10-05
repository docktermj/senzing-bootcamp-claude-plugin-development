# Senzing Bootcamp Claude Code Plugin

## Using the Claude Code CLI

In this section are instructions for
installing the Claude Code CLI,
installing the Senzing Bootcamp plugin,
and starting the Bootcamp.

For the desktop application instead, see
[Using Claude Desktop](../README.md#using-claude-desktop).

1. To install the Claude Code CLI on macOS, Linux, or WSL:

    ```console
    curl -fsSL https://claude.ai/install.sh | bash
    ```

1. To install the Claude Code CLI on Windows, in PowerShell:

    ```console
    irm https://claude.ai/install.ps1 | iex
    ```

    (Windows is fully supported. If you would rather not use a terminal at all,
    [Using Claude Desktop](../README.md#using-claude-desktop) is the graphical route and
    works on Windows too.)

1. Install Senzing Bootcamp Claude Plugin.

    ```console
    claude plugin marketplace add docktermj/senzing-bootcamp-claude-plugin-development
    claude plugin install senzing-bootcamp@senzing-bootcamp-dev
    ```

1. If the Senzing Bootcamp Claude Plugin is already installed, update it.

    ```console
    claude plugin update senzing-bootcamp@senzing-bootcamp-dev
    ```

1. Create a new directory for the bootcamp.
   Example:

    ```console
    mkdir senzing-bootcamp
    cd senzing-bootcamp
    ```

1. *Command line options:* run most of the bootcamp on **Sonnet 5.5** for
   the best value and switch up to **Opus 5.5** for the correctness-critical
   stretches: **SDK setup**, **Truth Set visualization**, and everything from
   **Data Quality, Mapping, and Transformation** through **graduation**.
   The bootcamp surfaces the recommendation at the start of
   each module, so you never have to remember which is which.

   For the smoothest ride, run the Claude Code CLI with `--permission-mode auto`.

1. Example command:

    ```console
    claude --model claude-sonnet-5-5 --effort medium --permission-mode auto
    ```

1. *Note:* besides the Claude Code CLI and Claude Desktop,
   the Senzing Bootcamp Claude Plugin can also be run in a Claude IDE extension:
    - [Claude Code for VSCode]

1. Start the bootcamp. Tell Claude:

    ```console
    Start the bootcamp
    ```

## Bootcamp commands

The plugin ships these slash commands. Each also works as plain English, so you never
have to remember them:

| Command | What it does |
| --- | --- |
| `/start-bootcamp` | Start the bootcamp, or resume one already in progress (same as saying "Start the bootcamp"). |
| `/bootcamp-feedback` | Share feedback about the bootcamp at any time (same as saying "bootcamp feedback"). Saved locally to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`. |
| `/graduate` | Graduate: render the recap PDF and generate the `production/` starter project. Bootcamp graduation normally follows the last module on its own, so use this only to graduate early or to re-run it. |
| `/bootcamp-note` | Jot down an idea, question, reminder or to-do at any time (same as saying "make a note"). Saved locally to `docs/bootcamp_notes.md` and folded into your recap at graduation. |
| `/package-bootcamp` | Package your bootcamp into a single zip under `backups/packages/` (same as saying "back up the bootcamp") — either the results to share, or everything needed to continue on another machine. Written locally; nothing is sent anywhere. |

## Uninstall plugin

1. Uninstall the plugin and marketplace.

    ```console
    claude plugin uninstall senzing-bootcamp@senzing-bootcamp-dev
    claude plugin marketplace remove senzing-bootcamp-dev
    ```

[Claude Code for VSCode]: https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code
