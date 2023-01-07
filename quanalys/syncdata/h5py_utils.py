import json
import os
import h5py
from typing import Dict, Optional, Protocol, Union

import numpy as np


class ClassWithAsdict(Protocol):
    """Any class with predefined `_asdict` attribute.
    `_asdict` class should return a dictionary with only list and dict.
    It should not be a dict of other classes"""

    def _asdict(self) -> dict:
        ...


class ClassWithAsarray(Protocol):
    """Any class with predefined `asarray` attribute.
    `asarray` class should return a np.ndarray."""

    def asarray(self) -> np.ndarray:
        ...


DICT_OR_LIST_LIKE = Optional[Union[dict, list, np.ndarray, ClassWithAsdict, ClassWithAsarray,
                                   np.int_, np.float_, float, int, str]]
RIGHT_DATA_TYPE = Union[dict, np.ndarray, np.int_, np.float_, float, int]


def transform_to_possible_formats(data: DICT_OR_LIST_LIKE) -> DICT_OR_LIST_LIKE:
    if hasattr(data, '__should_not_be_converted__'):
        if data.__should_not_be_converted__ is True:  # type: ignore
            return data
    if hasattr(data, '_asdict'):
        data = data._asdict()  # type: ignore

    if hasattr(data, 'asarray'):
        data = data.asarray()  # type: ignore

    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = transform_to_possible_formats(value)
        return data
    if isinstance(data, (tuple, set)):
        data = list(data)
    if isinstance(data, list):
        return np.array(data)
    return data


def transform_on_open(value):
    if isinstance(value, bytes):
        return value.decode()
    return value


def save_sub_dict(
    group: Union[h5py.File, h5py.Group],
    data: Union[dict, list, np.ndarray, ClassWithAsdict],
    key: str
):
    if hasattr(data, '_asdict'):
        data = data._asdict()  # type: ignore
    if hasattr(data, 'asarray'):
        data = data.asarray()  # type: ignore
    if isinstance(data, dict):
        g = group.create_group(key)
        for k, v in data.items():
            save_sub_dict(g, v, k)
    elif (key is not None) and (data is not None):
        group.create_dataset(key, data=data)


def save_dict(
    filename: str,
    data: dict,
):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    mode = 'a' if os.path.exists(filename) else 'w'
    with h5py.File(filename, mode) as file:
        for key, value in data.items():
            if key in file.keys():
                file.pop(key)
            if value is None:
                continue
            save_sub_dict(file, value, key)
    return filename


def del_dict(
    filename: str,
    key: str
):

    with h5py.File(filename, 'a') as file:
        file.pop(key)


def open_h5(fullpath: str) -> dict:
    with h5py.File(fullpath, 'r') as file:
        return open_h5_group(file)


def open_h5_group(group: Union[h5py.File, h5py.Group]) -> dict:
    data = {}
    for key, value in group.items():
        if isinstance(value, h5py.Group):
            data[key] = open_h5_group(value)
        else:
            data[key] = transform_on_open(value[()])  # type: ignore
    return data


def output_dict_structure(data: dict, additional_info: Optional[Dict[str, str]] = None) -> str:
    dict_str = dict_to_json_format_str(get_dict_structure(data))
    if additional_info:
        for key, value in additional_info.items():
            dict_str = dict_str.replace(f'"{key}":', f'"{key}"{value}:')
    return dict_str


def dict_to_json_format_str(data: dict) -> str:
    """" Outputs a dictionary structure """
    return json.dumps(data, sort_keys=True, indent=4)


def get_dict_structure(data: dict, level: int = 3) -> dict:
    structure = {}

    for k, v in data.items():
        if isinstance(v, dict):
            if level:
                internal_structure = get_dict_structure(v, level=level-1) if len(v) else "empty dict"
                structure[k] = "variable of type dict" if len(internal_structure) > 5 else internal_structure
            else:
                structure[k] = "variable of type dict"

        elif isinstance(v, (np.ndarray, list)):
            structure[k] = f"shape: {np.shape(v)} (type: {type(v).__name__})"
        elif isinstance(v, (int, np.int_)):  # type: ignore
            structure[k] = f"{v:.0f} (type : {type(v).__name__})"
        elif isinstance(v, (float, np.float_)):  # type: ignore
            str_value = f"{v:.3f}" if .1 <= v <= 100 else f"{v:.3e}"
            structure[k] = f"{str_value} (type : {type(v).__name__})"
        else:
            structure[k] = f"variable of type {type(v).__name__}"

    return structure
