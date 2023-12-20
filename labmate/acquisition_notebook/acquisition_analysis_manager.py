from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    TYPE_CHECKING,
)
import os
import logging
import time
from ..acquisition import AcquisitionManager, AnalysisData
from .. import utils
from .. import display
from . import display_widget

if TYPE_CHECKING:
    from ..acquisition import FigureProtocol
    from ..acquisition.config_file import ConfigFile
    from dh5.path import Path


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

_CallableWithNoArgs = Callable[[], Any]


class AcquisitionAnalysisManager(AcquisitionManager):
    """AcquisitionAnalysisManager.

    # Init:
    ```
    aqm = AcquisitionAnalysisManager("tmp_data/", use_magic=False, save_files=False)
    aqm.set_config_file("configuration.py")
    ```
    # acquisition_cell:
    ```
    aqm.acquisition_cell('simple_sine')
    ...
    aqm.save_acquisition(x=x, y=y)
    ```

    # analysis_cell:
    ```
    aqm.analysis_cell()
    ...
    plt.plot(aqm.d.x, aqm.d.y)
    aqm.save_fig()
    ```

    """

    _analysis_data: Optional[AnalysisData] = None
    _analysis_cell_str = None
    _is_old_data = False
    _last_fig_name = None
    _default_config_files: Tuple[str, ...] = tuple()
    _acquisition_started = 0
    _linting_external_vars = None
    _analysis_cell_prerun_hook: Optional[Tuple[_CallableWithNoArgs, ...]] = None
    _acquisition_cell_prerun_hook: Optional[Tuple[_CallableWithNoArgs, ...]] = None
    _connected_widgets: Optional[List["display_widget.WidgetProtocol"]] = None

    def __init__(
        self,
        data_directory: Optional[Union[str, Any]] = None,
        *,
        config_files: Optional[List[str]] = None,
        save_files: bool = False,
        use_magic: bool = False,
        save_on_edit: bool = True,
        save_on_edit_analysis: Optional[bool] = None,
        save_fig_inside_h5: bool = False,
        shell: Any = True,
    ):
        """
        AcquisitionAnalysisManager.

        Args:
            data_directory (Optional[str], optional):
                Path to data_directory. Should be explicitly set here or as environ parameter.
            config_files (Optional[List[str]], optional):
                List of paths to config files. Defaults to empty.
            save_files (bool, optional):
                True to additionally save config files and the cells to files. Defaults to False.
                So all information is saved inside the h5 file.
            use_magic (bool, optional):
                True to register the magic cells. Defaults to False.
            save_on_edit (bool. Defaults to True):
                True to save data for every change.
            save_on_edit_analysis (bool. Defaults to same as save_on_edit):
                save_on_edit parameter for AnalysisManager i.e. data inside analysis_cell
            shell (InteractiveShell | None, optional. Defaults to True):
                could be provided or explicitly set to None. Defaults to get_ipython().
        """
        if shell is False or shell is True:  # behavior by default shell
            try:
                from IPython.core.getipython import get_ipython

                self.shell = get_ipython()
            except ImportError:
                self.shell = None
        else:  # if any shell is provided. even None
            self.shell = shell

        if use_magic:
            from .acquisition_magic_class import load_ipython_extension

            load_ipython_extension(aqm=self, shell=self.shell)

        if save_on_edit_analysis is None:
            save_on_edit_analysis = save_on_edit

        self._save_on_edit_analysis = save_on_edit_analysis
        self._save_fig_inside_h5 = save_fig_inside_h5

        super().__init__(
            data_directory=str(data_directory),
            config_files=config_files,
            save_files=save_files,
            save_on_edit=save_on_edit,
        )

    @property
    def current_acquisition(self):
        """Return current acquisition if it's not an old data analyses."""
        if self._is_old_data:
            return None
        return super().current_acquisition

    @property
    def current_analysis(self):
        """Return the current analysis. Class where you cannot change existed keys."""
        return self._analysis_data

    @property
    def data(self):
        """Same as current_analysis."""
        if self._analysis_data is None:
            raise ValueError("No data set")
        return self._analysis_data

    @property
    def d(self):  # pylint: disable=invalid-name
        """Shorter alias for data."""
        return self.data

    def save_fig_only(
        self,
        fig: Optional["FigureProtocol"] = None,
        name: Optional[Union[str, int]] = None,
        extensions: Optional[str] = None,
        **kwds,
    ) -> "AcquisitionAnalysisManager":
        """Save the figure as a file.

        Args:
            fig (Figure, optional): Figure that should be saved. Figure could be any class with
             function save_fig implemented. By default gets plt.gcf().
            name (str, optional): Name of the fig. It's a suffix that will be added to the filename. Defaults to None.
            extensions(str, optional): Extensions of the file. Defaults to `pdf`.
            tight_layout(bool, optional): True to call fig.tight_layout(). Defaults to True.

        Raises:
            ValueError: if analysis_data is not loaded

        Return:
            self
        """
        self.data.save_fig(fig=fig, name=name, extensions=extensions, **kwds)
        return self

    def save_analysis_cell(
        self,
        name: Optional[Union[str, int]] = None,
        cell: Optional[Union[str, Literal["none"]]] = None,
    ) -> "AcquisitionAnalysisManager":
        if name is None:
            name = self.data.figure_last_name

        if name is not None:
            name = str(name)

        cell = cell or self._analysis_cell_str

        self.data.save_analysis_cell(code=cell, code_name=name)

        return self

    def save_fig(
        self,
        fig_or_name: Optional[Union["FigureProtocol", str, int]] = None,
        /,
        *,
        fig: Optional["FigureProtocol"] = None,
        name: Optional[Union[str, int]] = None,
        cell: Optional[str] = None,
        **kwds,
    ) -> "AcquisitionAnalysisManager":
        if fig_or_name is not None:
            if isinstance(fig_or_name, (str, int)):
                name = name or fig_or_name
            else:
                fig = fig or fig_or_name
        self.save_fig_only(fig=fig, name=name, **kwds)
        self.save_analysis_cell(name=name, cell=cell)
        if self._connected_widgets:
            display_widget.display_widgets(
                self._connected_widgets,
                aqm=self,
                fig=fig,
            )
        return self

    def __setitem__(self, __key: str, __value: Any) -> None:
        if self._analysis_data is not None:
            raise ValueError(
                "This is the way to save acquisition data. But analysis data was loaded. "
                "So you possibly run it outside of acquisition_cell"
            )
        acq_data = self.current_acquisition
        if acq_data is None:
            raise ValueError(
                "Cannot save data to acquisition as current acquisition is None."
                "Possibly because you have never run `acquisition_cell(..)` or it's an old data"
            )
        acq_data[__key] = __value

    def save_acquisition(self, **kwds) -> "AcquisitionAnalysisManager":
        acquisition_finished = time.time()
        additional_info: Dict[str, Any] = {
            "acquisition_duration": acquisition_finished - self._acquisition_started
        }
        if self._default_config_files:
            additional_info.update({"default_config_files": self._default_config_files})

        kwds.update({"info": additional_info})

        super().save_acquisition(**kwds)
        self._load_analysis_data()
        return self

    def _load_analysis_data(self, filepath: Optional[str] = None):
        filepath = filepath or str(self.current_filepath)

        self._analysis_data = self.load_file(filepath)

        if self._save_on_edit_analysis is False:
            self._analysis_data.save()

        return self._analysis_data

    def load_file(self, filename) -> "AnalysisData":
        filename = self._get_full_filename(filename)
        if not os.path.exists(filename if filename.endswith(".h5") else filename + ".h5"):
            raise ValueError(f"File {filename} cannot be found")

        data = AnalysisData(
            filepath=filename,
            save_files=self._save_files,
            save_on_edit=self._save_on_edit_analysis,
            save_fig_inside_h5=self._save_fig_inside_h5,
        )

        if not data.get("useful", True):
            data.unlock_data("useful").update(**{"useful": True}).lock_data("useful")

        if self._default_config_files:
            data.set_default_config_files(self._default_config_files)

        return data

    def acquisition_cell(
        self,
        name: str,
        cell: Optional[str] = None,
        prerun: Optional[Union[_CallableWithNoArgs, List[_CallableWithNoArgs]]] = None,
        save_on_edit: Optional[bool] = None,
    ) -> "AcquisitionAnalysisManager":
        self._analysis_cell_str = None
        self._analysis_data = None
        self._is_old_data = False
        self._acquisition_started = time.time()

        cell = cell or get_current_cell(self.shell)

        self.new_acquisition(name=name, cell=cell, save_on_edit=save_on_edit)

        logger.info(self.current_filepath.basename)

        utils.run_functions(self._acquisition_cell_prerun_hook)
        utils.run_functions(prerun)

        return self

    def analysis_cell(
        self,
        filename: Optional[Union[str, "Path"]] = None,
        *,
        acquisition_name=None,
        cell: Optional[str] = None,
        filepath: Optional[Union[str, "Path"]] = None,
        prerun: Optional[Union[_CallableWithNoArgs, List[_CallableWithNoArgs]]] = None,
    ) -> "AcquisitionAnalysisManager":
        # self.shell.get_local_scope(1)['result'].info.raw_cell  # type: ignore

        self._analysis_cell_str = cell or get_current_cell(self.shell)
        if filename or filepath:  # getting old data
            self._is_old_data = True
            if self.shell is not None:
                from labmate.display.html_output import display_warning

                display_warning("Old data analysis")

            filename = str(filepath or self._get_full_filename(filename))  # type: ignore
            filename = (filename.rsplit(".h5", 1)[0]) if filename.endswith(".h5") else filename

        else:
            self._is_old_data = False
            if acquisition_name is not None:
                import re

                if (
                    len(acquisition_name) == 0
                    or (
                        acquisition_name[0] != r"^"
                        and acquisition_name != self.current_experiment_name
                    )
                    or (
                        acquisition_name[0] == r"^"
                        and re.match(acquisition_name, self.current_experiment_name) is None
                    )
                ):
                    raise ValueError(
                        f"Current acquisition ('{self.current_experiment_name}') "
                        f"isn't the one expected ('{acquisition_name}') for this analysis"
                    )

            filename = str(self.current_filepath)  # without h5
        logger.info(os.path.basename(filename))

        if (
            (not self._is_old_data)
            and (self.shell is not None)
            and (
                "acquisition_cell(" in self.shell.last_execution_result.info.raw_cell
                and not self.shell.last_execution_result.success
            )
        ):
            raise ChildProcessError(
                "Last executed cell was probably an `acquisition_cell` and failed to run. "
                "Check if everything is ok and executive again"
            )

        if os.path.exists(filename + ".h5"):
            self._load_analysis_data(filename)
        else:
            if self._is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self._analysis_data = None

        if cell is not None:
            self.save_analysis_cell(cell=cell)

        if (self._analysis_cell_str is not None) and (self._linting_external_vars is not None):
            from ..utils import lint
            from ..acquisition import custom_lint

            # _, external_vars = lint.find_variables_from_code(
            #     self._analysis_cell_str, self._linting_external_vars
            # )
            lint_result = lint.find_variables_from_code(
                self._analysis_cell_str,
                self._linting_external_vars,
                run_on_call=custom_lint.on_call_functions,
            )
            for var in lint_result.external_vars:
                logger.warning("External variable used inside the analysis code: %s", var)
            for error in lint_result.errors:
                logger.warning(error)
        utils.run_functions(self._analysis_cell_prerun_hook)
        utils.run_functions(prerun)

        return self

    def get_analysis_code(self, look_inside: bool = True) -> str:
        code = self.data.get_analysis_code(update_code=look_inside)

        if self.shell is not None:
            self.shell.set_next_input(code)  # type: ignore
        return code

    # def open_analysis_fig(self) -> List[FigureProtocol]:
    #     return self.data.open_fig()

    def _get_full_filename(self, filename: Union[str, "Path"]) -> str:
        if filename is None:
            raise ValueError("Filename cannot be None")

        filepath = utils.get_path_from_filename(filename)
        if isinstance(filepath, tuple):
            return os.path.join(self.data_directory, *filepath)
        return filepath

    def parse_config_file(self, config_file_name: str, /) -> "ConfigFile":
        return self.data.parse_config_file(config_file_name)

    def parse_config(self, config_files: Optional[Tuple[str, ...]] = None) -> "ConfigFile":
        return self.data.parse_config(config_files=config_files)

    @property
    def cfg(self) -> "ConfigFile":
        return self.data.cfg

    def parse_config_str(
        self,
        values: List[str],
        /,
        max_length: Optional[int] = None,
    ) -> str:
        return self.data.parse_config_str(values, max_length=max_length)

    def linting(
        self, allowed_variables: Optional[Iterable[str]] = None, init_file: Optional[str] = None
    ):
        from ..utils import lint

        allowed_variables = set() if allowed_variables is None else set(allowed_variables)
        if init_file is not None:
            allowed_variables.update(lint.find_variables_from_file(init_file)[0])
        self._linting_external_vars = allowed_variables

    def set_default_config_files(self, config_files: Union[str, Tuple[str, ...], List[str]], /):
        self._default_config_files = (
            (config_files,) if isinstance(config_files, str) else tuple(config_files)
        )
        if self._analysis_data:
            self._analysis_data.set_default_config_files(self._default_config_files)

    def set_analysis_cell_prerun_hook(
        self,
        hook: Union[
            _CallableWithNoArgs, List[_CallableWithNoArgs], Tuple[_CallableWithNoArgs, ...]
        ],
    ):
        self._analysis_cell_prerun_hook = (
            tuple(hook) if isinstance(hook, (list, tuple)) else (hook,)
        )

    def set_acquisition_cell_prerun_hook(
        self,
        hook: Union[
            _CallableWithNoArgs, List[_CallableWithNoArgs], Tuple[_CallableWithNoArgs, ...]
        ],
    ):
        self._acquisition_cell_prerun_hook = (
            tuple(hook) if isinstance(hook, (list, tuple)) else (hook,)
        )

    def find_param_in_config(self, param: str) -> Optional[Tuple[str, int]]:
        for file in self._default_config_files:
            for line_no, line in enumerate(self.d["configs", file].split("\n")):
                if line.startswith(param):
                    return file, line_no + 1
        return None

    def display_param_link(
        self,
        params: Union[str, List[str], List[Tuple[str, str]]],
        after_text: Optional[str] = None,
        title: Optional[str] = None,
    ):
        if after_text is not None:
            if not isinstance(params, str):
                raise ValueError(
                    "Cannot use after_text with multiple params"
                    "Use params=[(param, after_text), ...] instead."
                )
            return self.display_param_link(params=[(params, after_text)], title=title)

        if isinstance(params, str):
            params = [params]

        links = "" if not title else title + "<br/>"
        for param in params:
            if not isinstance(param, str):
                param_text, after_text = param
            else:
                param_text, after_text = param, None

            res = self.find_param_in_config(param_text)
            if res is None:
                logger.warning("Parameter '%s' cannot be found in default config files.", param)
                continue
            file, line_no = res
            link = display.links.create_link(param_text, file, line_no, after_text)
            links += link + "<br/>"
        return display.display_html(links)

    def connect_default_widget(
        self,
        objs: Union["display_widget.WidgetProtocol", List["display_widget.WidgetProtocol"]],
    ):
        if not isinstance(objs, (list, tuple)):
            objs = [objs]
        if self._connected_widgets is None:
            self._connected_widgets = []
        self._connected_widgets.extend(objs)


def get_current_cell(shell: Any) -> Optional[str]:
    if shell is None:
        return None
    return shell.get_parent()["content"]["code"]


class AcquisitionAnalysisManagerDataOnly:
    def __init__(self, *args, **kwds):
        self.aqm = AcquisitionAnalysisManager(*args, **kwds)

    def analysis_cell(self, *args, **kwds):
        return self.aqm.analysis_cell(*args, **kwds)

    @property
    def current_acquisition(self):
        return None

    @property
    def current_analysis(self):
        return self.aqm.current_analysis

    @property
    def data(self):
        return self.aqm.data

    @property
    def d(self):  # pylint: disable=invalid-name
        return self.data
