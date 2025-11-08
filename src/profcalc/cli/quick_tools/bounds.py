"""Quick wrapper for the bounds tool.

Delegates to `profcalc.cli.tools.bounds` for implementation.
"""

try:
    from profcalc.cli.tools.bounds import (
        execute_from_cli as impl_execute_from_cli,
    )
    from profcalc.cli.tools.bounds import (
        execute_from_menu as impl_execute_from_menu,
    )
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("bounds tool is not available")

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise ImportError("bounds tool is not available")
else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            return impl_execute_from_cli([])
        except Exception as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error("bounds", f"Unhandled exception in bounds quick tool: {e}")
            raise

__all__ = ["execute_from_menu", "execute_from_cli"]
