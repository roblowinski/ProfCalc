# =============================================================================
# Beach Profile Name Assignment Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/assign.py
#
# PURPOSE:
# This tool automatically assigns profile names and identifiers to XYZ/CSV
# files that contain beach profile data but lack explicit profile identifiers.
# It uses spatial clustering algorithms to group survey points into logical
# profile transects and assigns meaningful names for further analysis.
#
# WHAT IT'S FOR:
# - Processes raw survey data files without profile identifiers
# - Uses DBSCAN clustering or distance-based heuristics to group points
# - Automatically assigns sequential profile names (Profile_001, Profile_002, etc.)
# - Supports multiple output formats (CSV, XYZ, BMAP)
# - Handles both 2D and 3D coordinate systems
# - Provides interactive parameter tuning for clustering algorithms
#
# WORKFLOW POSITION:
# This tool is used early in the data processing pipeline when working with
# raw survey data that hasn't been organized into named profiles. It's commonly
# used after data import but before detailed analysis, ensuring that profile
# data is properly structured and identifiable for subsequent processing.
#
# LIMITATIONS:
# - Requires scikit-learn for advanced clustering (optional dependency)
# - Clustering accuracy depends on survey point density and spacing
# - May not handle complex survey patterns or irregular point distributions
# - Interactive parameter selection can be time-consuming for large datasets
# - Assumes points represent cross-shore profile transects
#
# ASSUMPTIONS:
# - Input data contains X (cross-shore) and Z (elevation) coordinates
# - Points are organized in roughly parallel profile transects
# - Survey data represents beach profile morphology
# - Users can provide appropriate clustering parameters
# - Output formats are compatible with downstream analysis tools
#
# =============================================================================

"""Assign Profile Names

Assign profile names to XYZ/CSV files that lack profile identifiers. The
module groups points into profiles using clustering (DBSCAN or a simple
distance heuristic) and writes outputs in CSV/XYZ/BMAP formats.

Usage examples:
    - Menu: from the interactive menu choose the Quick Tools → Assign tool or
        call :func:`execute_from_menu` to run the interactive flow.
"""

import importlib
from pathlib import Path
from typing import TYPE_CHECKING, List

import numpy as np
import pandas as pd

# Import sklearn only for type checkers; do runtime import lazily to avoid
# language-server warnings in developer environments that don't have
# scikit-learn installed. Actual imports are performed inside
# `assign_profiles_by_clustering` when the spatial method is used.
if TYPE_CHECKING:
    from sklearn.cluster import DBSCAN  # type: ignore  # noqa: F401
    from sklearn.preprocessing import (
        StandardScaler,  # type: ignore  # noqa: F401
    )

from profcalc.cli.menu_system import notify_and_wait
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    timestamped_output_path,
)
from profcalc.common.bmap_io import Profile


def execute_from_cli(args: List[str]) -> None:
    """
    Execute assign tool from command line.

    Args:
        args: Command line arguments (file patterns)
    """
    if not args:
        print("Error: No input file patterns provided")
        log_quick_tool_error("assign", "No input file patterns provided")
        return

    from glob import glob

    # Expand wildcards and check for files
    input_paths = []
    for pattern in args:
        expanded = glob(pattern)
        if not expanded:
            print(f"❌ No files matched: {pattern}")
        input_paths.extend(expanded)
    if not input_paths:
        msg = "❌ No input files found."
        print(msg)
        log_quick_tool_error("assign", msg)
        return

    # If we get here, files were found - proceed with processing
    # Use default parameters for CLI mode
    output_file = ""
    method = "spatial"
    eps = 50.0
    min_samples = 5
    prefix = "Profile"
    verbose = False

    try:
        print(f"\n🔍 Reading points from {len(input_paths)} file(s):")
        for p in input_paths:
            print(f"   - {p}")
        all_dfs = []
        for f in input_paths:
            try:
                df = read_points_file(f)
                all_dfs.append(df)
            except (OSError, IOError, ValueError) as e:
                log_quick_tool_error("assign", f"Error reading file {f}: {e}", exc=e)
                print(f"❌ Error reading {f}: {e}")
        if not all_dfs:
            print("❌ No valid data loaded.")
            return
        points_df = pd.concat(all_dfs, ignore_index=True)
        print(f"   Found {len(points_df)} points")

        # Assign profiles
        profiles = assign_profiles_by_clustering(
            points_df,
            method=method,
            eps=eps,
            min_samples=min_samples,
            prefix=prefix,
            verbose=verbose,
        )

        print(f"\n📊 Created {len(profiles)} profiles")

        # Determine output file name
        if output_file:
            output_path = output_file
        else:
            ext = (
                ".csv"
                if input_paths and input_paths[0].lower().endswith(".csv")
                else ".xyz"
            )
            output_path = timestamped_output_path("assign", ext=ext)

        # Write output
        print(f"💾 Writing output: {output_path}")
        write_output_with_profiles(
            profiles, output_path, input_paths[0] if input_paths else None
        )
        print(f"\n✅ Profile assignment complete! Output saved to: {output_path}")

    except (OSError, ValueError, IOError, RuntimeError) as e:
        log_quick_tool_error("assign", f"Error in assign operation: {e}", exc=e)
        print(f"❌ Error: {e}")


