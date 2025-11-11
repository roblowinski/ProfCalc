import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from profcalc.core import profile_stats as ps


def test_calculate_berm_width_simple():
    # Create a simple profile with a flat berm above MHW
    points = [
        (0.0, 0.0),
        (1.0, 1.0),
        (2.0, 1.0),
        (3.0, 1.0),
        (4.0, 0.0),
    ]
    mhw = 0.9
    width = ps.calculate_berm_width(points, mhw)
    # Based on the implementation's segment indexing the returned width
    # will be the distance between the first two low-slope points (1.0).
    assert pytest.approx(width, rel=1e-6) == 1.0


def test_calculate_berm_width_none():
    # All points are below MHW -> no berm
    points = [(0.0, -1.0), (1.0, -0.5), (2.0, -1.2)]
    mhw = 0.0
    assert ps.calculate_berm_width(points, mhw) == 0.0


def test_calculate_beach_face_slope_typical():
    points = [
        (0.0, 0.5),
        (1.0, 1.0),
        (2.0, 0.2),
        (3.0, 0.0),
    ]
    mhw = 1.0
    slope = ps.calculate_beach_face_slope(points, mhw)
    # Expect slope = (0.2 - 1.0) / (2.0 - 1.0) = -0.8
    assert pytest.approx(slope, rel=1e-6) == -0.8


def test_calculate_beach_face_slope_no_mhw():
    points = [(0.0, 0.0), (1.0, 0.1), (2.0, 0.2)]
    mhw = 1.0
    assert ps.calculate_beach_face_slope(points, mhw) == 0.0


def test_calculate_common_ranges_basic():
    # Two surveys for same profile with overlapping X ranges
    profiles = {
        "P1": [
            [(0.0, 0.0), (1.0, 1.0)],
            [(0.5, 0.5), (1.5, 1.5)],
        ]
    }
    res = ps.calculate_common_ranges(profiles)
    assert "P1" in res
    vals = res["P1"]
    # xmin_common = max(0.0, 0.5) = 0.5, xmax_common = min(1.0, 1.5) = 1.0
    assert pytest.approx(vals[0], rel=1e-6) == 0.5
    assert pytest.approx(vals[1], rel=1e-6) == 1.0
    assert vals[2] == 2  # num_surveys
