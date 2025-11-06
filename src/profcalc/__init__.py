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
__all__ = ["common"]

# NOTE: avoid importing CLI entry points at package import time. Importing
# `profcalc` should be cheap and not pull in CLI subpackages with
# interactive/demo side-effects. Callers can import `profcalc.cli` or
# use console entry points instead.
