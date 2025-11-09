import logging

from profcalc.cli.quick_tools import quick_tool_logger
from profcalc.cli.tools import assign


def test_quick_tool_logger_writes_file(tmp_path):
    # Point the logger to a temporary log file and clear handlers to force reconfiguration
    log_file = tmp_path / "QuickToolErrors.log"
    quick_tool_logger.LOG_FILE = str(log_file)
    logging.getLogger("profcalc.quick_tools").handlers.clear()

    # Log a message
    quick_tool_logger.log_quick_tool_error("testtool", "intentional failure for test")

    # Ensure the file is created and contains the message
    assert log_file.exists(), "Log file was not created"
    content = log_file.read_text(encoding="utf-8")
    assert "[testtool] intentional failure for test" in content


def test_assign_logs_no_input(tmp_path):
    # Point the logger to a temporary log file and clear handlers to force reconfiguration
    log_file = tmp_path / "QuickToolErrors.log"
    quick_tool_logger.LOG_FILE = str(log_file)
    logging.getLogger("profcalc.quick_tools").handlers.clear()

    # Call execute_from_cli with a pattern that matches nothing
    assign.execute_from_cli(["NO_FILES_MATCHING_PATTERN_*.none"])  # should log and return

    assert log_file.exists(), "Log file was not created for assign"
    content = log_file.read_text(encoding="utf-8")
    assert "[assign]" in content
    assert "No input files found" in content or "No files matched" in content
