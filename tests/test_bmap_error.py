import pytest

from profcalc.common.error_handler import BeachProfileError
from profcalc.ref_code.modules.volume_bounded import BMAPParser


def test_bmapparser_parse_file_raises_beachprofileerror_on_invalid(tmp_path):
    # Create an invalid BMAP file (non-numeric count line)
    p = tmp_path.joinpath("invalid.bmap")
    p.write_text("Header line\nNOT_A_NUMBER\n1 2 3\n")

    parser = BMAPParser()

    with pytest.raises(BeachProfileError):
        parser.parse_file(str(p))
