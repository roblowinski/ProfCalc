"""
Test shapefile conversion functionality.

Tests:
1. Point shapefile export from CSV
2. Line shapefile export from CSV with origin azimuths
3. Point shapefile export from XYZ
4. Line shapefile export from BMAP
5. Error handling for missing dependencies
6. Error handling for missing origin azimuths (line export)
"""

import tempfile
from pathlib import Path

import pytest

# Check if geopandas is available
try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


def test_point_shapefile_from_csv():
    """Test exporting point shapefile from CSV with Y coordinates."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.common.csv_io import read_csv_profiles
    from profcalc.common.shapefile_io import (
        write_survey_points_shapefile,
    )

    # Read test CSV with Y coordinates
    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )
    if not csv_file.exists():
        pytest.skip("Test data not found")

    profiles = read_csv_profiles(str(csv_file))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_points.shp"

        # Export to point shapefile
        write_survey_points_shapefile(profiles, output_path, crs="EPSG:6347")

        # Verify shapefile was created
        assert output_path.exists(), "Point shapefile not created"

        # Read back and verify
        gdf = gpd.read_file(output_path)

        # Check geometry type
        assert all(isinstance(geom, Point) for geom in gdf.geometry), (
            "Not all geometries are Points"
        )

        # Check required columns
        required_cols = [
            "profile_id",
            "survey_dat",
            "point_num",
            "distance_f",
            "z",
        ]
        for col in required_cols:
            assert col in gdf.columns, f"Missing column: {col}"

        # Check CRS (CRS may be None; convert safely)
        crs_str = gdf.crs.to_string() if gdf.crs is not None else ""
        assert crs_str == "EPSG:6347", "Incorrect CRS"

        print(f"✓ Point shapefile created with {len(gdf)} points")
        print(f"  Columns: {list(gdf.columns)}")


def test_line_shapefile_from_csv():
    """Test exporting line shapefile from CSV with origin azimuths."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.common.csv_io import read_csv_profiles
    from profcalc.common.shapefile_io import (
        write_profile_lines_shapefile,
    )

    # Read test CSV
    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )
    baselines_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "temp"
        / "test_baselines.csv"
    )

    if not csv_file.exists() or not baselines_file.exists():
        pytest.skip("Test data not found")

    profiles = read_csv_profiles(str(csv_file))

    # Load baselines and add to metadata
    import pandas as pd

    baselines_df = pd.read_csv(baselines_file)
    baselines = {}
    for _, row in baselines_df.iterrows():
        baselines[row["Profile"]] = {
            "origin_x": row["Origin_X"],
            "origin_y": row["Origin_Y"],
            "azimuth": row["Azimuth"],
        }

    # Add baseline metadata to profiles
    for profile in profiles:
        if profile.name in baselines:
            baseline = baselines[profile.name]
            if profile.metadata is None:
                profile.metadata = {}
            profile.metadata["origin_x"] = baseline["origin_x"]
            profile.metadata["origin_y"] = baseline["origin_y"]
            profile.metadata["azimuth"] = baseline["azimuth"]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_lines.shp"

        # Export to line shapefile
        write_profile_lines_shapefile(profiles, output_path, crs="EPSG:6347")

        # Verify shapefile was created
        assert output_path.exists(), "Line shapefile not created"

        # Read back and verify
        gdf = gpd.read_file(output_path)

        # Check geometry type (should be LineString or LineStringZ)
        assert all(isinstance(geom, LineString) for geom in gdf.geometry), (
            "Not all geometries are LineStrings"
        )

        # Check required columns
        required_cols = [
            "profile_id",
            "survey_dat",
            "azimuth",
            "length_ft",
            "num_vertic",
            "z_min",
            "z_max",
        ]
        for col in required_cols:
            assert col in gdf.columns, f"Missing column: {col}"

        # Check CRS (CRS may be None; convert safely)
        crs_str = gdf.crs.to_string() if gdf.crs is not None else ""
        assert crs_str == "EPSG:6347", "Incorrect CRS"

        # Check 3D geometry (LineStringZ should have Z coordinates)
        first_line = gdf.geometry.iloc[0]
        coords = list(first_line.coords)
        assert len(coords[0]) == 3, (
            "Line geometry is not 3D (missing Z coordinate)"
        )

        print(f"✓ Line shapefile created with {len(gdf)} lines")
        print(f"  Columns: {list(gdf.columns)}")
        print(
            f"  First line has {len(coords)} vertices (3D: {len(coords[0]) == 3})"
        )


