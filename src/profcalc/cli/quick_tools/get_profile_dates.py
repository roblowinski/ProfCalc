"""Quick wrapper for the get_profile_dates tool.

Delegates to the implementation in scripts/quick_tools/get_profile_dates.py for menu integration.
Wraps execution and logs errors to the shared quick tool logger.
"""

import runpy
import sys

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error


def execute_from_menu() -> None:
    """Run the get_profile_dates tool as a menu option."""
    script_path = "scripts/quick_tools/get_profile_dates.py"
    try:
        runpy.run_path(script_path, run_name="__main__")
    except Exception as e:
        msg = f"Error running get_profile_dates tool: {e}"
        print(msg, file=sys.stderr)
        log_quick_tool_error("get_profile_dates", msg)


__all__ = ["execute_from_menu"]
