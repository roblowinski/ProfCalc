#!/usr/bin/env python3
"""Fix markdown fenced code block spacing.

This script ensures there's a blank line before an opening fence and after a
closing fence. It is safe to commit and can be run in --dry-run mode. By
default it targets `src/profcalc/docs` to avoid touching archives and editor
history.

Usage examples:
  python dev_scripts/fix_md_fences.py --dry-run
  python dev_scripts/fix_md_fences.py --apply --paths src/profcalc/docs
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List


def find_md_files(paths: Iterable[Path], excludes: Iterable[Path]) -> List[Path]:
    md: List[Path] = []
    for base in paths:
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            # skip excluded prefixes
            if any(str(p).startswith(str(ex)) for ex in excludes):
                continue
            md.append(p)
    return sorted(md)


def fix_file(p: Path) -> bool:
    """Return True if the file would be modified (and write changes if apply)."""
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return False

    fence_re = re.compile(r"^```")
    lines = text.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if fence_re.match(line.strip()):
            # ensure previous line is blank (if exists)
            if out and out[-1].strip() != "":
                out.append("")
            # write the fence line
            out.append(line)
            i += 1
            # copy fence content until next fence
            while i < len(lines):
                out.append(lines[i])
                if fence_re.match(lines[i].strip()):
                    # after closing fence, ensure next line (peek) is blank
                    if i + 1 < len(lines) and lines[i + 1].strip() != "":
                        out.append("")
                    i += 1
                    break
                i += 1
            continue
        else:
            out.append(line)
            i += 1

    new_text = "\n".join(out) + ("\n" if text.endswith("\n") else "\n")
    if new_text != text:
        return True
    return False


def apply_fix(p: Path) -> None:
    """Write the fixed content back to path (assumes fix_file would modify)."""
    text = p.read_text(encoding="utf-8")
    fence_re = re.compile(r"^```")
    lines = text.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if fence_re.match(line.strip()):
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            i += 1
            while i < len(lines):
                out.append(lines[i])
                if fence_re.match(lines[i].strip()):
                    if i + 1 < len(lines) and lines[i + 1].strip() != "":
                        out.append("")
                    i += 1
                    break
                i += 1
            continue
        else:
            out.append(line)
            i += 1
    new_text = "\n".join(out) + ("\n" if text.endswith("\n") else "\n")
    p.write_text(new_text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fix fenced code block spacing in markdown files"
    )
    ap.add_argument(
        "--paths",
        "-p",
        nargs="*",
        default=["src/profcalc/docs"],
        help="Paths to search for .md files (relative to repo root). Defaults to src/profcalc/docs",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write changes; if not set, runs as dry-run",
    )
    ap.add_argument(
        "--exclude",
        "-e",
        nargs="*",
        default=["archive", ".specstory", ".history", "data/testing_files", "logs"],
        help="Paths to exclude (prefix match)",
    )
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    bases = [root.joinpath(p) for p in args.paths]
    excludes = [root.joinpath(e) for e in args.exclude]

    md_files = find_md_files(bases, excludes)
    if args.verbose:
        print(f"Found {len(md_files)} markdown files to check")

    to_modify: List[Path] = []
    for p in md_files:
        try:
            if fix_file(p):
                to_modify.append(p)
        except Exception:
            # ignore unreadable files
            continue

    if not to_modify:
        print("No changes needed")
        return 0

    print("Files that would be modified:")
    for p in to_modify:
        print(str(p))

    if args.apply:
        for p in to_modify:
            apply_fix(p)
        print(f"Applied fixes to {len(to_modify)} files")
    else:
        print(
            f"Dry-run: {len(to_modify)} files would be changed. Rerun with --apply to write."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
