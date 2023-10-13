from typing import Optional


def create_link(
    link_text: str,
    file: str,
    line_no: int,
    after_text: Optional[str] = None,
):
    after_text = after_text if after_text else ""
    return (
        f"<a href='{file}:{line_no}' target='_blank' style='margin: 0!; padding:0!;'>"
        f"{link_text}</a> {after_text}"
    )
