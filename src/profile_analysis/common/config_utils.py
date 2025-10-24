import json
from pathlib import Path


def get_dx(default: float = 10.0) -> float:
    """
    Reads the global dX value (analysis spacing in feet) from config.json.
    Falls back to default if not found.
    """
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        return float(cfg.get("dx", default))
    except Exception:
        return default
