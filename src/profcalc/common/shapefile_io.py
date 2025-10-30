"""
Shapefile input/output for coastal profile data.

Provides functions to export beach profile data to ESRI Shapefiles with 3D geometry
(PointZ and PolyLineZ) for use in ArcGIS, QGIS, and other GIS software.

Supported exports:
    - Survey points shapefile (PointZ) - Individual survey measurements
    - Profile lines shapefile (PolyLineZ) - 3D profile transects

Requires:
    - geopandas>=0.14.0 (install with: pip install profile-analysis[gis])
    - Baseline data (origin coordinates and azimuths)
"""

import math
from pathlib import Path
from typing import List, Optional

import numpy as np

from profcalc.common.bmap_io import Profile

try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


def _check_geopandas() -> None:
    """Check if geopandas is available and raise helpful error if not."""
    if not GEOPANDAS_AVAILABLE:
        raise ImportError(
            "Shapefile export requires the 'geopandas' library.\n"
            "Install with: pip install profile-analysis[gis]\n"
            "Or manually: pip install geopandas>=0.14.0"
        )


def write_survey_points_shapefile(
    profiles: List[Profile],
    output_path: Path,
    crs: str = "EPSG:6347",
    include_extra_fields: bool = True,
) -> None:
    """
    Write individual survey points to shapefile (PointZ geometry).

    Creates a 3D point shapefile where each survey measurement becomes a separate
    point feature with X, Y, Z coordinates. Elevation is stored both in the 3D
    geometry and as an attribute for easy symbolization.

    Parameters:
        profiles: List of Profile objects with Y coordinates in metadata
        output_path: Path to output shapefile (.shp)
        crs: Coordinate reference system (EPSG code)
             Common options:
             - 'EPSG:6347' - NAD83(2011) StatePlane NJ (feet) [default]
             - 'EPSG:6348' - NAD83(2011) StatePlane DE (feet)
             - 'EPSG:2272' - NAD83 StatePlane PA South (feet)
             - 'EPSG:2252' - NAD83 StatePlane MD (feet)
        include_extra_fields: Include extra columns from CSV/XYZ metadata if present

    Raises:
        ImportError: If geopandas is not installed
        ValueError: If profiles lack Y coordinates or origin data
        BeachProfileError: If shapefile writing fails

    Example:
        >>> from profcalc.common.bmap_io import read_bmap_freeformat
        >>> from pathlib import Path
        >>> profiles = read_bmap_freeformat('survey.bmap')
        >>> # Add Y coordinates from baselines first
        >>> write_survey_points_shapefile(
        ...     profiles,
        ...     Path('survey_points.shp'),
        ...     crs='EPSG:6347'
        ... )
        ✅ Wrote 2,450 survey points to survey_points.shp

    Notes:
        - Uses ACTUAL surveyed X,Y coordinates (includes GPS drift)
        - Z elevation stored in 3D geometry AND as attribute
        - Each survey point becomes a separate feature
        - Shapefile field names limited to 10 characters
        - Output includes .shp, .shx, .dbf, .prj, .cpg files
    """
    _check_geopandas()

    if not profiles:
        raise ValueError("No profiles provided for shapefile export")

    # Validate profiles have Y coordinates
    for profile in profiles:
        if profile.metadata is None or ("y" not in profile.metadata and "y_coordinates" not in profile.metadata):
            raise ValueError(
                f"Profile '{profile.name}' missing Y coordinates.\n"
                f"Y coordinates required for point shapefile export.\n"
                f"Use --baselines to calculate real-world coordinates from BMAP files."
            )

    # Build geometry and attribute lists
    geometries: list = []
    attributes: dict = {
        "profile_id": [],
        "survey_dat": [],
        "point_num": [],
        "distance_f": [],
        "z": [],
    }

    # Track extra fields
    extra_field_names: list = []
    extra_field_data: dict = {}

    total_points = 0

    for profile in profiles:
        if profile.metadata is None:
            continue

        # Get Y coordinates - check both 'y' and 'y_coordinates' keys
        y_coords = profile.metadata.get("y") or profile.metadata.get("y_coordinates")
        if y_coords is None:
            continue

        # Validate Y coordinate count matches X coordinate count
        if len(y_coords) != len(profile.x):
            raise ValueError(
                f"Profile '{profile.name}': Y coordinate count ({len(y_coords)}) "
                f"does not match X coordinate count ({len(profile.x)})"
            )

        # Get extra fields from first profile with extras
        if include_extra_fields and "extra_columns" in profile.metadata:
            extra_cols = profile.metadata["extra_columns"]
            if not extra_field_names and "names" in extra_cols:
                extra_field_names = extra_cols["names"]
                # Initialize extra field data columns (truncate to 10 chars for shapefile)
                for field_name in extra_field_names:
                    truncated_name = field_name[:10]
                    extra_field_data[truncated_name] = []

        # Create point features
        for idx, (x, y, z) in enumerate(zip(profile.x, y_coords, profile.z)):
            # Create PointZ geometry
            geometries.append(Point(x, y, z))

            # Add standard attributes
            attributes["profile_id"].append(profile.name)
            attributes["survey_dat"].append(
                str(profile.date) if profile.date else ""
            )
            attributes["point_num"].append(idx + 1)

            # Calculate cross-shore distance from origin if available
            origin_x = 0.0
            if profile.metadata and "origin_x" in profile.metadata:
                origin_x = profile.metadata.get("origin_x", 0.0)
            distance = x - origin_x
            attributes["distance_f"].append(distance)
            attributes["z"].append(z)

            # Add extra field values if present
            if extra_field_data and profile.metadata and "extra_columns" in profile.metadata:
                extra_data = profile.metadata["extra_columns"].get("data", [])
                if idx < len(extra_data) and extra_data[idx]:
                    for field_idx, field_name in enumerate(extra_field_names):
                        truncated_name = field_name[:10]
                        if field_idx < len(extra_data[idx]):
                            extra_field_data[truncated_name].append(
                                extra_data[idx][field_idx]
                            )
                        else:
                            extra_field_data[truncated_name].append(None)
                else:
                    # No extra data for this point
                    for field_name in extra_field_names:
                        truncated_name = field_name[:10]
                        extra_field_data[truncated_name].append(None)

            total_points += 1

    # Merge extra field data into attributes
    attributes.update(extra_field_data)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs=crs)

    # Write to shapefile
    try:
        gdf.to_file(output_path, driver="ESRI Shapefile")
    except Exception as e:
        raise ValueError(
            f"Failed to write point shapefile: {e}"
        ) from e

    print(f"✅ Wrote {total_points:,} survey points to {output_path}")
    print("   Geometry type: PointZ (3D points with elevation)")
    print(f"   Coordinate system: {crs}")
    if extra_field_data:
        print(f"   Extra fields: {', '.join(extra_field_data.keys())}")


