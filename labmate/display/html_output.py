"""This submodule contains functions that create different html."""


def display_warning(text: str, logger=None):
    """Display div warning block with `text`.

    If IPython is not installed, log into `logger` at warning level.
    If `logger` is not provided, print the `text`.
    """
    from .main import display_html

    try:
        html = f"""<div style="
        background-color:#ec7413; padding: .5em; text-align:center"
        >{text}</div>"""

        display_html(str(html))  # type: ignore

    except ImportError:
        if logger is not None:
            logger.warning(text)
        else:
            print(text)
