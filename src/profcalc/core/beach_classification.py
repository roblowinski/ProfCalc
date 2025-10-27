"""
Beach morphodynamic classification module.

Classifies beach types based on beach face slope using the Wright & Short (1984)
morphodynamic framework.
"""


def classify_beach_type(beach_face_slope: float) -> str:
    """
    Classify beach morphodynamic type based on beach face slope.

    Args:
        beach_face_slope: Beach face slope (rise/run), typically negative

    Returns:
        Beach type classification: "REFLECTIVE", "INTERMEDIATE", or "DISSIPATIVE"
    """
    # =======================================================================
    # METHODOLOGY:
    # -----------
    # Beach morphodynamics describe how beaches respond to wave energy through
    # sediment transport and profile adjustment. This classification uses beach
    # face slope as a primary indicator of beach state, following the framework
    # established by Wright & Short (1984).
    #
    # MATHEMATICAL BASIS:
    # ------------------
    # Beach face slope is used as a proxy for wave energy dissipation:
    # - Steep slopes (>10%) indicate reflective beaches with high wave energy
    # - Gentle slopes (<2%) indicate dissipative beaches with low wave energy
    # - Intermediate slopes (2-10%) represent transitional beach states
    #
    # SLOPE THRESHOLDS:
    # ----------------
    # - REFLECTIVE: |slope| ≥ 0.10 (≥10% slope)
    #   High wave energy, steep beach face, minimal surf zone width
    # - INTERMEDIATE: 0.02 ≤ |slope| < 0.10 (2-10% slope)
    #   Moderate wave energy, balanced sediment transport
    # - DISSIPATIVE: |slope| < 0.02 (<2% slope)
    #   Low wave energy, wide surf zone, berm development
    #
    # MORPHODYNAMIC MODEL:
    # -------------------
    # The classification is based on the continuum of beach states where:
    # - Reflective beaches: Wave energy reflected, minimal dissipation
    # - Intermediate beaches: Partial wave energy dissipation
    # - Dissipative beaches: Maximum wave energy dissipation through surf zone
    #
    # REFERENCES:
    # ----------
    # - Wright, L. D., & Short, A. D. (1984). Morphodynamic variability of
    #   surf zones and beaches: A synthesis. Marine Geology, 56(1-4), 93-118.
    # - Short, A. D. (1999). Handbook of Beach and Shoreface Morphodynamics.
    #   John Wiley & Sons.
    # - Masselink, G., & Hughes, M. G. (2003). Introduction to Coastal Processes
    #   and Geomorphology. Hodder Arnold.
    # - USACE (2015). Coastal Engineering Manual. Part III-2, Beach Profiles.
    #
    # LIMITATIONS:
    # -----------
    # - Slope-based classification is a simplification of complex morphodynamics
    # - Does not account for grain size, tide range, or wave period
    # - Beach face slope may vary seasonally or with storm events
    # - Local factors (structures, currents) can modify beach response
    # =======================================================================

    slope_magnitude = abs(beach_face_slope)

    if slope_magnitude >= 0.10:  # ≥10% slope
        return "REFLECTIVE"
    elif slope_magnitude >= 0.02:  # 2-10% slope
        return "INTERMEDIATE"
    else:  # <2% slope
        return "DISSIPATIVE"