def write_profile_lines_shapefile(
    profiles: List[Profile],
    output_path: Path,
    crs: str = "EPSG:6347",
) -> None:
    """
    Write profile transect lines to shapefile (PolyLineZ geometry).

    Creates 3D line features representing beach profile transects. Each line is
    straight along the theoretical baseline azimuth with vertices at survey point
    cross-shore distances. Elevations are preserved at each vertex.

    Parameters:
        profiles: List of Profile objects with origin/azimuth in metadata
        output_path: Path to output shapefile (.shp)
        crs: Coordinate reference system (EPSG code)
             - 'EPSG:6347' - NAD83(2011) StatePlane NJ (feet) [default]
             - 'EPSG:6348' - NAD83(2011) StatePlane DE (feet)
             - 'EPSG:2272' - NAD83 StatePlane PA South (feet)
             - 'EPSG:2252' - NAD83 StatePlane MD (feet)

    Raises:
        ImportError: If geopandas is not installed
        ValueError: If profiles lack origin_x, origin_y, or azimuth
        BeachProfileError: If shapefile writing fails

    Example:
        >>> from profcalc.common.bmap_io import read_bmap_freeformat
        >>> from pathlib import Path
        >>> profiles = read_bmap_freeformat('survey.bmap')
        >>> # Add origin/azimuth from baselines first
        >>> write_profile_lines_shapefile(
        ...     profiles,
        ...     Path('profile_transects.shp'),
        ...     crs='EPSG:6347'
        ... )
        ✅ Wrote 25 profile lines (3D) to profile_transects.shp

    Notes:
        - Geometry type: PolyLineZ (3D line with Z elevation)
        - Number of vertices per line = number of survey points
        - Vertices placed at survey point cross-shore distances
        - Line follows theoretical baseline azimuth (straight line)
        - Z values stored in geometry AND as z_min/z_max attributes
        - Can be used for 3D visualization and cross-section extraction
    """
    _check_geopandas()

    if not profiles:
        raise ValueError("No profiles provided for shapefile export")

    geometries: list = []
    attributes: dict = {
        "profile_id": [],
        "survey_dat": [],
        "azimuth": [],
        "length_ft": [],
        "num_vertic": [],
        "z_min": [],
        "z_max": [],
    }

    total_vertices = 0

    for profile in profiles:
        # Validate required metadata
        if profile.metadata is None or "origin_x" not in profile.metadata:
            raise ValueError(
                f"Profile '{profile.name}' missing origin_x.\n"
                f"Origin coordinates required for line shapefile export.\n"
                f"Use --baselines to assign origin coordinates."
            )
        if "origin_y" not in profile.metadata:
            raise ValueError(
                f"Profile '{profile.name}' missing origin_y.\n"
                f"Origin coordinates required for line shapefile export.\n"
                f"Use --baselines to assign origin coordinates."
            )
        if "azimuth" not in profile.metadata:
            raise ValueError(
                f"Profile '{profile.name}' missing azimuth.\n"
                f"Azimuth required for line shapefile export.\n"
                f"Use --baselines to assign azimuth."
            )

        origin_x = profile.metadata["origin_x"]
        origin_y = profile.metadata["origin_y"]
        azimuth_deg = profile.metadata["azimuth"]
        azimuth_rad = math.radians(azimuth_deg)

        # Create 3D vertices at each survey point distance
        # Vertices projected onto theoretical azimuth line
        coords_3d = []
        for x_distance, z_elevation in zip(profile.x, profile.z):
            # Project point onto azimuth line
            real_x = origin_x + x_distance * math.cos(azimuth_rad)
            real_y = origin_y + x_distance * math.sin(azimuth_rad)
            coords_3d.append((real_x, real_y, z_elevation))

        # Create LineStringZ geometry
        line_geom = LineString(coords_3d)
        geometries.append(line_geom)

        # Populate attributes
        attributes["profile_id"].append(profile.name)
        attributes["survey_dat"].append(str(profile.date) if profile.date else "")
        attributes["azimuth"].append(azimuth_deg)
        attributes["length_ft"].append(float(max(profile.x)))
        attributes["num_vertic"].append(len(coords_3d))
        attributes["z_min"].append(float(min(profile.z)))
        attributes["z_max"].append(float(max(profile.z)))

        total_vertices += len(coords_3d)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs=crs)

    # Write to shapefile
    try:
        gdf.to_file(output_path, driver="ESRI Shapefile")
    except Exception as e:
        raise ValueError(
            f"Failed to write line shapefile: {e}"
        ) from e

    print(f"✅ Wrote {len(profiles)} profile lines (3D) to {output_path}")
    print("   Geometry type: PolyLineZ (Z-enabled)")
    print(f"   Total vertices: {total_vertices:,}")
    print(f"   Coordinate system: {crs}")


