import json
import h5py
from typing import Union

import numpy as np


def save_sub_dict(
    group: Union[h5py.File, h5py.Group],
    data: Union[dict, list, np.ndarray],
    key: str
):
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
    with h5py.File(filename, 'a') as file:
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
            data[key] = value[()]  # type: ignore
    return data


def output_dict_structure(data: dict) -> str:
    return dict_to_json_format_str(get_dict_structure(data))


def dict_to_json_format_str(data: dict) -> str:
    """" Outputs a dictionary structure """
    return json.dumps(data, sort_keys=True, indent=4)


def get_dict_structure(data: dict) -> dict:
    structure = {}
    for k, v in data.items():
        if isinstance(v, dict):
            structure[k] = get_dict_structure(v)
        elif isinstance(v, (np.ndarray, list)):
            structure[k] = f"shape: {np.shape(v)} (type: {type(v).__name__})"
        elif isinstance(v, (int)):
            structure[k] = f"{v:.0f} (type : {type(v).__name__})"
        elif isinstance(v, float):
            str_value = f"{v:.3f}" if .1 <= v <= 100 else f"{v:.3e}"
            structure[k] = f"{str_value} (type : {type(v).__name__})"
        else:
            structure[k] = f"variable of type {type(v).__name__}"
    return structure
