from typing import List, Optional

from .analysis_data import AnalysisData


class AnalysisLoop(AnalysisData):
    """TODO"""

    def __init__(self, data: Optional[dict] = None, loop_shape: Optional[List[int]] = None):
        super().__init__()
        data = data or {}
        if loop_shape is None:
            loop_shape = data.get("__loop_shape__", None)
        self.loop_shape = loop_shape
        self.update(**data)

    def __iter__(self):
        if self._data is None:
            raise ValueError("Data should be set before iterating over it")
        if self.loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")

        for index in range(self.loop_shape[0]):
            child_kwds = {}
            for key, value in self._data.items():
                if key[:1] == '_':
                    continue
                # if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
                if not hasattr(value, "__getitem__"):
                    child_kwds[key] = value
                elif len(value) == 1:
                    child_kwds[key] = value[0]
                else:
                    child_kwds[key] = value[index]

            if len(self.loop_shape) > 1:
                yield AnalysisLoop(child_kwds, loop_shape=self.loop_shape[1:])
            else:
                child = AnalysisData()
                child.update(**child_kwds)
                yield child