def validate_shapefile_export_requirements(
    profiles: List[Profile], baselines_file: Optional[Path] = None
) -> List[str]:
    """
    Validate that profiles have required data for shapefile export.

    Parameters:
        profiles: List of Profile objects to validate
        baselines_file: Path to baselines file (if provided)

    Returns:
        List of warning/error messages (empty if all validations pass)

    Example:
        >>> issues = validate_shapefile_export_requirements(profiles, baselines_path)
        >>> if issues:
        ...     for issue in issues:
        ...         print(issue)
    """
    issues = []

    if not profiles:
        issues.append("❌ No profiles to export")
        return issues

    # Check if baselines file was provided
    if not baselines_file:
        issues.append(
            "❌ Shapefile export requires --baselines <file>\n"
            "   Baseline file must contain: Profile, Origin_X, Origin_Y, Azimuth"
        )
        return issues

    # Check for missing origin coordinates
    missing_origins = []
    for profile in profiles:
        if (
            profile.metadata is None
            or "origin_x" not in profile.metadata
            or "origin_y" not in profile.metadata
        ):
            missing_origins.append(profile.name)

    if missing_origins:
        issues.append(
            f"❌ {len(missing_origins)} profile(s) missing origin coordinates:\n"
            f"   {', '.join(missing_origins[:5])}"
            + (f" ... and {len(missing_origins) - 5} more" if len(missing_origins) > 5 else "")
        )

    # Check for missing azimuths (needed for line shapefile)
    missing_azimuth = []
    for profile in profiles:
        if profile.metadata is None or "azimuth" not in profile.metadata:
            missing_azimuth.append(profile.name)

    if missing_azimuth:
        issues.append(
            f"⚠️  {len(missing_azimuth)} profile(s) missing azimuth:\n"
            f"   {', '.join(missing_azimuth[:5])}"
            + (f" ... and {len(missing_azimuth) - 5} more" if len(missing_azimuth) > 5 else "")
            + "\n   Cannot create line shapefile for these profiles"
        )

    # Check for missing Y coordinates (needed for point shapefile)
    missing_y = []
    for profile in profiles:
        if profile.metadata is None or ("y" not in profile.metadata and "y_coordinates" not in profile.metadata):
            missing_y.append(profile.name)

    if missing_y:
        issues.append(
            f"⚠️  {len(missing_y)} profile(s) missing Y coordinates:\n"
            f"   {', '.join(missing_y[:5])}"
            + (f" ... and {len(missing_y) - 5} more" if len(missing_y) > 5 else "")
            + "\n   Cannot create point shapefile for these profiles"
        )

    return issues


