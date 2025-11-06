from pathlib import Path

p=Path('src/profcalc/cli/menu_system.py')
if not p.exists():
    print('file missing')
    raise SystemExit(2)
b = p.read_bytes()
if b.startswith(b'\xef\xbb\xbf'):
    p.write_bytes(b[3:])
    print('BOM removed')
else:
    print('No BOM present')
