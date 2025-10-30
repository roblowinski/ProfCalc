"""
profcalc
----------------
A modular analysis framework for beach profile processing,
developed to replicate and extend the functionality of the
USACE Beach Morphology Analysis Package (BMAP).

Primary namespaces:
- common: shared utilities and configuration
- tools: analysis tools (BMAP, monitoring, construction, etc.)
"""

__version__ = "0.9.0"
__author__ = "U.S. Army Corps of Engineers, Philadelphia District"
__all__ = ["common", "tools", "docs", "main"]

# Import main CLI entry point
from .cli import main

