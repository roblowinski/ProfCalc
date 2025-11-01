"""
Test suite for the Beach Profile Analysis Toolkit (profcalc).
Ensures that all computational and reporting tools perform as expected.

You can run all tests using:
    pytest tests/
or directly from VS Code's Python Test Explorer.
"""

# Optional: allow relative imports during local test runs
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
)
