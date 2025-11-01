import pytest

from profcalc.tools.bmap.bmap_cut_fill import split_trap_area


def test_both_above():
    a, b = split_trap_area(0.0, 10.0, 1.0, 3.0)
    assert a == pytest.approx(0.5 * (1.0 + 3.0) * 10.0)
    assert b == pytest.approx(0.0)


def test_both_below():
    a, b = split_trap_area(0.0, 10.0, -1.0, -3.0)
    assert a == pytest.approx(0.0)
    assert b == pytest.approx(0.5 * (-1.0 + -3.0) * 10.0)


def test_cross_positive_to_negative():
    # za positive, zb negative -> crosses datum
    a, b = split_trap_area(0.0, 10.0, 2.0, -2.0)
    # crossing fraction = -za/(zb - za) = -2/(-2-2) = -2/-4 = 0.5 -> cross at x=5
    # area above: triangle/trap from x=0..5 with za=2 to 0
    expected_above = 0.5 * (2.0 + 0.0) * 5.0
    expected_below = 0.5 * (0.0 + -2.0) * 5.0
    assert a == pytest.approx(expected_above)
    assert b == pytest.approx(expected_below)


def test_cross_negative_to_positive():
    # za negative, zb positive -> crosses datum
    a, b = split_trap_area(0.0, 10.0, -2.0, 2.0)
    # crossing fraction = -za/(zb - za) = 2/(2-(-2)) = 2/4 = 0.5 -> cross at x=5
    expected_above = 0.5 * (0.0 + 2.0) * 5.0
    expected_below = 0.5 * (-2.0 + 0.0) * 5.0
    assert a == pytest.approx(expected_above)
    assert b == pytest.approx(expected_below)