def read_point_shapefile(shapefile_path: Path) -> List[Profile]:
    """
    Read point shapefile and convert to Profile objects.

    Supports Point and PointZ geometries. For Point geometries, Z values
    are taken from a 'Z' or 'z' attribute field if available.

    Parameters:
        shapefile_path (Path): Path to the shapefile (.shp file)

    Returns:
        List[Profile]: List of Profile objects

    Raises:
        ImportError: If geopandas is not available
        FileNotFoundError: If shapefile does not exist
        ValueError: If shapefile format is invalid
    """
    _check_geopandas()

    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

    # Read shapefile
    gdf = gpd.read_file(shapefile_path)

    if gdf.empty:
        raise ValueError("Shapefile contains no features")

    # Check geometry type
    geom_types = gdf.geometry.type.unique()
    if not all(t in ["Point", "PointZ"] for t in geom_types):
        raise ValueError(
            f"Unsupported geometry types: {geom_types}. Only Point and PointZ are supported."
        )

    # Group by profile identifier
    profile_column = None
    possible_profile_cols = [
        "profile",
        "profile_name",
        "profile_id",
        "id",
        "name",
    ]

    for col in possible_profile_cols:
        if col in gdf.columns:
            profile_column = col
            break

    if profile_column is None:
        # If no profile column found, treat all points as one profile
        profile_column = "profile"
        gdf[profile_column] = "Profile_1"

    profiles = []

    for profile_name, group in gdf.groupby(profile_column):
        points = []

        for _, row in group.iterrows():
            geom = row.geometry
            if geom is None:
                continue

            # Get coordinates
            if hasattr(geom, "z") and geom.z is not None:
                # PointZ geometry
                x, y, z = geom.x, geom.y, geom.z
            else:
                # Point geometry - try to get Z from attributes
                x, y = geom.x, geom.y
                z = row.get(
                    "Z",
                    row.get(
                        "z", row.get("elevation", row.get("Elevation", 0.0))
                    ),
                )

            points.append((x, y, z))

        if not points:
            continue

        # Sort points by X coordinate (assuming profile direction)
        points.sort(key=lambda p: p[0])

        # Extract coordinates
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        z_coords = [p[2] for p in points]

        # Create profile
        profile = Profile(
            name=str(profile_name),
            date=None,
            description=None,
            x=np.array(x_coords),
            z=np.array(z_coords),
            metadata={"y": y_coords},
        )

        profiles.append(profile)

    return profiles


def read_line_shapefile(shapefile_path: Path) -> List[Profile]:
    """
    Read line shapefile and convert to Profile objects.

    Supports LineString and LineStringZ geometries. For LineString geometries,
    Z values are taken from a 'Z' or 'z' attribute field if available.

    Parameters:
        shapefile_path (Path): Path to the shapefile (.shp file)

    Returns:
        List[Profile]: List of Profile objects

    Raises:
        ImportError: If geopandas is not available
        FileNotFoundError: If shapefile does not exist
        ValueError: If shapefile format is invalid
    """
    _check_geopandas()

    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

    # Read shapefile
    gdf = gpd.read_file(shapefile_path)

    if gdf.empty:
        raise ValueError("Shapefile contains no features")

    # Check geometry type
    geom_types = gdf.geometry.type.unique()
    if not all(t in ["LineString", "LineStringZ"] for t in geom_types):
        raise ValueError(
            f"Unsupported geometry types: {geom_types}. Only LineString and LineStringZ are supported."
        )

    profiles = []

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue

        # Get profile name
        profile_name = row.get(
            "profile",
            row.get("profile_name", row.get("name", f"Profile_{idx + 1}")),
        )

        # Extract coordinates
        coords = list(geom.coords)

        if hasattr(geom, "has_z") and geom.has_z:
            # LineStringZ
            x_coords = [c[0] for c in coords]
            y_coords = [c[1] for c in coords]
            z_coords = [c[2] for c in coords]
        else:
            # LineString - try to get Z from attributes or set to 0
            x_coords = [c[0] for c in coords]
            y_coords = [c[1] for c in coords]
            z_coords = [
                row.get("Z", row.get("z", row.get("elevation", 0.0)))
            ] * len(coords)

        # Create profile
        profile = Profile(
            name=str(profile_name),
            date=None,
            description=None,
            x=np.array(x_coords),
            z=np.array(z_coords),
            metadata={"y": y_coords},
        )

        profiles.append(profile)

    return profiles
