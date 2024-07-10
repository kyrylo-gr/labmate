"""This submodule contains functions that create Button widgets."""

from typing import TypeVar

from .main import display, widgets

# from functools import wraps
# def add_display_method(func):
#     """If a function changes the data it should be saved.
#     It's a wrapper for such function.
#     """

#     @wraps(func)
#     def wrapper(self, *args, **kwargs):
#         res = func(self, *args, **kwargs)

#         def display_self():
#             display_button(res)

#         res.display = display_self
#         return res

#     return wrapper


class DisplayingButton(widgets.Button):
    """Button widget that can be displayed with IPython.core.display.display_functions.display."""

    # def display(self) -> "DisplayingButton":
    #     return self


_T = TypeVar("_T")


# @add_display_method
def create_button(func, *args, name=None, **kwargs) -> "DisplayingButton":
    """Create a button widget that calls the given function when clicked.

    Args:
        func (callable): The function to call when the button is clicked.
        *args: Positional arguments to pass to the function.
        name (str, optional): The name to display on the button.
         Defaults to the function name with underscores replaced by spaces.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        A Button widget that calls the given function when clicked.

    Example:
    ```
    def abc(param1, param2=2):
        print(param1, param2)

    # Create button with the same name as function
    button = create_button(abc, param1=1)

    # Create button with given name
    button = create_button(abc, name="custom_name", param1=1)

    # All *arg and **kwargs are passed to the function.
    # Name kwarg is reserved for the button name and should goes after *arg.
    # This button will run abc(1, param2=4) on click
    button = create_button(abc, 1, name="custom_name", param2=4)

    ```
    """
    name = name or func.__name__.replace("_", " ")
    button: DisplayingButton = widgets.Button(description=name)  # type: ignore

    def on_button_click(_):
        func(*args, **kwargs)

    button.style.button_color = "transparent"  # type: ignore

    button.on_click(on_button_click)
    return button


def display_button(button: _T) -> _T:
    """Display a button widget and return itself."""
    # For unknown reasons display method with button should be call ed twice.
    display(button)
    return button


# @add_display_method
def copy_button(name, text) -> "DisplayingButton":
    """Create a button widget that copies the given text to the clipboard.

    Args:
        name (str): The name to display on the button.
        text (str): The text to copy to the clipboard.

    Returns:
        A Button widget that copies the given text to the clipboard when clicked.
    """
    from .platform_utils import copy_text

    return create_button(copy_text, text, name=name)
