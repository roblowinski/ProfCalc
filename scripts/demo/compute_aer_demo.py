# =============================================================================
# Annual Erosion Rate (AER) Computation Demo Script
# =============================================================================
#
# FILE: scripts/demo/compute_aer_demo.py
#
# PURPOSE:
# This demo script showcases programmatic usage of the compute_aer_noninteractive
# function for calculating Annual Erosion Rates. It provides examples of how to
# use the AER computation functionality both interactively and in automated
# environments.
#
# WHAT IT'S FOR:
# - Demonstrating AER computation functionality
# - Providing usage examples for developers
# - Supporting interactive exploration of AER calculations
# - Enabling CI/CD pipeline demonstrations
# - Testing AER computation with different input scenarios
#
# WORKFLOW POSITION:
# This script serves as a demonstration and testing tool for the AER computation
# capabilities. It shows how to integrate AER calculations into larger workflows
# and provides examples for both file-based and dataset-based operations.
#
# LIMITATIONS:
# - Demo script with hardcoded examples
# - Limited error handling for demonstration purposes
# - Not intended for production use
# - Requires specific test data files
#
# ASSUMPTIONS:
# - Required data files are available at specified paths
# - profcalc package is properly installed and configured
# - Input data follows expected format conventions
# - System has necessary permissions for file operations
#
# =============================================================================

"""Demo script showing programmatic usage of compute_aer_noninteractive

Usage examples:
- Run against two files:
    python scripts/compute_aer_demo.py --before src/profcalc/data/temp/9Col_WithHeader.csv --after src/profcalc/data/temp/9Col_WithHeader.csv

- Register files in the in-memory session and call by dataset id:
    python scripts/compute_aer_demo.py --register src/profcalc/data/temp/9Col_WithHeader.csv --register src/profcalc/data/temp/9Col_WithHeader.csv

This script is intended for interactive exploration and CI demos.
"""

from argparse import ArgumentParser

from profcalc.cli.tools.annual import compute_aer_noninteractive
from profcalc.cli.tools.data import import_data


def main() -> None:
    ap = ArgumentParser()
    ap.add_argument("--before", help="Path or dataset id for the earlier survey")
    ap.add_argument("--after", help="Path or dataset id for the later survey")
    ap.add_argument("--register", action="append", help="Register a file with the session (can be repeated)")
    ap.add_argument("--dx", type=float, default=0.1, help="Grid spacing dx in feet")
    ap.add_argument("--use-bmap-core", action="store_true", help="Use BMAP core splitting logic")
    args = ap.parse_args()

    if args.register:
        for p in args.register:
            print(f"Registering: {p}")
            import_data(p)

    if not args.before or not args.after:
        print("Please provide --before and --after paths or dataset ids.\nSee --help for details.")
        return

    res = compute_aer_noninteractive(args.before, args.after, dx=args.dx, use_bmap_core=args.use_bmap_core)
    print("AER Result Summary:")
    for k, v in res.items():
        # limit printing of arrays
        if k.startswith("_"):
            continue
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
