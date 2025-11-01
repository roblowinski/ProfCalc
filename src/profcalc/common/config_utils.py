import json
from pathlib import Path

from .error_handler import LogComponent, get_logger


def get_dx(default: float = 10.0) -> float:
    """Get the global dX value (analysis spacing) from configuration.

    Reads the analysis spacing parameter (dx) from the config.json file located
    in the same directory as this module. This value represents the horizontal
    spacing used in profile analysis calculations.

    Args:
        default: Fallback value to use if config file is missing, cannot be
            parsed, or doesn't contain the 'dx' key. Defaults to 10.0 feet.

    Returns:
        The configured dx value in feet, or the default value if configuration
        cannot be loaded.

    Raises:
        This function handles all exceptions internally and logs warnings,
        never raising exceptions to calling code.
    """
    config_path: Path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, "r") as f:
            cfg: dict = json.load(f)
        return float(cfg.get("dx", default))
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
    ) as e:
        logger = get_logger(LogComponent.FILE_IO)
        logger.warning(
            f"Failed to load config from {config_path}, using default dx={default}: {e}"
        )
        return default
