# =============================================================================
# Configuration Management Utilities
# =============================================================================
#
# FILE: src/profcalc/common/config_utils.py
#
# PURPOSE:
# This module provides configuration management functionality for ProfCalc,
# handling the loading and parsing of configuration files that control
# analysis parameters and system behavior. It provides a clean interface
# for accessing configuration values with appropriate defaults and error
# handling.
#
# WHAT IT'S FOR:
# - Loads configuration values from JSON configuration files
# - Provides default values when configuration is missing or invalid
# - Handles analysis parameters like spacing (dx) values
# - Manages runtime configuration for different analysis scenarios
# - Provides centralized configuration access across the application
# - Includes proper error handling and logging for configuration issues
#
# WORKFLOW POSITION:
# This module is used throughout ProfCalc wherever configuration values
# are needed. It's particularly important for analysis parameters that
# affect calculation results, ensuring consistent behavior across different
# runs and environments.
#
# LIMITATIONS:
# - Configuration files must be valid JSON format
# - Configuration loading is synchronous and blocking
# - No configuration validation beyond basic type checking
# - Configuration changes require application restart
#
# ASSUMPTIONS:
# - Configuration files are located in expected directories
# - JSON format is appropriate for configuration needs
# - Default values are reasonable for most use cases
# - Configuration values are relatively stable during execution
#
# =============================================================================

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
    config_path: Path = (
        Path(__file__).resolve().parents[3] / "config" / "runtime" / "config.json"
    )
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