def test_convert_csv_to_point_shapefile():
    """Test convert tool: CSV to point shapefile."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.cli.quick_tools.convert import convert_format

    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )

    if not csv_file.exists():
        pytest.skip("Test data not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_convert_points.shp"

        # Convert CSV to point shapefile
        convert_format(
            input_file=str(csv_file),
            output_file=str(output_path),
            from_format="csv",
            to_format="shp-points",
            crs="EPSG:6347",
        )

        # Verify output
        assert output_path.exists(), "Conversion failed - no output file"

        gdf = gpd.read_file(output_path)
        assert len(gdf) > 0, "No features in output shapefile"
        assert all(isinstance(geom, Point) for geom in gdf.geometry), (
            "Wrong geometry type"
        )

        print(
            f"✓ CSV → Point Shapefile conversion successful ({len(gdf)} points)"
        )


def test_convert_csv_to_line_shapefile():
    """Test convert tool: CSV to line shapefile with origin azimuths."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.cli.quick_tools.convert import convert_format

    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )
    baselines_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "temp"
        / "test_baselines.csv"
    )

    if not csv_file.exists() or not baselines_file.exists():
        pytest.skip("Test data not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_convert_lines.shp"

        # Convert CSV to line shapefile
        convert_format(
            input_file=str(csv_file),
            output_file=str(output_path),
            from_format="csv",
            to_format="shp-lines",
            baselines_file=str(baselines_file),
            crs="EPSG:6347",
        )

        # Verify output
        assert output_path.exists(), "Conversion failed - no output file"

        gdf = gpd.read_file(output_path)
        assert len(gdf) > 0, "No features in output shapefile"
        assert all(isinstance(geom, LineString) for geom in gdf.geometry), (
            "Wrong geometry type"
        )

        # Verify 3D
        first_line = gdf.geometry.iloc[0]
        coords = list(first_line.coords)
        assert len(coords[0]) == 3, "Line is not 3D"

        print(
            f"✓ CSV → Line Shapefile conversion successful ({len(gdf)} lines)"
        )
        print(f"  First line: {len(coords)} vertices (3D)")


def test_line_shapefile_requires_baselines():
    """Test that line shapefile export requires baselines."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.cli.quick_tools.convert import convert_format

    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )

    if not csv_file.exists():
        pytest.skip("Test data not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_no_baselines.shp"

        # Should raise error without origin azimuths
        with pytest.raises(ValueError, match="origin azimuth file"):
            convert_format(
                input_file=str(csv_file),
                output_file=str(output_path),
                from_format="csv",
                to_format="shp-lines",
                crs="EPSG:6347",
            )

        print("✓ Correctly requires origin azimuths for line shapefile export")


def test_crs_parameter():
    """Test different CRS options."""
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not installed")

    from profcalc.common.csv_io import read_csv_profiles
    from profcalc.common.shapefile_io import (
        write_survey_points_shapefile,
    )

    csv_file = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "input_examples"
        / "test_profiles.csv"
    )

    if not csv_file.exists():
        pytest.skip("Test data not found")

    profiles = read_csv_profiles(str(csv_file))

    # Test different CRS values
    crs_options = [
        "EPSG:6347",  # NJ State Plane
        "EPSG:6348",  # DE State Plane
        "EPSG:2272",  # PA State Plane
    ]

    for crs in crs_options:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / f"test_{crs.replace(':', '_')}.shp"

            write_survey_points_shapefile(profiles, output_path, crs=crs)

            gdf = gpd.read_file(output_path)
            crs_str = gdf.crs.to_string() if gdf.crs is not None else ""
            assert crs_str == crs, f"CRS mismatch for {crs}"

            print(f"✓ CRS {crs} works correctly")


if __name__ == "__main__":
    print("Testing Shapefile Conversion...")
    print("=" * 60)

    if not GEOPANDAS_AVAILABLE:
        print("⚠️  geopandas not installed - some tests will be skipped")
        print("   Install with: pip install profile-analysis[gis]")
        print()

    # Run tests
    try:
        test_point_shapefile_from_csv()
        print()
    except Exception as e:
        print(f"✗ Point shapefile test failed: {e}")
        print()

    try:
        test_line_shapefile_from_csv()
        print()
    except Exception as e:
        print(f"✗ Line shapefile test failed: {e}")
        print()

    try:
        test_convert_csv_to_point_shapefile()
        print()
    except Exception as e:
        print(f"✗ CSV→Point conversion test failed: {e}")
        print()

    try:
        test_convert_csv_to_line_shapefile()
        print()
    except Exception as e:
        print(f"✗ CSV→Line conversion test failed: {e}")
        print()

    try:
        test_line_shapefile_requires_baselines()
        print()
    except Exception as e:
        print(f"✗ Baselines requirement test failed: {e}")
        print()

    try:
        test_crs_parameter()
        print()
    except Exception as e:
        print(f"✗ CRS parameter test failed: {e}")
        print()

    print("=" * 60)
    print("Testing complete!")
