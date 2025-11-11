# =============================================================================
# Assign Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/assign.py
#
# PURPOSE:
# This module provides a quick tool wrapper for the assign functionality,
# which assigns missing profile names in XYZ/CSV files. It delegates to the
# main implementation in the tools module while providing error handling and
# logging specific to quick tool usage.
#
# WHAT IT'S FOR:
# - Providing quick access to profile name assignment functionality
# - Assigning missing profile identifiers in coordinate data files
# - Supporting XYZ and CSV file processing workflows
# - Enabling streamlined profile data preparation
# - Offering menu-integrated access to assignment tools
#
# WORKFLOW POSITION:
# This quick tool wrapper sits between the menu system and the core assignment
# implementation. It provides the menu-accessible interface for profile name
# assignment while ensuring proper error handling and logging for quick tool
# operations.
#
# LIMITATIONS:
# - Menu-only execution (no direct CLI support)
# - Depends on tools.assign implementation
# - Limited to supported file formats (XYZ/CSV)
# - Requires user interaction for file selection
#
# ASSUMPTIONS:
# - Assignment tool implementation is available and functional
# - Input files follow expected format conventions
# - Users can navigate menu system for tool access
# - Error logging is sufficient for troubleshooting
#
# =============================================================================

"""Quick wrapper for the assign tool.

Delegates to `profcalc.cli.tools.assign` for implementation.
"""

try:
    from profcalc.cli.tools import assign as _impl

    impl_execute_from_menu = getattr(_impl, "execute_from_menu", None)
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("assign tool is not available")

else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            raise ImportError("assign implementation has no menu entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "assign", f"Unhandled exception in assign quick tool: {e}"
            )
            raise

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise NotImplementedError(
            "Quick tools are menu-only; run via the interactive menu."
        )


__all__ = ["execute_from_menu", "execute_from_cli"]
