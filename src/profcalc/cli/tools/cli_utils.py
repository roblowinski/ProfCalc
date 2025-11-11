# =============================================================================
# CLI Formatting and User Interaction Utilities
# =============================================================================
#
# FILE: src/profcalc/cli/tools/cli_utils.py
#
# PURPOSE:
# This module provides reusable utilities for CLI (Command-Line Interface)
# formatting, user interaction, and terminal management. It offers consistent
# styling, input handling, and display formatting across all CLI tools in
# ProfCalc.
#
# WHAT IT'S FOR:
# - Provides consistent terminal formatting and color schemes
# - Offers reusable input prompting with default value handling
# - Manages screen clearing and section breaks for better UX
# - Supports colored output for different types of messages
# - Enables consistent CLI appearance across all tools
# - Handles platform-specific terminal operations
#
# WORKFLOW POSITION:
# This utility module is used throughout the CLI tools to maintain consistent
# user interface patterns. It's imported by various CLI modules that need
# formatted output, user prompts, or terminal management functionality.
#
# LIMITATIONS:
# - Color output depends on terminal capabilities and colorama library
# - Screen clearing may not work in all terminal environments
# - Platform-specific operations may behave differently across systems
# - Color schemes may not be visible in some terminal configurations
#
# ASSUMPTIONS:
# - Terminal/console environment supports basic ANSI color codes
# - Colorama library is available for cross-platform color support
# - Users prefer formatted, colorful CLI output over plain text
# - Terminal width is sufficient for formatted displays
#
# =============================================================================

"""CLI utilities for formatting and user interaction.

Reusable helpers for CLI formatting and simple interactive prompts used by
the menu-driven quick tools.

Usage examples:
    - Import helpers in a tool module::

            from profcalc.cli.tools.cli_utils import print_header, prompt_input

    - Use :func:`prompt_input` to ask the user for values with defaults.
"""

import os
from typing import Any, Optional

from colorama import Fore, Style


def clear_screen() -> None:
    """Clear the terminal screen using platform-specific commands."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, color: Any = Fore.CYAN) -> None:
    """Print a formatted header with a title."""
    print()
    print(color + Style.BRIGHT + "=" * 70)
    print(f"{title:^70}")
    print("=" * 70 + Style.RESET_ALL)
    print()


def print_section_break() -> None:
    """Print a section break for spacing."""
    print()
    print(Fore.WHITE + "-" * 70 + Style.RESET_ALL)
    print()


def prompt_input(
    message: str, default: Optional[str] = None, color: Any = Fore.YELLOW
) -> str:
    """Prompt the user for input with an optional default value."""
    if default is not None:
        prompt_text = f"{color}{message} [{default}]: {Style.RESET_ALL}"
    else:
        prompt_text = f"{color}{message}: {Style.RESET_ALL}"

    response = input(prompt_text).strip()

    # Return default if user just pressed Enter
    if not response and default is not None:
        return default
    return response
