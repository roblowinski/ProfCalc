# =============================================================================
# Auto Write Test Script
# =============================================================================
#
# FILE: scripts/test_support/test_auto_write.py
#
# PURPOSE:
# This test support script tests the auto-write functionality of the bounds tool.
# It simulates user input and mocked data to verify that bounds processing and
# output generation work correctly in automated scenarios.
#
# WHAT IT'S FOR:
# - Testing bounds tool auto-write functionality
# - Verifying automated bounds processing
# - Simulating user input for testing
# - Validating bounds output generation
# - Supporting automated testing of bounds operations
#
# WORKFLOW POSITION:
# This script is used during testing to validate the bounds tool's automated
# processing capabilities. It helps ensure that bounds calculations work
# correctly when run programmatically without user interaction.
#
# LIMITATIONS:
# - Uses mocked data instead of real files
# - Simulates specific test scenario only
# - Limited to bounds tool testing
# - Basic validation without comprehensive checks
#
# ASSUMPTIONS:
# - Bounds tool is properly implemented
# - Mocked data represents valid input format
# - System has necessary dependencies
# - Output generation works as expected
#
# =============================================================================

import sys

sys.path.insert(0, 'src')
from types import SimpleNamespace
from unittest import mock

from profcalc.cli.tools import bounds

p1 = SimpleNamespace(name='P1', date='2020-10-26', x=[1.0, 5.0], z=[0.0, 0.0], y=[10.0, 15.0])
p1b = SimpleNamespace(name='P1', date='2021-03-15', x=[0.5, 4.5], z=[0.0, 0.0], y=None)
p2 = SimpleNamespace(name='P2', date=None, x=[2.0, 6.0], z=[0.0, 0.0], y=[8.0, 12.0])

with mock.patch('profcalc.cli.tools.bounds.read_bmap_freeformat', return_value=[p1, p1b, p2]):
    # add an extra empty input to skip baseline prompting (no origin azimuth file)
    inputs = iter(['dummy_pattern', '', 'both', ''])
    with mock.patch('builtins.input', lambda prompt='': next(inputs)):
        bounds.execute_from_menu()

print('done')
