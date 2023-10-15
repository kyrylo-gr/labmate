import logging
import sys
from typing import Callable, List


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


try:
    if "pytest" in sys.modules:
        raise ImportError
    from IPython.core.display import HTML  # type: ignore
    from IPython.core import display  # type: ignore
    import ipywidgets as widgets  # pylint: disable=W0611 # type: ignore

    display = display.display_functions.display

except ImportError:

    def HTML(text):
        return text

    def display(text):
        logger.info(text)

    class widgets:
        class Button:
            func: str
            description: str

            def __init__(self, description: str):
                self.description = description

            def on_click(self, func: Callable):
                self.func = func.__name__

        class HBox:
            def __init__(self, lst: list) -> None:
                pass

        class CoreWidget:
            pass


def display_html(html):
    display(HTML(html))


def display_widgets(objs: List[widgets.CoreWidget]):
    button_row = widgets.HBox(objs)
    display(button_row)
