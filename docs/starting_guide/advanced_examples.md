# Advanced example

## Mode understanding

Modes can be set by providing `mode=..` keyword or explicitly by specifying `read_only` and `overwrite` options.

'w' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False)
```

'a' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False, overwrite=False)
```

'r' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=True)
```

DH5.open_overwrite method is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False, overwrite=True)
or
>>> sd = DH5('somedata.h5', mode='w', overwrite=True)
```

## Mirroring acquisitions with lifecycle hooks

Use [`LifecycleHooks`](../code/lifecycle_hooks.md) on `AcquisitionAnalysisManager`: create the manager, then **`MirrorDirectoryPlugin(mirror_root).attach(aqm.hooks)`**. No `backend=` argument.

**`MirrorDirectoryPlugin` below is example code** — it is not shipped with the `labmate` package. Copy it into your project or notebook (see also [`use_local_mirror_backend.ipynb`](../examples/more/use_local_mirror_backend.ipynb)).

The plugin copies the HDF5 and any same-stem sidecar files into `mirror_root / <experiment_dir_name> /` after saves, and before each analysis load it may copy a missing `.h5` back from that mirror.

```python
from __future__ import annotations

import logging
import shutil
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Union

from labmate.acquisition import NotebookAcquisitionData, LifecycleHooks

logger = logging.getLogger(__name__)


class MirrorDirectoryPlugin:
    """Mirrors acquisition files to a second directory and can restore ``.h5`` before analysis."""

    def __init__(self, mirror_root: Union[str, Path]) -> None:
        self._mirror_root = Path(mirror_root)

    def attach(self, hooks: LifecycleHooks) -> None:
        hooks.add_acquisition_saved(self._mirror_after_persist)
        hooks.add_figure_saved(self._mirror_after_persist)
        hooks.add_analysis_data_loading(self._on_analysis_data_loading)

    def _mirror_after_persist(self, acquisition: NotebookAcquisitionData, **kwargs: Any) -> None:
        """Schedule mirror copy on a worker thread so the notebook thread is not blocked."""

        executor = ThreadPoolExecutor(max_workers=1)

        def copy_job() -> None:
            self._mirror_copy_to_destination(acquisition)

        def shutdown_executor(_future: Future) -> None:
            executor.shutdown(wait=False)

        future = executor.submit(copy_job)
        future.add_done_callback(shutdown_executor)

    def _mirror_copy_to_destination(self, acquisition: NotebookAcquisitionData) -> None:
        source_prefix = Path(acquisition.filepath)
        source_dir = source_prefix.parent
        prefix_name = source_prefix.name

        destination_dir = self._mirror_root / source_dir.name
        destination_dir.mkdir(parents=True, exist_ok=True)

        for src in source_dir.glob(f"{prefix_name}*"):
            if src.is_file():
                shutil.copy2(src, destination_dir / src.name)

    def _on_analysis_data_loading(self, full_h5_path: str, **kwargs: Any) -> None:
        """Restore missing local ``.h5`` from mirror; must stay synchronous before open."""

        target = Path(full_h5_path)
        if target.is_file():
            return

        mirror_path = self._mirror_root / target.parent.name / target.name

        if not mirror_path.is_file():
            return

        logger.info("Restoring %s from mirror at %s", target, self._mirror_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mirror_path, target)
```

```python
from labmate.acquisition_notebook import AcquisitionAnalysisManager

aqm = AcquisitionAnalysisManager("/data/labmate")
MirrorDirectoryPlugin("/mnt/labmate-mirror").attach(aqm.hooks)
```

For custom behavior, register callbacks on `aqm.hooks` with `add_acquisition_saved`, `add_figure_saved`, `add_analysis_data_loading`, etc.
