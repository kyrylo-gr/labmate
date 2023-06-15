from typing import Any, Callable, List, Optional, Tuple, Union


def get_timestamp() -> str:
    import datetime
    x = datetime.datetime.now()
    return x.strftime("%Y_%m_%d__%H_%M_%S")


def lstrip_int(line: str) -> Optional[Tuple[str, str, str]]:
    """Find whether timestamp ends.
    Returns timestamp and rest of the line, if possible.
    """
    # this algorithm with regex is 2x faster than the easiest one

    import re

    main = re.search("_[A-Za-z]", line)
    if main is None:
        return None
    prefix, main = line[:main.start()], line[main.start()+1:]
    if '__' in main:
        suffix_index = main.rfind('__')
        suffix = main[suffix_index+2:]
        if suffix.isdecimal():
            main = main[:suffix_index]
        else:
            suffix = ''
    else:
        suffix = ''

    if not prefix.replace('_', '').replace('-', '').isdigit():
        return None

    return prefix, main, suffix


def get_var_name_from_def():
    import traceback
    line = traceback.extract_stack()[-3].line
    if line and "=" in line:
        return line.split("=")[0].strip()
    return None


def get_var_name_from_glob(variable):
    globals_dict = globals()
    return [var_name for var_name in globals_dict if globals_dict[var_name] is variable]


_CallableWithNoArgs = Callable[[], Any]


def run_functions(
        funcs: Optional[Union[_CallableWithNoArgs, List[_CallableWithNoArgs], Tuple[_CallableWithNoArgs, ...]]] = None):
    if funcs is not None:
        if isinstance(funcs, (list, tuple)):
            for func in funcs:
                func()
        else:
            funcs()
