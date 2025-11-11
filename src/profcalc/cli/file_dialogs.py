# =============================================================================
# Shared Tkinter File Dialog Utilities
# =============================================================================
#
# FILE: src/profcalc/cli/file_dialogs.py
#
# PURPOSE:
# This module provides a unified set of tkinter-based file and directory
# selection dialogs for use across all ProfCalc CLI tools. It replaces manual
# text-based file path input with user-friendly graphical dialogs, improving
# the overall user experience and reducing input errors.
#
# WHAT IT'S FOR:
# - Provides consistent file selection interface across all CLI tools
# - Enables graphical file browsing instead of manual path typing
# - Supports single file selection, multiple file selection, and directory selection
# - Handles both input file selection and output file specification
# - Ensures dialogs appear on top and are properly cleaned up after use
#
# WORKFLOW POSITION:
# This utility module sits between the CLI tools and the underlying tkinter
# library. It's used throughout the CLI workflow whenever users need to specify
# file paths or directories. Individual tools import these functions instead of
# implementing their own file dialogs, ensuring consistency and maintainability.
#
# LIMITATIONS:
# - Requires tkinter to be available (typically included with Python installations)
# - Needs a graphical environment - won't work in headless/server environments
# - Dialog behavior may vary slightly across different operating systems
# - Cannot be used in automated scripts without user interaction
# - File type filtering is not implemented (shows all files by design)
#
# ASSUMPTIONS:
# - Tkinter is installed and functional on the user's system
# - User has access to a graphical desktop environment
# - Dialogs are used in interactive contexts where user input is expected
# - Users prefer graphical file selection over manual path entry
# - Cross-platform compatibility is important (works on Windows, macOS, Linux)
# - Dialog windows should be brought to the front for immediate user attention
#
# =============================================================================

"""Shared tkinter file dialog utilities for CLI tools."""

import tkinter as tk
from tkinter import filedialog


def select_input_file(title: str = "Select Input File", initial_dir: str = ".") -> str:
    """Show file dialog to select an input file.

    Args:
        title: Dialog window title
        initial_dir: Initial directory to open

    Returns:
        Selected file path or empty string if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)  # Bring dialog to front

    file_path = filedialog.askopenfilename(
        title=title,
        initialdir=initial_dir,
    )

    root.destroy()
    return file_path if file_path else ""


def select_output_file(
    title: str = "Select Output File", initial_file: str = "", initial_dir: str = "."
) -> str:
    """Show file dialog to select an output file.

    Args:
        title: Dialog window title
        initial_file: Suggested filename
        initial_dir: Initial directory to open

    Returns:
        Selected file path or empty string if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)  # Bring dialog to front

    file_path = filedialog.asksaveasfilename(
        title=title,
        initialfile=initial_file,
        initialdir=initial_dir,
    )

    root.destroy()
    return file_path if file_path else ""


def select_directory(title: str = "Select Directory", initial_dir: str = ".") -> str:
    """Show directory selection dialog.

    Args:
        title: Dialog window title
        initial_dir: Initial directory to open

    Returns:
        Selected directory path or empty string if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)  # Bring dialog to front

    dir_path = filedialog.askdirectory(
        title=title,
        initialdir=initial_dir,
    )

    root.destroy()
    return dir_path if dir_path else ""


def select_multiple_files(
    title: str = "Select Files", initial_dir: str = "."
) -> list[str]:
    """Show file dialog to select multiple input files.

    Args:
        title: Dialog window title
        initial_dir: Initial directory to open

    Returns:
        List of selected file paths, empty list if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)  # Bring dialog to front

    file_paths = filedialog.askopenfilenames(
        title=title,
        initialdir=initial_dir,
    )

    root.destroy()
    return list(file_paths) if file_paths else []
