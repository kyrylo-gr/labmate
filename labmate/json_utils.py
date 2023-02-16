"""
This model saves the classical dict to json file and load it from there.
"""
from typing import Optional, Union
import os
import json
from .path import Path


class JSONDecoder(json.JSONDecoder):
    """decoder for JSON to convert str to int or float if posible."""

    def decode(self, s):  # pylint: disable=arguments-differ
        result = super().decode(s)
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str):
            try:
                return int(o)
            except ValueError:
                try:
                    return float(o)
                except ValueError:
                    return o

        elif isinstance(o, dict):
            return {k: self._decode(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o


class JSONEncoder(json.JSONEncoder):
    """Classical JSONEncoder will not try to convert objects to a str. This does."""

    def default(self, o):
        try:
            if hasattr(o, "__iter__"):
                return list(iter(o))
            return str(o)
        except TypeError:
            pass
        return None


def get_file_path(file_name: Union[str, Path],
                  path: Optional[Union[str, Path]] = None,
                  extension: Optional[str] = None) -> Path:
    file_name = str(file_name)
    if extension is not None:
        if extension[0] != '.':
            extension = '.' + extension
        if not file_name.endswith(extension):
            file_name = file_name + extension
    if path is not None:
        return Path(path, file_name)
    return Path(file_name)


def json_read(file: Union[str, Path],
              path: Optional[Union[str, Path]] = None) -> dict:
    """Load a JSON file. And decode """
    path = get_file_path(file,
                         path=path,
                         extension='.json')
    with open(path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file, cls=JSONDecoder)


def json_write(file: Union[str, Path],
               data: dict,
               path: Optional[Union[str, Path]] = None
               ) -> None:
    """Saves data(Dict) to the file.
    Path is optional to precise the location of the file.
    Extension in filename is optional."""
    path = get_file_path(file, path, '.json')

    path_dir = os.path.dirname(path)
    if not os.path.exists(path_dir):
        os.makedirs(path_dir, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as outfile:
        json.dump(
            data,
            outfile,
            sort_keys=True,
            indent=4,
            cls=JSONEncoder)
