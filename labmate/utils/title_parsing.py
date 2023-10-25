"""This file contains function of title generation.
(parsing expected units and format, creating title)
"""
from typing import Any, List, NamedTuple, Optional, Tuple


def parse_get_format(key: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Convert a key into a key, units, format.

    Example:
        >>> speed__km/s__2f -> (speed, km/s, 2f)
        >>> speed -> (speed, None, None)
        >>> speed__2f -> (speed, None, '2f')
        >>> speed__km/s -> (speed, 'km/s', None)
    """
    args = key.split("__")
    if len(args) >= 3:
        return args[0], args[1], args[2]
    elif len(args) == 2 and len(args[1]) > 0 and args[1][0].isdigit():
        return args[0], None, args[1]
    elif len(args) == 2:
        return args[0], args[1], None
    return args[0], None, None


class ValueForPrint(NamedTuple):
    """Value with key, units and format."""

    key: str
    value: Any
    units: Optional[str] = None
    format: Optional[str] = None


def format_title(values: List[ValueForPrint], max_length: Optional[int] = None) -> str:
    """Create title out of a list of valuesForPrint.

    Args:
        values (List[ValueForPrint]): list of values to print.
        max_length (Optional[int], optional): Maximal possible line length. Defaults to None.

    Returns:
        Multiline title.
    """
    txt = ""
    last_line_len = 0
    for value in values:
        units = f" ({value.units})" if value.units is not None else ""
        value_str = (
            value.value if value.format is None else value.value.__format__(f".{value.format}")
        )
        new_txt = f"{value.key} = {value_str}{units}"
        if not max_length or ((last_line_len + len(new_txt) < max_length) or last_line_len == 0):
            txt += ("; " if txt != "" else "") + new_txt
            last_line_len += len(new_txt) + 2
        else:
            last_line_len = len(new_txt)
            txt += "\n" + new_txt
    return txt
