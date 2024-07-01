# flake8: noqa: F401
import importlib
from typing import TYPE_CHECKING, Any

from .main import display, display_html, display_widgets, logger

__all__ = ["links", "buttons", "logger"]


class _LazyModule:
    def __init__(self, name):
        self.__module = None
        self.__name = name

    def __getattr__(self, name):
        if self.__module is None:
            self.__module = importlib.import_module(
                f".{self.__name}", package=__package__
            )
        return getattr(self.__module, name)

    # @property
    # def module(self):
    #     if self.__module is None:
    #         self.__module = importlib.import_module(f".{self.__name}", package=__package__)
    #     return self.__module


links = _LazyModule("links")
buttons = _LazyModule("buttons")


if TYPE_CHECKING:
    from . import buttons, links