def execute_from_menu() -> None:
    from tabulate import tabulate

    def make_profile_summary(profiles: List[Profile]) -> str:
        rows = []
        for p in profiles:
            x_min, x_max = float(np.min(p.x)), float(np.max(p.x))
            y_vals = (
                p.metadata.get("y", [0.0] * len(p.x))
                if p.metadata
                else [0.0] * len(p.x)
            )
            y_min, y_max = float(np.min(y_vals)), float(np.max(y_vals))
            z_min, z_max = float(np.min(p.z)), float(np.max(p.z))
            rows.append(
                [
                    p.name,
                    len(p.x),
                    f"{x_min:.2f} – {x_max:.2f}",
                    f"{y_min:.2f} – {y_max:.2f}",
                    f"{z_min:.2f} – {z_max:.2f}",
                ]
            )
        headers = ["Profile Name", "Points", "X Range", "Y Range", "Z Range"]
        return tabulate(rows, headers, tablefmt="github")

    """Execute profile name assignment from interactive menu."""
    print("\n" + "=" * 60)
    print("PROFILE NAME ASSIGNMENT")
    print("=" * 60)
    print("Assign profile names to XYZ/CSV files missing profile IDs.")
    print("Uses spatial clustering to group points into logical profiles.")

    # Get user inputs

    input_patterns = (
        input("Enter input file path(s) or wildcard(s) (XYZ/CSV, space-separated): ")
        .strip()
        .split()
    )
    output_file = input(
        "Enter output file path (leave blank for auto-naming): "
    ).strip()

    method_choice = (
        input("\nClustering method (spatial/distance) [spatial]: ").strip().lower()
    )
    method = "spatial" if method_choice != "distance" else "distance"

    if method == "spatial":
        eps_input = input("DBSCAN epsilon (spatial distance in feet) [50.0]: ").strip()
        eps = float(eps_input) if eps_input else 50.0

        min_samples_input = input("DBSCAN minimum samples [5]: ").strip()
        min_samples = int(min_samples_input) if min_samples_input else 5
    else:
        eps = 50.0
        min_samples = 5

    prefix = input("Profile name prefix [Profile]: ").strip()
    prefix = prefix if prefix else "Profile"

    verbose = input("Show detailed clustering info? (y/n) [n]: ").strip().lower() == "y"

    from glob import glob

    try:
        # Expand wildcards and aggregate all points
        input_paths = []
        for pattern in input_patterns:
            expanded = glob(pattern)
            if not expanded:
                print(f"❌ No files matched: {pattern}")
            input_paths.extend(expanded)
        if not input_paths:
            msg = "❌ No input files found. Exiting."
            print(msg)
            log_quick_tool_error("assign", msg)
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

        print(f"\n🔍 Reading points from {len(input_paths)} file(s):")
        for p in input_paths:
            print(f"   - {p}")
        all_dfs = []
        for f in input_paths:
            try:
                df = read_points_file(f)
                all_dfs.append(df)
            except (OSError, IOError, ValueError) as e:
                log_quick_tool_error("assign", f"Error reading file {f}: {e}", exc=e)
                print(f"❌ Error reading {f}: {e}")
        if not all_dfs:
            print("❌ No valid data loaded. Exiting.")
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return
        points_df = pd.concat(all_dfs, ignore_index=True)
        print(f"   Found {len(points_df)} points")

        # Assign profiles
        profiles = assign_profiles_by_clustering(
            points_df,
            method=method,
            eps=eps,
            min_samples=min_samples,
            prefix=prefix,
            verbose=verbose,
        )

        print(f"\n📊 Created {len(profiles)} profiles")
        print("\nProfile Assignment Summary:")
        print(make_profile_summary(profiles))

        # Determine output file name if not provided (menu: timestamped)
        if output_file:
            output_path = output_file
        else:
            ext = (
                ".csv"
                if input_paths and input_paths[0].lower().endswith(".csv")
                else ".xyz"
            )
            output_path = timestamped_output_path("assign", ext=ext)
            print(
                f"💡 Output file not specified. Using timestamped file: {output_path}"
            )

        # Write summary to a text file
        base = Path(output_path).with_suffix("")
        summary_path = str(base) + "_summary.txt"
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(make_profile_summary(profiles) + "\n")
            print(f"\n📝 Profile summary saved to: {summary_path}")
        except (OSError, IOError) as e:
            log_quick_tool_error("assign", f"Failed to write summary file: {e}", e)
            print(f"\n❌ Failed to write summary file: {e}")

        # Write output
        print(f"💾 Writing output: {output_path}")
        try:
            write_output_with_profiles(
                profiles, output_path, input_paths[0] if input_paths else None
            )
            print("\n✅ Profile assignment complete!")
            print(f"   Output saved to: {output_path}")
        except (OSError, IOError, ValueError) as e:
            log_quick_tool_error("assign", f"Failed to write assign output: {e}", e)
            print(f"❌ Failed to write assign output: {e}")

    except FileNotFoundError:
        log_quick_tool_error("assign", "Input file not found")
        print("\n❌ Error: Input file not found.")
    except (OSError, ValueError, TypeError, ImportError) as e:
        log_quick_tool_error("assign", f"Error during assign operation: {e}", exc=e)
        print(f"\n❌ Error: {e}")

    notify_and_wait("", prompt="\nPress Enter to continue...")


