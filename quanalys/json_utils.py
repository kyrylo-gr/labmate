"""
This model saves the classical dict to json file and load it from there.
"""
from pathlib import Path
import json
from typing import Optional, Union


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


def get_file_path(file_name: str,
                  path: Optional[Union[str, Path]] = None,
                  extension: Optional[str] = None) -> Path:

    if extension is not None:
        if extension[0] != '.':
            extension = '.' + extension
        if not file_name.endswith(extension):
            file_name = file_name + extension
    if path is not None:
        return Path(path, file_name)
    return Path(file_name)


def json_read(file: str,
              path: Optional[Union[str, Path]] = None) -> dict:
    """Load a JSON file. And decode """
    path = get_file_path(file,
                         path=path,
                         extension='.json')
    with open(path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file, cls=JSONDecoder)


def json_write(file: str,
               data: dict,
               path: Optional[Union[str, Path]] = None
               ) -> None:
    """Saves data(Dict) to the file.
    Path is optional to precise the location of the file.
    Extension in filename is optional."""
    path = get_file_path(file, path, '.json')

    with open(path, 'w', encoding='utf-8') as outfile:
        json.dump(
            data,
            outfile,
            sort_keys=True,
            indent=4)
