import os
import h5py
from typing import Literal, Optional, Set, Union
from ..utils.errors import FileLockedError

from .types import ClassWithAsdict
from .data_transformation import transform_not_dict_on_save, transform_on_open

import numpy as np


class LockFile:
    """Context manager that create lock file during writing to prevent conflicts."""

    def __init__(self, filename):
        self.lock_filename = os.path.splitext(filename)[0] + ".lock"

    def __enter__(self):
        if os.path.exists(self.lock_filename):
            raise FileLockedError("File locked and cannot be opened in write mode")
        with open(self.lock_filename, 'w', encoding='utf-8'):
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.lock_filename):
            os.remove(self.lock_filename)


# -------------- Open file ----------------


def open_h5_group(
    group: Union[h5py.File, h5py.Group],
    key: Optional[Union[str, Set[str]]] = None,
    key_prefix: Optional[str] = None,
) -> dict:
    """Open h5 group and return dict.

    Args:
        group (Union[h5py.File, h5py.Group]): group to open
        key (Optional[Union[str, Set[str]]], optional): Keys to load. Defaults to None.
        key_prefix (Optional[str], optional): Key prefix. Defaults to None.

    Returns:
        dict: The loaded data. Each value was transform using transform_on_open function.
    """
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


def open_h5(
    fullpath: str, key: Optional[Union[str, Set[str]]] = None, key_prefix: Optional[str] = None
) -> dict:
    """Open h5 file and return dict.

    Args:
        fullpath (str): Full filepath to the file.
        key (str | set[str], optional): Key or keys to load. Defaults to all keys.
        key_prefix (str, optional): Key prefix to put before each key. Defaults to None.

    Returns:
        dict: The loaded data. Each value was transform using transform_on_open function.
    """
    with h5py.File(fullpath, 'r') as file:
        if key_prefix is None:
            return open_h5_group(file, key=key)
        return open_h5_group(file[key_prefix], key=key)  # type: ignore


# -------------- Save file ----------------


def save_sub_dict(
    group: Union[h5py.File, h5py.Group],
    data: Union[dict, list, np.ndarray, ClassWithAsdict],
    key: str,
    use_compression: Optional[Union[Literal[True], str]] = None,
):
    """Save the dict to a group. Each object is converted to a dict, array or simple value.

    Args:
        group (Union[h5py.File, h5py.Group]): h5 group where to save.
        data (Union[dict, list, np.ndarray, ClassWithAsdict]): Any object that either has 'asdict'
         or 'asarray' method, either is a dict, list or np.ndarray, either can be transformed
         using transform_not_dict_on_save function.
        key (str): Desire key for the data inside h5 file .
        use_compression (str|True, optional): If compression should be used.
         If true, 'gzip' is used, otherwise you can specify compression by providing a str.
         Defaults to not compressed.
    """
    if hasattr(data, 'asdict'):
        data = data.asdict()  # type: ignore
    if hasattr(data, 'asarray'):
        data = data.asarray()  # type: ignore
    if isinstance(data, dict):
        g = group.create_group(key)
        for k, v in data.items():
            save_sub_dict(g, v, k, use_compression=use_compression)
    elif (key is not None) and (data is not None):
        data = transform_not_dict_on_save(data)  # type: ignore
        if isinstance(data, (np.ndarray, list)):
            use_compression = "gzip" if use_compression is True else use_compression
            group.create_dataset(key, data=data, compression=use_compression)  # compression="gzip"
        else:
            group.create_dataset(key, data=data)


def save_dict(
    filename: str,
    data: dict,
    key_prefix: Optional[str] = None,
    use_compression: Optional[Union[Literal[True], str]] = None,
) -> float:
    """Save dict to h5 file.

    Args:
        filename (str): Full filepath to the file.
        data (dict): Data to save.
        key_prefix (str, optional): Key prefix of the desired location inside h5 file.
         If nested use `key1/key2`. Defaults to None, i.e. root of the file.
        use_compression (str|True, optional): If compression should be used. If true,
         'gzip' is used, otherwise you can specify compression by providing a str.
         Defaults to not compressed.

    Returns:
        float: Time of the last modification of the file.
    """
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    mode = 'a'  # if os.path.exists(filename) else 'w'
    with LockFile(filename), h5py.File(filename, mode) as file:
        for key, value in data.items():
            key = key if key_prefix is None else f"{key_prefix}/{key}"
            if key in file:  # .keys():
                file.pop(key)
            if value is None:
                continue
            save_sub_dict(file, value, key, use_compression=use_compression)
    return os.path.getmtime(filename)


# -------------- Load keys ----------------


def keys_h5(filename, key_prefix: Optional[str] = None) -> Set[str]:
    """Return keys of h5 file.

    Args:
        filename (_type_): Full filepath to the file.
        key_prefix (str, optional): Key prefix to look at. If nested use `key1/key2`.
         Defaults to None.

    Returns:
        Set[str]: Set of the keys.
    """
    with h5py.File(filename, 'r') as file:
        if key_prefix is not None:
            file = file[key_prefix]
        return set(file.keys())  # type: ignore


# -------------- Delete keys ----------------


def del_dict(
    filename: str,
    key: str,
    key_prefix: Optional[str] = None,
) -> float:
    """Delete key from h5 file.

    Args:
        filename (str): Full filepath to the file.
        key (str): key to delete. If nested use `key1/key2`.
        key_prefix (str, optional): If provided, key_prefix/key is used. Defaults to None.

    Returns:
        float: Time of the last modification of the file.
    """
    with LockFile(filename), h5py.File(filename, 'a') as file:
        key = key if key_prefix is None else f"{key_prefix}/{key}"
        file.pop(key)
    return os.path.getmtime(filename)
