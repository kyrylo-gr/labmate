from typing import Any, Callable, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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
    prefix, main = line[: main.start()], line[main.start() + 1 :]
    if "__" in main:
        suffix_index = main.rfind("__")
        suffix = main[suffix_index + 2 :]
        if suffix.isdecimal():
            main = main[:suffix_index]
        else:
            suffix = ""
    else:
        suffix = ""

    if not prefix.replace("_", "").replace("-", "").isdigit():
        return None

    return prefix, main, suffix


def get_path_from_filename(filename: Union[str, "Path"]) -> Union[str, tuple]:
    """
    Given a filename, returns the path to the file.

    If the filename contains a path, returns the filename as is.
    If the filename ends with '.h5', removes the extension.
    If the filename starts with a timestamp, returns a tuple with (the suffix that does after
    the timestamp, the full filename without '.h5' extension in the end).

    Args:
        filename (Union[str, "Path"]): The filename to get the path from.

    Returns:
        Union[str, tuple]: The path to the file as tuple (folder, filename) or the filename itself.
        Return directly filename if it contains a slash, therefore represents the path.
    """
    filename = str(filename)

    if "/" in filename or "\\" in filename:
        return filename

    filename = filename[:-3] if filename.endswith(".h5") else filename

    name_with_prefix = lstrip_int(filename)

    if name_with_prefix:
        suffix = name_with_prefix[1]
        return (suffix, filename)
    return filename


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
    funcs: Optional[
        Union[_CallableWithNoArgs, List[_CallableWithNoArgs], Tuple[_CallableWithNoArgs, ...]]
    ] = None
):
    """Run functions if some provided."""
    if funcs is not None:
        if isinstance(funcs, (list, tuple)):
            for func in funcs:
                func()
        else:
            funcs()


def output_warning(text: str, logger=None):
    try:
        from IPython import display

        html = f"""<div style="
        background-color:#ec7413; padding: .5em; text-align:center"
        >{text}</div>"""

        display.display(display.HTML(str(html)))  # type: ignore

    except ImportError:
        if logger is not None:
            logger.warning(text)
        else:
            print(text)
