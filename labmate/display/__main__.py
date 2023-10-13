import logging
import sys


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

    display = display.display_functions.display
except ImportError:

    def HTML(text):
        return text

    def display(text):
        logger.info(text)


def display_html(html):
    display(HTML(html))
