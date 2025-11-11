# =============================================================================
# Terminal Color and Formatting Utilities
# =============================================================================
#
# FILE: src/profcalc/common/colors.py
#
# PURPOSE:
# This module provides consistent ANSI color codes and formatting functions
# for terminal output throughout the ProfCalc CLI interface. It ensures
# consistent, readable, and visually appealing output across all CLI tools
# and menu systems.
#
# WHAT IT'S FOR:
# - Provides standardized ANSI color codes for terminal output
# - Offers color classes and formatting functions for different message types
# - Supports both regular and bright color variants
# - Includes background colors and text styling options
# - Enables consistent visual hierarchy in CLI displays
# - Works well in both light and dark terminal themes
#
# WORKFLOW POSITION:
# This utility module is used throughout the CLI interface to provide visual
# formatting and improve user experience. It's imported by menu systems,
# CLI tools, and any component that needs formatted terminal output.
#
# LIMITATIONS:
# - Color output depends on terminal ANSI support
# - May not display correctly in all terminal environments
# - Color perception varies between users
# - Some terminals may not support all color codes
#
# ASSUMPTIONS:
# - Terminal environment supports basic ANSI color codes
# - Users prefer colored output over plain text
# - Color schemes enhance rather than hinder readability
# - Terminal width and color capabilities are adequate
#
# =============================================================================

"""Color utilities for terminal output.

This module provides consistent ANSI color codes and formatting functions
for use throughout the ProfCalc CLI interface. All colors are designed to
work well in both light and dark terminal themes.
"""

from typing import Any


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"

    # Text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"


# Semantic color schemes for consistent usage
class Theme:
    """Semantic color schemes for different UI elements."""

    # Headers and titles
    HEADER = Colors.BRIGHT_CYAN + Colors.BOLD
    SUBHEADER = Colors.BRIGHT_BLUE + Colors.BOLD

    # Menu elements
    MENU_TITLE = Colors.BRIGHT_YELLOW + Colors.BOLD
    MENU_OPTION = Colors.CYAN  # Menu items in cyan
    MENU_NUMBER = Colors.BRIGHT_GREEN + Colors.BOLD

    # Prompts and input
    PROMPT = Colors.YELLOW + Colors.BOLD  # Prompts asking for input in yellow
    PROMPT_DEFAULT = Colors.GREEN  # Default selections in green
    INPUT_HINT = Colors.BRIGHT_CYAN  # Input hints in bright cyan

    # Status messages
    SUCCESS = Colors.GREEN + Colors.BOLD  # Success messages in green
    WARNING = Colors.BRIGHT_YELLOW + Colors.BOLD  # Warning messages in bright yellow
    ERROR = Colors.RED + Colors.BOLD  # Error statements in red
    INFO = Colors.BRIGHT_BLUE  # Info messages in bright blue

    # Data display
    DATA_LABEL = Colors.BRIGHT_WHITE + Colors.BOLD  # Table headers in bright white
    DATA_VALUE = Colors.WHITE  # Data values in regular white
    DATA_HIGHLIGHT = Colors.BRIGHT_MAGENTA  # Highlighted data in bright magenta

    # Borders and separators
    BORDER = Colors.BRIGHT_BLACK  # Borders in bright black
    SEPARATOR = Colors.DIM  # Separators with dim text


def colorize(text: Any, color_code: str) -> str:
    """Apply ANSI color codes to text.

    Args:
        text: Text to colorize
        color_code: ANSI color code

    Returns:
        Colorized text string
    """
    return f"{color_code}{text}{Colors.RESET}"


def header(text: str) -> str:
    """Format text as a header."""
    return colorize(text, Theme.HEADER)


def subheader(text: str) -> str:
    """Format text as a subheader."""
    return colorize(text, Theme.SUBHEADER)


def menu_title(text: str) -> str:
    """Format text as a menu title."""
    return colorize(text, Theme.MENU_TITLE)


def menu_option(number: str, text: str) -> str:
    """Format a menu option with number and text."""
    return f"{colorize(number, Theme.MENU_NUMBER)}. {colorize(text, Theme.MENU_OPTION)}"


