"""
quick_tool_logger.py

Shared logger utility for all quick tools.
Logs errors and issues to QuickToolErrors.log with timestamps and tool name.
"""
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "QuickToolErrors.log")

def log_quick_tool_error(tool_name: str, message: str):
    """Log an error or issue to the shared QuickToolErrors.log file with timestamp and tool name."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{tool_name}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write to log file: {e}")
