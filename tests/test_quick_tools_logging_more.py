import logging

import pytest

from profcalc.cli.quick_tools import bounds, inventory, quick_tool_logger


def _reset_logger(log_file_path: str):
    quick_tool_logger.LOG_FILE = log_file_path
    logging.getLogger("profcalc.quick_tools").handlers.clear()


def test_bounds_quick_tool_logs_on_exception(tmp_path):
    log_file = tmp_path / "QuickToolErrors.log"
    _reset_logger(str(log_file))

    # Monkeypatch the impl to raise
    orig = getattr(bounds, "impl_execute_from_menu", None)

    def _boom():
        raise RuntimeError("boom-bounds")

    setattr(bounds, "impl_execute_from_menu", _boom)
    try:
        with pytest.raises(RuntimeError):
            bounds.execute_from_menu()
    finally:
        # Restore
        setattr(bounds, "impl_execute_from_menu", orig)

    assert log_file.exists(), "Bounds quick tool did not create a log file"
    content = log_file.read_text(encoding="utf-8")
    assert "[bounds]" in content
    assert "boom-bounds" in content


def test_inventory_quick_tool_logs_on_exception(tmp_path):
    log_file = tmp_path / "QuickToolErrors.log"
    _reset_logger(str(log_file))

    orig = getattr(inventory, "impl_execute_from_menu", None)

    def _boom():
        raise FileNotFoundError("no-inventory")

    setattr(inventory, "impl_execute_from_menu", _boom)
    try:
        with pytest.raises(FileNotFoundError):
            inventory.execute_from_menu()
    finally:
        setattr(inventory, "impl_execute_from_menu", orig)

    assert log_file.exists(), "Inventory quick tool did not create a log file"
    content = log_file.read_text(encoding="utf-8")
    assert "[inventory]" in content
    assert "no-inventory" in content
