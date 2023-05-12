from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union


def parse_str(file: str, /) -> Dict[str, Union[str, int, float]]:
    """Parse strings.
    Return a dictionary of int or float if conversion is possible otherwise str"""
    parsed_values = {}
    for line in file.split('\n'):
        if len(line) == 0 or not line[0].isalpha() or '=' not in line:
            continue
        param, value = line.split('=')[:2]

        if "# value: " in value:
            value = value[value.find("# value: ") + 9:]

        value = value.split('#')[0].strip()
        value_without_underscores = value.replace("_", "")

        try:
            if len(value_without_underscores) == 0:
                pass
            elif value_without_underscores.isdigit() or \
                    (value_without_underscores[0] == '-' and value[1:].isdigit()):
                value = int(value)
            elif value_without_underscores.replace('.', '').isdigit() or \
                    (value[0] == '-' and value_without_underscores[1:].replace('.', '').isdigit()):
                value = float(value)
            elif (value[0].isdigit() or (value[0] == "-" and value[1].isdigit())) \
                    and value[-1].isdigit() and 'e' in value:
                value = float(value)
        except ValueError:
            pass

        parsed_values[param.strip()] = value

    return parsed_values


def parse_get_format(key: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Convert a key into a key, units, format.
    Example:
        speed__km/s__2f -> (speed, km/s, 2f)
        speed -> (speed, None, None)
        speed__2f -> (speed, None, '2f')
        speed__km/s -> (speed, 'km/s', None)
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
    key: str
    value: Any
    units: Optional[str] = None
    format: Optional[str] = None


def format_title(values: List[ValueForPrint], max_length: Optional[int] = None):
    max_length = max_length or 60
    txt = ""
    last_line_len = 0
    for value in values:
        units = f" ({value.units})" if value.units is not None else ""
        value_str = value.value if value.format is None else value.value.__format__(f".{value.format}")
        new_txt = f"{value.key} = {value_str}{units}"
        if last_line_len + len(new_txt) < max_length:
            txt += ("; " if txt != "" else "") + new_txt
            last_line_len += len(new_txt) + 2
        else:
            last_line_len = len(new_txt)
            txt += "\n" + new_txt
    return txt
