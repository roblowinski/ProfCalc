"""
Smoke-run quick tools (non-interactive) to validate they work end-to-end.
This script is for local developer verification in the workspace and is not a unit test.
"""
from pathlib import Path

from profcalc.cli.tools import assign, convert, fix_bmap, inventory

BASE = Path(__file__).resolve().parents[1] / "data" / "required_inputs"
OUT = Path(__file__).resolve().parents[1] / "data" / "temp"
OUT.mkdir(parents=True, exist_ok=True)

# 1) Fix BMAP point counts
bmap_in = BASE / "bmap_bad.bmap"
bmap_out = OUT / "bmap_bad_fix.bmap"
print("\n=== Running fix_bmap smoke check ===")
corrections = fix_bmap.fix_bmap_point_counts(str(bmap_in), str(bmap_out), verbose=True, skip_confirmation=True)
print("fix_bmap corrections:", corrections)
print("written:", bmap_out.exists())

# 2) Inventory report
print("\n=== Running inventory smoke check ===")
inv_report_path = OUT / "inventory_report.txt"
report = inventory.generate_inventory_report(str(bmap_in), verbose=True)
inv_report_path.write_text(report, encoding="utf-8")
print("inventory report written:", inv_report_path.exists())

# 3) Assign profiles
print("\n=== Running assign smoke check (distance method) ===")
assign_in = BASE / "assign_points.xyz"
assign_out = OUT / "assign_output.csv"
points_df = assign.read_points_file(str(assign_in))
profiles = assign.assign_profiles_by_clustering(points_df, method="distance", eps=50.0, min_samples=1, prefix="SMOKE", verbose=True)
assign.write_output_with_profiles(profiles, str(assign_out), str(assign_in))
print("assign output written:", assign_out.exists())

# 4) Convert - use existing small test_profiles.csv if present
print("\n=== Running convert smoke check ===")
conv_in = BASE / "test_profiles.csv"
conv_out = OUT / "convert_output.csv"
if conv_in.exists():
    convert.convert_format(str(conv_in), str(conv_out), from_format="csv", to_format="csv", mode="2d")
    print("convert output written:", conv_out.exists())
else:
    print("Skipped convert: test_profiles.csv not found")

print("\n=== Smoke run complete ===")
