"""This submodule contains functions that create html links."""

from typing import Optional


def create_link(
    link_text: str,
    file: str,
    line_no: int,
    after_text: Optional[str] = None,
) -> str:
    """Create HTML link to a given file at given line_no.

    Args:
        link_text (str): Text of html link.
        file (str): File to link to.
        line_no (int): Line number to link to.
        after_text (Optional[str], optional): Text to put after the link. Defaults to nothing.

    Returns:
        html <a> link.
    """
    after_text = after_text if after_text else ""
    return (
        f"<a href='{file}:{line_no}' target='_blank' style='margin: 0!; padding:0!;'>"
        f"{link_text}</a> {after_text}"
    )