def prompt(text: str) -> str:
    """Format text as a prompt."""
    return colorize(text, Theme.PROMPT)


def prompt_with_default(prompt_text: str, default_value: str) -> str:
    """Format a prompt with a default value."""
    return f"{colorize(prompt_text, Theme.PROMPT)} {colorize(f'[{default_value}]', Theme.PROMPT_DEFAULT)}"


def success(text: str) -> str:
    """Format text as a success message."""
    return colorize(text, Theme.SUCCESS)


def warning(text: str) -> str:
    """Format text as a warning message."""
    return colorize(text, Theme.WARNING)


def error(text: str) -> str:
    """Format text as an error message."""
    return colorize(text, Theme.ERROR)


def info(text: str) -> str:
    """Format text as an info message."""
    return colorize(text, Theme.INFO)


def data_label(text: str) -> str:
    """Format text as a data label (table header - all caps bright white)."""
    return colorize(text.upper(), Theme.DATA_LABEL)


def data_value(text: str) -> str:
    """Format text as a data value."""
    return colorize(text, Theme.DATA_VALUE)


def data_highlight(text: str) -> str:
    """Format text as highlighted data."""
    return colorize(text, Theme.DATA_HIGHLIGHT)


def border(text: str = "", width: int = 60) -> str:
    """Create a border line."""
    if text:
        padding = (width - len(text) - 4) // 2
        left_pad = "=" * padding
        right_pad = "=" * (width - len(text) - 4 - padding)
        return colorize(f"{left_pad} {text} {right_pad}", Theme.BORDER)
    else:
        return colorize("=" * width, Theme.BORDER)


def separator(width: int = 60) -> str:
    """Create a separator line."""
    return colorize("-" * width, Theme.SEPARATOR)


def print_header(text: str, width: int = 60) -> None:
    """Print a formatted header."""
    print()
    print(border(text.upper(), width))
    print()


def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print()
    print(subheader(text))
    print()


def print_menu_title(text: str) -> None:
    """Print a formatted menu title."""
    print()
    print(menu_title(text))
    print()


def print_separator(width: int = 60) -> None:
    """Print a separator line."""
    print(separator(width))


def print_success(text: str) -> None:
    """Print a success message."""
    print(success(f"✅ {text}"))


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(warning(f"⚠️  {text}"))


def print_error(text: str) -> None:
    """Print an error message."""
    print(error(f"❌ {text}"))


def print_info(text: str) -> None:
    """Print an info message."""
    print(info(f"ℹ️  {text}"))


# Enhanced UI Components


def print_table(headers: list[str], rows: list[list[str]], width: int = 80) -> None:
    """Print a formatted table with borders and proper alignment.

    Args:
        headers: List of column header strings
        rows: List of rows, where each row is a list of cell values
        width: Maximum table width
    """
    if not headers or not rows:
        return

    # Calculate column widths
    all_rows = [headers] + rows
    col_widths = []
    for i in range(len(headers)):
        col_values = [str(row[i]) if i < len(row) else "" for row in all_rows]
        col_widths.append(max(len(val) for val in col_values))

    # Ensure total width doesn't exceed limit
    total_width = sum(col_widths) + len(col_widths) * 3 + 1
    if total_width > width:
        # Scale down column widths proportionally
        scale_factor = width / total_width
        col_widths = [max(3, int(w * scale_factor)) for w in col_widths]

    # Create border characters
    top_border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    mid_border = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    bot_border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

    print(colorize(top_border, Theme.BORDER))

    # Print header row
    header_cells = []
    for i, header in enumerate(headers):
        cell = colorize(header.upper(), Theme.DATA_LABEL)
        header_cells.append(cell.center(col_widths[i] + 2))
    print("│" + "│".join(header_cells) + "│")

    print(colorize(mid_border, Theme.BORDER))

    # Print data rows
    for row in rows:
        row_cells = []
        for i in range(len(headers)):
            value = str(row[i]) if i < len(row) else ""
            cell = colorize(value, Theme.DATA_VALUE)
            row_cells.append(cell.ljust(col_widths[i] + 2))
        print("│" + "│".join(row_cells) + "│")

    print(colorize(bot_border, Theme.BORDER))


