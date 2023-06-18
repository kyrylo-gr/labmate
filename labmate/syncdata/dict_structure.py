"""Output the structure of a dictionary in a pretty way."""


import json
from typing import Dict, Optional

import numpy as np


def output_dict_structure(data: dict, additional_info: Optional[Dict[str, str]] = None) -> str:
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
                internal_structure = (
                    get_dict_structure(v, level=level - 1) if len(v) else "empty dict"
                )
                structure[k] = (
                    "variable of type dict" if len(internal_structure) > 5 else internal_structure
                )
            else:
                structure[k] = "variable of type dict"

        elif isinstance(v, (np.ndarray, list)):
            structure[k] = f"shape: {np.shape(v)} (type: {type(v).__name__})"
        elif isinstance(v, (int, np.int_)):  # type: ignore
            structure[k] = f"{v:.0f} (type : {type(v).__name__})"
        elif isinstance(v, (float, np.float_, complex, np.complex_)):  # type: ignore
            str_value = f"{v:.3f}" if 0.1 <= abs(v) <= 100.0 else f"{v:.3e}"
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