def read_points_file(file_path: str) -> pd.DataFrame:
    """
    Read XYZ or CSV file containing point data.

    Args:
        file_path: Path to input file

    Returns:
        DataFrame with columns: x, y, z (and any extra columns)
    """
    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
        # Try to detect coordinate columns
        coord_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if "x" in col_lower and "coord" not in col_lower:
                coord_cols.append(("x", col))
            elif "y" in col_lower and "coord" not in col_lower:
                coord_cols.append(("y", col))
            elif "z" in col_lower or "elev" in col_lower or "depth" in col_lower:
                coord_cols.append(("z", col))

        if len(coord_cols) < 3:
            raise ValueError("Could not identify X, Y, Z columns in CSV file")

        # Rename to standard names
        rename_dict = {col: name for name, col in coord_cols}
        df = df.rename(columns=rename_dict)

    else:
        # Assume XYZ format (space/comma separated)
        df = pd.read_csv(file_path, sep=r"\s+|,", engine="python", header=None)
        if df.shape[1] < 3:
            raise ValueError("XYZ file must have at least 3 columns (X, Y, Z)")

        df.columns = pd.Index(
            ["x", "y", "z"] + [f"extra_{i}" for i in range(df.shape[1] - 3)]
        )

    # Ensure numeric types
    for col in ["x", "y", "z"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["x", "y", "z"])

    return df


