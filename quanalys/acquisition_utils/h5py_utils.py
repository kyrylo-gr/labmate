import h5py
from typing import Union

import numpy as np


def save_sub_dict(
    group: Union[h5py.File, h5py.Group],
    data: Union[dict, list, np.ndarray],
    key: str
):
    if isinstance(data, dict):
        print(f"Creating group with {key}")
        g = group.create_group(key)
        for k, v in data.items():
            save_sub_dict(g, v, k)
    elif (key is not None) and (data is not None):
        print(f"Creating dataset with {key}")
        group.create_dataset(key, data=data)


def save_dict(
    filename: str,
    data: dict,
):
    with h5py.File(filename, 'a') as file:
        for k, v in data.items():
            if k in file.keys():
                file.pop(k)
            if v is None:
                continue
            save_sub_dict(file, v, k)
    return filename


def del_dict(
    filename: str,
    key: str
):
    with h5py.File(filename, 'a') as file:
        file.pop(key)
