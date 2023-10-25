"""This module contains the AttrDict class."""
from typing import Any, List, Optional, Tuple, Union, overload
from ..utils import title_parsing as utils_parse


class AttrDict(dict):
    """A dictionary that allows to access its keys as attributes.

    Examples:
        >>> data = AttrDict({'param_1': 'value1', 'param_2': 'value2'})
        >>> data['param_1'] # -> 'value1'
        >>> data.param_1 # -> 'value1'

    """

    def __init__(self, *args, **kwargs):
        """Use the same constructor as classical dictionary."""
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = AttrDict(v)
        self.__dict__ = self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {super().__repr__()}"

    def __add__(self, other):
        result = self.copy()
        result.update(other)
        return type(self)(result)

    @overload
    def find_all(self, key: str) -> List[Tuple[str, Any]]:
        ...

    @overload
    def find_all(self, key: list) -> List[List[Tuple[str, Any]]]:
        ...

    def find_all(self, key: Union[str, list]):
        """Find all keys that contain the given string.

        Examples:
        ----------
            >>> data = AttrDict({'param_1': 'value1', 'param_2': 'value2'})
            >>> data.find_all('param') # -> [('param_1', 'value1'), ('param_2', 'value2')]
        """
        if not isinstance(key, str):
            return [self.find_all(k) for k in key]
        elms = []
        for true_key, value in self.items():
            if key in true_key:
                elms.append((true_key, value))
        return elms

    @overload
    def find(self, key: str) -> Optional[Tuple[str, Any]]:
        ...

    @overload
    def find(self, key: list) -> List[Optional[Tuple[str, Any]]]:
        ...

    def find(self, key: Union[str, list]) -> Union[Optional[tuple], list]:
        """Find the first key that contain the given string.

        Examples:
        ----------
            >>> data = AttrDict({'param_1': 'value1', 'param_2': 'value2'})
            >>> data.find('param') # -> ('param_1', 'value1')
        """
        if not isinstance(key, str):
            return [self.find(k) for k in key]
        for true_key, value in self.items():
            if key in true_key:
                return (true_key, value)
        return None

    def output(self, keys: List[str], max_length: Optional[int] = None):
        """Ouput the given keys with provided format.

        It's possible to provide a unit and a format to parse config function.
        Use the such structure for the string `key__unit__format`.

        Examples:
        ----------
            >>> data =  AttrDict({'param_1': 123.43})
            >>> data.output(["param_1"]) # -> param_1 = 123.43
            >>> data.output(["param_1__m/s__1f"]) # -> param_1 = 123.4 (m/s)
            >>> data.output(["param_1__m/s"]) # -> 'param_1 = 123.43 (m/s)'
            >>> data.output(["param_1__2f"]) # -> 'param_1 = 123.43'
            >>> data.output(["param_1__2e"]) # -> 'param_1 = 1.23e+02'
        """
        keys_with_values = self.__get_value_for_output(keys)
        return utils_parse.format_title(keys_with_values, max_length=max_length)

    def __get_value_for_output(self, keys: List[str]) -> List[utils_parse.ValueForPrint]:
        """Prepare the values for output. Returns list of ValueForPrint(key, value, unit, format))."""
        keys_with_values = []
        for key in keys:
            key_value, key_units, key_format = utils_parse.parse_get_format(key)
            if key_value in self:
                keys_with_values.append(
                    utils_parse.ValueForPrint(key_value, self[key_value], key_units, key_format)
                )
            else:
                raise ValueError(f"Cannot find key={key} inside {self.__class__.__name__}")
        return keys_with_values
