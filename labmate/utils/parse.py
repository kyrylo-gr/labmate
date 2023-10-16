from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union


class BracketsScore:
    def __init__(self) -> None:
        self.round = 0
        self.curly = 0
        self.square = 0

    def is_zero(self):
        return self.round == 0 and self.curly == 0 and self.square == 0

    def update_from_str(self, text: str):
        self.round += text.count("(") - text.count(")")
        self.curly += text.count("{") - text.count("}")
        self.square += text.count("[") - text.count("]")


class ParsedValue:
    original: Union[str, int, float, complex]
    value: Union[str, int, float, complex]

    def __init__(self, original, value):
        self.original = original
        self.value = value

    def __iter__(self):
        return iter((self.original, self.value))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"ParsedValue: {self.original}={self.value}"

    def __format__(self, __format_spec: str) -> str:
        return self.value.__format__(__format_spec)

    def __eq__(self, __value: object) -> bool:
        return self.value.__eq__(__value)

    def __abs__(self) -> float:
        return self.value.__abs__()  # type: ignore

    def __add__(self, other):
        other = self.convert_other(other)
        return self.value + other

    def __radd__(self, other):
        other = self.convert_other(other)
        return self.__add__(other)

    def __sub__(self, other):
        other = self.convert_other(other)
        return self.value - other  # type: ignore

    def __rsub__(self, other):
        other = self.convert_other(other)
        return self.__sub__(other)

    def __mul__(self, other):
        other = self.convert_other(other)
        return self.value * other

    def __rmul__(self, other):
        other = self.convert_other(other)
        return self.__mul__(other)

    def __truediv__(self, other):
        other = self.convert_other(other)
        return self.value / other  # type: ignore

    def __floordiv__(self, other):
        other = self.convert_other(other)
        return self.value // other  # type: ignore

    def __mod__(self, other):
        other = self.convert_other(other)
        return self.value % other

    def __pow__(self, other):
        other = self.convert_other(other)
        return self.value**other

    def __lt__(self, other):
        other = self.convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__lt__(other)

    def __gt__(self, other):
        other = self.convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__gt__(other)

    def __le__(self, other):
        other = self.convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__le__(other)

    def __ge__(self, other):
        other = self.convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__ge__(other)

    def __ne__(self, other):
        other = self.convert_other(other)
        return self.value.__ne__(other)

    @property
    def is_complex(self):
        return isinstance(self.value, complex)

    @property
    def real(self):
        if isinstance(self.value, complex):
            return self.value.real
        return self.value

    @property
    def imag(self):
        if isinstance(self.value, complex):
            return self.value.imag
        return 0

    @staticmethod
    def convert_other(other) -> Any:
        if isinstance(other, ParsedValue):
            return other.value
        return other


def parse_value(value: str) -> Union[str, int, float]:
    """Convert str to int or float if possible."""
    if not isinstance(value, str):
        return value

    value_without_underscores = value.replace("_", "")
    try:
        if len(value_without_underscores) == 0:
            pass
        elif value_without_underscores.isdigit() or (
            value_without_underscores[0] == "-" and value[1:].isdigit()
        ):
            return int(value)
        elif value_without_underscores.replace(".", "").isdigit() or (
            value[0] == "-" and value_without_underscores[1:].replace(".", "").isdigit()
        ):
            return float(value)
        elif (
            (value[0].isdigit() or (value[0] == "-" and value[1].isdigit()))
            and value[-1].isdigit()
            and "e" in value
        ):
            return float(value)
    except ValueError:
        return value

    return value


def parse_str(file: str, /) -> Dict[str, ParsedValue]:
    """Parse strings.

    Return a dictionary of int or float if conversion is possible otherwise str"""
    parsed_values = {}
    brackets = BracketsScore()
    param, value = "", ""
    for line in file.split("\n"):
        if not brackets.is_zero():
            value += f"{line.split('#')[0].strip()}\n"  # type: ignore
        elif len(line) == 0 or not line[0].isalpha() or "=" not in line:
            continue
        else:
            param, value = line.split("=")[:2]

        brackets.update_from_str(line)
        if not brackets.is_zero():
            continue

        if "# value: " in value:
            value_eval = value[value.rfind("# value: ") + 9 :]
            value_eval = parse_value(value_eval)
        else:
            value_eval = None

        value = parse_value(value.split("#")[0].strip())

        if value_eval is None:
            value_eval = value

        parsed_values[param.strip()] = ParsedValue(value, value_eval)

    return parsed_values


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


def format_title(values: List[ValueForPrint], max_length: Optional[int] = None):
    # max_length = max_length or 60
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
