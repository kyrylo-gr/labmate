"""This submodule contains functions that create different html."""


def display_warning(text: str):
    """Display div warning block with `text`.

    If IPython is not installed, log into logger from display submodule at warning level.
    """
    from .main import display_html

    html = f"""<div style="
    background-color:#ec7413; padding: .5em; text-align:center"
    >{text}</div>"""

    display_html(str(html))
