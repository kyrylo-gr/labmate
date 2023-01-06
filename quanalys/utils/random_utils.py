from typing import Dict, Optional, Tuple, Union


def get_timestamp() -> str:
    import datetime
    x = datetime.datetime.now()
    return x.strftime("%Y_%m_%d__%H_%M_%S")


def parse_str(file: str, /) -> Dict[str, Union[str, int, float]]:
    """Parsing a str.
    Return a dictionary of int or float if conversion is possible otherwise str"""
    parsed_values = {}
    for line in file.split('\n'):
        if len(line) == 0 or not line[0].isalpha() or '=' not in line:
            continue
        param, value = line.split('=')[:2]
        value = value.split('#')[0].replace("_", "").strip()
        try:
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            elif value[0].isdigit() and value[-1].isdigit() and 'e' in value:
                value = float(value)
        except ValueError:
            pass

        parsed_values[param.strip()] = value

    return parsed_values


def lstrip_int(line: str) -> Optional[Tuple[str, str]]:
    """Find whether timestamp ends.
    Returns timestamp and rest of the line, if possible.
    """
    # this algorithm with regex is 2x faster than the easiest one

    import re

    suffix = re.search("_[A-Za-z]", line)
    if suffix is None:
        return None
    prefix, suffix = line[:suffix.start()], line[suffix.start()+1:]

    if not prefix.replace('_', '').replace('-', '').isdigit():
        return None

    return prefix, suffix


def get_var_name_from_def():
    import traceback
    line = traceback.extract_stack()[-3].line
    if line and "=" in line:
        return line.split("=")[0].strip()
    return None


def get_var_name_from_glob(variable):
    globals_dict = globals()
    return [var_name for var_name in globals_dict if globals_dict[var_name] is variable]


def test():
    print(3)
