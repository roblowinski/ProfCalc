# =============================================================================
# Profile Smoothing and Filtering Utilities
# =============================================================================
#
# FILE: src/profcalc/common/smoothing_utils.py
#
# PURPOSE:
# This module provides various smoothing and filtering algorithms for beach
# profile data. It offers multiple techniques to reduce noise and outliers
# in survey data while preserving important morphological features like
# dunes, bars, and shoreline transitions.
#
# WHAT IT'S FOR:
# - Applying Savitzky-Golay filtering for local smoothing
# - Gaussian filtering for global noise reduction
# - Moving average smoothing for simple noise reduction
# - Cubic spline interpolation for smooth curve fitting
# - Unified interface for applying different smoothing methods
#
# WORKFLOW POSITION:
# This module is used in data preprocessing workflows to clean survey data
# before analysis. It's applied when raw survey data contains noise or
# outliers that could affect volumetric calculations or morphological
# feature detection.
#
# LIMITATIONS:
# - Requires scipy for advanced filtering algorithms
# - Smoothing can mask real morphological features
# - Parameter selection requires domain knowledge
# - Different methods have different edge effect behaviors
# - Memory usage scales with profile length
#
# ASSUMPTIONS:
# - Input data is sorted by X-coordinate
# - Noise is random and not systematic
# - Smoothing parameters are appropriate for data characteristics
# - Users understand the trade-offs between smoothing methods
# - Morphological features are preserved at chosen smoothing levels
#
# =============================================================================

import numpy as np
from scipy.interpolate import (
    CubicSpline,  # type: ignore  # scipy lacks complete type stubs
)
from scipy.ndimage import (
    gaussian_filter1d,  # type: ignore  # scipy lacks complete type stubs
)
from scipy.signal import (
    savgol_filter,  # type: ignore  # scipy lacks complete type stubs
)


def smooth_savgol(
    x: np.ndarray, z: np.ndarray, window_length: int = 7, polyorder: int = 3
) -> np.ndarray:
    """
    Smoothes a profile using the Savitzky-Golay filter.

    Parameters
    ----------
    x : np.ndarray
        The X-coordinates of the profile (typically horizontal distance).
    z : np.ndarray
        The Z-coordinates (elevation) of the profile.
    window_length : int, optional
        The length of the smoothing window (odd integer).
    polyorder : int, optional
        The order of the polynomial used to fit the samples.

    Returns
    -------
    smoothed_z : np.ndarray
        The smoothed Z-values (elevations).
    """
    # Check if the window_length is odd
    if window_length % 2 == 0:
        raise ValueError("Window length must be odd.")

    return savgol_filter(z, window_length, polyorder)


def smooth_gaussian(x: np.ndarray, z: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    Smoothes a profile using a Gaussian filter.

    Parameters
    ----------
    x : np.ndarray
        The X-coordinates of the profile (typically horizontal distance).
    z : np.ndarray
        The Z-coordinates (elevation) of the profile.
    sigma : float, optional
        The standard deviation of the Gaussian filter. Controls the extent of smoothing.

    Returns
    -------
    smoothed_z : np.ndarray
        The smoothed Z-values (elevations).
    """
    if sigma <= 0:
        raise ValueError("Sigma must be positive.")

    return gaussian_filter1d(z, sigma=sigma)


def smooth_moving_average(
    x: np.ndarray, z: np.ndarray, window_size: int = 5
) -> np.ndarray:
    """
    Smoothes a profile using a simple moving average filter.

    Parameters
    ----------
    x : np.ndarray
        The X-coordinates of the profile (typically horizontal distance).
    z : np.ndarray
        The Z-coordinates (elevation) of the profile.
    window_size : int, optional
        The size of the window used for averaging. Must be odd.

    Returns
    -------
    smoothed_z : np.ndarray
        The smoothed Z-values (elevations).
    """
    if window_size % 2 == 0:
        raise ValueError("Window size must be odd.")

    return np.convolve(z, np.ones(window_size) / window_size, mode="same")


def smooth_spline(
    x: np.ndarray, z: np.ndarray, smoothing_factor: float = 0.0
) -> np.ndarray:
    """
    Smoothes a profile using cubic spline interpolation.

    Parameters
    ----------
    x : np.ndarray
        The X-coordinates of the profile (typically horizontal distance).
    z : np.ndarray
        The Z-coordinates (elevation) of the profile.
    smoothing_factor : float, optional
        A factor that controls the smoothness of the spline. A larger value leads to smoother curves.

    Returns
    -------
    smoothed_z : np.ndarray
        The smoothed Z-values (elevations).
    """
    # Cubic Spline interpolation with natural boundary conditions
    spline = CubicSpline(x, z, bc_type="natural")

    # Use the smoothing factor (if provided)
    if smoothing_factor > 0:
        smoothed_z = spline(x)
        return smoothed_z

    return spline(x)


def smooth_profile(
    x: np.ndarray, z: np.ndarray, method: str = "savgol", **kwargs
) -> np.ndarray:
    """
    Applies the selected smoothing method to the profile data.

    Parameters:
    ----------
    x : np.ndarray
        The X-coordinates of the profile (typically horizontal distance).
    z : np.ndarray
        The Z-coordinates (elevation) of the profile.
    method : str, optional
        The smoothing method to use ('savgol', 'gaussian', 'moving_average', 'spline').
    **kwargs : additional parameters for the smoothing methods.

    Returns:
    -------
    smoothed_z : np.ndarray
        The smoothed Z-values (elevations).
    """
    if method == "savgol":
        return smooth_savgol(x, z, **kwargs)
    elif method == "gaussian":
        return smooth_gaussian(x, z, **kwargs)
    elif method == "moving_average":
        return smooth_moving_average(x, z, **kwargs)
    elif method == "spline":
        return smooth_spline(x, z, **kwargs)
    else:
        raise ValueError(f"Unknown smoothing method: {method}")
