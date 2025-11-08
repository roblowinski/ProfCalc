import importlib
from pathlib import Path


def test_quick_tool_wrappers_exist():
    mods = [
        "assign",
        "bounds",
        "convert",
        "fix_bmap",
        "get_profile_dates",
        "inventory",
    ]
    for m in mods:
        mn = f"profcalc.cli.quick_tools.{m}"
        mod = importlib.import_module(mn)
        assert hasattr(mod, "execute_from_menu") or hasattr(mod, "execute_from_cli")


def test_quick_tool_utils_parse_and_paths():
    from profcalc.cli.quick_tools.quick_tool_utils import (
        default_output_path,
        parse_date,
        timestamped_output_path,
    )

    # parse a few date formats
    assert parse_date("2020-01-02") is not None
    assert parse_date("02NOV2020") is not None

    s = default_output_path("testtool", "data/temp/9Col_WithHeader.csv", ext=".csv")
    assert "output_testtool" in s

    t = timestamped_output_path("testtool", ext=".txt")
    assert "output_testtool" in t and t.endswith(".txt")


def test_quick_tool_logger_writes():
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    log_quick_tool_error("smoke_test", "This is a smoke test entry")
    p = Path(__file__).resolve().parents[1].joinpath("src/profcalc/QuickToolErrors.log")
    # allow either repo path or package-relative
    if not p.exists():
        p = Path(__file__).resolve().parents[2].joinpath("src/profcalc/QuickToolErrors.log")

    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "smoke_test" in content
