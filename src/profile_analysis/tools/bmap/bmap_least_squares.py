"""
Module: least_squares
Location: profile_analysis.modules.profiles
--------------------------------------------
Performs least-squares regression of a beach profile
to the Dean equilibrium equation within a user-defined range:

    h(x) = A * x^(2/3)

to estimate the A-parameter, correlation coefficient (R²),
and median grain size (d50, mm).

Equation reference:
    Dean, R.G. (1977). "Equilibrium Beach Profiles: U.S. Atlantic
    and Gulf Coasts." Department of Civil Engineering, Ocean
    Engineering Report No. 12, University of Delaware.

Example:
    fitted_df, report = compute_least_squares(
        profile_df, xon=0.0, xoff=600.0
    )
"""

import numpy as np
import pandas as pd


def compute_least_squares(
    profile: pd.DataFrame,
    xon: float,
    xoff: float
) -> tuple[pd.DataFrame, str]:
    """
    Perform least-squares fit to h = A * x^(2/3) between Xon and Xoff.

    Parameters
    ----------
    profile : pd.DataFrame
        Profile with columns ['X', 'Z'].
        Z positive upward (ft NAVD).
    xon : float
        Landward limit of fitting range (ft).
    xoff : float
        Seaward limit of fitting range (ft).

    Returns
    -------
    fitted_df : pd.DataFrame
        DataFrame with columns ['X', 'Z_observed', 'Z_fitted'].
    report : str
        Text summary in BMAP report format.
    """
    # --- Validate input ---
    if not {"X", "Z"}.issubset(profile.columns):
        raise ValueError("Profile must contain columns ['X', 'Z'].")

    if xoff <= xon:
        raise ValueError("xoff must be greater than xon.")

    # --- Subset profile within range ---
    prof = profile[(profile["X"] >= xon) & (profile["X"] <= xoff)].copy()
    if len(prof) < 3:
        raise ValueError("Not enough points within Xon/Xoff range for regression.")

    x = np.array(prof["X"], dtype=float)
    z = np.array(prof["Z"], dtype=float)

    # Convert elevation (positive up) to depth (positive down)
    h = np.maximum(0.0, -z)

    # Only use submerged points
    mask = h > 0
    x_fit = x[mask]
    h_fit = h[mask]

    if len(x_fit) < 3:
        raise ValueError("Insufficient valid submerged points within range for regression.")

    # --- Linearize Dean equation: h^(3/2) = (A^(3/2)) * x ---
    Y = h_fit ** 1.5
    X = x_fit

    n = len(X)
    sum_x = np.sum(X)
    sum_y = np.sum(Y)
    sum_xx = np.sum(X * X)
    sum_xy = np.sum(X * Y)

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
    intercept = (sum_y - slope * sum_x) / n  # not used, included for completeness

    # --- A-parameter and correlation ---
    A = slope ** (2.0 / 3.0)

    y_pred = slope * X + intercept
    ss_res = np.sum((Y - y_pred) ** 2)
    ss_tot = np.sum((Y - np.mean(Y)) ** 2)
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # --- Median grain size (mm) ---
    d50_mm = (A / 0.21) ** (1 / 0.48)

    # --- Compute fitted Z values for full X range ---
    x_all = np.array(profile["X"], dtype=float)
    h_est = A * (x_all ** (2.0 / 3.0))
    z_est = -h_est

    fitted_df = pd.DataFrame({
        "X": x_all,
        "Z_observed": profile["Z"].values,
        "Z_fitted": z_est
    })

    fitted_df.attrs["method"] = "Least Squares (Dean Fit)"
    fitted_df.attrs["parameters"] = {
        "A_ft13": float(A),
        "R2": float(R2),
        "d50_mm": float(d50_mm),
        "fit_range_ft": [xon, xoff]
    }

    # --- Report string (BMAP format) ---
    report = (
        "Least-Square Report\n"
        f"Fitting Range: {xon:.2f} to {xoff:.2f} ft\n"
        f"A-Parameter:\t{A:.3f} ft^1/3\n"
        f"Correlation Coefficient (R²):\t{R2:.2f}\n"
        f"Median Grain Size (d50):\t{d50_mm:.2f} mm\n"
    )

    return fitted_df, report
