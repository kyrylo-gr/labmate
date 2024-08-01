"""Different method to read files."""

import json
import os
import re
from typing import Any, Dict, List, Optional

from ..parsing.brackets_score import BracketsScore


def read_file(file: str, /) -> str:
    """Read the contents of a file and returns it as a string.

    Args:
        file (str): The path to the file to be read.

    Returns:
        str: The contents of the file as a string.

    Raises:
        ValueError: If the file does not exist or is not a file.
    """
    if not os.path.isfile(file):
        raise ValueError(
            "Cannot read a file if it doesn't exist or it's not a file."
            f"Path: {os.path.abspath(file)}"
        )

    with open(file, "r", encoding="utf-8") as file_opened:
        return file_opened.read()


def read_files(files: List[str], /) -> Dict[str, str]:
    """Read the contents of the given  files and returns them as a dictionary.

    Args:
        files: A list of file paths to read.

    Returns:
        A dictionary where the keys are the file names and the values are the contents of the files.

    Raises:
        ValueError: If some of the files have the same name, which would cause a key collision in the dictionary.
    """
    configs: Dict[str, str] = {}
    for config_file in files:
        config_file_name = os.path.basename(config_file)
        if config_file_name in configs:
            raise ValueError(
                "Some of the files have the same name. So it cannot be pushed into dictionary to"
                " preserve unique key"
            )
        configs[config_file_name] = read_file(config_file)
    return configs


def update_file_variable(file, params: Dict[str, Any]):
    """
    Update the variables in a file with the given parameters.

    Args:
        file (str): The path to the file to update.
        params (Dict[str, Any]): The parameters to update the file with.
    """
    with open(file, "r", encoding="utf-8") as file_opened:
        lines = file_opened.readlines()
    brackets = BracketsScore()
    current_param: Optional[str] = None
    # print(lines)
    for line in lines:
        # print(line)
        if len(line) == 0:
            continue
        if brackets.is_zero() and "=" in line:
            param = line.split("=")[0].strip()
            # print("param", param)
            if param in params:
                current_param = param
                start_line = lines.index(line)

        brackets.update_from_str(line)
        if brackets.is_zero() and current_param is not None:
            end_line = lines.index(line)
            end_comment = "#".join(line.split("#")[1:]).strip() if "#" in line else None
            del lines[start_line : end_line + 1]
            value_str = json.JSONEncoder().encode(params[current_param])

            print("value_str", value_str)
            if re.match(
                r"^['\"]?[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?['\"]?$", value_str
            ):
                value_str = value_str.replace('"', "")

            lines.insert(
                start_line,
                (
                    f"{current_param} = {value_str}"
                    + (f"  # {end_comment}" if end_comment is not None else "")
                    + "\n"
                ),
            )
            current_param = None

    with open(file, "w", encoding="utf-8") as file_opened:
        file_opened.writelines(lines)
