import pathlib
import os


class Path(type(pathlib.Path())):
    """Make pathlib.Path better"""

    def __add__(self, other: str):
        """Sums 2 str"""
        if not isinstance(other, str):
            other = str(other)
        return type(self)(self.as_posix() + other)

    def makedirs(self, mode=0o777, exist_ok=False):
        if not os.path.exists(self):
            os.makedirs(self, mode=mode, exist_ok=exist_ok)
        return self
