# =============================================================================
# Bounds Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/bounds.py
#
# PURPOSE:
# This module provides a quick tool wrapper for bounds analysis functionality,
# which finds common X and Y bounds in profile groups. It delegates to the main
# implementation while providing flexible entry points and comprehensive error
# handling for quick tool usage.
#
# WHAT IT'S FOR:
# - Providing quick access to bounds analysis functionality
# - Finding common spatial bounds across profile datasets
# - Supporting profile group analysis workflows
# - Enabling streamlined bounds calculation and reporting
# - Offering menu-integrated access to bounds tools
#
# WORKFLOW POSITION:
# This quick tool wrapper provides menu-accessible bounds analysis while
# maintaining compatibility with both menu and CLI execution models. It serves
# as the primary interface for bounds operations in interactive workflows.
#
# LIMITATIONS:
# - Depends on tools.bounds implementation availability
# - May fallback to CLI execution if menu entry not available
# - Limited to spatial bounds analysis
# - Requires compatible profile data formats
#
# ASSUMPTIONS:
# - Bounds tool implementation provides necessary entry points
# - Profile data includes spatial coordinate information
# - Users understand bounds analysis concepts
# - Error logging captures sufficient diagnostic information
#
# =============================================================================

"""Quick wrapper for the bounds tool.

Delegates to `profcalc.cli.tools.bounds` for implementation.
"""

try:
    # Import the interactive entry if available; the implementation may not
    # expose a CLI shim (execute_from_cli), so handle that gracefully.
    from profcalc.cli.tools import bounds as _bounds_impl

    impl_execute_from_menu = getattr(_bounds_impl, "execute_from_menu", None)
    impl_execute_from_cli = getattr(_bounds_impl, "execute_from_cli", None)
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("bounds tool is not available")

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise NotImplementedError(
            "Quick tools are menu-only; run via the interactive menu."
        )
else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            # Fallback: if only a CLI shim exists, call it with no args.
            if impl_execute_from_cli:
                return impl_execute_from_cli([])
            raise ImportError("bounds implementation has no usable entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "bounds", f"Unhandled exception in bounds quick tool: {e}"
            )
            raise


__all__ = ["execute_from_menu", "execute_from_cli"]
