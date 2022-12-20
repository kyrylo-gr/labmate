from typing import List, Optional, Iterable

from .analysis_data import AnalysisData


class AnalysisLoop(AnalysisData):
    """TODO"""

    def __init__(self, data: Optional[dict] = None, loop_shape: Optional[List[int]] = None):
        super().__init__()
        data = data or {}
        if loop_shape is None:
            loop_shape = data.get("__loop_shape__", None)
        self._loop_shape = loop_shape
        self.update(**data)

    def __iter__(self):
        if self._data is None:
            raise ValueError("Data should be set before iterating over it")
        if self._loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")

        for index in range(self._loop_shape[0]):
            child_kwds = {}
            for key, value in self._data.items():
                if key[:1] == '_':
                    continue
                # if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
                if not hasattr(value, "__getitem__") or isinstance(value, (int, float)):
                    child_kwds[key] = value
                elif len(value) == 1:
                    child_kwds[key] = value[0]
                else:
                    child_kwds[key] = value[index]

                val = child_kwds[key]
                if isinstance(val, (Iterable)) and \
                        len(val) == 1 and not isinstance(val[0], (Iterable)):  # type: ignore
                    child_kwds[key] = val[0]  # type: ignore

            if len(self._loop_shape) > 1:
                yield AnalysisLoop(child_kwds, loop_shape=self._loop_shape[1:])
            else:
                child = AnalysisData()
                child.update(**child_kwds)
                yield child

    def __repr__(self):
        self._get_repr()
        return f"AnalysisLoop: \n {self._repr}"
