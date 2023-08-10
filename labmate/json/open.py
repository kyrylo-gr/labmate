import json
from typing import Optional, Type, Union
from .decoders import NumbersDecoder
from .encoders import StringEncoder
from ..path import Path, get_file_path


def write(
    file: Union[str, 'Path'],
    data: dict,
    path: Optional[str] = None,
    encoder: Type[json.JSONEncoder] = StringEncoder,
) -> None:
    """Write data to a file. Sort keys.

    Args:
        file (str): file name or path.
        data (dict): data.
        path (Optional[str], optional): Path to the folder with file. Defaults to None.

    Examples:
        >>> write(path, data)
    """
    file = get_file_path(file, path=path, extension='.json')
    file.dirname.makedirs()
    with open(file, 'w', encoding="utf-8") as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4, cls=encoder)


def read(
    file: Union[str, 'Path'],
    path: Optional[str] = None,
    decoder: Type[json.JSONDecoder] = NumbersDecoder,
) -> dict:
    """Load a data from file at path. Decode number by default.

    Args:
        file (Union[str, Path]): file name or path to file.
        path (Optional[str], optional): path to folder with file. Defaults to None.

    Returns:
        dict: Data loaded from file.

    Examples:
        >>> read(path)

    """
    file = get_file_path(file, path=path, extension='.json')

    with open(file, encoding="utf-8") as json_file:
        return json.load(json_file, cls=decoder)
