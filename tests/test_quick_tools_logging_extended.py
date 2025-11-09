import logging

import pytest

from profcalc.cli.quick_tools import quick_tool_logger
from profcalc.cli.tools import convert, fix_bmap


def _reset_logger(log_file_path: str):
    quick_tool_logger.LOG_FILE = log_file_path
    # Clear existing handlers so logger re-initializes with new LOG_FILE
    logging.getLogger("profcalc.quick_tools").handlers.clear()


def test_convert_logs_invalid_columns(tmp_path):
    log_file = tmp_path / "QuickToolErrors.log"
    _reset_logger(str(log_file))

    # Call convert with an invalid columns specification to trigger ValueError
    convert.execute_from_cli(["input.dat", "--columns", "BADORDER"])

    assert log_file.exists(), "Convert did not create a log file"
    content = log_file.read_text(encoding="utf-8")
    assert "[convert] Column order parse error" in content


def test_fix_bmap_logs_no_files(tmp_path):
    log_file = tmp_path / "QuickToolErrors.log"
    _reset_logger(str(log_file))

    outdir = tmp_path / "out"
    # Call fix_bmap with a pattern that matches nothing; it should log and exit
    with pytest.raises(SystemExit) as excinfo:
        fix_bmap.execute_from_cli(["NO_FILES_MATCHING_*.none", "-o", str(outdir)])

    assert excinfo.value.code == 1
    assert log_file.exists(), "fix_bmap did not create a log file"
    content = log_file.read_text(encoding="utf-8")
    assert "[fix_bmap]" in content
    assert "No files matched pattern" in content or "No files matched" in content
