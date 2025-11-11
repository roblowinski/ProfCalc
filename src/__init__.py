# =============================================================================
# ProfCalc Source Package Initialization
# =============================================================================
#
# FILE: src/__init__.py
#
# PURPOSE:
# This is the main package initialization file for the ProfCalc coastal profile
# analysis framework. It serves as the entry point for the entire ProfCalc
# package and defines the package-level structure and exports.
#
# WHAT IT'S FOR:
# - Defines the ProfCalc package namespace and structure
# - Provides package-level imports and exports
# - Serves as the root module for all ProfCalc functionality
# - Enables the package to be imported as 'profcalc' from external code
#
# WORKFLOW POSITION:
# This file is the foundation of the entire ProfCalc package. It sits at the
# root of the source code hierarchy and is imported whenever any part of
# ProfCalc is used. All other modules in the package depend on this file
# being properly structured and imported.
#
# LIMITATIONS:
# - This is a pure initialization file with no executable code
# - Does not contain any business logic or data processing
# - Relies on proper Python package structure for functionality
#
# ASSUMPTIONS:
# - Python package structure is correctly set up with proper __init__.py files
# - All submodules are importable and properly structured
# - The package is installed or available in the Python path
# - No circular import dependencies exist in the package structure
#
# =============================================================================

"""ProfCalc Source Package

This package contains the ProfCalc beach profile analysis framework.
"""
