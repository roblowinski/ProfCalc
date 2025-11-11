# =============================================================================
# ProfCalc Interactive Menu System
# =============================================================================
#
# FILE: src/profcalc/cli/menu_system.py
#
# PURPOSE:
# This module implements the comprehensive interactive menu system for ProfCalc,
# providing a hierarchical, user-friendly command-line interface to all analysis
# tools and utilities. It organizes complex coastal profile analysis workflows
# into logical menu categories and handles user navigation, input validation,
# and tool execution.
#
# WHAT IT'S FOR:
# - Provides hierarchical menu navigation for all ProfCalc functionality
# - Organizes tools into logical categories (Data Management, Annual Monitoring, etc.)
# - Handles user input validation and error recovery
# - Manages data source selection (file-based with database placeholders)
# - Provides consistent user experience across all analysis tools
# - Supports both guided workflows and direct tool access
#
# WORKFLOW POSITION:
# This file sits at the center of the CLI user experience, bridging the gap between
# raw command-line execution and structured analysis workflows. It coordinates
# between data management, analysis tools, and user interaction, ensuring that
# complex multi-step processes are presented in an intuitive, guided manner.
#
# LIMITATIONS:
# - Requires interactive terminal environment for menu display
# - Menu navigation can be slower than direct command execution
# - Large file with many functions - could benefit from modularization
# - Some database integration features are placeholder-only
# - Error handling depends on user acknowledgement for continuation
#
# ASSUMPTIONS:
# - Users prefer guided, menu-driven workflows over command-line arguments
# - Terminal/console environment supports ANSI color codes for formatting
# - Users need clear navigation and help text for complex analysis tasks
# - File-based data sources are primary (database integration is future enhancement)
# - Interactive input methods (like file dialogs) are available and functional
# - Users understand basic menu navigation concepts (numbers, back/cancel options)
#
# =============================================================================

