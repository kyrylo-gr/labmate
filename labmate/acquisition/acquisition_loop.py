from typing import Any, Dict, Iterable, Iterator, List, Optional, Union, overload

import numpy as np

from ..syncdata import h5py_utils
from ..syncdata_types.h5_np_array import SyncNp
from ..syncdata.syncdata_class import SyncData


class AcquisitionLoop(SyncData):
    _level = 0

    def __init__(self) -> None:
        super().__init__()
        self._level = 0
        self._shape = []
        self._iteration = []

    @overload
    def __call__(self, **kwds) -> None:
        """Save the kwds. Same as calling the function append_data(kwds)."""

    @overload
    def __call__(self, iterable: Iterable) -> Iterator:
        """Return an iterator given an iterable."""

    @overload
    def __call__(self, stop: Union[int, float], /) -> Iterator:
        """Return np.arange(stop) given a stop value."""

    @overload
    def __call__(self, start: Union[int, float], stop: Union[int, float], step: Union[int, float], /
                 ) -> Iterator:
        """Return np.arange(start, stop, step) given a start, stop and step."""

    def __call__(self, *args, iterable: Optional[Iterable] = None, **kwds) -> Optional[Iterator]:
        """Append_data or arange.

        If kwds are provided then is same as calling append_data(kwds),
        otherwise returns iterator over iterable or np.arange(*args).
        """
        if iterable is None and len(args) == 0:
            self.append(**kwds)
            return None

        if iterable is None:
            if isinstance(args[0], (int, float, np.int_, np.float_)):  # type: ignore
                iterable = np.arange(*args)
            else:
                iterable = args[0]

        if iterable is None:
            raise ValueError("You should provide an iterable")

        return self.iter(iterable)

    def append(self, level=None, **kwds):
        if len(kwds) == 0:
            raise ValueError("You should provide keywords and values to save.")

        level = level if level is not None else self._level
        shape = tuple(self._shape[:self._level])

        iteration = tuple(self._iteration[:self._level])
        for key, value in kwds.items():
            if isinstance(value, (np.ndarray, )):
                key_shape = (*shape, *value.shape)
            else:
                key_shape = shape

            if key in self:
                # if self.data[key].shape == shape:
                # print(self.data[key].shape, shape)
                if self[key].shape == key_shape:
                    self[key][iteration] = value
                    # pass
                else:
                    # print("app",list(i-j for i, j in zip(shape, self.data[key].shape)))
                    if len(key_shape) < len(self[key].shape):
                        raise ValueError(
                            f"Object {key} hasn't the same shape as before. Now it's "
                            f"{key_shape[len(shape):]}, but before it was {self[key].shape[len(shape):]}.")

                    elif len(key_shape) > len(self[key].shape):
                        raise ValueError(
                            f"Object {key} cannot be save as the shape is not compatible. "
                            f"Before the shape was {self[key].shape}, but now it is {key_shape}.")

                    # print(self[key].shape)
                    # print(f"{key_shape=}")
                    # print(tuple((0, i-j) for i, j in zip(
                    #             key_shape,
                    #             self[key].shape)))
                    self[key] = SyncNp(
                        np.pad(
                            self[key],
                            pad_width=tuple((0, i-j) for i, j in zip(
                                key_shape,
                                self[key].shape)))
                    )
                    self[key][iteration] = value
                    # data = self.data[key]
                    # self.data[key] = np.zeros(shape)
                    # self.data[key][:, :data.shape[-1]] = data
            else:
                if isinstance(value, (complex, np.complex_)):  # type: ignore
                    self[key] = SyncNp(np.zeros(key_shape, dtype=np.complex128))
                else:
                    self[key] = SyncNp(np.zeros(key_shape))

                self[key][iteration] = value

    def iter(self, iterable: Iterable, level=None):
        if not hasattr(iterable, "__len__"):
            iterable = list(iterable)

        length = len(iterable)  # type: ignore

        def loop_iter(array, level):
            array = list(array)
            level = level if level is not None else self._level
            length = len(array)
            # self.iteration[-1]=0
            if len(self._iteration) <= level:
                self._iteration.append(0)

            # print(self.shape, level)
            if len(self._shape) <= level:
                self._shape.append(length)
                self['__loop_shape__'] = self._shape
            elif self._iteration[level] != 0 and \
                    (len(self._iteration) == 1 or self._iteration[level-1] == 0):
                self._shape[level] = self._shape[level]+length
                self['__loop_shape__'] = self._shape

            self._level += 1
            for a in array:
                yield a
                if len(self._iteration)-1 > level:
                    self._iteration[-1] = 0
                self._iteration[self._level-1] += 1
            if len(self._iteration)-1 > level:
                self._iteration.pop()
            self._level -= 1

        return GenerToIter(
            loop_iter(iterable, level=level), length)

    def enum(self, *args, iterable: Optional[Iterable] = None):
        return enumerate(self(*args, iterable=iterable))  # type: ignore


