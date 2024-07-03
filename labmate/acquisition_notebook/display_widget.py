import os
from typing import TYPE_CHECKING, List, Optional, Protocol, TypeVar

from .. import display as lm_display
from ..display import platform_utils

if TYPE_CHECKING:
    from labmate.acquisition_notebook import AcquisitionAnalysisManager

_T = TypeVar("_T")


def _get_filepath(aqm: "AcquisitionAnalysisManager") -> Optional[str]:
    filepath = aqm.current_analysis or aqm.current_acquisition
    return filepath.filepath if filepath else None


def _create_file_link(aqm: "AcquisitionAnalysisManager", level_up) -> str:
    filepath = _get_filepath(aqm)
    if filepath is None:
        return ""
    link_name = os.path.basename(filepath)
    link = "/".join(
        os.path.abspath(filepath).replace("\\", "/").split("/")[-level_up:]
    ).replace(" ", "%20")
    link = f"[{link_name}](//kyrylo-gr.github.io/h5viewer/open?url={link})"
    return link


def display_widgets(objs: List["WidgetProtocol"], *args, **kwargs):
    """Create (with *args, **kwargs) and display a list of widgets."""
    widgets = [obj.create(*args, **kwargs) for obj in objs]
    lm_display.display_widgets(widgets)  # type: ignore


class WidgetProtocol(Protocol):
    """Protocol for widgets that can be displayed with AcquisitionAnalysisManager.

    It could have `__init__` method with custom keywords and it should
    have `create` method that returns ipywidgets.widget that can be
    displayed with IPython.core.display.display_functions.display.

    """

    def __init__(self, **kwargs):
        """Any custom init method."""

    def create(self, **kwargs) -> "lm_display.buttons.DisplayingButton":
        """Create ipywidgets.widget method.

        The following arguments will be provided by AcquisitionAnalysisManager
        during widget creation.

        Args:
            aqm (AcquisitionAnalysisManager): current AcquisitionAnalysisManager instance.
            fig (mpl.Figure, optional): Figure of current analysis if such exist.

        Returns:
            ipywidgets.widget that can be displayed using
                IPython.core.display.display_functions.display
        """
        ...  # pylint: disable=W2301


class BaseWidget:
    """Base widget class. Every other widget should inherit from it."""

    widget: "lm_display.buttons.DisplayingButton"

    def __init__(self, **kwargs):
        """Init method for widget.

        For BaseWidget it does nothing.
        """

    def create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        """Create a widget from ipywidgets.

        Args:
            aqm (AcquisitionAnalysisManager): current AcquisitionAnalysisManager instance.
            fig (mpl.Figure, optional): Figure to work with. Not every widget needs a figure
                provided. Defaults to None.

        Returns:
            ipywidgets.widget
        """
        return self._create(aqm=aqm, fig=fig, **kwargs)

    # @abc.abstractmethod
    def _create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        raise NotImplementedError("This method is not implemented for the base class.")


class CopyFileURLPathButton(BaseWidget):
    """Create button to copy file path to clipboard.

    Examples:
        >>> from labmate.acquisition_notebook.display_widget import CopyFilePathButton
        >>> aqm = AcquisitionAnalysisManager()
        >>> aqm.connect_default_widget(CopyFilePathButton())
        Now every time you run aqm.save_fig(), button will appear in the output cell.

        Or you can do it just ones:
        >>> aqm.save_fig(widgets=CopyFilePathButton())

    """

    def __init__(self, level_up=3, **kwargs) -> None:
        """Create button instance.

        Args:
            level_up (int, optional): number of parent directory to include into path as paths are
                relative. Defaults to 3.
        """
        del kwargs
        if level_up < 1:
            raise ValueError("level_up should be >= 1")
        self.level_up = level_up
        super().__init__()

    def _create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        del fig, kwargs
        link = _create_file_link(aqm, self.level_up)
        self.widget = lm_display.buttons.copy_button("Copy url", link)

        return self.widget


class CopyFigButton(BaseWidget):
    """Create button to copy fig to clipboard.

    Examples:
        >>> from labmate.acquisition_notebook.display_widget import CopyFigButton
        >>> aqm = AcquisitionAnalysisManager()
        >>> aqm.connect_default_widget(CopyFigButton())
        Now every time you run aqm.save_fig(), button will appear in the output cell.

        Or you can do it just ones:
        >>> aqm.save_fig(widgets=CopyFigButton())

    """

    def __init__(self, level_up=3, **kwargs) -> None:
        """Create button instance.

        Args:
            level_up (int, optional): number of parent directory to include into path as paths are
                relative. Defaults to 3.
        """
        del kwargs
        if level_up < 1:
            raise ValueError("level_up should be >= 1")
        self.level_up = level_up
        super().__init__()

    def _create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        del kwargs
        link = _create_file_link(aqm, self.level_up)

        def copy_fig():
            platform_utils.copy_fig(fig, text_to_copy=link)

        self.widget = lm_display.buttons.create_button(copy_fig, name="Copy fig")
        return self.widget


class OpenFinderButton(BaseWidget):
    """Create button to open file in finder/explorer.

    Examples:
        >>> from labmate.acquisition_notebook.display_widget import OpenFinderButton
        >>> aqm = AcquisitionAnalysisManager()
        >>> aqm.connect_default_widget(OpenFinderButton())
        Now every time you run aqm.save_fig(), button will appear in the output cell.

        Or you can do it just ones:
        >>> aqm.save_fig(widgets=OpenFinderButton())

    """

    def __init__(self, level_up=3, **kwargs) -> None:
        del kwargs

        super().__init__()

    def _create(self, aqm: "AcquisitionAnalysisManager", fig=None, **kwargs):
        del kwargs
        filepath = _get_filepath(aqm)
        if filepath is None:
            return None

        import subprocess
        import sys

        def open_finder():
            path = os.path.abspath(filepath) + ".h5"
            if sys.platform == "win32":
                path = path.replace("/", "\\")
                subprocess.run(["explorer", "/select,", path], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", os.path.dirname(path)])
            else:
                subprocess.Popen(["nautilus", "--select", os.path.dirname(path)])

        self.widget = lm_display.buttons.create_button(open_finder, name="Open finder")
        return self.widget
