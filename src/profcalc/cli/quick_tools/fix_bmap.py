"""Quick wrapper for the fix_bmap tool.

This module provides the small surface API expected by callers/tests in
`profcalc.cli.quick_tools` while delegating implementation to
`profcalc.cli.tools.fix_bmap`.
"""
from typing import Any

try:
    from profcalc.cli.tools.fix_bmap import (
        execute_from_cli as impl_execute_from_cli,
    )
    from profcalc.cli.tools.fix_bmap import (
        execute_from_menu as impl_execute_from_menu,
    )
    from profcalc.cli.tools.fix_bmap import (
        execute_modify_headers_menu as impl_execute_modify_headers_menu,
    )
    from profcalc.cli.tools.fix_bmap import (
        fix_bmap_point_counts as impl_fix_bmap_point_counts,
    )
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
            return impl_execute_from_menu()
        except Exception as e:
            log_quick_tool_error("fix_bmap", f"Unhandled exception in fix_bmap quick tool: {e}")
            raise

    def execute_from_cli(args: list[str]) -> None:
        try:
            return impl_execute_from_cli(args)
        except Exception as e:
            log_quick_tool_error("fix_bmap", f"Unhandled exception in fix_bmap quick tool (CLI): {e}")
            raise

    def fix_bmap_point_counts(*args: Any, **kwargs: Any) -> Any:
        return impl_fix_bmap_point_counts(*args, **kwargs)

    def execute_modify_headers_menu() -> None:
        try:
            return impl_execute_modify_headers_menu()
        except Exception as e:
            log_quick_tool_error("fix_bmap", f"Unhandled exception in fix_bmap modify headers: {e}")
            raise

__all__ = [
    "execute_from_cli",
    "execute_from_menu",
    "fix_bmap_point_counts",
    "execute_modify_headers_menu",
]
