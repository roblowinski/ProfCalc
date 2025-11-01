import json
from pathlib import Path

import pytest

from profcalc.cli.menu import MenuEngine


def test_menu_loads_json_with_bom(tmp_path: Path):
    # Create a temporary JSON file with a UTF-8 BOM
    menu = {"menu": [{"title": "Test BOM", "handler": ""}]}
    p = tmp_path / "menu_with_bom.json"
    # Write bytes with BOM prefix
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps(menu).encode("utf-8"))

    engine = MenuEngine(menu_path=p)

    assert engine.menu[0]["title"] == "Test BOM"
