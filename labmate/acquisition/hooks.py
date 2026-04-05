from __future__ import annotations

import inspect
import warnings
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Union


if TYPE_CHECKING:
    from .acquisition_data import NotebookAcquisitionData

SaveAcquisitionCallback = Callable[["NotebookAcquisitionData"], None]
AnalysisCellBeforeLoadCallback = Callable[[str], None]
_CallableWithNoArgs = Callable[[], Any]

_HOOK_KWARGS_WARNING = (
    "Lifecycle hook callbacks may receive extra keyword arguments from dispatch in a future "
    "version. Add **kwargs to the hook signature to receive that context; without it, those "
    "keywords will be omitted when the hook is called."
)


def _normalize_no_arg_hooks(
    hook: Union[
        _CallableWithNoArgs,
        List[_CallableWithNoArgs],
        Tuple[_CallableWithNoArgs, ...],
    ],
) -> List[_CallableWithNoArgs]:
    if isinstance(hook, (list, tuple)):
        return list(hook)
    return [hook]


def _callable_accepts_var_keyword(fn: Callable[..., Any]) -> bool:
    try:
        sig = inspect.signature(fn, follow_wrapped=True)
    except (TypeError, ValueError):
        return False
    return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())


class LifecycleHooks:
    """Lifecycle callbacks for acquisitions and analysis. Plugins register via ``add_*``."""

    def __init__(self) -> None:
        self._acquisition_saved: List[SaveAcquisitionCallback] = []
        self._figure_saved: List[SaveAcquisitionCallback] = []
        self._acquisition_data_loaded: List[SaveAcquisitionCallback] = []
        self._analysis_data_loading: List[AnalysisCellBeforeLoadCallback] = []
        self._analysis_cell_ready: List[_CallableWithNoArgs] = []
        self._acquisition_cell_ready: List[_CallableWithNoArgs] = []
        self._var_keyword_cache: Dict[int, bool] = {}

    def _accepts_var_keyword_cached(self, fn: Callable[..., Any]) -> bool:
        key = id(fn)
        if key not in self._var_keyword_cache:
            self._var_keyword_cache[key] = _callable_accepts_var_keyword(fn)
        return self._var_keyword_cache[key]

    def _warn_if_hook_ignores_dispatch_kwargs(self, fn: Callable[..., Any]) -> None:
        if self._accepts_var_keyword_cached(fn):
            return
        warnings.warn(_HOOK_KWARGS_WARNING, FutureWarning, stacklevel=3)

    def _invoke_hook(
        self,
        cb: Callable[..., Any],
        positional: Tuple[Any, ...],
        hook_kwargs: Dict[str, Any],
    ) -> None:
        if hook_kwargs and self._accepts_var_keyword_cached(cb):
            cb(*positional, **hook_kwargs)
        else:
            cb(*positional)

    # --- acquisition_saved ---

    def add_acquisition_saved(self, callback: SaveAcquisitionCallback) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(callback)
        self._acquisition_saved.append(callback)

    def dispatch_acquisition_saved(
        self, acquisition: NotebookAcquisitionData, **kwargs: Any
    ) -> None:
        """Run callbacks after acquisition data is persisted (synchronously)."""

        for cb in self._acquisition_saved:
            self._invoke_hook(cb, (acquisition,), kwargs)

    # --- figure_saved ---

    def add_figure_saved(self, callback: SaveAcquisitionCallback) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(callback)
        self._figure_saved.append(callback)

    def dispatch_figure_saved(self, acquisition: NotebookAcquisitionData, **kwargs: Any) -> None:
        """Run callbacks after a figure is persisted (synchronously)."""

        for cb in self._figure_saved:
            self._invoke_hook(cb, (acquisition,), kwargs)

    # --- acquisition_data_loaded ---

    def add_acquisition_data_loaded(self, callback: SaveAcquisitionCallback) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(callback)
        self._acquisition_data_loaded.append(callback)

    def dispatch_acquisition_data_loaded(
        self, acquisition: NotebookAcquisitionData, **kwargs: Any
    ) -> None:
        """Run callbacks after acquisition data is loaded (synchronously)."""

        for cb in self._acquisition_data_loaded:
            self._invoke_hook(cb, (acquisition,), kwargs)

    # --- analysis_data_loading ---

    def add_analysis_data_loading(self, callback: AnalysisCellBeforeLoadCallback) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(callback)
        self._analysis_data_loading.append(callback)

    def dispatch_analysis_data_loading(self, full_h5_path: str, **kwargs: Any) -> None:
        """Run callbacks before analysis data is loaded."""

        for cb in self._analysis_data_loading:
            self._invoke_hook(cb, (full_h5_path,), kwargs)

    # --- analysis_cell_ready ---

    def add_analysis_cell_ready(self, hook: _CallableWithNoArgs) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(hook)
        self._analysis_cell_ready.append(hook)

    def dispatch_analysis_cell_ready(self, **kwargs: Any) -> None:
        """Run after analysis data is loaded and before analysis runs."""

        for cb in self._analysis_cell_ready:
            self._invoke_hook(cb, (), kwargs)

    def set_analysis_cell_ready(
        self,
        hook: Union[
            _CallableWithNoArgs,
            List[_CallableWithNoArgs],
            Tuple[_CallableWithNoArgs, ...],
        ],
    ) -> None:
        """Replace registered analysis-cell-ready hooks (same semantics as a single ``set_*``)."""

        normalized = _normalize_no_arg_hooks(hook)
        for h in normalized:
            self._warn_if_hook_ignores_dispatch_kwargs(h)
        self._analysis_cell_ready = normalized

    # --- acquisition_cell_ready ---

    def add_acquisition_cell_ready(self, hook: _CallableWithNoArgs) -> None:
        self._warn_if_hook_ignores_dispatch_kwargs(hook)
        self._acquisition_cell_ready.append(hook)

    def dispatch_acquisition_cell_ready(self, **kwargs: Any) -> None:
        """Run after acquisition data is created and before user code runs."""

        for cb in self._acquisition_cell_ready:
            self._invoke_hook(cb, (), kwargs)

    def set_acquisition_cell_ready(
        self,
        hook: Union[
            _CallableWithNoArgs,
            List[_CallableWithNoArgs],
            Tuple[_CallableWithNoArgs, ...],
        ],
    ) -> None:
        """Replace registered acquisition-cell-ready hooks."""

        normalized = _normalize_no_arg_hooks(hook)
        for h in normalized:
            self._warn_if_hook_ignores_dispatch_kwargs(h)
        self._acquisition_cell_ready = normalized


__all__ = ["LifecycleHooks"]
