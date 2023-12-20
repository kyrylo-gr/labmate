"""ParsedValue class."""

from typing import Any, Union


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


class ParsedValue:
    """Store the original value and the converted value and perform any operations on value.


    ParsedValue has `original` and `value` attribute.
    `original` is the original value as a string.
    `value` is the value converted to different possible types if possible.

    This class does not convert values. It should be converted before and given on init.

    Examples:
        >>> v1 = ParsedValue("1", 1)
        >>> v2 = ParsedValue("2", 2)
        >>> v1 + v2
        3

    """

    original: Union[str, int, float, complex]
    value: Union[str, int, float, complex]

    def __init__(self, original, value):
        """Initialize ParsedValue.

        Args:
            original (str): original value as a string
            value (Any): converted value if possible
        """
        self.original = parse_value(original)
        self.value = parse_value(value)

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
        return abs(self.value)  # type: ignore

    def __float__(self) -> float:
        return float(self.value)  # type: ignore

    def __add__(self, other):
        other = self._convert_other(other)
        return self.value + other

    def __radd__(self, other):
        other = self._convert_other(other)
        return self.__add__(other)

    def __sub__(self, other):
        other = self._convert_other(other)
        return self.value - other  # type: ignore

    def __rsub__(self, other):
        other = self._convert_other(other)
        return self.__sub__(other)

    def __mul__(self, other):
        other = self._convert_other(other)
        return self.value * other

    def __rmul__(self, other):
        other = self._convert_other(other)
        return self.__mul__(other)

    def __truediv__(self, other):
        other = self._convert_other(other)
        return self.value / other  # type: ignore

    def __floordiv__(self, other):
        other = self._convert_other(other)
        return self.value // other  # type: ignore

    def __mod__(self, other):
        other = self._convert_other(other)
        return self.value % other

    def __pow__(self, other):
        other = self._convert_other(other)
        return self.value**other

    def __lt__(self, other):
        other = self._convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__lt__(other)

    def __gt__(self, other):
        other = self._convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__gt__(other)

    def __le__(self, other):
        other = self._convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__le__(other)

    def __ge__(self, other):
        other = self._convert_other(other)
        if isinstance(self.value, complex):
            raise TypeError("Cannot compare complex values")
        return self.value.__ge__(other)

    def __ne__(self, other):
        other = self._convert_other(other)
        return self.value.__ne__(other)

    @property
    def is_complex(self):
        """Returns if current value is complex."""
        return isinstance(self.value, complex)

    @property
    def real(self):
        """Return real value of self.value."""
        if isinstance(self.value, complex):
            return self.value.real
        return self.value

    @property
    def imag(self):
        """Return imaginary value of self.value."""
        if isinstance(self.value, complex):
            return self.value.imag
        return 0

    @staticmethod
    def _convert_other(other) -> Any:
        if isinstance(other, ParsedValue):
            return other.value
        return other
