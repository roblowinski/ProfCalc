from pathlib import Path

from profcalc.cli.tools.annual import compute_aer_noninteractive


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
