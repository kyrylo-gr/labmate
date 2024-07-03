"""This submodule contains functions that help to display content in IPython."""

import logging
import sys
from typing import Callable, List

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.WARNING)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)
logger.propagate = False


try:
    if "pytest" in sys.modules:
        raise ImportError

    import ipywidgets as widgets  # pylint: disable=W0611 # type: ignore
    from IPython.core import display  # type: ignore
    from IPython.core.display import HTML  # type: ignore

    display = display.display_functions.display

except ImportError:
    # For testing purposes every IPython function should have a simpler version.
    # pylint: disable=C0115, C0103, R0903

    def HTML(text):  # noqa: D103
        return text

    def display(text):  # noqa: D103
        logger.info(text)

    class widgets:  # noqa: D101
        class Button:  # noqa: D106
            func: str
            description: str

            def __init__(self, description: str):  # noqa: D107
                self.description = description

            def on_click(self, func: Callable):  # noqa: D102
                self.func = func.__name__

        class HBox:  # noqa: D106
            def __init__(self, lst: list) -> None:  # noqa: D107
                pass

        class VBox:  # noqa: D106
            def __init__(self, lst: list) -> None:  # noqa: D107
                pass

        class CoreWidget:  # noqa: D106
            pass

        class Layout:
            def __init__(self, *args, **kwargs) -> None:
                del args, kwargs

    # pylint: enable=C0115, C0103, R0903


def display_html(html):
    """Display the given str of html."""
    display(HTML(html))


def display_widgets(objs: List[widgets.CoreWidget]):
    """Display the given list of widgets in a HBox ."""
    button_row = widgets.HBox(objs)
    display(button_row)


def display_widgets_vertically(objs: List[widgets.CoreWidget], class_: str = ""):
    """Display the given list of widgets in a VBox ."""
    button_row = widgets.VBox(objs)
    if class_:
        button_row.add_class(class_)  # type: ignore
    display(button_row)
