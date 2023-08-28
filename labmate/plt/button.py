import ipywidgets as widgets
from IPython.core import display

display = display.display_functions.display


def create_button(func, *args, **kwargs):
    """Create a button with name of the function and run function onclick."""
    name = func.__name__.replace('_', ' ')
    button = widgets.Button(description=name)

    def on_button_click(_):
        func(*args, **kwargs)

    button.on_click(on_button_click)
    return button


def display_button(button):
    display(button)
    display(button)


def create_and_display_button(func, *args, **kwargs):
    button = create_button(func, *args, **kwargs)
    display_button(button)
    return button
