from typing import TYPE_CHECKING, List, Protocol, TypeVar
from .. import display as lm_display
from ..display import windows_utils

if TYPE_CHECKING:
    from labmate.acquisition_notebook import AcquisitionAnalysisManager

_T = TypeVar("_T")


class WidgetProtocol(Protocol):
    def __init__(self, **kwargs):
        ...

    def create(self, **kwargs) -> "lm_display.buttons.DisplayingButton":
        ...


class BaseWidget:
    widget: "lm_display.buttons.DisplayingButton"


class CopyFilePathButton(BaseWidget):
    def __init__(self, level_up=3, **kwargs) -> None:
        del kwargs
        if level_up < 1:
            raise ValueError("level_up should be >= 1")
        self.level_up = level_up
        super().__init__()

    def create(self, aqm: "AcquisitionAnalysisManager", **kwargs):
        link = _create_file_link(aqm, self.level_up)
        self.widget = lm_display.buttons.copy_button("Copy url", link)

        return self.widget


class CopyFigButton(BaseWidget):
    def __init__(self, level_up=3, **kwargs) -> None:
        del kwargs
        if level_up < 1:
            raise ValueError("level_up should be >= 1")
        self.level_up = level_up
        super().__init__()

    def create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        del kwargs
        link = _create_file_link(aqm, self.level_up)

        def copy_fig():
            windows_utils.copy_fig(fig, text_to_copy=link)

        self.widget = lm_display.buttons.create_button(copy_fig, name="Copy fig")
        return self.widget


def _create_file_link(aqm: "AcquisitionAnalysisManager", level_up) -> str:
    link_name = aqm.current_filepath.basename
    link = "/".join(
        str(aqm.current_filepath.resolve().absolute()).replace("\\", "/").split("/")[-level_up:]
    ).replace(" ", "%20")
    link = f"[{link_name}](//kyrylo-gr.github.io/h5viewer/open?url={link})"
    return link


def display_widgets(objs: List["WidgetProtocol"], *args, **kwargs):
    widgets = [obj.create(*args, **kwargs) for obj in objs]
    lm_display.display_widgets(widgets)  # type: ignore
