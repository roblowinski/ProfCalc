import re

# Copied from modify_bmap_header.py for testability


def validate_date(val):
    # Accept DDMMMYYYY (e.g., 07NOV2025) or blank
    if not val.strip():
        return True
    return bool(re.match(r"^\d{2}[A-Z]{3}\d{4}$", val.strip()))


def validate_purpose(val):
    # Only allow letters, digits, spaces, and underscores
    return bool(re.match(r"^[A-Za-z0-9_ ]*$", val))


def format_header(date, purpose):
    return f"{date} {purpose}".strip()


def test_validate_date():
    assert validate_date("08NOV2025")
    assert validate_date("01JAN2000")
    assert validate_date("")  # blank allowed
    assert not validate_date("2025-11-08")
    assert not validate_date("8NOV2025")
    assert not validate_date("08NOV25")
    assert not validate_date("08Nov2025")  # must be uppercase
    assert not validate_date("08NOV2025!")
    assert not validate_date("321JAN2025")  # too many digits


def test_validate_purpose():
    assert validate_purpose("Purpose_1")
    assert validate_purpose("Test123")
    assert validate_purpose("With Spaces")
    assert validate_purpose("")
    assert not validate_purpose("Bad!Char")
    assert not validate_purpose("New\nLine")
    assert not validate_purpose("Tab\tChar")
    assert not validate_purpose("Dash-Char")
    assert not validate_purpose("Comma,Char")


def test_format_header():
    assert format_header("08NOV2025", "Purpose_1") == "08NOV2025 Purpose_1"
    assert format_header("", "Purpose_1") == "Purpose_1"
    assert format_header("08NOV2025", "") == "08NOV2025"
    assert format_header("", "") == ""
