from profcalc.cli.tools import fix_bmap


def _make_bmap_content(profile_name: str, declared_count: int, coords: list[tuple]) -> str:
    """Helper to build a simple BMAP-like content string."""
    lines = [f"{profile_name}\n", f"{declared_count}\n"]
    for x, y in coords:
        lines.append(f"{x} {y}\n")
    return "".join(lines)


def test_fix_bmap_declared_less_than_actual(tmp_path):
    """Declared count is less than actual coordinate lines -> should be corrected."""
    profile_name = "TEST_LESS"
    # declared 2 but actually 3 coordinate lines
    content = _make_bmap_content(profile_name, 2, [(10, 1), (20, 2), (30, 3)])

    in_file = tmp_path / "less.bmap"
    out_file = tmp_path / "less_fixed.bmap"
    in_file.write_text(content, encoding="utf-8")

    corrections = fix_bmap.fix_bmap_point_counts(str(in_file), str(out_file), verbose=False, skip_confirmation=True)

    # Should detect correction
    assert profile_name in corrections
    declared, actual = corrections[profile_name]
    assert declared == 2
    assert actual == 3

    # Output file should exist and contain corrected count
    assert out_file.exists()
    out_lines = out_file.read_text(encoding="utf-8").splitlines()
    # Second line should be the corrected actual count
    assert out_lines[1].strip() == str(actual)


def test_fix_bmap_declared_greater_than_actual(tmp_path):
    """Declared count is greater than actual coordinate lines -> should be corrected down."""
    profile_name = "TEST_GREATER"
    # declared 4 but actually 3 coordinate lines
    content = _make_bmap_content(profile_name, 4, [(10, 1), (20, 2), (30, 3)])

    in_file = tmp_path / "greater.bmap"
    out_file = tmp_path / "greater_fixed.bmap"
    in_file.write_text(content, encoding="utf-8")

    corrections = fix_bmap.fix_bmap_point_counts(str(in_file), str(out_file), verbose=False, skip_confirmation=True)

    # Should detect correction
    assert profile_name in corrections
    declared, actual = corrections[profile_name]
    assert declared == 4
    assert actual == 3

    assert out_file.exists()
    out_lines = out_file.read_text(encoding="utf-8").splitlines()
    assert out_lines[1].strip() == str(actual)
