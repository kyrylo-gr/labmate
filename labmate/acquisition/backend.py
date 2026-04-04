from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .acquisition_data import NotebookAcquisitionData


class AcquisitionBackend:
    """Lightweight backend interface used by :class:`AcquisitionManager`."""

    def save_snapshot(self, acquisition: "NotebookAcquisitionData") -> None:
        """Persist a snapshot of the acquisition remotely."""

        pass

    def load_snapshot(self, acquisition: "NotebookAcquisitionData") -> None:
        """Hydrate the acquisition from a remote snapshot."""

        pass

    def ensure_local_file(self, filepath: str) -> bool:
        """
        Ensure that filepath exists locally.
        Called by labmate if a required file is missing.
        Return True if the file was fetched/created.
        Default: do nothing.
        """
        return False


__all__ = ["AcquisitionBackend"]
