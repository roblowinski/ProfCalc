from pathlib import Path

BASE = Path(__file__).resolve().parents[1].joinpath('data', 'temp')
orig = BASE.joinpath('9Col_WithHeader.csv')
if not orig.exists():
    print('Original 9Col_WithHeader.csv not found at', orig)
    raise SystemExit(1)

before = BASE.joinpath('9Col_WithHeader_before.csv')
after = BASE.joinpath('9Col_WithHeader_after.csv')

text = orig.read_text(encoding='utf-8')
# Write before as exact copy
before.write_text(text, encoding='utf-8')

# Modify elevations for `after`: add +0.5 to ELEVATION (7th column)
lines = text.splitlines()
if not lines:
    raise SystemExit(1)
header = lines[0]
out_lines = [header]
for ln in lines[1:]:
    parts = ln.split(',')
    if len(parts) >= 7:
        try:
            z = float(parts[6])
            parts[6] = f"{z+0.5:.2f}"
        except ValueError:
            # Non-numeric elevation value, skip modification for this row
            pass
    out_lines.append(','.join(parts))

after.write_text('\n'.join(out_lines), encoding='utf-8')
print('Wrote', before, 'and', after)
