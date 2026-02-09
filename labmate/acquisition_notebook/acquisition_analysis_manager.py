from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING, Any

from .. import display, utils
from ..acquisition import AcquisitionManager, AnalysisData
from ..logger import logger
from . import display_widget

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from dh5.path import Path

    from ..acquisition import FigureProtocol
    from ..acquisition.backend import AcquisitionBackend
    from ..acquisition.config_file import ConfigFile


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

_CallableWithNoArgs = Callable[[], Any]

CATCH_PRINT = True


class AcquisitionAnalysisManager(AcquisitionManager):
    """AcquisitionAnalysisManager.

    # Init
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

    _analysis_data: AnalysisData | None = None
    _analysis_cell_str = None
    _is_old_data = False
    _last_fig_name = None
    _default_config_files: tuple[str, ...] = ()
    _acquisition_started = 0
    _linting_external_vars = None
    _analysis_cell_prerun_hook: tuple[_CallableWithNoArgs, ...] | None = None
    _acquisition_cell_prerun_hook: tuple[_CallableWithNoArgs, ...] | None = None
    _connected_widgets: list["display_widget.WidgetProtocol"] | None = None

    def __init__(
        self,
        data_directory: str | Any | None = None,
        *,
        config_files: list[str] | None = None,
        save_files: bool = False,
        use_magic: bool = False,
        save_on_edit: bool = True,
        save_on_edit_analysis: bool | None = None,
        save_fig_inside_h5: bool = False,
        shell: Any = True,
        backend: AcquisitionBackend | Iterable[AcquisitionBackend] | None = None,
    ):
        """
        AcquisitionAnalysisManager.

        Args:
            data_directory:
                Path to data_directory. Should be explicitly set here or as environ parameter.
            config_files:
                List of paths to config files. Defaults to empty.
            save_files:
                True to additionally save config files and the cells to files. Defaults to False.
                So all information is saved inside the h5 file.
            use_magic:
                True to register the magic cells. Defaults to False.
            save_on_edit:
                True to save data for every change.
            save_on_edit_analysis:
                save_on_edit parameter for AnalysisManager i.e. data inside analysis_cell
            shell:
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
            from .acquisition_magic_class import (  # noqa: I001
                load_ipython_extension,
            )

            load_ipython_extension(aqm=self, shell=self.shell)

        if save_on_edit_analysis is None:
            save_on_edit_analysis = save_on_edit

        self._save_on_edit_analysis = save_on_edit_analysis
        self._save_fig_inside_h5 = save_fig_inside_h5

        self._logger = logger
        super().__init__(
            data_directory=str(data_directory),
            config_files=config_files,
            save_files=save_files,
            save_on_edit=save_on_edit,
            backend=backend,
        )

    @property
    def logger(self):
        return self._logger

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
        fig: FigureProtocol | None = None,
        name: str | int | None = None,
        extensions: str | None = None,
        **kwds,
    ) -> "AcquisitionAnalysisManager":
        """Save the figure as a file."""
        self.data.save_fig(fig=fig, name=name, extensions=extensions, **kwds)
        return self

    def save_analysis_cell(
        self,
        name: str | int | None = None,
        cell: str | "Literal['none']" | None = None,
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
        fig_or_name: FigureProtocol | str | int | None = None,
        /,
        *,
        fig: FigureProtocol | None = None,
        name: str | int | None = None,
        cell: str | None = None,
        **kwds,
    ) -> "AcquisitionAnalysisManager":
        if fig_or_name is not None:
            if isinstance(fig_or_name, (str, int)):
                name = name or fig_or_name
            else:
                fig = fig or fig_or_name

        self.save_fig_only(fig=fig, name=name, **kwds)
        self.save_analysis_cell(name=name, cell=cell)

        if self.current_acquisition is not None:
            self._schedule_backend_save(self.current_acquisition)

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
        acq_data[__key] = __value  # pylint: disable=E1137

    def save_acquisition(
        self,
        update_: bool = True,
        /,
        file_suffix: str | None = None,
        **kwds,
    ) -> "AcquisitionAnalysisManager":
        acquisition_finished = time.time()
        if not self._once_saved:
            additional_info: dict[str, Any] = {
                "acquisition_duration": acquisition_finished - self._acquisition_started,
                "logs": self.logger.getvalue(),
                "prints": self.logger.get_stdout(),
            }
            if self._default_config_files:
                additional_info.update({"default_config_files": self._default_config_files})
            kwds.update({"info": additional_info})

        super().save_acquisition(update_, file_suffix=file_suffix, **kwds)
        self._load_analysis_data()
        return self

    def _load_analysis_data(self, filepath: str | None = None):
        filepath = filepath or str(self.current_filepath)

        self._analysis_data = self.load_file(filepath)

        if self._save_on_edit_analysis is False:
            self._analysis_data.save()

        return self._analysis_data

    def load_file(self, filename) -> "AnalysisData":
        filename = self._get_full_filename(filename)
        if not os.path.exists(filename if filename.endswith(".h5") else filename + ".h5"):  # noqa: PTH110
            raise ValueError(f"File {filename} cannot be found")

        data = AnalysisData(
            filepath=filename,
            save_files=self._save_files,
            save_on_edit=self._save_on_edit_analysis,
            save_fig_inside_h5=self._save_fig_inside_h5,
            open_on_init=False,
        )

        if not data.get("useful", True):
            data.unlock_data("useful").update(**{"useful": True}).lock_data("useful")

        if self._default_config_files:
            data.set_default_config_files(self._default_config_files)

        return data

    def acquisition_cell(
        self,
        name: str,
        cell: str | None = None,
        prerun: _CallableWithNoArgs | list[_CallableWithNoArgs] | None = None,
        save_on_edit: bool | None = None,
        step: int = 1,
    ) -> "AcquisitionAnalysisManager":
        self._analysis_cell_str = None
        self._analysis_data = None
        self._is_old_data = False
        self._acquisition_started = time.time()

        cell = cell or get_current_cell(self.shell)
        if step == 1:
            self.logger.reset()
            self.new_acquisition(name=name, cell=cell, save_on_edit=save_on_edit)
        elif self._current_acquisition is None:
            raise ValueError("Acquisition should start from step 1")
        elif self._current_acquisition.current_step == step:
            raise ValueError(
                "This step was already run. Please run the next step or restart from step 1"
            )
        else:
            if self._current_acquisition.experiment_name != name:
                raise ValueError(
                    f"Current acquisition ('{self.current_experiment_name}') "
                    f"isn't the one expected ('{name}') for this acquisition. "
                    f"Possible solutions: run acquisition '{name}' with step 1; "
                    f"or change current acquisition name to '{self.current_experiment_name}'"
                )
            self._current_acquisition.current_step = step
            self._current_acquisition.set_cell(cell, step=step)
            self._current_acquisition.save_cell(cell, suffix=str(step))
            configs_modified = self._get_configs_last_modified()
            if configs_modified != self._configs_last_modified:
                raise ValueError(
                    "Config files were modified since the previous acquisition step. "
                    "Please rerun the acquisition from the first step."
                )
            self.logger.stdout_flush()

        self.logger.info(f"{step}:{self.current_filepath.basename}")  # pylint: disable=W1203

        if step == 1:
            utils.run_functions(self._acquisition_cell_prerun_hook)

        utils.run_functions(prerun)
        return self

    def analysis_cell(
        self,
        filename: str | Path | None = None,
        *,
        acquisition_name=None,
        cell: str | None = None,
        filepath: str | Path | None = None,
        prerun: _CallableWithNoArgs | list[_CallableWithNoArgs] | None = None,
    ) -> "AcquisitionAnalysisManager":
        self._analysis_cell_str = cell or get_current_cell(self.shell)
        if filename or filepath:  # getting old data
            self._is_old_data = True
            if self.shell is not None:
                from labmate.display.html_output import display_warning

                display_warning("Old data analysis")

            filename = str(filepath or self._get_full_filename(filename))  # type: ignore[arg-type]
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

        self.logger.info(os.path.basename(filename))  # noqa: PTH119

        if (
            (not self._is_old_data)
            and (self.shell is not None)
            and (
                "acquisition_cell(" in self.shell.last_execution_result.info.raw_cell  # type: ignore
                and not self.shell.last_execution_result.success  # type: ignore
            )
        ):
            raise ChildProcessError(
                "Last executed cell was probably an `acquisition_cell` and failed to run. "
                "Check if everything is ok and executive again"
            )

        full_h5 = filename + ".h5"

        if not os.path.exists(full_h5):  # noqa: PTH110
            backends = self._backend

            if backends is None:
                backend_list: list[Any] = []
            elif isinstance(backends, (list, tuple)):
                backend_list = list(backends)
            else:
                backend_list = [backends]

            for be in backend_list:
                ensure = getattr(be, "ensure_local_file", None)
                if ensure is None:
                    continue

                self.logger.info(
                    "File %s not found locally; asking backend %s to fetch it",
                    full_h5,
                    be.__class__.__name__,
                )
                try:
                    fetched = bool(ensure(full_h5))
                except Exception as exc:
                    self.logger.warning(
                        "Backend %s failed to fetch %s: %s",
                        be.__class__.__name__,
                        full_h5,
                        exc,
                    )
                    fetched = False

                if fetched and os.path.exists(full_h5):  # noqa: PTH110
                    self.logger.info(
                        "File %s fetched successfully by backend %s",
                        full_h5,
                        be.__class__.__name__,
                    )
                    break

        if os.path.exists(full_h5):  # noqa: PTH110
            self._load_analysis_data(filename)
        else:
            if self._is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self._analysis_data = None

        if cell is not None:
            self.save_analysis_cell(cell=cell)

        if (self._analysis_cell_str is not None) and (self._linting_external_vars is not None):
            from ..acquisition import custom_lint
            from ..utils import lint

            lint_result = lint.find_variables_from_code(
                self._analysis_cell_str,
                self._linting_external_vars,
                run_on_call=custom_lint.on_call_functions,
            )
            for var in lint_result.external_vars:
                self.logger.warning("External variable used inside the analysis code: %s", var)
            for error in lint_result.errors:
                self.logger.warning(error)

        utils.run_functions(self._analysis_cell_prerun_hook)
        utils.run_functions(prerun)
        return self

    def get_analysis_code(self, look_inside: bool = True) -> str:
        code = self.data.get_analysis_code(update_code=look_inside)

        if self.shell is not None:
            self.shell.set_next_input(code)  # type: ignore
        return code

    def _get_full_filename(self, filename: str | Path) -> str:
        if filename is None:
            raise ValueError("Filename cannot be None")

        filepath = utils.get_path_from_filename(filename)
        if isinstance(filepath, tuple):
            return os.path.join(self.data_directory, *filepath)  # noqa: PTH118
        return filepath

    def parse_config_file(self, config_file_name: str, /) -> "ConfigFile":
        return self.data.parse_config_file(config_file_name)

    def parse_config(self, config_files: tuple[str, ...] | None = None) -> "ConfigFile":
        return self.data.parse_config(config_files=config_files)

    @property
    def cfg(self) -> "ConfigFile":
        return self.data.cfg

    def parse_config_str(self, values: list[str], /, max_length: int | None = None) -> str:
        return self.data.parse_config_str(values, max_length=max_length)

    def linting(self, allowed_variables: "Iterable[str]" | None = None, init_file: str | None = None):
        from ..utils import lint

        allowed = set() if allowed_variables is None else set(allowed_variables)
        if init_file is not None:
            allowed.update(lint.find_variables_from_file(init_file)[0])
        self._linting_external_vars = allowed

    def set_default_config_files(self, config_files: str | tuple[str, ...] | list[str], /):
        self._default_config_files = (
            (config_files,) if isinstance(config_files, str) else tuple(config_files)
        )
        if self._analysis_data:
            self._analysis_data.set_default_config_files(self._default_config_files)

    def set_analysis_cell_prerun_hook(
        self,
        hook: _CallableWithNoArgs | list[_CallableWithNoArgs] | tuple[_CallableWithNoArgs, ...],
    ):
        self._analysis_cell_prerun_hook = tuple(hook) if isinstance(hook, (list, tuple)) else (hook,)

    def set_acquisition_cell_prerun_hook(
        self,
        hook: _CallableWithNoArgs | list[_CallableWithNoArgs] | tuple[_CallableWithNoArgs, ...],
    ):
        self._acquisition_cell_prerun_hook = tuple(hook) if isinstance(hook, (list, tuple)) else (hook,)

    def find_param_in_config(self, param: str) -> tuple[str, int] | None:
        for file in self._default_config_files:
            for line_no, line in enumerate(self.d["configs", file].split("\n")):
                if line.startswith(param):
                    return file, line_no + 1
        return None

    def display_param_link(
        self,
        params: str | list[str] | list[tuple[str, str]],
        after_text: str | None = None,
        title: str | None = None,
    ):
        if after_text is not None:
            if not isinstance(params, str):
                raise ValueError(
                    "Cannot use after_text with multiple params. "
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
                self.logger.warning("Parameter '%s' cannot be found in default config files.", param)
                continue

            file, line_no = res
            file = self._config_files_names_to_path.get(file, file)
            link = display.links.create_link(param_text, file, line_no, after_text)
            links += link + "<br/>"
        return display.display_html(links)

    def display_cfg_link(self, parameters: dict[str, Any], update_button: bool = False):
        from labmate.display import html_output

        links = []
        for param, value in parameters.items():
            param_eq = f"{param.strip()} = "
            res = self.find_param_in_config(param_eq)
            if res is None:
                self.logger.warning("Parameter '%s' cannot be found in default config files.", param)
                continue

            file, line_no = res
            file = self._config_files_names_to_path.get(file, file)

            def update_value(param, value):
                self.update_config_params_on_disk({param: value})

            buttons = (
                [display.buttons.create_button(update_value, param, value, name="Update")]
                if update_button
                else None
            )

            link = html_output.create_link_row(
                link_text=f"{param} = ",
                link_url=f"{file}:{line_no}",
                text=str(value),
                buttons=buttons,  # type: ignore
            )
            links.append(link)
        return display.display_widgets_vertically(links, class_="labmate-params")

    def update_config_params_on_disk(self, params: dict[str, Any]):
        for file in self.config_files:
            file = self._config_files_names_to_path.get(file, file)
            utils.file_read.update_file_variable(file, params)
        return self

    def connect_default_widget(
        self,
        objs: "display_widget.WidgetProtocol" | list["display_widget.WidgetProtocol"],
    ):
        if not isinstance(objs, (list, tuple)):
            objs = [objs]
        if self._connected_widgets is None:
            self._connected_widgets = []
        self._connected_widgets.extend(objs)


def get_current_cell(shell: Any) -> str | None:
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
