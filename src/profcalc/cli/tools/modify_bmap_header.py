# =============================================================================
# BMAP Profile Header Editor Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/modify_bmap_header.py
#
# PURPOSE:
# This module provides interactive utilities for inspecting and editing
# profile header information in BMAP (Beach Morphology Analysis Package)
# free-format files. It offers both a full-screen curses-based editor and
# a simpler prompt-based interface for modifying profile metadata.
#
# WHAT IT'S FOR:
# - Provides interactive editing of BMAP profile headers
# - Allows modification of profile names, dates, descriptions, and purposes
# - Supports both curses-based full-screen editing and simple prompts
# - Enables batch header updates across multiple profiles
# - Validates header changes before writing output files
# - Provides preview and confirmation of header modifications
#
# WORKFLOW POSITION:
# This tool is used when BMAP files contain incorrect or incomplete header
# information that needs to be corrected before analysis. It's commonly used
# for data cleanup, metadata standardization, and preparing datasets for
# publication or sharing with other analysis teams.
#
# LIMITATIONS:
# - Requires curses library for full-screen editing (may not be available on all systems)
# - Header editing is manual and may be time-consuming for large numbers of profiles
# - Changes are applied to all selected profiles (no selective editing)
# - Requires understanding of BMAP header format conventions
#
# ASSUMPTIONS:
# - Users understand BMAP file structure and header requirements
# - Input BMAP files are properly formatted and readable
# - Header information needs to be corrected or standardized
# - Users have appropriate permissions to modify and save files
# - Curses library is available for full editing experience
#
# =============================================================================

"""Modify BMAP profile headers (interactive)

Interactive utilities to inspect and edit profile header lines in BMAP
free-format files. This module provides a curses-based full-screen editor
and a simpler prompt-based editor when curses is unavailable.

Usage examples:
    - Menu: Quick Tools → Modify BMAP Profile Header (invokes :func:`execute_from_menu`).
    - Programmatic: import and call :func:`execute_modify_headers_menu` from a script.
"""

try:
    import curses
except ImportError:
    import sys

    # Log and inform user that curses is unavailable
    try:
        from profcalc.cli.quick_tools.quick_tool_logger import (
            log_quick_tool_error,
        )

        log_quick_tool_error(
            "modify_bmap_header",
            "curses module not available on this system; interactive curses UI disabled",
        )
    except (ImportError, ModuleNotFoundError):
        # best-effort logging; ignore failures to import logger
        pass
    print(
        "\n❌ The 'curses' module is not available on this system.\n"
        "If you are on Windows, install it with: pip install windows-curses\n"
        "(You may need to run this in your activated virtual environment.)\n"
    )
    sys.exit(1)
from typing import Any

from profcalc.cli.file_dialogs import select_input_file
from profcalc.common.bmap_io import read_bmap_freeformat, write_bmap_profiles


