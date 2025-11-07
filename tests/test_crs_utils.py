import pytest

from profcalc.common import crs_utils


def _pyproj_or_skip():
    pytest.importorskip("pyproj")


def test_infer_new_jersey():
    _pyproj_or_skip()
    # sample points roughly in NJ NAD83 / New Jersey (ftUS) area
    samples = [
        (425000, 470000),
        (425100, 470100),
        (424900, 469900),
        (425200, 470050),
    ]
    crs, label = crs_utils.infer_state_plane_crs_from_samples(samples)
    assert crs is not None, "Expected CRS to be detected for NJ samples"
    assert label == "NJ"


def test_infer_delaware():
    _pyproj_or_skip()
    # sample points roughly in DE NAD83 / Delaware (ftUS) area
    samples = [
        (140000, 336000),
        (140100, 336200),
        (139900, 336100),
    ]
    crs, label = crs_utils.infer_state_plane_crs_from_samples(samples)
    assert crs is not None, "Expected CRS to be detected for DE samples"
    assert label == "DE"


def test_ambiguous_samples():
    _pyproj_or_skip()
    # samples that shouldn't match either state's bbox
    samples = [(0, 0), (10000000, 10000000)]
    crs, label = crs_utils.infer_state_plane_crs_from_samples(samples)
    assert crs is None and label is None
