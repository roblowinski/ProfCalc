# =============================================================================
# Inventory Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/inventory.py
#
# PURPOSE:
# This module provides a quick tool wrapper for profile inventory functionality,
# which analyzes multi-profile files and generates comprehensive inventories of
# profile data. It provides insights into profile collections and dataset
# characteristics.
#
# WHAT IT'S FOR:
# - Providing quick access to profile inventory functionality
# - Analyzing multi-profile file contents and structure
# - Generating comprehensive profile inventories
# - Supporting dataset assessment and validation
# - Offering menu-integrated access to inventory tools

# WORKFLOW POSITION:
# This quick tool wrapper provides the primary interface for profile inventory
# operations. It enables users to quickly assess the contents and characteristics
# of profile datasets through the menu system with proper error handling.

# LIMITATIONS:
# - Limited to multi-profile file formats
# - Depends on tools.inventory implementation
# - Menu-only execution model
# - Analysis scope limited to supported formats

# ASSUMPTIONS:
# - Inventory tool implementation is available
# - Input files contain multiple profiles
# - Users need summary information about datasets
# - Error logging provides sufficient diagnostics

# =============================================================================

"""Quick wrapper for the inventory tool.

Delegates to `profcalc.cli.tools.inventory` for implementation.
"""

try:
    # Prefer the interactive menu entry. Quick tools are menu-driven only;
    # CLI entrypoints are intentionally disabled to avoid accidental use.
    from profcalc.cli.tools import inventory as _impl

    impl_execute_from_menu = getattr(_impl, "execute_from_menu", None)
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("inventory tool is not available")

else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            raise ImportError("inventory implementation has no menu entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "inventory",
                f"Unhandled exception in inventory quick tool: {e}",
            )
            raise

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise NotImplementedError(
            "Quick tools are menu-only; run via the interactive menu."
        )


__all__ = ["execute_from_menu", "execute_from_cli"]