def execute_from_menu() -> None:
    print("\n" + "=" * 60)
    print("MODIFY BMAP PROFILE HEADER")
    print("=" * 60)
    print(
        "Edit profile headers (name, date, description, purpose) in a BMAP free format file."
    )

    print("\nSelect a BMAP free format file...")
    input_file = select_input_file("Select BMAP Free Format File")
    if not input_file:
        return

    try:
        profiles = read_bmap_freeformat(input_file)
    except (OSError, ValueError, TypeError) as e:
        try:
            from profcalc.cli.quick_tools.quick_tool_logger import (
                log_quick_tool_error,
            )

            log_quick_tool_error(
                "modify_bmap_header",
                f"Error reading file {input_file}: {e}",
            )
        except (ImportError, ModuleNotFoundError):
            # If central logger isn't available, ignore logging failure
            pass
        print(f"❌ Error reading file: {e}")
        input("Press Enter to continue...")
        return

    print(f"\nFound {len(profiles)} profiles:")
    for idx, prof in enumerate(profiles, 1):
        print(
            f"  {idx}. {prof.name} (Date: {getattr(prof, 'date', None) or '-'}; Desc: {getattr(prof, 'description', None) or '-'})"
        )

    try:
        prof_idx = int(input(f"\nSelect profile to edit [1-{len(profiles)}]: ")) - 1
        if not (0 <= prof_idx < len(profiles)):
            raise ValueError
    except ValueError:
        print("❌ Invalid selection.")
        input("Press Enter to continue...")
        return

    """
    Modify BMAP Free Format Profile Header - Menu Tool (curses-based)

    Allows interactive editing of BMAP profile headers (full header line) via a full-screen console UI.
    """

    def execute_from_menu() -> None:
        print("\n" + "=" * 60)
        print("MODIFY BMAP PROFILE HEADER (CURSES UI)")
        print("=" * 60)
        print("Edit BMAP profile header lines in a full-screen console UI.")

        print("\nSelect a BMAP free format file...")
        input_file = select_input_file("Select BMAP Free Format File")
        if not input_file:
            return

        try:
            profiles = read_bmap_freeformat(input_file)
        except (OSError, ValueError, TypeError) as e:
            try:
                from profcalc.cli.quick_tools.quick_tool_logger import (
                    log_quick_tool_error,
                )

                log_quick_tool_error(
                    "modify_bmap_header",
                    f"Error reading file {input_file}: {e}",
                )
            except (ImportError, ModuleNotFoundError):
                # If central logger isn't available, ignore logging failure
                pass
            print(f"❌ Error reading file: {e}")
            input("Press Enter to continue...")
            return

        # Prompt for date and purpose/description for all profiles
        date_str = input(
            "Enter a date to use for all profiles (or leave blank): "
        ).strip()
        purpose_str = input(
            "Enter a purpose or description for all profiles (or leave blank): "
        ).strip()

        # Prepare original and editable header lines
        orig_headers = []
        for prof in profiles:
            # Compose the original header as a single line (as written in file)
            # If raw_header is available, use it; else reconstruct
            if hasattr(prof, "raw_header") and prof.raw_header:
                orig_headers.append(prof.raw_header)
            else:
                parts = [prof.name]
                if getattr(prof, "date", None):
                    parts.append(str(prof.date))
                if getattr(prof, "description", None):
                    parts.append(str(prof.description))
                if getattr(prof, "purpose", None):
                    parts.append(str(prof.purpose))
                orig_headers.append(" ".join(parts))

        # Editable headers: field-aware (date, purpose)
        editable_headers = []
        for _ in orig_headers:
            editable_headers.append({"date": date_str, "purpose": purpose_str})

        def curses_header_editor(stdscr: Any) -> None:
            import curses
            import re

            curses.curs_set(1)
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            left_col_x = 2
            date_col_x = max_x // 3
            purpose_col_x = 2 * max_x // 3
            n = len(orig_headers)
            current = 0
            field = 0  # 0 = date, 1 = purpose
            edits = [dict(e) for e in editable_headers]
            dirty = False
            help_line = "Arrows: Move  Tab: Switch Field  PgUp/PgDn: Page  D: Set All Dates  P: Set All Purpose  g: Go to  /: Search  Enter: Edit  F2: Save  Esc: Cancel  h: Help"
            show_help = False
            window_size = max_y - 8 if max_y > 12 else 10
            scroll = 0

            def prompt_confirm(prompt: str) -> bool:
                stdscr.addstr(n + 6, left_col_x, prompt + " (y/n) ", curses.A_BOLD)
                stdscr.clrtoeol()
                stdscr.refresh()
                while True:
                    ch = stdscr.getch()
                    if ch in (ord("y"), ord("Y")):
                        return True
                    elif ch in (ord("n"), ord("N")):
                        return False

            def prompt_input(prompt: str) -> str:
                stdscr.addstr(n + 6, left_col_x, prompt, curses.A_BOLD)
                stdscr.clrtoeol()
                curses.echo()
                stdscr.refresh()
                inp = stdscr.getstr(n + 6, left_col_x + len(prompt), 40).decode("utf-8")
                curses.noecho()
                return inp

            def validate_date(val: str) -> bool:
                # Accept DDMMMYYYY (e.g., 07NOV2025) or blank
                if not val.strip():
                    return True
                return bool(re.match(r"^\d{2}[A-Z]{3}\d{4}$", val.strip()))

            def validate_purpose(val: str) -> bool:
                # Only allow letters, digits, spaces, and underscores
                import re

                return bool(re.match(r"^[A-Za-z0-9_ ]*$", val))

            def update_scroll() -> None:
                nonlocal scroll
                if current < scroll:
                    scroll = current
                elif current >= scroll + window_size:
                    scroll = current - window_size + 1
                scroll = max(0, min(scroll, max(0, n - window_size)))

            while True:
                stdscr.clear()
                stdscr.addstr(0, left_col_x, "Original Header", curses.A_BOLD)
                stdscr.addstr(0, date_col_x, "Date (DDMMMYYYY)", curses.A_BOLD)
                stdscr.addstr(0, purpose_col_x, "Purpose/Description", curses.A_BOLD)
                update_scroll()
                for idx in range(window_size):
                    i = scroll + idx
                    if i >= n:
                        break
                    stdscr.addstr(
                        idx + 2,
                        left_col_x,
                        orig_headers[i][: date_col_x - left_col_x - 1],
                    )
                    # Highlight current row/field
                    if i == current and field == 0:
                        stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(
                            idx + 2,
                            date_col_x,
                            (edits[i]["date"] or "")[: purpose_col_x - date_col_x - 1],
                        )
                        stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(
                            idx + 2,
                            date_col_x,
                            (edits[i]["date"] or "")[: purpose_col_x - date_col_x - 1],
                        )
                    if i == current and field == 1:
                        stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(
                            idx + 2,
                            purpose_col_x,
                            (edits[i]["purpose"] or "")[: max_x - purpose_col_x - 1],
                        )
                        stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(
                            idx + 2,
                            purpose_col_x,
                            (edits[i]["purpose"] or "")[: max_x - purpose_col_x - 1],
                        )
                # Show help or main instructions
                if show_help:
                    stdscr.addstr(
                        window_size + 4,
                        left_col_x,
                        "KEYS: ↑/k: Up  ↓/j: Down  Tab: Switch Field  PgUp/PgDn: Page  D: Set All Dates  P: Set All Purpose  g: Go to  /: Search  Enter: Edit  F2: Save  Esc: Cancel  h: Toggle Help",
                        curses.A_DIM,
                    )
                    stdscr.addstr(
                        window_size + 5,
                        left_col_x,
                        "Edit a field, then press F2 to save or Esc to cancel. Unsaved changes will prompt.",
                        curses.A_DIM,
                    )
                else:
                    stdscr.addstr(window_size + 4, left_col_x, help_line, curses.A_DIM)
                if dirty:
                    stdscr.addstr(
                        window_size + 5, left_col_x, "* Unsaved changes", curses.A_BOLD
                    )
                # Move cursor to current field
                if field == 0:
                    stdscr.move(
                        (current - scroll) + 2,
                        date_col_x + len(edits[current]["date"] or ""),
                    )
                else:
                    stdscr.move(
                        (current - scroll) + 2,
                        purpose_col_x + len(edits[current]["purpose"] or ""),
                    )
                stdscr.refresh()

                ch = stdscr.getch()
                if ch in (curses.KEY_UP, ord("k")):
                    if current > 0:
                        current -= 1
                        update_scroll()
                elif ch in (curses.KEY_DOWN, ord("j")):
                    if current < n - 1:
                        current += 1
                        update_scroll()
                elif ch == 9:  # Tab
                    field = (field + 1) % 2
                elif ch == curses.KEY_PPAGE:  # Page Up
                    current = max(0, current - window_size)
                    update_scroll()
                elif ch == curses.KEY_NPAGE:  # Page Down
                    current = min(n - 1, current + window_size)
                    update_scroll()
                elif ch in (curses.KEY_ENTER, 10, 13):
                    # Edit current field
                    if field == 0:
                        new_val = prompt_input("Edit date (DDMMMYYYY): ")
                        if validate_date(new_val):
                            if new_val != (edits[current]["date"] or ""):
                                edits[current]["date"] = new_val
                                dirty = True
                        else:
                            stdscr.addstr(
                                window_size + 6,
                                left_col_x,
                                "Invalid date format! Use DDMMMYYYY (e.g., 07NOV2025) or blank.",
                                curses.A_BOLD,
                            )
                            stdscr.refresh()
                            stdscr.getch()
                    else:
                        new_val = prompt_input("Edit purpose/description: ")
                        if validate_purpose(new_val):
                            if new_val != (edits[current]["purpose"] or ""):
                                edits[current]["purpose"] = new_val
                                dirty = True
                        else:
                            stdscr.addstr(
                                window_size + 6,
                                left_col_x,
                                "Invalid purpose: only letters, digits, spaces, and underscores are allowed.",
                                curses.A_BOLD,
                            )
                            stdscr.refresh()
                            stdscr.getch()
                elif ch == 27:  # ESC
                    if dirty:
                        if prompt_confirm("Discard unsaved changes?"):
                            return None
                        else:
                            continue
                    else:
                        return None
                elif ch == curses.KEY_F2:
                    return edits
                elif ch in (ord("h"), ord("H")):
                    show_help = not show_help
                elif ch in (ord("g"), ord("G")):
                    try:
                        val = prompt_input("Go to header #: ")
                        idx = int(val) - 1
                        if 0 <= idx < n:
                            current = idx
                            update_scroll()
                    except ValueError:
                        pass
                elif ch == ord("/"):
                    query = prompt_input("Search: ")
                    if query:
                        start = (current + 1) % n
                        found = None
                        for i in range(n):
                            idx = (start + i) % n
                            if (
                                query.lower() in (edits[idx]["date"] or "").lower()
                                or query.lower()
                                in (edits[idx]["purpose"] or "").lower()
                                or query.lower() in orig_headers[idx].lower()
                            ):
                                found = idx
                                break
                        if found is not None:
                            current = found
                            update_scroll()
                elif ch in (ord("D")):
                    # Bulk set all dates
                    new_val = prompt_input("Set date for ALL (DDMMMYYYY): ")
                    if validate_date(new_val):
                        for i in range(n):
                            if edits[i]["date"] != new_val:
                                edits[i]["date"] = new_val
                                dirty = True
                    else:
                        stdscr.addstr(
                            window_size + 6,
                            left_col_x,
                            "Invalid date format! Use DDMMMYYYY (e.g., 07NOV2025) or blank.",
                            curses.A_BOLD,
                        )
                        stdscr.refresh()
                        stdscr.getch()
                elif ch in (ord("P")):
                    # Bulk set all purpose
                    new_val = prompt_input("Set purpose/description for ALL: ")
                    if validate_purpose(new_val):
                        for i in range(n):
                            if edits[i]["purpose"] != new_val:
                                edits[i]["purpose"] = new_val
                                dirty = True
                    else:
                        stdscr.addstr(
                            window_size + 6,
                            left_col_x,
                            "Invalid purpose: only letters, digits, spaces, and underscores are allowed.",
                            curses.A_BOLD,
                        )
                        stdscr.refresh()
                        stdscr.getch()

        # Launch curses UI
        try:
            result = curses.wrapper(curses_header_editor)
        except curses.error as e:
            # Known curses-related failure (e.g., terminal doesn't support required features)
            print(f"❌ Error in curses UI: {e}")
            input("Press Enter to continue...")
            return
        except (RuntimeError, OSError, ValueError) as e:
            # Unexpected errors should be logged with the central quick-tool logger
            try:
                from profcalc.cli.quick_tools.quick_tool_logger import (
                    log_quick_tool_error,
                )

                log_quick_tool_error(
                    "modify_bmap_header",
                    f"Unexpected error in curses UI: {e}",
                    exc=e,
                )
            except (ImportError, ModuleNotFoundError):
                # best-effort logging; if logger is unavailable, continue to raise
                pass
            # Re-raise to avoid silently hiding bugs
            raise

        if result is None:
            print("Edit cancelled.")
            print("Press any key to return to the previous menu...")
            try:
                import msvcrt

                msvcrt.getch()
            except ImportError:
                import sys
                import termios
                import tty

                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return

        # Update profile headers with edited fields
        for prof, edit in zip(profiles, result):
            # Compose header as '<date> <purpose>'
            header = f"{edit['date']} {edit['purpose']}".strip()
            if hasattr(prof, "raw_header"):
                prof.raw_header = header
            else:
                # Fallback: set name to first word, rest to description
                parts = header.split()
                prof.name = parts[0] if parts else ""
                if len(parts) > 1:
                    prof.description = " ".join(parts[1:])

        # Save to new file
        out_file = input_file.replace(".bmap", "_headeredit.bmap")
        if out_file == input_file:
            out_file = input_file + "_headeredit"
        print(f"\nSaving modified file as: {out_file}")
        try:
            write_bmap_profiles(profiles, out_file)
            print(f"✅ Modified file written: {out_file}")
        except (OSError, IOError, ValueError) as e:
            try:
                from profcalc.cli.quick_tools.quick_tool_logger import (
                    log_quick_tool_error,
                )

                log_quick_tool_error(
                    "modify_bmap_header",
                    f"Error writing modified file {out_file}: {e}",
                )
            except (ImportError, ModuleNotFoundError):
                # If the central logger cannot be imported, ignore logging failure
                pass
            print(f"❌ Error writing file: {e}")

        # Save old/new header table to a .txt file
        table_file = (
            out_file.replace(".bmap", "_table.txt")
            if out_file.endswith(".bmap")
            else out_file + "_table.txt"
        )
        # Compose table: headers and aligned columns
        old_headers = orig_headers
        new_headers = [f"{edit['date']} {edit['purpose']}".strip() for edit in result]
        col1 = "Original Header"
        col2 = "New Header"
        col1_width = max(len(col1), max((len(h) for h in old_headers), default=0))
        col2_width = max(len(col2), max((len(h) for h in new_headers), default=0))
        sep = " | "
        header_line = f"{col1:<{col1_width}}{sep}{col2:<{col2_width}}"
        divider = f"{'-' * col1_width}{sep}{'-' * col2_width}"
        lines = [header_line, divider]
        for old, new in zip(old_headers, new_headers):
            lines.append(f"{old:<{col1_width}}{sep}{new:<{col2_width}}")
        table_str = "\n".join(lines)
        try:
            with open(table_file, "w", encoding="utf-8") as f:
                f.write(table_str)
            print(f"Table of changes saved as: {table_file}")
        except (OSError, IOError, ValueError) as e:
            print(f"❌ Error writing table file: {e}")

        print("Press any key to return to the previous menu...")
        try:
            import msvcrt

            msvcrt.getch()
        except ImportError:
            import sys
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