def status_badge(text: str, status: str) -> str:
    """Create a colored status badge.

    Args:
        text: The status text
        status: Status type ('success', 'warning', 'error', 'info', 'processing')

    Returns:
        Formatted status badge string
    """
    badges = {
        "success": ("[✓]", Theme.SUCCESS),
        "warning": ("[!]", Theme.WARNING),
        "error": ("[✗]", Theme.ERROR),
        "info": ("[i]", Theme.INFO),
        "processing": ("[○]", Theme.DATA_HIGHLIGHT),
        "ready": ("[●]", Theme.SUCCESS),
        "pending": ("[○]", Theme.WARNING),
    }

    badge, color = badges.get(status.lower(), ("[?]", Theme.DATA_VALUE))
    return f"{colorize(badge, color)} {colorize(text, color)}"


def print_status(text: str, status: str) -> None:
    """Print a status message with badge.

    Args:
        text: The status text
        status: Status type
    """
    print(status_badge(text, status))


def print_section(title: str, content: list[str], width: int = 60) -> None:
    """Print a formatted section with title and content.

    Args:
        title: Section title
        content: List of content lines
        width: Section width
    """
    print()
    print(border(title.upper(), width))
    print()
    for line in content:
        print(f"  {line}")
    print()
    print(separator(width))


def center_text(text: str, width: int = 60) -> str:
    """Center text within a given width.

    Args:
        text: Text to center
        width: Total width

    Returns:
        Centered text string
    """
    return text.center(width)


def indent_text(text: str, indent: int = 4) -> str:
    """Indent text by a specified number of spaces.

    Args:
        text: Text to indent
        indent: Number of spaces to indent

    Returns:
        Indented text string
    """
    return " " * indent + text


def print_shortcuts(shortcuts: dict[str, str]) -> None:
    """Print formatted keyboard shortcuts.

    Args:
        shortcuts: Dictionary of shortcut -> description
    """
    print()
    print(info("Available shortcuts:"))
    for key, desc in shortcuts.items():
        print(
            f"  {colorize(key, Theme.DATA_HIGHLIGHT)} - {colorize(desc, Theme.INPUT_HINT)}"
        )
    print()


def print_help(help_text: str | list[str]) -> None:
    """Print context-sensitive help text.

    Args:
        help_text: Help text (string or list of strings)
    """
    print()
    print(colorize("HELP", Theme.HEADER))
    print(separator())

    if isinstance(help_text, str):
        help_text = [help_text]

    for line in help_text:
        print(colorize(line, Theme.INPUT_HINT))
    print()


def print_confirmation(message: str) -> None:
    """Print a confirmation prompt with colored options.

    Args:
        message: Confirmation message
    """
    print()
    print(colorize(message, Theme.PROMPT))
    print(f"  {colorize('Y', Theme.SUCCESS)} - Yes")
    print(f"  {colorize('N', Theme.ERROR)} - No")
    print(f"  {colorize('[Enter]', Theme.PROMPT_DEFAULT)} - Default (Yes)")
    print()


def print_selection(
    options: list[str], default_index: int = 0, title: str = "Select an option:"
) -> None:
    """Print a selection menu with numbered options.

    Args:
        options: List of option strings
        default_index: Index of default selection (0-based)
        title: Menu title
    """
    print()
    print(colorize(title, Theme.PROMPT))
    print()

    for i, option in enumerate(options, 1):
        marker = "►" if i - 1 == default_index else " "
        color = Theme.DATA_HIGHLIGHT if i - 1 == default_index else Theme.MENU_OPTION
        print(
            f"  {marker} {colorize(str(i), Theme.MENU_NUMBER)}. {colorize(option, color)}"
        )

    if default_index >= 0 and default_index < len(options):
        print()
        print(colorize(f"Default: {options[default_index]}", Theme.PROMPT_DEFAULT))

    print()


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H]", end="")
