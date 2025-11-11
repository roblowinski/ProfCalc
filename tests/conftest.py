# =============================================================================
# Pytest Configuration and Test Fixtures
# =============================================================================
#
# FILE: tests/conftest.py
#
# PURPOSE:
# This file configures the pytest testing framework for the ProfCalc project,
# setting up the Python path, test discovery rules, and shared test fixtures.
# It ensures that tests can import ProfCalc modules correctly and provides
# common test infrastructure.
#
# WHAT IT'S FOR:
# - Configures Python path to include the src directory for imports
# - Sets up pytest collection rules and ignore patterns
# - Provides shared test fixtures and configuration
# - Ensures consistent test environment across all test files
# - Handles special cases like backup test files that shouldn't be run
#
# WORKFLOW POSITION:
# This file is automatically loaded by pytest when running tests from the
# tests/ directory. It runs before any individual test files and establishes
# the testing environment. It's part of the test infrastructure that supports
# the development and validation workflow.
#
# LIMITATIONS:
# - Only affects pytest runs, not other testing frameworks
# - Path manipulation assumes standard project structure
# - Collection ignores are hardcoded and may need updates
#
# ASSUMPTIONS:
# - Tests are run from the project root or tests directory
# - Project structure follows the expected src/tests layout
# - pytest is the testing framework being used
# - Backup files with .bak extension should be ignored
#
# =============================================================================

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Ignore stray backup test files that are not valid Python module names
collect_ignore = ["test_quick_tools_logging.bak.py"]
# Also support glob-based ignore for PyTest versions that use globs
collect_ignore_glob = ["test_quick_tools_logging.bak.py"]
