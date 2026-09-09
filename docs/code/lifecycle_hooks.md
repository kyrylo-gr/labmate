# Lifecycle hooks

`LifecycleHooks` groups callbacks for acquisition and analysis. Every `AcquisitionManager` / `AcquisitionAnalysisManager` has **`aqm.hooks`** (one shared instance per manager). Plugins register with **`add_*`**; the managers call **`dispatch_*`** at fixed points—you implement the behavior.

**Dispatch is always synchronous:** `LifecycleHooks` does not use `ThreadPoolExecutor` or background threads. Each `dispatch_*` runs registered callbacks on the **same thread** as the caller (typically the notebook main thread). If a plugin needs non-blocking I/O (e.g. copying large files), it should start work itself—[`MirrorDirectoryPlugin`](#mirror-example) does that for mirror-on-save only.

## When things run

| Register with | Dispatched when | Callback shape |
|---------------|-----------------|----------------|
| `add_acquisition_saved` | After `save_acquisition` persists acquisition data | `(acquisition) -> None` |
| `add_figure_saved` | After `save_fig` updates figures / analysis cell on disk | same |
| `add_acquisition_data_loaded` | After `get_acquisition` / `create_acquisition` build the in-memory acquisition | same |
| `add_analysis_data_loading` | **Every** `analysis_cell` run, **before** opening the `.h5` — pass the full path | `(full_h5_path: str) -> None` (no-op if the file is already there) |
| `add_analysis_cell_ready` / `set_analysis_cell_ready` | After analysis data is loaded and lint (if any), before your analysis code | `() -> None` |
| `add_acquisition_cell_ready` / `set_acquisition_cell_ready` | `acquisition_cell` step 1, after the acquisition exists, before your cell body | `() -> None` |

`set_analysis_cell_ready` and `set_acquisition_cell_ready` **replace** the list for that slot (same idea as the old global “prerun” setters on `AcquisitionAnalysisManager`).

## Mirror example

Copy the **`MirrorDirectoryPlugin`** class from [Mirroring acquisitions with lifecycle hooks](../starting_guide/advanced_examples.md#mirroring-acquisitions-with-lifecycle-hooks) or [`use_local_mirror_backend.ipynb`](../examples/more/use_local_mirror_backend.ipynb) (it is not shipped inside the `labmate` package). Then:

```python
from labmate.acquisition_notebook import AcquisitionAnalysisManager

aqm = AcquisitionAnalysisManager("/data/labmate")
MirrorDirectoryPlugin("/mnt/labmate-mirror").attach(aqm.hooks)
```

`MirrorDirectoryPlugin` is **not** part of `LifecycleHooks`: it registers callbacks that run under the synchronous `dispatch_*` rules above. Inside those callbacks it may use a **`ThreadPoolExecutor`** to copy files to the mirror after save so the notebook thread returns quickly. Restoring a missing `.h5` before analysis stays **synchronous** inside `dispatch_analysis_data_loading` so the file exists before open.

See also: [advanced examples](../starting_guide/advanced_examples.md#mirroring-acquisitions-with-lifecycle-hooks).
