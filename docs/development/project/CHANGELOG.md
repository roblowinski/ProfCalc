# Changelog

## Unreleased

- Rename: Replaced occurrences of the legacy token `profile_analysis` with
  `profcalc` repository-wide to reflect the current package name and layout.
- Bugfix: Load JSON menu files with ``utf-8-sig`` encoding to handle UTF-8
  BOMs inserted by some Windows editors (fixes JSONDecodeError in
  `profcalc.cli.menu`).
