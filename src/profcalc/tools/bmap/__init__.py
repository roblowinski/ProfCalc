"""
BMAP Tools
----------
Replicates the original USACE Beach Morphology Analysis Package tools
for beach profile generation, translation, comparison, and volume analysis.

Each script implements one tool equivalent to the legacy BMAP interface.
"""

from importlib import import_module

__all__ = [
    "bmap_align",
    "bmap_average",
    "bmap_bar_properties",
    "bmap_combine",
    "bmap_compare",
    "bmap_cut_fill",
    "bmap_equilibrium",
    "bmap_interpolate",
    "bmap_least_squares",
    "bmap_mod_equilibrium",
    "bmap_sed_transport",
    "bmap_slope",
    "bmap_translate",
    "bmap_vol_above_contour",
    "bmap_vol_xon_xoff",
]

# Optional registry for programmatic access
TOOLS = {
    name.replace("bmap_", ""): import_module(f"profcalc.tools.bmap.{name}")
    for name in __all__
}

