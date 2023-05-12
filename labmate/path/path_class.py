import pathlib
import os
from typing import Iterable, Optional, Union


class Path(type(pathlib.Path())):
    """Make pathlib.Path better.

    Functionality added:
    - sum 2 path or path and str. Action: sum 2 str
    - makedirs. Action: os.makedirs
    - make_extension
    - dirname
    - basename
    """

    def __add__(self, other: str):
        """Sum 2 str."""
        if not isinstance(other, str):
            other = str(other)
        return type(self)(self.as_posix() + other)

    def makedirs(self, mode=0o777, exist_ok=False):
        """Create a directories if needed.

        If self is a file creates directories to dirname(self)."""
        file = os.path.dirname(self) \
            if '.' in os.path.basename(self) else self
        if not os.path.exists(file):
            os.makedirs(file, mode=mode, exist_ok=exist_ok)
        return self

    def make_extension(self, extension: Union[Iterable[str], str]):
        """Make sure that the extension is the one provided.

        If the list of extensions provided, then any extensions are allowed,
        but is no one satisfied, uses first to determine extension."""
        if isinstance(extension, str):
            extension = [extension]
        if not isinstance(extension, Iterable):
            raise ValueError("Extension must be a string or an iterable")
        extension = [ext if ext.startswith('.') else ('.' + ext)
                     for ext in extension]
        path = self.as_posix()
        for ext in extension:
            if path.endswith(ext):
                return self
        return type(self)(self.as_posix() + extension[0])

    @property
    def dirname(self) -> 'Path':
        return type(self)(os.path.dirname(self))

    @property
    def basename(self) -> 'Path':
        return type(self)(os.path.basename(self))


def get_file_path(file_name: Union[str, Path], *,
                  path: Optional[Union[str, Path]] = None,
                  extension: Optional[str] = None) -> Path:
    file_name = Path(file_name)
    if extension:
        file_name.make_extension(extension)
    if path is not None:
        return Path(path, file_name)
    return Path(file_name)