"""Interactive Menu System for ProfCalc.

This module provides the command-line interface for ProfCalc, offering
a hierarchical menu system for accessing various analysis tools and
utilities. The menu system supports both database and file-based data
sources, with placeholders for future database integration.

The menu is organized into logical workflows:
- Data Management: Source selection and data operations
- Annual Monitoring: Shoreline analysis and reporting tools
- Profile Analysis: Survey comparison and volumetric calculations
- Quick Tools: Utility functions for common tasks
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Use the package-level data tools to keep dataset registration centralized
from profcalc.cli.file_dialogs import select_input_file
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.tools import data as data_tools
from profcalc.common.colors import (
    menu_option,
    print_header,
    print_menu_title,
    success,
)


def notify_and_wait(
    message: str,
    prompt: str = "Press Enter to continue...",
) -> None:
    """Print a message and wait for user acknowledgement.

    This helper prints the provided message and then
    prompts the user with a simple Enter-to-continue prompt.

    Parameters:
        message: The message to display before waiting
        prompt: The prompt to show when waiting for user input
    """
    print(message)
    try:
        input(prompt)
    except (KeyboardInterrupt, EOFError):
        # Treat interrupt like a normal acknowledgement in interactive use
        print("")


# Simple session context for storing user choices
class AppState:
    """Lightweight application state for the interactive menu.

    We keep only a minimal set of attributes here (data_source selection and
    optional details). Dataset registration and active dataset are handled by
    `profcalc.cli.tools.data.session` so the menu delegates to that module for
    data operations.
    """

    def __init__(self) -> None:
        """Initialize the application state with default values."""
        self.data_source: str | None = None
        self.data_source_details: str | None = None


app_state = AppState()


def main_menu() -> None:
    """Display and handle the main ProfCalc menu.

    Provides access to all major ProfCalc functionality through a numbered menu:
    - Data Management
    - Annual Monitoring Report Analyses
    - File Conversion Tools
    - Profile Analysis Tools
    - Batch Processing
    - Configuration & Settings
    - Quick Tools
    - Help & Documentation
    - Exit
    """
    while True:
        print_header("ProfCalc - Coastal Profile Analysis")
        print_menu_title("Main Menu")
        print(menu_option("1", "Data Management"))
        print(menu_option("2", "Annual Monitoring Report Analyses"))
        print(menu_option("3", "File Conversion Tools"))
        print(menu_option("4", "Profile Analysis Tools"))
        print(menu_option("5", "Batch Processing"))
        print(menu_option("6", "Configuration & Settings"))
        print(menu_option("7", "Quick Tools"))
        print(menu_option("8", "Help & Documentation"))
        print(menu_option("9", "Exit"))
        print()
        choice = input("Select an option: ").strip()

        if choice == "1":
            data_management_menu()
        elif choice == "2":
            annual_monitoring_menu()
        elif choice == "3":
            # File Conversion Tools
            conversion_submenu()
        elif choice == "4":
            # Profile Analysis Tools
            profcalc_profcalc_menu()
        elif choice == "8":
            # Help & Documentation
            about()
        elif choice == "9":
            print()
            print(success("Goodbye!"))
            # Return from main_menu to allow clean shutdown of the launcher
            return
        elif choice == "5":
            print("Batch Processing - Coming Soon!")
        elif choice == "6":
            print("Configuration & Settings - Coming Soon!")
        elif choice == "7":
            quick_tools_menu()
        else:
            print("Invalid selection. Please try again.")


def ensure_data_source() -> None:
    """Prompt the user to select a data source if one is not already set.

    This convenience prompts once when entering Data Management so users
    choose File/Database/Session up-front. Import is optional when choosing
    File.
    """
    if app_state.data_source:
        return

    print("\nNo data source configured. Select data source:")
    print("1. Load from file")
    print("2. Connect to database")
    print("3. Use in-memory session (no external source)")
    choice = input("Select a source [1/2/3]: ").strip()
    if choice == "1":
        app_state.data_source = "file"
        path = select_input_file("Select 9-column data file")
        if not path:
            print("Import cancelled.")
            return
            try:
                result = data_tools.import_data(path)
                imported = result.get("imported") if isinstance(result, dict) else "?"
                print(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Import failed during ensure_data_source: {exc}",
                    exc=exc,
                )
                print(f"Import failed: {exc}")
    elif choice == "2":
        app_state.data_source = "database"
        app_state.data_source_details = None
        print("\n[INFO] Database mode selected. (DB connection not yet implemented)")
    else:
        app_state.data_source = "session"
        print("\n[INFO] Using in-memory session (no external source configured).")


def data_management_menu() -> None:
    """Display and handle the Data Management menu.

    Provides data management operations:
    - Change Data Source
    - Import/Export Data (stub)
    - View Data Summary (stub)
    """
    # Prompt for data source up-front if none selected
    ensure_data_source()

    while True:
        print_header("Data Management")
        print_menu_title("Data Operations")
        print(
            menu_option(
                "1",
                f"Select Data Source (Current: {app_state.data_source or 'Not Set'})",
            )
        )
        print(menu_option("2", "Import Data (9-col CSV)"))
        print(menu_option("3", "List Registered Datasets"))
        print(menu_option("4", "Select Active Dataset"))
        print(menu_option("5", "View Data Summary"))
        print(menu_option("6", "Back to Main Menu"))
        print()
        choice = input("Select an option: ").strip()
        if choice == "1":
            ensure_data_source()
        elif choice == "2":
            path = select_input_file("Select 9-column CSV file to import")
            if not path:
                print("Import cancelled.")
                continue
            try:
                result = data_tools.import_data(path)
                imported = result.get("imported") if isinstance(result, dict) else "?"
                print(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Import failed in data_management_menu: {exc}",
                    exc=exc,
                )
                print(f"Import failed: {exc}")
        elif choice == "3":
            data_tools.list_datasets()
        elif choice == "4":
            dsid = input(
                "Enter dataset ID to set active (or blank to cancel): "
            ).strip()
            if not dsid:
                print("Selection cancelled.")
                continue
            try:
                data_tools.select_dataset(dsid)
            except (
                KeyError,
                ValueError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to select dataset: {exc}")
        elif choice == "5":
            data_tools.summary()
        elif choice == "6":
            break
        else:
            print("Invalid selection. Please try again.")


def annual_monitoring_menu() -> None:
    """Display and handle the Annual Monitoring Report Analyses menu.

    Provides access to shoreline monitoring and analysis tools:
    - Import Survey Data
    - Profile Analysis
    - Shoreline Analysis
    - Condition Evaluation
    - Reporting & Export
    - Run XOn/XOff Volume Tool
    """
    while True:
        print_header("Annual Monitoring Report Analyses")
        print_menu_title("Monitoring Tools")
        print(menu_option("1", "Import Survey Data"))
        print(menu_option("2", "Compute Annual Erosion Rate (AER)"))
        print(menu_option("3", "Profile Analysis"))
        print(menu_option("4", "Shoreline Analysis"))
        print(menu_option("5", "Condition Evaluation"))
        print(menu_option("6", "Reporting & Export"))
        print(menu_option("7", "Back to Main Menu"))
        print()
        choice = input("Select an option: ").strip()
        if choice == "1":
            # Prompt for a survey file and import using the shared data tools
            path = select_input_file("Select CSV file to import")
            if not path:
                print("Import cancelled.")
                continue
            try:
                res = data_tools.import_data(path)
                imported = res.get("imported") if isinstance(res, dict) else "?"
                print(f"Imported {imported} rows from {path}.")
                # Make success explicit and pause so the user can see the result
                notify_and_wait("Import successful.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error("menu_system", f"Import failed: {exc}", exc=exc)
                notify_and_wait(f"Import failed: {exc}")
        elif choice == "2":
            # Compute AER via the Annual tools handler
            try:
                from profcalc.cli.tools import annual as annual_tools

                annual_tools.compute_aer()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system", f"Failed to run AER handler: {exc}", exc=exc
                )
                print(f"Failed to run AER handler: {exc}")
        elif choice == "3":
            # Profile Analysis submenu
            profcalc_profcalc_menu()
        elif choice == "4":
            # Shoreline Analysis submenu
            shoreline_analysis_menu()
        elif choice == "5":
            # Condition Evaluation (stub)
            print("[STUB] Condition Evaluation - Not yet implemented.")
        elif choice == "6":
            # Reporting & Export (stub)
            print("[STUB] Reporting & Export - Not yet implemented.")
        elif choice == "7":
            # Back to Main Menu
            break
        else:
            print("Invalid selection. Please try again.")


def shoreline_analysis_menu() -> None:
    """Display and handle the Shoreline Analysis workflow submenu.

    Provides a workflow-centric menu for shoreline analysis with steps:
    - Extract & Prepare Shoreline Data
    - Calculate Shoreline Metrics
    - Summarize & Review Results
    - Export Results

    Note: All analysis steps are currently stub implementations.
    """
    while True:
        print("\n--- Shoreline Analysis (Annual Monitoring) ---")
        print("1. Extract & Prepare Shoreline Data")
        print("2. Calculate Shoreline Metrics")
        print("3. Summarize & Review Results")
        print("4. Export Results")
        print("5. Back to Annual Monitoring Menu")
        choice = input("Select an option: ").strip()
        if choice == "1":
            print("[STUB] Extract & Prepare Shoreline Data - Not yet implemented.")
        elif choice == "2":
            print("[STUB] Calculate Shoreline Metrics - Not yet implemented.")
        elif choice == "3":
            print("[STUB] Summarize & Review Results - Not yet implemented.")
        elif choice == "4":
            print("[STUB] Export Results - Not yet implemented.")
        elif choice == "5":
            break
        else:
            print("Invalid selection. Please try again.")


def profcalc_profcalc_menu() -> None:
    """Display and handle the Profile Analysis Tools menu.

    Provides access to profile analysis workflows:
    - Survey vs. Design Template Analysis
    - Survey vs. Survey (Multi-Year) Analysis
    """
    while True:
        print("\n--- Profile Analysis ---")
        print(f"[Current Data Source: {app_state.data_source or 'Not Set'}]")
        print("1. Survey vs. Design Template Analysis")
        print("2. Survey vs. Survey (Multi-Year) Analysis")
        print("3. Back to Main Menu")
        choice = input("Select an option: ").strip()
        if choice == "1":
            survey_vs_design_menu()
        elif choice == "2":
            survey_vs_survey_menu()
        elif choice == "3":
            break
        else:
            print("Invalid selection. Please try again.")


def survey_vs_design_menu() -> None:
    """Display and handle the Survey vs. Design Template Analysis menu.

    Provides workflow steps for comparing survey data against design templates:
    - Prepare & Load Data
    - Pair & Align Profiles
    - Compute Volumes
    - Review & Export Results
    - Run Full Workflow

    Note: All options are currently stub implementations.
    """
    while True:
        print("\n--- Survey vs. Design Template Analysis ---")
        print("1. Prepare & Load Data (survey, template, azimuth)")
        print("2. Pair & Align Profiles")
        print("3. Compute Volumes (interpolate, distance, area, wedge)")
        print("4. Review & Export Results")
        print("5. Run Full Workflow")
        print("6. Back to Profile Analysis Menu")
        choice = input("Select an option: ").strip()
        if choice == "6":
            break
        else:
            print(f"[STUB] Option {choice} not yet implemented.")


def survey_vs_survey_menu() -> None:
    """Display and handle the Survey vs. Survey (Multi-Year) Analysis menu.

    Provides workflow steps for comparing multiple survey datasets:
    - Prepare & Load Data
    - Select Comparison Mode
    - Pair & Align Profiles
    - Compute Volumes for Selected Comparisons
    - Review & Export Results
    - Run Full Workflow

    Note: All options are currently stub implementations.
    """
    while True:
        print("\n--- Survey vs. Survey (Multi-Year) Analysis ---")
        print("1. Prepare & Load Data (multiple surveys, azimuth)")
        print("2. Select Comparison Mode (adjacent, custom, all-vs-all)")
        print("3. Pair & Align Profiles")
        print("4. Compute Volumes for Selected Comparisons")
        print("5. Review & Export Results")
        print("6. Run Full Workflow")
        print("7. Back to Profile Analysis Menu")
        choice = input("Select an option: ").strip()
        if choice == "7":
            break
        else:
            print(f"[STUB] Option {choice} not yet implemented.")


def cross_sectional_analysis(state: "AppState") -> None:
    """Perform cross-sectional analysis.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Cross-sectional analysis not yet implemented.")


