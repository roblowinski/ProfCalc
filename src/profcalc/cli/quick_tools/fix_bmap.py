# =============================================================================
# Fix BMAP Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/fix_bmap.py
#
# PURPOSE:
# This module provides a quick tool wrapper for BMAP file correction functionality,
# including point count fixes and header modifications. It delegates to the main
# implementation while providing comprehensive error handling and multiple entry
# points for different BMAP correction operations.
#
# WHAT IT'S FOR:
# - Providing quick access to BMAP file correction tools
# - Fixing BMAP point count discrepancies
# - Modifying BMAP file headers and metadata
# - Supporting BMAP format validation and repair
# - Offering menu-integrated access to BMAP tools
#
# WORKFLOW POSITION:
# This quick tool wrapper provides the primary interface for BMAP file correction
# operations. It offers multiple entry points for different types of BMAP fixes
# while ensuring proper error handling and logging for quick tool usage.
#
# LIMITATIONS:
# - Depends on tools.fix_bmap implementation availability
# - Limited to BMAP format files
# - May require multiple operations for complex fixes
# - Some fixes may be destructive to original files
#
# ASSUMPTIONS:
# - BMAP tool implementation provides necessary functions
# - Input files are valid BMAP format (may be corrupted)
# - Users understand BMAP format requirements
# - Backup files are created when necessary
#
# =============================================================================

"""Quick wrapper for the fix_bmap tool.

This module provides the small surface API expected by callers/tests in
`profcalc.cli.quick_tools` while delegating implementation to
`profcalc.cli.tools.fix_bmap`.
"""

from typing import Any

try:
    # Import the interactive entry if available; the implementation may not
    # expose a CLI shim (execute_from_cli), so handle that gracefully.
    from profcalc.cli.tools import fix_bmap as _fix_bmap_impl

    impl_execute_from_menu = getattr(_fix_bmap_impl, "execute_from_menu", None)
    impl_execute_from_cli = getattr(_fix_bmap_impl, "execute_from_cli", None)
    impl_execute_modify_headers_menu = getattr(
        _fix_bmap_impl, "execute_modify_headers_menu", None
    )
    impl_fix_bmap_point_counts = getattr(_fix_bmap_impl, "fix_bmap_point_counts", None)
except ImportError:  # pragma: no cover - import fallback
    # Provide minimal placeholders to fail loudly if tools not available
    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise ImportError("fix_bmap tool is not available")

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("fix_bmap tool is not available")

    def fix_bmap_point_counts(*args: Any, **kwargs: Any) -> Any:  # type: ignore
        raise ImportError("fix_bmap tool is not available")

    def execute_modify_headers_menu() -> None:  # type: ignore
        raise ImportError("fix_bmap tool is not available")
else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            # Fallback: if only a CLI shim exists, call it with no args.
            if impl_execute_from_cli:
                return impl_execute_from_cli([])
            raise ImportError("fix_bmap implementation has no usable entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:
            log_quick_tool_error(
                "fix_bmap", f"Unhandled exception in fix_bmap quick tool: {e}"
            )
            raise

    def execute_from_cli(args: list[str]) -> None:
        try:
            if impl_execute_from_cli:
                return impl_execute_from_cli(args)
            raise NotImplementedError(
                "Quick tools are menu-only; run via the interactive menu."
            )
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "fix_bmap", f"Unhandled exception in fix_bmap CLI: {e}"
            )
            raise

    def fix_bmap_point_counts(*args: Any, **kwargs: Any) -> Any:
        try:
            if impl_fix_bmap_point_counts:
                return impl_fix_bmap_point_counts(*args, **kwargs)
            raise ImportError(
                "fix_bmap implementation has no fix_bmap_point_counts function"
            )
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "fix_bmap",
                f"Unhandled exception in fix_bmap_point_counts: {e}",
            )
            raise

    def execute_modify_headers_menu() -> None:
        try:
            if impl_execute_modify_headers_menu:
                return impl_execute_modify_headers_menu()
            raise ImportError(
                "fix_bmap implementation has no execute_modify_headers_menu function"
            )
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "fix_bmap",
                f"Unhandled exception in execute_modify_headers_menu: {e}",
            )
            raise


__all__ = [
    "execute_from_menu",
    "execute_from_cli",
    "fix_bmap_point_counts",
    "execute_modify_headers_menu",
]
