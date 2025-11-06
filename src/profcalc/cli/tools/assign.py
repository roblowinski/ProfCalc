"""
Assign Profile Names - Assign profile names to XYZ/CSV files missing profile IDs.

Automatically groups points into profiles based on spatial clustering and assigns
meaningful profile names. Useful for raw survey data without profile identification.
"""

import argparse
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

from profcalc.common.bmap_io import Profile


def execute_from_cli(args: list[str]) -> None:
    """
    Execute profile name assignment from command line.

    Args:
        args: Command-line arguments (excluding the -a flag)
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -a",
        description="Assign profile names to XYZ/CSV files missing profile IDs",
    )
    parser.add_argument(
        "input_file", help="Input XYZ/CSV file without profile names"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output file path"
    )
    parser.add_argument(
        "--method",
        choices=["spatial", "distance"],
        default="spatial",
        help="Clustering method: spatial (DBSCAN) or distance-based (default: spatial)",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=50.0,
        help="DBSCAN epsilon parameter for spatial clustering (feet, default: 50.0)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=5,
        help="DBSCAN minimum samples parameter (default: 5)",
    )
    parser.add_argument(
        "--prefix",
        default="Profile",
        help="Profile name prefix (default: 'Profile')",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed clustering info",
    )

    parsed_args = parser.parse_args(args)

    print(f"🔍 Reading points from: {parsed_args.input_file}")
    print(f"📐 Clustering method: {parsed_args.method}")
    if parsed_args.method == "spatial":
        print(f"   DBSCAN eps: {parsed_args.eps} ft")
        print(f"   DBSCAN min_samples: {parsed_args.min_samples}")

    # Read input file
    points_df = read_points_file(parsed_args.input_file)
    print(f"   Found {len(points_df)} points")

    # Assign profiles using clustering
    profiles = assign_profiles_by_clustering(
        points_df,
        method=parsed_args.method,
        eps=parsed_args.eps,
        min_samples=parsed_args.min_samples,
        prefix=parsed_args.prefix,
        verbose=parsed_args.verbose,
    )

    print(f"\n📊 Created {len(profiles)} profiles")

    # Write output
    print(f"💾 Writing output: {parsed_args.output}")
    write_output_with_profiles(
        profiles, parsed_args.output, parsed_args.input_file
    )

    print("✅ Profile assignment complete!")


def execute_from_menu() -> None:
    """Execute profile name assignment from interactive menu."""
    print("\n" + "=" * 60)
    print("PROFILE NAME ASSIGNMENT")
    print("=" * 60)
    print("Assign profile names to XYZ/CSV files missing profile IDs.")
    print("Uses spatial clustering to group points into logical profiles.")

    # Get user inputs
    input_file = input("Enter input file path (XYZ/CSV): ").strip()
    output_file = input("Enter output file path: ").strip()

    method_choice = (
        input("\nClustering method (spatial/distance) [spatial]: ")
        .strip()
        .lower()
    )
    method = "spatial" if method_choice != "distance" else "distance"

    if method == "spatial":
        eps_input = input(
            "DBSCAN epsilon (spatial distance in feet) [50.0]: "
        ).strip()
        eps = float(eps_input) if eps_input else 50.0

        min_samples_input = input("DBSCAN minimum samples [5]: ").strip()
        min_samples = int(min_samples_input) if min_samples_input else 5
    else:
        eps = 50.0
        min_samples = 5

    prefix = input("Profile name prefix [Profile]: ").strip()
    prefix = prefix if prefix else "Profile"

    verbose = (
        input("Show detailed clustering info? (y/n) [n]: ").strip().lower()
        == "y"
    )

    try:
        print(f"\n🔍 Reading points from: {input_file}")

        # Read input file
        points_df = read_points_file(input_file)
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

        # Write output
        print(f"💾 Writing output: {output_file}")
        write_output_with_profiles(profiles, output_file, input_file)

        print("\n✅ Profile assignment complete!")
        print(f"   Output saved to: {output_file}")

    except FileNotFoundError:
        print(f"\n❌ Error: Input file not found: {input_file}")
    except (OSError, ValueError, TypeError, ImportError) as e:
        print(f"\n❌ Error: {e}")

    input("\nPress Enter to continue...")


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
            elif (
                "z" in col_lower or "elev" in col_lower or "depth" in col_lower
            ):
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
            print(
                f"   DBSCAN found {n_clusters} clusters, {n_noise} noise points"
            )

    else:
        # Simple distance-based clustering (group by Y coordinate ranges)
        y_coords = points_df["y"].values
        y_sorted = np.sort(np.array(y_coords))  # Convert to numpy array first
        y_diffs = np.diff(y_sorted)

        # Find gaps larger than eps
        gap_indices = np.where(y_diffs > eps)[0] + 1
        cluster_bounds = np.concatenate([[0], gap_indices, [len(y_sorted)]])

        clusters = np.zeros(len(points_df), dtype=int)
        for i, (start, end) in enumerate(
            zip(cluster_bounds[:-1], cluster_bounds[1:])
        ):
            # Use end-1 to avoid index out of bounds, since end can equal len(y_sorted)
            upper_bound = (
                y_sorted[end - 1]
                if end < len(y_sorted)
                else y_sorted[-1] + eps
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
                lines.append(
                    f"{profile.x[i]:.2f} {y_val:.2f} {profile.z[i]:.2f}"
                )

        output_path.write_text("\n".join(lines))

    else:
        # Default to BMAP format
        from profcalc.common.bmap_io import write_bmap_profiles

        write_bmap_profiles(profiles, output_file, source_filename=source_file)
