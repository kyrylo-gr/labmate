# flake8: noqa: F401
from typing import Any, TYPE_CHECKING
import importlib
from .__main__ import display_html, display, logger

__all__ = ["links", "buttons", "logger"]


class _LazyModule:
    def __init__(self, name):
        self.__module = None
        self.__name = name

    def __getattr__(self, name):
        if self.__module is None:
            self.__module = importlib.import_module(f".{self.__name}", package=__package__)
        # return self.__module.__getattr__(name)
        return getattr(self.__module, name)


links = _LazyModule("links")
buttons = _LazyModule("buttons")


if TYPE_CHECKING:
    from . import links
