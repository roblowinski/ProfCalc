from pathlib import Path

from profcalc.cli.tools.annual import compute_aer_noninteractive
from profcalc.cli.tools.data import import_data
from profcalc.cli.tools.data import session as data_session


def test_compute_aer_noninteractive_sample_files():
    data_dir = Path(__file__).resolve().parents[1].joinpath("data", "temp").resolve()
    before = data_dir.joinpath("9Col_WithHeader.csv")
    after = data_dir.joinpath("9Col_WithHeader.csv")

    # Using same file for before/after is okay for smoke test; expect zero net
    res = compute_aer_noninteractive(before, after, dx=0.5, use_bmap_core=False)
    assert "cut_cuyd_per_ft" in res
    assert "fill_cuyd_per_ft" in res
    assert "all_cuyd_per_ft" in res
    assert isinstance(res["cut_cuyd_per_ft"], float)


def test_compute_aer_noninteractive_with_session_datasets():
    data_dir = (
        Path(__file__).resolve().parents[1].joinpath("data", "temp").resolve()
    )
    before = data_dir.joinpath("9Col_WithHeader.csv")
    after = data_dir.joinpath("9Col_WithHeader.csv")

    # Register both files with the session via import_data
    import_data(str(before))
    import_data(str(after))

    # Find dataset ids for each path
    ds_before = None
    ds_after = None
    for dsid, info in data_session.list_datasets().items():
        p = info.get("path")
        if p and Path(p) == before.resolve():
            ds_before = dsid
        if p and Path(p) == after.resolve():
            ds_after = dsid

    assert ds_before is not None and ds_after is not None

    # Call non-interactive AER using dataset ids
    res = compute_aer_noninteractive(
        ds_before, ds_after, dx=0.5, use_bmap_core=False
    )
    assert "cut_cuyd_per_ft" in res
    assert isinstance(res["cut_cuyd_per_ft"], float)