def volumetric_change(state: "AppState") -> None:
    """Analyze volumetric changes between surveys.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Volumetric change analysis not yet implemented.")


def shoreline_change(state: "AppState") -> None:
    """Analyze shoreline position changes over time.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Shoreline change analysis not yet implemented.")


def temporal_trends(state: "AppState") -> None:
    """Analyze temporal trends in profile data.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Temporal trends analysis not yet implemented.")


def outlier_detection(state: "AppState") -> None:
    """Detect outliers in profile datasets.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Outlier detection not yet implemented.")


def statistics_summaries(state: "AppState") -> None:
    """Generate statistical summaries of profile data.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Statistics & summaries not yet implemented.")


def export_results(state: "AppState") -> None:
    """Export analysis results to various formats.

    Args:
        session: Current session context with data source information.

    Note: This function is currently a stub implementation.
    """
    print("[STUB] Export results not yet implemented.")


def quick_tools_menu() -> None:
    """Display and handle the Quick Tools submenu.

    Provides access to utility functions for common tasks:
    - Fix BMAP point counts (correct profile point counts)
    - Convert File Format & Create Shapefiles
    - Get an Inventory of Profiles from a BMap File
    - Assign Profile Names to XYZ/CSV Files Missing Profile IDs
    """
    while True:
        print_header("Quick Tools")
        print_menu_title("Available Tools")
        print(menu_option("1", "Correct BMAP Free Format Profile Point Count"))
        print(menu_option("2", "Find Common X Bounds and Y Bounds in Profile Group"))
        print(menu_option("3", "Inventory of Profiles from Multi-Profile File"))
        print(menu_option("4", "Assign Missing Profile Names in a XYZ/CSV File"))
        print(menu_option("5", "Modify BMAP Free Format Profile Headers"))
        print(menu_option("6", "Retrieve Survey Dates for a Profile from 9-Col File"))
        print(menu_option("7", "Scan a folder for profiles (Profile Scanner)"))
        print(menu_option("8", "Return to Main Menu"))
        print()
        choice = input("Select a quick tool: ").strip()

        if choice == "1":
            try:
                from profcalc.cli.quick_tools import fix_bmap as fix_bmap_tool

                fix_bmap_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to run BMAP fixer tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to run BMAP fixer tool: {exc}")

        elif choice == "2":
            try:
                # Use importlib to ensure monkeypatched sys.modules entries (tests)
                import importlib

                bounds_tool = importlib.import_module("profcalc.cli.quick_tools.bounds")
                if hasattr(bounds_tool, "execute_from_menu"):
                    bounds_tool.execute_from_menu()
                else:
                    raise AttributeError("bounds tool missing execute_from_menu")
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system", f"Failed to run bounds tool: {exc}", exc=exc
                )
                print(f"Failed to run bounds tool: {exc}")

        elif choice == "3":
            try:
                import importlib

                inventory_tool = importlib.import_module(
                    "profcalc.cli.quick_tools.inventory"
                )
                if hasattr(inventory_tool, "execute_from_menu"):
                    inventory_tool.execute_from_menu()
                else:
                    raise AttributeError("inventory tool missing execute_from_menu")
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to run inventory tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to run inventory tool: {exc}")

        elif choice == "4":
            try:
                from profcalc.cli.quick_tools import assign as assign_tool

                assign_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system", f"Failed to run assign tool: {exc}", exc=exc
                )
                print(f"Failed to run assign tool: {exc}")

        elif choice == "5":
            try:
                from profcalc.cli.quick_tools import fix_bmap as fix_bmap_tool

                # fix_bmap module provides an interactive header modification helper
                if hasattr(fix_bmap_tool, "execute_modify_headers_menu"):
                    fix_bmap_tool.execute_modify_headers_menu()
                else:
                    print(
                        "Header modification tool is not available in fix_bmap module."
                    )
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to run header modification tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to run header modification tool: {exc}")

        elif choice == "6":
            try:
                from profcalc.cli.quick_tools import (
                    get_profile_dates as get_profile_dates_tool,
                )
            except (ImportError, AttributeError) as exc:
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to import get_profile_dates tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to import get_profile_dates tool: {exc}")
                notify_and_wait("", prompt="\nPress Enter to continue...")
                continue
            try:
                get_profile_dates_tool.execute_from_menu()
            except (ImportError, AttributeError, OSError, ValueError) as exc:
                # Catch common runtime/import errors from the tool execution
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to run get_profile_dates tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to run get_profile_dates tool: {exc}")
            notify_and_wait("", prompt="\nPress Enter to continue...")

        elif choice == "7":
            try:
                from profcalc.cli.quick_tools import (
                    profile_scanner as profile_scanner_tool,
                )

                if hasattr(profile_scanner_tool, "execute_from_menu"):
                    profile_scanner_tool.execute_from_menu()
                else:
                    raise AttributeError(
                        "profile_scanner tool missing execute_from_menu"
                    )
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                log_quick_tool_error(
                    "menu_system",
                    f"Failed to run profile scanner tool: {exc}",
                    exc=exc,
                )
                print(f"Failed to run profile scanner tool: {exc}")

        elif choice == "8":
            # Return to previous menu
            break

        else:
            print("Invalid selection. Please try again.")


def conversion_submenu() -> None:
    """Display and handle the Conversion submenu under Quick Tools option 2.

    Provides options for converting between different file formats:
    - BMAP Free Format to XYZ/9-Col
    - BMAP Free Format to Shapefile
    - XYZ/9-Col to BMAP Free Format
    - XYZ/9-Col to Shapefile
    - Point Shapefile conversions

    Note: All conversion options are currently stub implementations.
    """
    while True:
        print_header("File Conversion Tools")
        print_menu_title("Conversion Options")
        print(menu_option("1", "BMAP Free Format to XYZ/9-Col"))
        print(menu_option("2", "BMAP Free Format to Shapefile"))
        print(menu_option("3", "XYZ/9-Col to BMAP Free Format"))
        print(menu_option("4", "XYZ/9-Col to Shapefile"))
        print(menu_option("5", "Point Shapefile to BMAP Free Format"))
        print(menu_option("6", "Point Shapefile to XYZ/9-Col"))
        print(menu_option("7", "Return to Previous Menu"))
        print()
        choice = input("Select a conversion: ").strip()

        if choice == "1":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "2":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "3":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "4":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "5":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "6":
            try:
                from profcalc.cli.quick_tools import convert as convert_tool

                convert_tool.execute_from_menu()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run conversion tool: {exc}")
        elif choice == "7":
            break
        else:
            print("Invalid selection. Please try again.")


def launch_menu() -> None:
    """Launch the interactive menu system."""
    # Start at the main menu immediately. Data source selection is handled
    # by the Data Management menu (or by individual tools) when needed.
    main_menu()


def _retrieve_profile_date_range() -> None:
    """Prompt for a BMAP file and a profile name (or all) and print date range."""
    try:
        from profcalc.common.bmap_io import read_bmap_freeformat
    except ImportError as e:  # pragma: no cover - import-time issues
        print(f"Required bmap reader not available: {e}")
        return

    input_file = select_input_file("Select BMAP Free Format File")
    if not input_file:
        print("Cancelled.")
        return

    try:
        profiles = read_bmap_freeformat(input_file)
    except (OSError, ValueError, TypeError) as e:
        print(f"Failed to read BMAP file: {e}")
        return

    if not profiles:
        print("No profiles found in file.")
        return

    names = sorted({p.name for p in profiles})
    print("Found profiles:")
    for n in names:
        print(f"  - {n}")

    choice = input("Enter profile name to examine (or 'all' for whole file): ").strip()
    targets = []
    if not choice or choice.lower() == "all":
        targets = profiles
    else:
        targets = [p for p in profiles if p.name == choice]

    if not targets:
        print("No matching profiles found.")
        return

    # Collect dates (profile.date may be None or string)
    dates = [p.date for p in targets if getattr(p, "date", None)]
    if not dates:
        print("No date information available for selected profiles.")
        return

    try:
        # attempt to sort ISO-like strings; otherwise show min/max lexicographically
        sorted_dates = sorted(dates)
        print(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
    except (TypeError, ValueError):
        print(f"Dates: {', '.join(sorted(set(dates)))}")


def about() -> None:
    """Print a concise about/version message."""
    try:
        from profcalc import __version__  # type: ignore

        ver = __version__
    except (ImportError, AttributeError):
        ver = "(version unknown)"
    print(
        f"ProfCalc {ver} - interactive menu system\nFor help see README.md in the project root."
    )


if __name__ == "__main__":
    launch_menu()
