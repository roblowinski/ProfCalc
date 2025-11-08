"""CLI utilities for formatting and user interaction.

Reusable helpers for CLI formatting and simple interactive prompts used by
the menu-driven quick tools.

Usage examples:
    - Import helpers in a tool module::

            from profcalc.cli.tools.cli_utils import print_header, prompt_input

    - Use :func:`prompt_input` to ask the user for values with defaults.
"""

import os

from colorama import Fore, Style


def clear_screen():
    """Clear the terminal screen using platform-specific commands."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, color=Fore.CYAN):
    """Print a formatted header with a title."""
    print()
    print(color + Style.BRIGHT + "=" * 70)
    print(f"{title:^70}")
    print("=" * 70 + Style.RESET_ALL)
    print()

def print_section_break():
    """Print a section break for spacing."""
    print()
    print(Fore.WHITE + "-" * 70 + Style.RESET_ALL)
    print()

def prompt_input(message, default=None, color=Fore.YELLOW):
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
