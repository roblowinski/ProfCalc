import csv
from pathlib import Path

from profcalc.cli.handlers.data import import_data


def test_import_csv_happy_path(tmp_path: Path):
    # create a temporary CSV file
    p = tmp_path / "sample.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["profile_id", "x", "y"])
        writer.writerow(["R01", "0", "1.0"])
        writer.writerow(["R02", "10", "2.0"])

    result = import_data(str(p))

    assert result["status"] == "ok"
    assert result["imported"] == 2
    assert isinstance(result["sample"], list)
    assert result["sample"][0]["profile_id"] == "R01"


def test_import_missing_file_raises(tmp_path: Path):
    missing = tmp_path / "nope.csv"
    try:
        import_data(str(missing), require_exists=True)
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError:
        pass
