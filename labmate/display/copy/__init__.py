# flake8: noqa: F401
import os
import pyperclip


def copy_text(text: str) -> None:
    """Copy the given text to the clipboard."""
    pyperclip.copy(text)
