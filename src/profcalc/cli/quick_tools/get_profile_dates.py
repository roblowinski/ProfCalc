# =============================================================================
# Get Profile Dates Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/get_profile_dates.py
#
# PURPOSE:
# This module provides a quick tool wrapper for retrieving survey dates from
# profile data files. It extracts temporal information from 9-column format
# files and other profile datasets, enabling date-based analysis and filtering.
#
# WHAT IT'S FOR:
# - Providing quick access to profile date extraction functionality
# - Retrieving survey dates from 9-column and other profile formats
# - Supporting temporal analysis of profile datasets
# - Enabling date-based filtering and organization
# - Offering menu-integrated access to date extraction tools
#
# WORKFLOW POSITION:
# This quick tool wrapper provides streamlined access to profile date extraction
# for temporal analysis workflows. It serves as the menu-accessible interface
# for date retrieval operations while ensuring proper error handling.
#
# LIMITATIONS:
# - Limited to supported profile formats with date information
# - Depends on tools.get_profile_dates implementation
# - May not extract dates from all file types
# - Requires consistent date formatting in source files
#
# ASSUMPTIONS:
# - Profile files contain date information in expected formats
# - Date extraction tool is available and functional
# - Users need temporal information for analysis
# - Date formats are parseable and consistent
#
# =============================================================================

"""Quick wrapper for the get_profile_dates tool.

Delegates to `profcalc.cli.tools.get_profile_dates` for implementation.
"""

try:
    from profcalc.cli.tools import get_profile_dates as _impl

    impl_execute_from_menu = getattr(_impl, "execute_from_menu", None)
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("get_profile_dates tool is not available")

else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            raise ImportError("get_profile_dates implementation has no menu entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "get_profile_dates",
                f"Unhandled exception in get_profile_dates quick tool: {e}",
            )
            raise


__all__ = ["execute_from_menu"]


__all__ = ["execute_from_menu"]
