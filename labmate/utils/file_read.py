"""Different method to read files."""
import os
from typing import Dict, List


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
