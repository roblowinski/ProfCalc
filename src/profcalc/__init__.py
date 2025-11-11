# =============================================================================
# ProfCalc Main Package Initialization
# =============================================================================
#
# FILE: src/profcalc/__init__.py
#
# PURPOSE:
# This is the main initialization file for the ProfCalc package, serving as the
# central hub for the beach profile analysis framework. It defines the package
# metadata, version information, and primary namespace structure while avoiding
# heavy imports that could slow down package loading.
#
# WHAT IT'S FOR:
# - Defines the ProfCalc package identity and metadata (version, author)
# - Establishes the primary namespace structure (common, tools, cli)
# - Provides controlled imports to avoid circular dependencies
# - Serves as the main entry point for the ProfCalc framework
# - Enables selective importing of submodules without loading everything
#
# WORKFLOW POSITION:
# This file sits at the heart of the ProfCalc package hierarchy. It is imported
# whenever the profcalc package is used and controls what gets exposed to
# external users. It sits between the basic package structure (src/__init__.py)
# and the actual functionality modules (common/, tools/, cli/).
#
# LIMITATIONS:
# - Deliberately avoids importing CLI components to keep package import lightweight
# - Does not expose all submodules by default (only 'common' in __all__)
# - Requires explicit imports for tools and CLI functionality
# - No executable code - purely structural and metadata
#
# ASSUMPTIONS:
# - The package structure follows standard Python conventions
# - Submodules are properly implemented and importable when needed
# - No circular import issues exist between major namespaces
# - Version numbering follows semantic versioning principles
# - Package is designed for both programmatic use and CLI interaction
#
# =============================================================================

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
