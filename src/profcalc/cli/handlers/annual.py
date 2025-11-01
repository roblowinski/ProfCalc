"""Handlers for annual monitoring workflows.

This module contains small CLI-facing handlers used by the interactive
menu. Each function is intentionally lightweight and delegates to the
data management handlers or the session object where appropriate.
"""

from typing import Optional

from profcalc.cli.context import Session
from profcalc.cli.handlers.data import import_data

# Initialize a session object
session = Session()


def import_survey() -> Optional[dict]:
    """Import survey data using the active session dataset or prompt user.

    The function first checks whether a dataset is already active in the
    current :pyclass:`Session`. If present, that dataset's metadata is
    returned. Otherwise, the user is prompted for a file path and the
    request is forwarded to :pyfunc:`profcalc.cli.handlers.data.import_data`.

    Returns:
        Optional[dict]: The active dataset info or the import result
            dictionary from :pyfunc:`import_data`. Returns ``None`` on
            import failure.
    """
    active_dataset = session.get_active()

    if active_dataset:
        print(f"Using active dataset: {active_dataset.get('info')}")
        return active_dataset

    print("No active dataset found. Prompting user to import data...")
    file_path = input("Enter the path to the survey data file: ")

    try:
        result = import_data(file_path)
        print(f"Data imported successfully: {result['imported']} rows.")
        return result
    except Exception as e:
        print(f"Error importing data: {e}")
        return None
