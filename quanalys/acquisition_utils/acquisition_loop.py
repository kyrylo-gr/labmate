from typing import Any, Dict, List

import numpy as np


class AcquisitionLoop(object):
    """TODO"""

    def __init__(self):
        self.loop_shape: List[int] = []  # length of each loop level
        self.current_loop = 0  # stores the current loop level we are in
        self.data_level = {}  # for each keyword, indicates at which loop_level it is scanned
        self._data_flatten = {}

    def __call__(self, iterable):
        length = len(iterable)

        def loop_iter():
            self.current_loop += 1
            if self.current_loop > len(self.loop_shape):
                self.loop_shape.append(length)
            else:
                assert length == self.loop_shape[self.current_loop - 1]
            for i in iterable:
                yield i  # for body executes here
            self.current_loop -= 1

        return GenerToIter(loop_iter(), length)

    def atomic_data_shape(self, key):
        return np.shape(self._data_flatten[key][0])

    def _reshape_tuple(self, key):
        tuple_shape = [1] * len(self.loop_shape)
        tuple_shape += self.atomic_data_shape(key)
        if self.data_level[key] > 0:
            for loop_index in range(self.data_level[key]):
                tuple_shape[loop_index] = self.loop_shape[loop_index]
        return tuple_shape

    @property
    def data(self) -> Dict[str, Any]:
        data_reshape = {}
        for key, data_flatten in self._data_flatten.items():
            data_flatten = np.array(data_flatten).flatten()
            expected_len = np.prod(self._reshape_tuple(key))
            if expected_len < len(data_flatten):
                # print(key, expected_len, len(data_flatten))
                data_flatten = data_flatten[-expected_len:]

            data_reshape[key] = np.pad(data_flatten, (0, expected_len-len(data_flatten))).reshape(
                self._reshape_tuple(key))
        return data_reshape

    def append_data(self, level=0, **kwds):
        current_loop = self.current_loop + level

        for key, value in kwds.items():
            if key not in self.data_level:  # if key was never scanned, notice that it is scanned at the current level
                self.data_level[key] = current_loop
            else:  # otherwise make sure that key was previously scanned at the current loop level
                assert self.data_level[key] == current_loop

            if key not in self._data_flatten:
                self._data_flatten[key] = [value]
            else:
                # print()
                self._data_flatten[key].append(value)

    def _asdict(self):
        data = self.data
        data['__loop_shape__'] = self.loop_shape
        return data


class GenerToIter:
    def __init__(self, gen, length=None):
        self.gen = gen
        self.length = length

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.gen)

    def __len__(self):
        return self.length
