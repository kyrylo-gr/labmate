"""Random utilities."""
from typing import Any, Callable, List, Optional, Tuple, Union

from dh5.utils.random_utils import (  # pylint: disable=unused-import # noqa: F401
    get_path_from_filename,
    get_timestamp,
)


_CallableWithNoArgs = Callable[[], Any]


def run_functions(
    functions: Optional[
        Union[_CallableWithNoArgs, List[_CallableWithNoArgs], Tuple[_CallableWithNoArgs, ...]]
    ] = None,
    /,
):
    """Run functions if any provided."""
    if functions is not None:
        if isinstance(functions, (list, tuple)):
            for func in functions:
                func()
        else:
            functions()
