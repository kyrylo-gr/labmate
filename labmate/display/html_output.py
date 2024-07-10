"""This submodule contains functions that create different html."""

from typing import List, Optional

from .main import widgets


def display_warning(text: str):
    """Display div warning block with `text`.

    If IPython is not installed, log into logger from display submodule at warning level.
    """
    from .main import display_html

    html = f"""<div style="
    background-color:#ec7413; padding: .5em; text-align:center"
    >{text}</div>"""

    display_html(str(html))


def create_link_row(
    link_text: str,
    link_url: str,
    text: str,
    buttons: Optional[List[widgets.Button]] = None,
):

    # Create the HTML link with custom styling
    link_widget = widgets.HTML(
        value=f'<a href="{link_url}" target="_blank" onclick="return false;">{link_text}</a>'
    )

    # Create the text with custom styling
    text_widget = widgets.HTML(
        value=f'<span style="padding: 0 10px;">{text}</span>',
        layout=widgets.Layout(background_color="transparent"),
    )

    custom_css = """
    <style>
    .cell-output-ipywidget-background:has(.labmate-params) {
        background: transparent !important;
    }
    .labmate-params, .labmate-params * {
        color: inherit !important;
    }
    .labmate-params a {
        text-decoration: underline;
        color: blue;

    }

    </style>
    """
    buttons = buttons or []

    hbox = widgets.HBox(
        [widgets.HTML(custom_css), link_widget, text_widget, *buttons],
        layout=widgets.Layout(background_color="transparent"),
    )
    hbox.add_class("labmate-params")
    return hbox
