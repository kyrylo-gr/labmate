"""This file contains function of title generation.
(parsing expected units and format, creating title)
"""

from typing import Any, List, NamedTuple, Optional, Tuple


def parse_get_format(key: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Convert a key into a key, units, format.

    The separator can be a comma (``,``) or semicolon (``;``). Comma takes
    precedence if both are present. A plain key with no separator is returned as-is,
    allowing variable names that contain double underscores.

    Example:
        >>> speed,km/s,2f -> (speed, km/s, 2f)
        >>> speed -> (speed, None, None)
        >>> speed,2f -> (speed, None, '2f')
        >>> speed,km/s -> (speed, 'km/s', None)
        >>> speed;km/s;2f -> (speed, km/s, 2f)
        >>> double__underscore -> (double__underscore, None, None)
    """
    if "," in key:
        sep = ","
    elif ";" in key:
        sep = ";"
    else:
        return key, None, None
    args = key.split(sep)
    if len(args) >= 3:
        return args[0], args[1], args[2]
    if len(args) == 2 and len(args[1]) > 0 and (args[1][0].isdigit() or args[1][0] in (".", "_")):
        return args[0], None, args[1]
    if len(args) == 2:
        return args[0], args[1], None
    return args[0], None, None


class ValueForPrint(NamedTuple):
    """Value with key, units and format."""

    key: str
    value: Any
    units: Optional[str] = None
    format: Optional[str] = None

    def format_value(self, format_spec: Optional[str] = None) -> str:
        format_spec = format_spec or self.format
        if not format_spec:
            return str(self.value)
        if format_spec.endswith("p"):
            format_spec = format_spec[:-1] + "e"
            value_str = format(self.value, format_spec)
            number, power = value_str.split("e")
            number = number.rstrip("0_").rstrip(".") if "." in number else number
            power = (power[0].lstrip("+0") + power[1:].lstrip("+0")) if len(power) > 1 else power
            return f"{number}e{power}"
        return format(self.value, format_spec)


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
        value_str = value.format_value()
        new_txt = f"{value.key} = {value_str}{units}"
        if not max_length or ((last_line_len + len(new_txt) < max_length) or last_line_len == 0):
            txt += ("; " if txt != "" else "") + new_txt
            last_line_len += len(new_txt) + 2
        else:
            last_line_len = len(new_txt)
            txt += "\n" + new_txt
    return txt
