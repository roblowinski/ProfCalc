"""Session/Context management for dataset tracking."""

import uuid
from pathlib import Path
from typing import Dict, Optional


class Session:
    """Lightweight in-memory session for tracking datasets.

    The Session object is intentionally minimal: it provides deterministic
    methods to register datasets, select an active dataset, and list
    registered datasets. It is *not* a replacement for a database-backed
    store; rather it is a convenience for CLI workflows and testing.

    Attributes:
        datasets: Mapping of dataset_id -> metadata dictionary.
        active_dataset: Currently selected dataset id or ``None``.
    """

    def __init__(self) -> None:
        """Initialize the session with an empty dataset registry.

        Example:
            session = Session()
            id = session.load_dataset('/tmp/survey.csv')
        """
        self.datasets: Dict[str, Dict] = {}
        self.active_dataset: Optional[str] = None

    def load_dataset(self, path: str) -> str:
        """Register a dataset path with the session and return its id.

        Args:
            path: Filesystem path to the dataset file to register.

        Returns:
            str: A newly generated UUID string identifying the dataset.
        """
        dataset_id = str(uuid.uuid4())
        self.datasets[dataset_id] = {
            "path": Path(path).resolve(),
            "info": f"Dataset loaded from {path}",
        }
        return dataset_id

    def set_active(self, dataset_id: str) -> None:
        """Set the active dataset by its id.

        Raises:
            ValueError: If the provided ``dataset_id`` is not registered.
        """
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset ID {dataset_id} not found in session.")
        self.active_dataset = dataset_id

    def get_active(self) -> Optional[Dict]:
        """Return metadata for the currently active dataset, or ``None``.

        Returns:
            Optional[Dict]: The metadata dictionary stored when the dataset
            was loaded, or ``None`` when no dataset is active.
        """
        if self.active_dataset:
            return self.datasets[self.active_dataset]
        return None

    def list_datasets(self) -> Dict[str, Dict]:
        """Return the internal mapping of registered datasets.

        The function returns the raw internal data structure and is
        suitable for small-scale CLI workflows and tests. Consumers should
        not mutate the returned mapping.
        """
        return self.datasets
