# Issue #37: Fix CLI init --force flag parsing

## Description

The `tasker init --force` command does not work. The flag `--force` / `-f` is defined in the init command but Typer is not recognizing it as a valid option.

### Steps to reproduce

1. Run `tasker init <directory> --force` or `tasker init <directory> -f`
2. Error: "No such command '--force'" or "No such command '-f'"

### Root cause

The `init_app` is registered as a subcommand of the main app with `add_typer(init_app, name="init")`. The `--force` option is defined as an Option in the init command callback, but due to how Typer handles nested typer apps with `invoke_without_command=True`, the option parsing is not working correctly.

### Expected behavior

`tasker init <target> --force` should work to overwrite existing scaffolded files.

## Status: PENDING
