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
