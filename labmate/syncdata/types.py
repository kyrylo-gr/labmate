from typing import Callable, Optional, Protocol, Union
import numpy as np


class ClassWithAsdict(Protocol):
    """Any class with predefined `_asdict` attribute.
    `_asdict` class should return a dictionary with only list and dict.
    It should not be a dict of other classes"""

    def asdict(self) -> dict:
        ...


class ClassWithAsarray(Protocol):
    """Any class with predefined `asarray` attribute.
    `asarray` class should return a np.ndarray."""

    def asarray(self) -> Union[np.ndarray, list]:
        ...


DICT_OR_LIST_LIKE = Optional[
    Union[
        dict,
        list,
        np.ndarray,
        ClassWithAsdict,
        ClassWithAsarray,
        np.int_,
        np.float_,
        float,
        int,
        str,
        Callable,
    ]
]
RIGHT_DATA_TYPE = Union[dict, np.ndarray, np.int_, np.float_, float, int]
