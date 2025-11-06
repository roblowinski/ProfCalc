import math
from typing import List

import numpy as np
import pytest

from profcalc.core.aer import calculate_aer


def _linear_profile(x0: float, x1: float, n: int, z_offset: float = 0.0) -> tuple[List[float], List[float]]:
    xs = np.linspace(x0, x1, num=n).tolist()
    zs = (np.zeros(n) + z_offset).tolist()
    return xs, zs


def test_identical_profiles_zero_volumes():
    x, z = _linear_profile(0.0, 100.0, 11, z_offset=1.5)
    res = calculate_aer(x, z, x, z, None, None, dx=1.0)
    assert math.isclose(res["cut_cuyd_per_ft"], 0.0, abs_tol=1e-12)
    assert math.isclose(res["fill_cuyd_per_ft"], 0.0, abs_tol=1e-12)
    assert math.isclose(res["all_cuyd_per_ft"], 0.0, abs_tol=1e-12)
    assert math.isnan(res["aer_cuyd_per_ft_per_yr"])


def test_constant_offset_area_matches_expected():
    # Two profiles where before = after + C (constant positive offset)
    x0, x1 = 0.0, 200.0
    C = 2.0  # ft
    xs = [0.0, 200.0]
    za = [C, C]
    zb = [0.0, 0.0]

    # analytic expected cut (ft^3 per foot alongshore) = C * width
    width = x1 - x0
    expected_cut_ft3 = C * width
    expected_cut_cuyd = expected_cut_ft3 / 27.0

    res = calculate_aer(xs, za, xs, zb, None, None, dx=1.0)
    assert pytest.approx(res["cut_cuyd_per_ft"], rel=1e-6) == expected_cut_cuyd
    assert math.isclose(res["fill_cuyd_per_ft"], 0.0, abs_tol=1e-12)


def test_small_dx_converges_to_same_area():
    xs = [0.0, 100.0]
    za = [1.0, 1.0]
    zb = [0.0, 0.0]

    res_coarse = calculate_aer(xs, za, xs, zb, None, None, dx=5.0)
    res_fine = calculate_aer(xs, za, xs, zb, None, None, dx=0.01)

    assert pytest.approx(res_coarse["cut_cuyd_per_ft"], rel=1e-3) == res_fine["cut_cuyd_per_ft"]


def test_two_point_sparse_profiles_ok():
    # Two point profiles should be accepted (interpolate_to_common_grid requires >=2)
    xs = [0.0, 50.0]
    za = [0.5, 0.5]
    zb = [0.0, 0.0]
    res = calculate_aer(xs, za, xs, zb, None, None, dx=1.0)
    # expected cut = diff (0.5) * width (50) / 27
    expected_cut = 0.5 * 50.0 / 27.0
    assert pytest.approx(res["cut_cuyd_per_ft"], rel=1e-6) == expected_cut
