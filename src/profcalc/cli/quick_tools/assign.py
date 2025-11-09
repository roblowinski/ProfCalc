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
        except Exception as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error("assign", f"Unhandled exception in assign quick tool: {e}")
            raise

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise NotImplementedError(
            "Quick tools are menu-only; run via the interactive menu."
        )


__all__ = ["execute_from_menu", "execute_from_cli"]
