import importlib
import os
import pkgutil
import sys
import traceback

# Walk package directory for profcalc modules
src_dir = os.path.join(os.getcwd(), 'src')
base = os.path.join(src_dir, 'profcalc')

# Ensure package root (src) is on sys.path so 'profcalc' is importable
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
modules = []
for finder, name, ispkg in pkgutil.walk_packages([base], prefix='profcalc.'):
    modules.append((name, ispkg))

print(f"Found {len(modules)} modules under profcalc")
failed = []
for name, ispkg in modules:
    try:
        importlib.import_module(name)
    except Exception:
        # Capture full traceback for diagnostics
        failed.append((name, traceback.format_exc()))

if not failed:
    print('All modules imported successfully')
    sys.exit(0)

print(f"{len(failed)} modules failed to import:")
for nm, tb in failed:
    print('\n--- FAILED:', nm)
    print(tb)

sys.exit(2)