class AcquisitionLoopOld:
    """Acquisition loop allow to save data during for loops.

    - Example 1 that saves list of squares till 10:
    ```
    sd.test_loop = loop = AcquisitionLoop()
    for i in loop(10):
        loop.append_data(x=i**2)
    ```

    - Example 2 with not direct manipulation:
    ```
    loop = AcquisitionLoop()
    for i in loop(10):
        loop.append_data(x=i**2)
    sd.update(test_loop = loop)
    ```
    """

    __filename__: Optional[str] = None
    __filekey__: Optional[str] = None
    __should_not_be_converted__ = True
    __save_on_edit__: bool = False

    def __init__(self):
        self.loop_shape: List[int] = []  # length of each loop level
        self.current_loop = 0  # stores the current loop level we are in
        self.data_level = {}  # for each keyword, indicates at which loop_level it is scanned
        self._data_flatten = {}

    # @overload
    # def __call__(self, *arg) -> Iterator:
    #     ...

    @overload
    def __call__(self, **kwds) -> None:
        """Save the kwds. Same as calling the function append_data(kwds)."""

    @overload
    def __call__(self, iterable: Iterable) -> Iterator:
        """Given an iterable returns an iterator."""

    @overload
    def __call__(self, stop: Union[int, float], /) -> Iterator:
        """Given a stop value returns np.arange(stop)."""

    @overload
    def __call__(self, start: Union[int, float], stop: Union[int, float], step: Union[int, float], /
                 ) -> Iterator:
        """Given a start, stop and step returns np.arange(start, stop, step)."""

    def __call__(self, *args, iterable: Optional[Iterable] = None, **kwds) -> Optional[Iterator]:
        """Append_data or arange.

        If kwds are provided then is same as calling append_data(kwds),
        otherwise returns iterator over iterable or np.arange(*args)
        """
        if iterable is None and len(args) == 0:
            self.append_data(**kwds)
            return None

        if iterable is None:
            if isinstance(args[0], (int, float, np.int_, np.float_)):  # type: ignore
                iterable = np.arange(*args)
            else:
                iterable = args[0]

        if iterable is None:
            raise ValueError("You should provide an iterable")

        return self.iter(iterable)

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

        if self.__save_on_edit__:
            self.save(just_update=True)

    def iter(self, iterable: Iterable) -> Iterator:
        if not hasattr(iterable, "__len__"):
            iterable = list(iterable)

        length = len(iterable)  # type: ignore

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

            data_reshape[key] = np.pad(data_flatten, (0, expected_len-len(data_flatten))).reshape(  # type: ignore
                self._reshape_tuple(key))
        return data_reshape

    def asdict(self):
        data = self.data
        data['__loop_shape__'] = self.loop_shape
        return data

    def __init__filepath__(self, *, filepath: str, filekey: str, save_on_edit: bool = False, **_):
        self.__filename__ = filepath
        self.__filekey__ = filekey
        self.__save_on_edit__ = save_on_edit

    def save(self, just_update=False):
        del just_update

        if not self.__filename__ or not self.__filekey__:
            raise ValueError("Cannot save changes without filename and filekey provided")

        h5py_utils.save_dict(
            filename=self.__filename__,
            data={self.__filekey__: self.asdict()})


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
