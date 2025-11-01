"""Tests for the Session class."""

import pytest

from profcalc.cli.context import Session


def test_load_dataset():
    session = Session()
    dataset_id = session.load_dataset("/path/to/dataset.csv")

    assert dataset_id in session.list_datasets()
    assert session.list_datasets()[dataset_id]["path"].name == "dataset.csv"


def test_set_active():
    session = Session()
    dataset_id = session.load_dataset("/path/to/dataset.csv")
    session.set_active(dataset_id)

    active_dataset = session.get_active()
    assert active_dataset is not None
    assert active_dataset["path"].name == "dataset.csv"


def test_set_active_invalid():
    session = Session()

    with pytest.raises(ValueError):
        session.set_active("invalid_id")


def test_list_datasets():
    session = Session()
    session.load_dataset("/path/to/dataset1.csv")
    session.load_dataset("/path/to/dataset2.csv")

    datasets = session.list_datasets()
    assert len(datasets) == 2


def test_get_active_no_active():
    session = Session()

    assert session.get_active() is None
