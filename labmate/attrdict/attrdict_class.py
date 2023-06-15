from typing import Any, Generic, List, Optional, Tuple, TypeVar, Union, overload
from ..utils import parse as utils_parse
# import ValueForPrint, format_title

# KT = TypeVar('KT')
# VT = TypeVar('VT')


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = AttrDict(v)
        self.__dict__ = self

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {super().__repr__()}'

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
        if not isinstance(key, str):
            return [self.find(k) for k in key]
        for true_key, value in self.items():
            if key in true_key:
                return (true_key, value)
        return None

    def output(self, keys: List[str], max_length: Optional[int] = None):
        keys_with_values = self.__get_value_for_output(keys)
        return utils_parse.format_title(keys_with_values, max_length=max_length)

    def __get_value_for_output(self, keys: List[str]) -> List[utils_parse.ValueForPrint]:
        keys_with_values = []
        for key in keys:
            key_value, key_units, key_format = utils_parse.parse_get_format(key)
            if key_value in self:
                keys_with_values.append(utils_parse.ValueForPrint(
                    key_value, self[key_value], key_units, key_format))
            else:
                raise ValueError(f"Cannot find key={key} inside {self.__class__.__name__}")
        return keys_with_values
