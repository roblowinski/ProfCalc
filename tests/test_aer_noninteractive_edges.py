from pathlib import Path

import pytest

from profcalc.cli.tools.annual import (
    _parse_date_str,
    compute_aer_noninteractive,
)
from profcalc.cli.tools.data import import_data
from profcalc.cli.tools.data import session as data_session


def _data_file(name: str) -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("data", "samples", "format_examples", name)
    )


def test_missing_files_raise_file_not_found():
    before = Path("nonexistent_before.csv")
    after = Path("nonexistent_after.csv")

    with pytest.raises(FileNotFoundError):
        compute_aer_noninteractive(before, after)


def test_invalid_profile_index_raises_index_error():
    data_file = _data_file("9Col_WithHeader.csv")
    # Use a very large index that will be out of range
    with pytest.raises(IndexError):
        compute_aer_noninteractive(data_file, data_file, profile_before=9999)


def test_profile_name_fallback_to_first():
    data_file = _data_file("9Col_WithHeader.csv")
    # Non-matching name should fall back to the first profile (index 0)
    res_name = compute_aer_noninteractive(
        data_file, data_file, profile_before="NON_EXISTENT_NAME", profile_after=0
    )
    res_index0 = compute_aer_noninteractive(
        data_file, data_file, profile_before=0, profile_after=0
    )
    # Numeric fields should be equal when fallback occurs
    assert pytest.approx(res_name["all_cuyd_per_ft"]) == res_index0["all_cuyd_per_ft"]


def test_parse_date_str_accepts_iso_and_yyyymmdd_and_rejects_bad():
    assert _parse_date_str("2024-10-26").isoformat() == "2024-10-26"
    assert _parse_date_str("20241026").isoformat() == "2024-10-26"
    assert _parse_date_str("bad-date") is None


def test_compute_with_session_dataset_ids():
    data_file = _data_file("9Col_WithHeader.csv")
    # Register file and call via dataset id
    import_data(str(data_file))
    dsid = None
    for k, v in data_session.list_datasets().items():
        if Path(v.get("path")) == data_file.resolve():
            dsid = k
            break
    assert dsid is not None
    res = compute_aer_noninteractive(dsid, dsid, dx=0.2)
    assert "aer_cuyd_per_ft_per_yr" in res


def test_dx_zero_and_negative_raise_value_error():
    data_file = _data_file("9Col_WithHeader.csv")
    with pytest.raises(ValueError):
        compute_aer_noninteractive(data_file, data_file, dx=0.0)
    with pytest.raises(ValueError):
        compute_aer_noninteractive(data_file, data_file, dx=-1.0)


def test_sparse_profiles_raise_value_error():
    # Create minimal profiles with a single point each and call calculate_aer
    from profcalc.core.aer import calculate_aer

    x = [0.0]
    z = [0.0]
    with pytest.raises(ValueError):
        calculate_aer(x, z, x, z)
