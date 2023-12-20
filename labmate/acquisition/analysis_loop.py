"""Contains only AnalysisLoop which is subclass of DH5.
It has mainly __iter__ method and __getitem__ method for slicing.
"""

from typing import Any, List, Optional, Iterable, Tuple, Union

from dh5 import DH5


class AnalysisLoop(DH5):
    """A class for reading a dictionary that was created by AcquisitionLoop.

    Args:
        data (Optional[dict]): The dictionary to read. Defaults to None.
        loop_shape (Optional[List[int]]): The shape of the loop. Defaults to None.

    Examples:
        Example 1: How to use it:
        ```
        for data_level1 in loop:
            print(data_level1.x)
            for data_level2 in data_level1:
                print(data_level2.x)
                print(data_level2.y)
        ```

        Example 2: With slicing:
        ```
        for d in loop[:5]:
            print(d.x)
        ```

        Example 3: Slicing returns not a generator but an object of the same class, so
        it's possible to analyze the data directly:
        ```
        data = loop[2:10:2]
        print(data.x)
        ```

    """

    def __init__(self, data: Optional[dict] = None, loop_shape: Optional[List[int]] = None):
        """Initialize an AnalysisLoop object.

        Args:
            data (Optional[dict]): A dictionary containing data to initialize the object with.
            loop_shape (Optional[List[int]]): A list of integers representing the shape of the analysis loop.
                If not provided, the shape is retrieved from the object's '__loop_shape__' attribute.
        """
        super().__init__(data=data)
        if loop_shape is None:
            loop_shape = self.get("__loop_shape__")
        self._loop_shape = loop_shape

    def __iter__(self):
        """Iterate over the data.

        Yields:
            The next item in the iteration.

        Raises:
            ValueError: If data or loop_shape is not set before iterating over it.

        """
        if self._data is None:
            raise ValueError("Data should be set before iterating over it")
        if self._loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")

        for index in range(self._loop_shape[0]):
            child_kwds = {}
            for key, value in self._data.items():
                if key[:1] == "_":
                    continue

                # if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
                if not hasattr(value, "__getitem__") or isinstance(
                    value, (str, bytes, int, float, complex)
                ):
                    child_kwds[key] = value
                elif len(value) == 1:
                    child_kwds[key] = value[0]
                else:
                    child_kwds[key] = value[index]

                val = child_kwds[key]
                if isinstance(val, (Iterable)) and len(val) == 1 and not isinstance(val[0], (Iterable)):  # type: ignore
                    child_kwds[key] = val[0]  # type: ignore

            if len(self._loop_shape) > 1:
                yield AnalysisLoop(child_kwds, loop_shape=self._loop_shape[1:].copy())
            else:
                child = DH5(child_kwds)
                yield child

    def __getitem__(self, __key: Union[str, tuple, slice]) -> Any:
        """Get an item from the data.

        Args:
            __key (Union[str, tuple, slice]): The key to get.

        Returns:
            The item at the specified key.

        """
        if isinstance(__key, slice):
            sliced_data, new_shape = self.get_slice(__key)
            return AnalysisLoop(sliced_data, loop_shape=new_shape)

        return super().__getitem__(__key)

    def get_slice(self, __slice: Optional[slice] = None) -> Tuple[dict, list]:
        """Get a slice of the data.

        Args:
            __slice (Optional[slice], optional): The slice to get. Defaults to None.

        Returns:
            Tuple[dict, list]: The sliced data and the new shape.

        """
        length = self.__len__()

        if __slice is None:
            __slice = slice(0, length, 1)
        __slice = slice(*__slice.indices(length))

        child_data = {}
        for key, value in self._data.items():
            if key[:1] == "_":
                continue
            if not hasattr(value, "__getitem__"):
                child_data[key] = value
            elif len(value) == 1:
                child_data[key] = value[0]
            else:
                child_data[key] = value[__slice]

        new_shape = [(__slice.stop - __slice.start) // __slice.step]
        new_shape.extend(self._loop_shape[1:])
        return child_data, new_shape

    def __len__(self) -> int:
        """Get the length of the data.

        Returns:
            int: The length of the data.

        Raises:
            ValueError: If loop_shape is not set before iterating over it.

        """
        if self._loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")
        return self._loop_shape[0]
