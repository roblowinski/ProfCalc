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

from typing import TYPE_CHECKING, Optional, Callable, Tuple
from dataclasses import dataclass
import builtins

if TYPE_CHECKING:
    pass

# Use the package-level data tools to keep dataset registration centralized
from profcalc.cli.tools import data as data_tools


@dataclass
class AppIO:
    input_fn: Callable[[str], str] = builtins.input
    print_fn: Callable[..., None] = builtins.print


def _get_io(io: Optional[AppIO]) -> Tuple[Callable[[str], str], Callable[..., None]]:
    if io is None:
        return builtins.input, builtins.print
    return io.input_fn, io.print_fn


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
        print("\n--- File Conversion Options ---")
        print("1. BMAP Free Format to XYZ/9-Col")
        print("2. BMAP Free Format to Shapefile")
        print("3. XYZ/9-Col to BMAP Free Format")
        print("4. XYZ/9-Col to Shapefile")
        print("5. Point Shapefile to BMAP Free Format")
        print("6. Point Shapefile to XYZ/9-Col")
        print("7. Return to Previous Menu")
        choice = input("Select a conversion: ").strip()

        if choice == "1":
            print("[STUB] BMAP to CSV conversion not yet implemented.")
        elif choice == "2":
            print("[STUB] BMAP to Shapefile conversion not yet implemented.")
        elif choice == "3":
            print("[STUB] CSV to BMAP conversion not yet implemented.")
        elif choice == "4":
            print("[STUB] CSV to Shapefile conversion not yet implemented.")
        elif choice == "5":
            print("[STUB] Shapefile to BMAP conversion not yet implemented.")
        elif choice == "6":
            print("[STUB] Shapefile to XYZ conversion not yet implemented.")
        elif choice == "7":
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
            print(
                "[STUB] Extract & Prepare Shoreline Data - Not yet implemented."
            )
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
        print("\n=== ProfCalc Main Menu ===")
        print("1. Data Management")
        print("2. Annual Monitoring Report Analyses")
        print("3. File Conversion Tools")
        print("4. Profile Analysis Tools")
        print("5. Batch Processing")
        print("6. Configuration & Settings")
        print("7. Quick Tools")
        print("8. Help & Documentation")
        print("9. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            data_management_menu()
        elif choice == "2":
            annual_monitoring_menu()
        elif choice == "3":
            print("File Conversion Tools - Coming Soon!")
        elif choice == "4":
            profcalc_profcalc_menu()
        elif choice == "5":
            print("Batch Processing - Coming Soon!")
        elif choice == "6":
            print("Configuration & Settings - Coming Soon!")
        elif choice == "7":
            quick_tools_menu()
        elif choice == "8":
            print("Help & Documentation - Coming Soon!")
        elif choice == "9":
            print("Goodbye!")
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
        print("\n--- Annual Monitoring Report Analyses ---")
        print("1. Import Survey Data")
        print("2. Compute Annual Erosion Rate (AER)")
        print("3. Profile Analysis")
        print("4. Shoreline Analysis")
        print("5. Condition Evaluation")
        print("6. Reporting & Export")
        print("7. Back to Main Menu")
        choice = input("Select an option: ").strip()
        if choice == "1":
            # Prompt for a survey file and import using the shared data tools
            path = input(
                "Enter path to survey CSV to import (or blank to cancel): "
            ).strip()
            if not path:
                print("Import cancelled.")
                continue
            try:
                res = data_tools.import_data(path)
                imported = (
                    res.get("imported") if isinstance(res, dict) else "?"
                )
                print(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Import failed: {exc}")
        elif choice == "2":
            # Compute AER via the Annual tools handler
            try:
                from profcalc.cli.tools import annual as annual_tools

                annual_tools.compute_aer()
            except (
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - interactive
                print(f"Failed to run AER handler: {exc}")
        elif choice == "3":
            shoreline_analysis_menu()
        elif choice == "4":
            print("[STUB] Condition Evaluation - Not yet implemented.")
        elif choice == "5":
            print("[STUB] Reporting & Export - Not yet implemented.")
        elif choice == "6":
            break
        elif choice == "7":
            break
        else:
            print("Invalid selection. Please try again.")


# Simple session context for storing user choices
class AppState:
    """Lightweight application state for the interactive menu.

    We keep only a minimal set of attributes here (data_source selection and
    optional details). Dataset registration and active dataset are handled by
    `profcalc.cli.tools.data.session` so the menu delegates to that module for
    data operations.
    """

    def __init__(self) -> None:
        self.data_source: Optional[str] = None
        self.data_source_details: Optional[str] = None


app_state = AppState()


def select_data_source() -> None:
    """Prompt user to select data source for analysis.

    Allows selection between:
    - Database connection (placeholder for future implementation)
    - File-based data import (placeholder for future implementation)
    - Exit the application
    """
    while True:
        print("\n=== Select Data Source ===")
        print("1. Connect to Profile Database")
        print("2. Import/Load Data from File(s)")
        print("3. Exit")
        choice = input("Choose data source: ").strip()
        if choice == "1":
            app_state.data_source = "database"
            app_state.data_source_details = None
            print(
                "\n[INFO] Database mode selected. (DB connection not yet implemented)"
            )
            break
        elif choice == "2":
            # Prompt for a file path and attempt import using data_tools
            app_state.data_source = "file"
            path = input(
                "Enter path to 9-column CSV file to import (or blank to cancel): "
            ).strip()
            if not path:
                print("Import cancelled.")
                break
            try:
                result = data_tools.import_data(path)
                imported = (
                    result.get("imported") if isinstance(result, dict) else "?"
                )
                print(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive error path
                print(f"Import failed: {exc}")
            break
        elif choice == "3":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid selection. Please try again.")


def ensure_data_source(io: Optional[AppIO] = None) -> None:
    """Prompt the user to select a data source if one is not already set.

    This convenience prompts once when entering Data Management so users
    choose File/Database/Session up-front. Import is optional when choosing
    File.
    """
    if app_state.data_source:
        return

    input_fn, print_fn = _get_io(io)

    print_fn("\nNo data source configured. Select data source:")
    print_fn("1. Load from file")
    print_fn("2. Connect to database")
    print_fn("3. Use in-memory session (no external source)")
    choice = input_fn("Select a source [1/2/3]: ").strip()
    if choice == "1":
        app_state.data_source = "file"
        path = input_fn(
            "Enter path to 9-column CSV to import now (or blank to skip): "
        ).strip()
        if path:
            try:
                result = data_tools.import_data(path)
                imported = result.get("imported") if isinstance(result, dict) else "?"
                print_fn(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                print_fn(f"Import failed: {exc}")
    elif choice == "2":
        app_state.data_source = "database"
        app_state.data_source_details = None
        print_fn("\n[INFO] Database mode selected. (DB connection not yet implemented)")
    else:
        app_state.data_source = "session"
        print_fn("\n[INFO] Using in-memory session (no external source configured).")


def data_management_menu(io: Optional[AppIO] = None) -> None:
    """Display and handle the Data Management menu.

    Provides data management operations:
    - Change Data Source
    - Import/Export Data (stub)
    - View Data Summary (stub)
    """
    # Prompt for data source up-front if none selected
    ensure_data_source(io)

    input_fn, print_fn = _get_io(io)

    while True:
        print_fn("\n--- Data Management ---")
        print_fn(
            f"1. Select Data Source (Current: {app_state.data_source or 'Not Set'})"
        )
        print("2. Import Data (9-col CSV)")
        print("3. List Registered Datasets")
        print("4. Select Active Dataset")
        print("5. View Data Summary")
        print("6. Back to Main Menu")
        choice = input_fn("Select an option: ").strip()
        if choice == "1":
            select_data_source()
        elif choice == "2":
            path = input_fn(
                "Enter path to 9-column CSV file to import (or blank to cancel): "
            ).strip()
            if not path:
                print_fn("Import cancelled.")
                continue
            try:
                result = data_tools.import_data(path)
                imported = (
                    result.get("imported") if isinstance(result, dict) else "?"
                )
                print_fn(f"Imported {imported} rows from {path}.")
            except (
                FileNotFoundError,
                ValueError,
                NotImplementedError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                print_fn(f"Import failed: {exc}")
        elif choice == "3":
            data_tools.list_datasets()
        elif choice == "4":
            dsid = input_fn(
                "Enter dataset ID to set active (or blank to cancel): "
            ).strip()
            if not dsid:
                print_fn("Selection cancelled.")
                continue
            try:
                data_tools.select_dataset(dsid)
            except (
                KeyError,
                ValueError,
                OSError,
            ) as exc:  # pragma: no cover - interactive
                print_fn(f"Failed to select dataset: {exc}")
        elif choice == "5":
            data_tools.summary()
        elif choice == "6":
            break
        else:
            print_fn("Invalid selection. Please try again.")


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


def quick_tools_menu() -> None:
    """Display and handle the Quick Tools submenu.

    Provides access to utility functions for common tasks:
    - Find Common X Bounds Within a Group of Profiles
    - Convert File Format & Create Shapefiles
    - Get an Inventory of Profiles from a BMap File
    - Assign Profile Names to XYZ/CSV Files Missing Profile IDs
    """
    while True:
        print("\n--- Quick Tools ---")
        print(
            "1. Find Common X Bounds Within a Group of Profiles in a BMap Free Format File"
        )
        print("2. Convert File Format & Create Shapefiles (i.e., 3D to 2D)")
        print("3. Get an Inventory of Profiles from a BMap Free Format File")
        print("4. Assign Profile Names to XYZ/CSV Files Missing Profile IDs")
        print("5. Back to Main Menu")
        choice = input("Select a quick tool: ").strip()

        if choice == "1":
            print("[STUB] Bounds tool not yet implemented.")
        elif choice == "2":
            conversion_submenu()
        elif choice == "3":
            print("[STUB] Inventory tool not yet implemented.")
        elif choice == "4":
            print("[STUB] Assign tool not yet implemented.")
        elif choice == "5":
            break
        else:
            print("Invalid selection. Please try again.")


def launch_menu() -> None:
    """Launch the interactive menu system."""
    select_data_source()
    main_menu()


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
