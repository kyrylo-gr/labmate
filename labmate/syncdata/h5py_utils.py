import json
import os
import h5py
from typing import Callable, Dict, Literal, Optional, Protocol, Set, Union
from ..utils.errors import FileLockedError

import numpy as np


class ClassWithAsdict(Protocol):
    """Any class with predefined `_asdict` attribute.
    `_asdict` class should return a dictionary with only list and dict.
    It should not be a dict of other classes"""

    def asdict(self) -> dict:
        ...


# class ClassWithSave(Protocol):
#     """Class that can be save without passing by dict"""
#     __should_not_be_converted__ = True

#     def save(self):
#         """Function that saves the object without converting to a dict"""


class ClassWithAsarray(Protocol):
    """Any class with predefined `asarray` attribute.
    `asarray` class should return a np.ndarray."""

    def asarray(self) -> Union[np.ndarray, list]:
        ...


class LockFile:
    def __init__(self, filename):
        self.lock_filename = os.path.splitext(filename)[0] + ".lock"

    def __enter__(self):
        if os.path.exists(self.lock_filename):
            raise FileLockedError("File locked and cannot be opened in write mode")
        with open(self.lock_filename, 'w', encoding='utf-8'):
            pass
        # print("lock file", time.time())

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.lock_filename):
            os.remove(self.lock_filename)
        #     print("lock del", time.time())
        # else:
        #     print("exit without lock file", time.time())


DICT_OR_LIST_LIKE = Optional[Union[dict, list, np.ndarray, ClassWithAsdict, ClassWithAsarray,
                                   np.int_, np.float_, float, int, str, Callable]]
RIGHT_DATA_TYPE = Union[dict, np.ndarray, np.int_, np.float_, float, int]


def np_array_check(lst, size: Optional[int] = None) -> int:
    if isinstance(lst, (list, np.ndarray)):
        if size is not None and size != len(lst):
            return -1
        for lst_elm in lst:
            check = np_array_check(lst_elm, size)
            if check >= 0:
                size = check
            else:
                return -1
        return len(lst)
    if isinstance(lst, (np.number)):
        return 0
    return -1


def transform_to_possible_formats(data: DICT_OR_LIST_LIKE) -> DICT_OR_LIST_LIKE:
    if hasattr(data, '__should_not_be_converted__') \
            and data.__should_not_be_converted__ is True:  # type: ignore
        return data

    if hasattr(data, 'asdict'):
        data = data.asdict()  # type: ignore

    if hasattr(data, 'asarray'):
        data = data.asarray()  # type: ignore

    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = transform_to_possible_formats(value)
        return data

    if isinstance(data, (tuple, set)):
        data = list(data)

    if isinstance(data, list):
        if np_array_check(data) < 0:
            return data
    return data


def transform_on_open(value):
    if isinstance(value, bytes):
        value = value.decode()
    if isinstance(value, str) and value.startswith('__json__'):
        return json.loads(value[8:])
    if isinstance(value, str) and value.startswith('__function__'):
        from . import function_save
        return function_save.Function(value[12:])
    return value


def transform_list_on_save(value, level=0):
    if isinstance(value, np.ndarray):
        if level == 0:
            return value
        return value.tolist()

    if isinstance(value, (list)):
        if np_array_check(value) < 0:
            try:
                return '__json__' + json.dumps(value)
            except TypeError:
                value_transformed = [transform_list_on_save(v) for v in value]
                return '__json__' + json.dumps(value_transformed)

    if isinstance(value, Callable):
        from . import function_save
        return '__function__' + function_save.function_to_str(value)

    return value


def save_sub_dict(
    group: Union[h5py.File, h5py.Group],
    data: Union[dict, list, np.ndarray, ClassWithAsdict],
    key: str,
    use_compression: Optional[Union[Literal[True], str]] = None
):
    if hasattr(data, 'asdict'):
        data = data.asdict()  # type: ignore
    if hasattr(data, 'asarray'):
        data = data.asarray()  # type: ignore
    if isinstance(data, dict):
        g = group.create_group(key)
        for k, v in data.items():
            save_sub_dict(g, v, k, use_compression=use_compression)
    elif (key is not None) and (data is not None):
        data = transform_list_on_save(data)  # type: ignore
        if isinstance(data, (np.ndarray, list)):
            use_compression = "gzip" if use_compression is True else use_compression
            group.create_dataset(key, data=data, compression=use_compression)  # compression="gzip"
        else:
            group.create_dataset(key, data=data)


def save_dict(
    filename: str,
    data: dict,
    key_prefix: Optional[str] = None,
    use_compression: Optional[Union[Literal[True], str]] = None
):
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    mode = 'a'  # if os.path.exists(filename) else 'w'
    with LockFile(filename):
        with h5py.File(filename, mode) as file:
            for key, value in data.items():
                key = key if key_prefix is None else f"{key_prefix}/{key}"
                if key in file.keys():
                    file.pop(key)
                if value is None:
                    continue
                save_sub_dict(file, value, key, use_compression=use_compression)
    return os.path.getmtime(filename)


def del_dict(
    filename: str,
    key: str,
    key_prefix: Optional[str] = None,
):
    with LockFile(filename):
        with h5py.File(filename, 'a') as file:
            key = key if key_prefix is None else f"{key_prefix}/{key}"
            file.pop(key)
    return os.path.getmtime(filename)


def keys_h5(
    filename,
    key_prefix: Optional[str] = None
) -> Set[str]:
    with h5py.File(filename, 'r') as file:
        if key_prefix is not None:
            file = file[key_prefix]
        return set(file.keys())  # type: ignore


def open_h5(
    fullpath: str,
    key: Optional[Union[str, Set[str]]] = None,
    key_prefix: Optional[str] = None
) -> dict:
    with h5py.File(fullpath, 'r') as file:
        if key_prefix is None:
            return open_h5_group(file, key=key)
        return open_h5_group(file[key_prefix], key=key)  # type: ignore


def open_h5_group(
    group: Union[h5py.File, h5py.Group],
    key: Optional[Union[str, Set[str]]] = None,
    key_prefix: Optional[str] = None
) -> dict:
    data = {}
    if key is not None:
        key = key if isinstance(key, set) else set([key])

    for group_key in group.keys():
        key = key if key_prefix is None else f"{key_prefix}/{key}"
        if key is not None and group_key not in key:
            continue
        value = group[group_key]
        if isinstance(value, h5py.Group):
            data[group_key] = open_h5_group(value)
        else:
            data[group_key] = transform_on_open(value[()])  # type: ignore
    return data


def output_dict_structure(
        data: dict,
        additional_info: Optional[Dict[str, str]] = None
) -> str:
    dict_str = dict_to_json_format_str(get_dict_structure(data))
    if additional_info:
        for key, value in additional_info.items():
            dict_str = dict_str.replace(f'"{key}":', f'"{key}"{value}:')
    return dict_str


def dict_to_json_format_str(data: dict) -> str:
    """Output a dictionary structure."""
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
        elif isinstance(v, (float, np.float_, complex, np.complex_)):  # type: ignore
            str_value = f"{v:.3f}" if .1 <= abs(v) <= 100. else f"{v:.3e}"
            structure[k] = f"{str_value} (type : {type(v).__name__})"
        else:
            structure[k] = f"variable of type {type(v).__name__}"
    return structure


def get_keys_structure(data) -> dict:
    structure = {}
    for k, v in data.items():
        if isinstance(v, dict):
            structure[k] = get_keys_structure(v)
        else:
            structure[k] = None

    return structure
