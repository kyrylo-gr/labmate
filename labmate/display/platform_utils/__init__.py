"""This module contains different function that are specific to the operating system.

The goal it to have a single interface for all such functions.
"""
import os
import sys
import subprocess

if os.name == "nt":
    from . import windows_utils as current_utils


def copy_text(text: str) -> None:
    """Copy the given text to the clipboard."""
    import pyperclip

    pyperclip.copy(text)


def copy_fig(fig=None, format_=None, text_to_copy=None, **kwargs):
    """Copy mpl.Figure to clipboard."""
    if os.name == "nt":
        return current_utils.copy_fig(
            fig=fig,
            format_=format_,
            text_to_copy=text_to_copy,
            **kwargs,
        )
    raise NotImplementedError()


def open_finder(path):
    """Open finder with specified path selected."""
    if sys.platform == "win32":
        path = path.replace("/", "\\")
        subprocess.run(["explorer", "/select,", path], shell=False, check=False)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", path])
    else:
        subprocess.Popen(["nautilus", "--select", path])


if "pytest" in sys.modules:
    pass
