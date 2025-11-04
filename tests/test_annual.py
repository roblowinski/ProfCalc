from unittest.mock import patch

from profcalc.cli.tools.annual import profcalc_profcalc


@patch("profcalc.cli.menu_system.profcalc_profcalc_menu")
def test_profcalc_profcalc(mock_submenu):
    """Test the profcalc_profcalc handler calls the profile analysis submenu."""
    profcalc_profcalc()
    mock_submenu.assert_called_once()
