"""Parsing module.

Examples:
    >>> from labmate import parsing
    >>> parsing.parse_str('''
        a = 1
        b = a # value: 1
        ''')
    {'a': ParsedValue: 1=1, 'b': ParsedValue: 'a'=1}


"""

from typing import Dict

from .brackets_score import BracketsScore
from .parsed_value import ParsedValue


def parse_str(file: str, /) -> Dict[str, ParsedValue]:
    """Parse multiline string.

    Return a dictionary of { 'variable name' : (converted value if possible | str) }.
    """
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

        value_eval = value[value.rfind("# value: ") + 9 :] if ("# value: " in value) else None

        value = value.split("#")[0].strip()

        if value_eval is None:
            value_eval = value

        parsed_values[param.strip()] = ParsedValue(value, value_eval)

    return parsed_values
