from typing import List, Optional

from .analysis_data import AnalysisData


class AnalysisLoop():
    """TODO"""

    def __init__(self, data=None, loop_shape: Optional[List[int]] = None):
        self.data = data
        self.loop_shape = loop_shape

    @classmethod
    def load_from_h5(cls, h5group):
        loop = cls()
        loop.loop_shape = h5group['__loop_shape__'][()]
        loop.data = AnalysisData()
        loop.data.update(**{key: h5group[key][()] for key in h5group if key != '__loop_shape__'})
        return loop

    def __iter__(self):
        if self.data is None:
            raise ValueError("Data should be set before iterating over it")
        if self.loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")

        for index in range(self.loop_shape[0]):
            child_kwds = {}
            for key, value in self.data.items():
                if len(value) == 1:
                    child_kwds[key] = value[0]
                else:
                    child_kwds[key] = value[index]

            if len(self.loop_shape) > 1:
                yield AnalysisLoop(child_kwds, loop_shape=self.loop_shape[1:])
            else:
                child = AnalysisData()
                child.update(**child_kwds)
                yield child