def assign_profiles_by_clustering(
    points_df: pd.DataFrame,
    method: str = "spatial",
    eps: float = 50.0,
    min_samples: int = 5,
    prefix: str = "Profile",
    verbose: bool = False,
) -> List[Profile]:
    """
    Assign profile names using spatial clustering.

    Args:
        points_df: DataFrame with x, y, z columns
        method: Clustering method ("spatial" or "distance")
        eps: DBSCAN epsilon parameter
        min_samples: DBSCAN minimum samples parameter
        prefix: Profile name prefix
        verbose: Show detailed info

    Returns:
        List of Profile objects with assigned names
    """
    if method == "spatial":
        # Import sklearn lazily to avoid top-level import errors in environments
        # where scikit-learn is not installed. Provide a clear runtime error if
        # the spatial method is requested but sklearn isn't available.
        try:
            # Use importlib to avoid static import checks in editors that don't
            # have sklearn installed. We still provide TYPE_CHECKING imports
            # above so static type checkers understand the types.
            cluster_mod = importlib.import_module("sklearn.cluster")
            preprocess_mod = importlib.import_module("sklearn.preprocessing")
            DBSCAN = getattr(cluster_mod, "DBSCAN")
            StandardScaler = getattr(preprocess_mod, "StandardScaler")
        except ImportError as e:
            # ImportError covers ModuleNotFoundError as well. If importing the
            # module fails due to other runtime errors inside the package, let
            # those propagate so the caller sees the real problem.
            print(
                "❌ Error: sklearn required for spatial clustering. Install with: pip install scikit-learn"
            )
            raise ImportError("sklearn not available") from e

        # Use DBSCAN for spatial clustering
        coords = points_df[["x", "y"]].values
        scaler = StandardScaler()
        coords_scaled = scaler.fit_transform(coords)

        dbscan = DBSCAN(eps=eps / 1000.0, min_samples=min_samples)  # Scale eps
        clusters = dbscan.fit_predict(coords_scaled)

        if verbose:
            n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
            n_noise = list(clusters).count(-1)
            print(f"   DBSCAN found {n_clusters} clusters, {n_noise} noise points")

    else:
        # Simple distance-based clustering (group by Y coordinate ranges)
        y_coords = points_df["y"].values
        y_sorted = np.sort(np.array(y_coords))  # Convert to numpy array first
        y_diffs = np.diff(y_sorted)

        # Find gaps larger than eps
        gap_indices = np.where(y_diffs > eps)[0] + 1
        cluster_bounds = np.concatenate([[0], gap_indices, [len(y_sorted)]])

        clusters = np.zeros(len(points_df), dtype=int)
        for i, (start, end) in enumerate(zip(cluster_bounds[:-1], cluster_bounds[1:])):
            # Use end-1 to avoid index out of bounds, since end can equal len(y_sorted)
            upper_bound = (
                y_sorted[end - 1] if end < len(y_sorted) else y_sorted[-1] + eps
            )
            mask = (y_coords >= y_sorted[start]) & (y_coords <= upper_bound)
            clusters[mask] = i

        if verbose:
            n_clusters = len(set(clusters))
            print(f"   Distance-based clustering found {n_clusters} profiles")

    # Create profiles from clusters
    profiles = []
    unique_clusters = sorted(set(clusters))

    for cluster_id in unique_clusters:
        if cluster_id == -1:  # Noise points
            continue

        mask = clusters == cluster_id
        cluster_points = points_df[mask]

        # Sort by x coordinate
        cluster_points = cluster_points.sort_values("x")

        profile_name = f"{prefix}_{cluster_id + 1:03d}"

        # Create Profile object
        profile = Profile(
            name=profile_name,
            date=None,
            description=f"Auto-assigned profile {cluster_id + 1}",
            x=cluster_points["x"].values,
            z=cluster_points["z"].values,
            metadata={"y": cluster_points["y"].values},
        )

        profiles.append(profile)

        if verbose:
            print(f"   {profile_name}: {len(cluster_points)} points")

    return profiles


def write_output_with_profiles(
    profiles: List[Profile], output_file: str, source_file: str
) -> None:
    """
    Write profiles to output file in appropriate format.

    Args:
        profiles: List of Profile objects
        output_file: Output file path
        source_file: Original input file path
    """
    output_path = Path(output_file)

    if output_path.suffix.lower() == ".csv":
        # Write as CSV
        all_data = []
        for profile in profiles:
            for i in range(len(profile.x)):
                row = {
                    "profile": profile.name,
                    "x": profile.x[i],
                    "y": profile.metadata.get("y", [0.0] * len(profile.x))[i]
                    if profile.metadata
                    else 0.0,
                    "z": profile.z[i],
                }
                all_data.append(row)

        df = pd.DataFrame(all_data)
        df.to_csv(output_file, index=False)

    elif output_path.suffix.lower() in [".xyz", ""]:
        # Write as XYZ format
        lines = []
        for profile in profiles:
            lines.append(f"> {profile.name}")
            for i in range(len(profile.x)):
                y_val = (
                    profile.metadata.get("y", [0.0] * len(profile.x))[i]
                    if profile.metadata
                    else 0.0
                )
                lines.append(f"{profile.x[i]:.2f} {y_val:.2f} {profile.z[i]:.2f}")

        output_path.write_text("\n".join(lines))

    else:
        # Default to BMAP format
        from profcalc.common.bmap_io import write_bmap_profiles

        write_bmap_profiles(profiles, output_file, source_filename=source_file)
