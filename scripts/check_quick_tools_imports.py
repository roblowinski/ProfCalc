"""Quick import check for quick-tools modules."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The package `profcalc` is located under the `src/` directory in the repo.
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

modules = [
    "profcalc.cli.tools.bounds",
    "profcalc.cli.tools.inventory",
    "profcalc.cli.tools.convert",
    "profcalc.cli.tools.assign",
]

for m in modules:
    try:
        importlib.import_module(m)
        print(f"{m} OK")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"{m} ERR: {e}")

print("Done.")
