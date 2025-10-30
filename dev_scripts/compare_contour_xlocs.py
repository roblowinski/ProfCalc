import csv
from pathlib import Path
from typing import List, Optional, Tuple

# File paths
# For batch validation, use the large OC_2021-2024_Monitoring.dat output
PYTHON_OUT = Path("temp/test_contour_xlocs_oc2021.csv")
BMAP_OUT = Path("data/testing_files/bmap_calcs/ContourLocationTest_BMAP_Results.rpt")


# Helper to parse Python tool output (skips header, returns list of (profile, xon, xoff, vol, xloc))
def parse_python_output(path: Path) -> List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float]]]:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for i, row in enumerate(reader):
            if i < 5 or not row:
                continue
            # Profile name is not present, so use index as key
            name = f"Profile_{i-4:03d}"
            xon = xoff = vol = xloc = None
            if len(row) >= 5:
                try:
                    xon = float(row[1])
                    xoff = float(row[2])
                    vol = float(row[3])
                    xloc = float(row[4])
                except (IndexError, ValueError):
                    xon = xoff = vol = xloc = None
            rows.append((name, xon, xoff, vol, xloc))
    return rows

# Helper to parse BMAP output (returns list of (profile, xon, xoff, vol, xloc))
def parse_bmap_output(path: Path) -> List[Tuple[str, Optional[float], Optional[float], Optional[float], Optional[float]]]:
    rows = []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 5 or not line.strip():
                continue
            parts = line.strip().split('\t')
            name = parts[0].strip() if len(parts) > 0 else f"Profile_{i-4:03d}"
            xon = xoff = vol = xloc = None
            if len(parts) >= 5:
                try:
                    xon = float(parts[1])
                    xoff = float(parts[2])
                    vol = float(parts[3])
                    xloc = float(parts[4])
                except ValueError:
                    xon = xoff = vol = xloc = None
            rows.append((name, xon, xoff, vol, xloc))
    return rows

# Parse both outputs
py_rows = parse_python_output(PYTHON_OUT)
bmap_rows = parse_bmap_output(BMAP_OUT)

# Side-by-side comparison (by order, since Python output lacks names)
results: list[tuple] = []
match_counts = {'xon': 0, 'xoff': 0, 'vol': 0, 'xloc': 0, 'all': 0}
tol_x = 1.0
tol_vol = 0.05
for i, (bmap, py) in enumerate(zip(bmap_rows, py_rows)):
    bmap_name, bmap_xon, bmap_xoff, bmap_vol, bmap_xloc = bmap
    _, py_xon, py_xoff, py_vol, py_xloc = py
    match_xon = abs(bmap_xon - py_xon) < tol_x if bmap_xon is not None and py_xon is not None else False
    match_xoff = abs(bmap_xoff - py_xoff) < tol_x if bmap_xoff is not None and py_xoff is not None else False
    match_vol = abs(bmap_vol - py_vol) < tol_vol if bmap_vol is not None and py_vol is not None else False
    match_xloc = abs(bmap_xloc - py_xloc) < tol_x if bmap_xloc is not None and py_xloc is not None else False
    match_all = match_xon and match_xoff and match_vol and match_xloc
    if match_xon:
        match_counts['xon'] += 1
    if match_xoff:
        match_counts['xoff'] += 1
    if match_vol:
        match_counts['vol'] += 1
    if match_xloc:
        match_counts['xloc'] += 1
    if match_all:
        match_counts['all'] += 1
    results.append((i+1, bmap_name, bmap_xon, py_xon, match_xon, bmap_xoff, py_xoff, match_xoff, bmap_vol, py_vol, match_vol, bmap_xloc, py_xloc, match_xloc, match_all))

total = len(bmap_rows)

with open("dev_scripts/TOOL_VALIDATION_LOG.md", "a", encoding="utf-8") as f:
    f.write("\n## Test 1d: Full Side-by-Side Comparison (XOn, XOff, Volume, Xloc)\n")
    f.write("\n| # | Profile | BMAP XOn | Py XOn | XOn ✓ | BMAP XOff | Py XOff | XOff ✓ | BMAP Vol | Py Vol | Vol ✓ | BMAP Xloc | Py Xloc | Xloc ✓ | All ✓ |\n")
    f.write("|---|---------|----------|--------|--------|-----------|---------|---------|----------|--------|--------|-----------|---------|--------|--------|\n")
    for (idx, name, bxon, pxon, mxon, bxoff, pxoff, mxoff, bvol, pvol, mvol, bxloc, pxloc, mxloc, mall) in results:
        f.write(f"| {idx} | {name} | {bxon:.2f} | {pxon:.2f} | {'✔️' if mxon else '❌'} | {bxoff:.2f} | {pxoff:.2f} | {'✔️' if mxoff else '❌'} | {bvol:.3f} | {pvol:.3f} | {'✔️' if mvol else '❌'} | {bxloc:.2f} | {pxloc:.2f} | {'✔️' if mxloc else '❌'} | {'✔️' if mall else '❌'} |\n")
    f.write(f"\n**Match Score (All Columns):** {match_counts['all']} / {total} = {match_counts['all']/total:.2%}\n")
    f.write(f"**XOn:** {match_counts['xon']}/{total} | XOff: {match_counts['xoff']}/{total} | Vol: {match_counts['vol']}/{total} | Xloc: {match_counts['xloc']}/{total}\n")
    if match_counts['all'] == total:
        f.write("\n✅ The Python tool matches the BMAP results for all columns and all profiles.\n")
    else:
        f.write("\n❌ Differences found in one or more columns. Review needed.\n")
