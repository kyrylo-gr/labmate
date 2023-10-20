from typing import Iterable, Iterator, Optional, Union, overload

import numpy as np
from dh5.dh5_types import SyncNp
from dh5 import DH5


class AcquisitionLoop(DH5):
    """Comfort way to save a data inside a loop.

    Examples:
    ----------
    Update the file each time your save something:

    ```
    sd.test_loop = loop = AcquisitionLoop()
    for i in loop(10):
        loop.append_data(x=i**2)
        # loop.save() # necessary if save_on_edit=False
    ```

    Update the file only in the end:

    ```
    loop = AcquisitionLoop()
    for i in loop(10):
        loop.append_data(x=i**2)
    sd.update(test_loop = loop)
    # sd.save() # necessary if save_on_edit=False
    ```
    """

    _level = 0
    _save_indexes = True

    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, mode="a", **kwds)

        self._shape = []

        self._level = 0
        self._iteration = []

        self.__post__init__()

    def __post__init__(self):
        if "__loop_shape__" in self:
            self._shape = list(self.get("__loop_shape__"))

        # if self._save_on_edit:
        last_update_keys, self._last_update = self._last_update, set()

        for key in self.keys():
            self[key] = SyncNp(self[key])

        self._last_update = last_update_keys

    @overload
    def __call__(self, **kwds) -> None:
        """Save the kwds. Same as calling the function append_data(kwds)."""

    @overload
    def __call__(self, iterable: Iterable, **kwds) -> Iterator:
        """Return an iterator given an iterable."""

    @overload
    def __call__(self, stop: Union[int, float], /) -> Iterator:
        """Return np.arange(stop) given a stop value."""

    @overload
    def __call__(
        self, start: Union[int, float], stop: Union[int, float], step: Union[int, float], /
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

        return self.iter(iterable, **kwds)

    def append(self, level: Optional[int] = None, **kwds):
        if len(kwds) == 0:
            raise ValueError("You should provide keywords and values to save.")

        level = level if level is not None else self._level
        shape = tuple(self._shape[: self._level])

        iteration = tuple(self._iteration[: self._level])
        for key, value in kwds.items():
            if isinstance(value, (np.ndarray,)):
                key_shape = (*shape, *value.shape)
            elif hasattr(value, "__len__"):
                key_shape = (*shape, len(value))
            else:
                key_shape = shape

            if key in self:
                if self[key].shape == key_shape:
                    self[key][iteration] = value
                else:
                    if len(key_shape) < len(self[key].shape):
                        raise ValueError(
                            f"Object {key} hasn't the same shape as before. Now it's"
                            f" {key_shape[len(shape):]},"
                            f" but before it was {self[key].shape[len(shape):]}."
                        )
                    elif len(key_shape) > len(self[key].shape):
                        raise ValueError(
                            f"Object {key} cannot be save as the shape is not compatible. "
                            f"Before the shape was {self[key].shape}, but now it is {key_shape}."
                        )

                    self[key] = SyncNp(
                        np.pad(
                            self[key],
                            pad_width=tuple((0, i - j) for i, j in zip(key_shape, self[key].shape)),
                        )
                    )
                    self[key][iteration] = value
            else:
                if isinstance(value, (complex, np.complex_)) or (  # type: ignore
                    isinstance(value, (np.ndarray,)) and value.dtype == np.complex_
                ):
                    self[key] = SyncNp(np.zeros(key_shape, dtype=np.complex128))
                else:
                    self[key] = SyncNp(np.zeros(key_shape))

                self[key][iteration] = value

            self._last_update.add(key)

    def iter(
        self,
        iterable: Iterable,
        length: Optional[int] = None,
    ):
        if length is None:
            if not hasattr(iterable, "__len__"):
                raise TypeError("Iterable should has __len__ method or length should be provided")
            length = len(iterable)  # type: ignore

        def loop_iter(array, length):
            level = self._level  # level if level is not None else self._level
            # self.iteration[-1]=0
            if len(self._iteration) <= level:
                self._iteration.append(0)

            if len(self._shape) <= level:
                self._shape.append(length)
                self["__loop_shape__"] = self._shape
            elif self._iteration[level] != 0 and (
                len(self._iteration) == 1 or self._iteration[level - 1] == 0
            ):
                self._shape[level] = self._shape[level] + length
                self["__loop_shape__"] = self._shape

            self._level += 1
            for index, a in enumerate(array):
                yield a
                if self._save_indexes:
                    self.append(**{f"__index_{self._level}__": index + 1})
                if len(self._iteration) - 1 > level:
                    self._iteration[-1] = 0
                self._iteration[self._level - 1] += 1
            if len(self._iteration) - 1 > level:
                self._iteration.pop()
            self._level -= 1

        return GenerToIter(loop_iter(iterable, length=length), length)

    def enum(self, *args, iterable: Optional[Iterable] = None, **kwds):
        return enumerate(self(*args, iterable=iterable, **kwds))  # type: ignore

    def already_saved(self, key: Optional[str] = None) -> bool:
        if key is None:
            if not self._save_indexes:
                raise ValueError("As indexes are not saved with the Loop, key should be provided.")
            key = f"__index_{self._level}__"

        iteration = tuple(self._iteration[: self._level])
        if f"__index_{self._level}__" not in self:
            return False
        return self[key][iteration] != 0

    def reset_level(self):
        self._level = 0
        self._iteration = []


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
