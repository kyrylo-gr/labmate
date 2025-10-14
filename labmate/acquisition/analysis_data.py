"""AnalysisData class."""

import json
import os
from typing import List, Literal, Optional, Protocol, Tuple, TypedDict, TypeVar, Union

from dh5 import DH5
from dh5.path import Path

from .. import utils
from ..logger import logger
from .analysis_loop import AnalysisLoop
from .config_file import ConfigFile

_T = TypeVar("_T", bound="AnalysisData")


class FigureProtocol(Protocol):
    """mpl.Figure protocol that has only `savefig` method."""

    def savefig(self, fname, **kwds):
        """Save the figure to a file."""


class PdfMetadataDict(TypedDict, total=False):
    """Metadata for the pdf file."""

    Subject: Union[str, dict]
    Keywords: Union[str, dict]


class AnalysisData(DH5):
    """A subclass of DH5 that provides additional functionality for analyzing data.

    This class opens a provided file and locks all the data. It means that
    you can add new keys and read old one, but cannot change old keys.

    This class allows to save figure at the under the same filename with suffix.
    For this use `save_fig` method.

    This class allows to save the code that was run to generate during analysis.
    If a `cell` was provided during init, it will save it to the h5 file under `analysis_cell` key.
    You can also save it to a `ANALYSIS_CELL.py` in the same directory, if `save_files` is True.
    Additionally, there is always possible to not provide `cell` on init, but save it afterwards
    with `save_analysis_cell` method.

    Args:
        filepath (Union[str, Path]): The path to the file to open.
        cell (Optional[str]): The cell to save to the h5 file and `_ANALYSIS_CELL.py` file.
        save_files (bool): Whether to save files.
        save_on_edit (bool): Whether to save on edit.
        save_fig_inside_h5 (bool): Whether to save the figure inside the h5 file.

    Examples:
        >>> DH5(PATH, 'w').update(x=5).save() # create some data

        >>> data = AnalysisData(filepath) # open this data.

        >>> data.x # You can access old data
        5

        >>> data.x = 1 # But cannot change it.
        ReadOnlyKeyError: "Cannot set a read-only key 'x'."

        >>> data['y'] = [1,2,3] # Nevertheless, you can add more data

        >>> # If you really want to change old data, you can unlock it. And even lock it again.
        >>> data.unlock_data('x').update(x=3).lock_data('x')

    """

    _figure_last_name = None
    _figure_saved = False
    _fig_index = 0
    _default_parse_config_str_max_length = 60

    def __init__(
        self,
        filepath: Union[str, Path],
        cell: Optional[str] = "none",
        save_files: bool = False,
        save_on_edit: bool = True,
        save_fig_inside_h5: bool = False,
        save_interactive_fig: bool = False,
        open_on_init: Optional[bool] = None,
    ):
        """Load data from a filepath and lock it to prevent any changes.

        Args:
            filepath (Union[str, Path]): The path to the file to open.
            cell (Optional[str]): The analysis code. Defaults to "none". If None is given,
                then logger.warning is raised.
            save_files (bool): Whether to save code additionally into a file in the same directory.
            save_on_edit (bool): Whether to save as soon as any changes are made.
            save_fig_inside_h5 (bool): Whether to save the figure inside the h5 file instead of
                a file in the same directory. Default to False, i.e. creates a separate image file.
        """
        if filepath is None:
            raise ValueError("You must specify filepath")
        filepath = str(filepath)
        filepath = filepath if filepath.endswith(".h5") else filepath + ".h5"

        if not os.path.exists(filepath):
            raise ValueError(f"File '{filepath}' does not exist.")

        super().__init__(
            filepath=filepath,
            overwrite=False,
            read_only=False,
            save_on_edit=save_on_edit,
            open_on_init=open_on_init,
        )

        self.lock_data()

        self._save_files = save_files
        self._save_fig_inside_h5 = save_fig_inside_h5
        self._save_interactive_fig = save_interactive_fig

        self._default_config_files: Tuple[str, ...] = tuple()
        if "info" in self and "default_config_files" in self["info"]:
            self._default_config_files = tuple(self["info"]["default_config_files"])

        self._reset_attrs()

        for key, value in self.items():
            if isinstance(value, dict) and value.get("__loop_shape__") is not None:
                self._update({key: AnalysisLoop(value)})

        self._analysis_cell = cell

        self.save_analysis_cell()

    def _reset_attrs(self):
        self._fig_index = 0
        self._figure_saved = False
        self._parsed_configs = {}

    def save_analysis_cell(
        self: _T,
        code: Optional[Union[str, Literal["none"]]] = None,
        code_name: Optional[str] = None,
    ) -> _T:
        """Save the analysis cell to the h5 file and optionally to a separate file.

        Args:
            code (str | Literal["none"], optional): The analysis cell to save. Defaults to None.
                If None is given, then logger.warning is raised. To raise nothing, use cell='none'.
            code_name (str, optional): The name of the analysis cell. Defaults to None.
        Returns:
            self
        """
        code = code or self._analysis_cell
        if code == "none":
            return self
        code_name = code_name or "default"
        cell_name_key = f"analysis_cells/{code_name}"

        if code is None or code == "":
            logger.warning("Analysis cell is not set. Nothing to save")
            return self

        self.unlock_data(cell_name_key).update({cell_name_key: code}).lock_data(
            cell_name_key
        ).save([cell_name_key])

        if self._save_files:
            assert self.filepath, "You must set self.filepath before saving"
            with open(
                self.filepath + f"_ANALYSIS_CELL_{code_name}.py", "w", encoding="UTF-8"
            ) as file:
                file.write(code)

        return self

    def save_fig(
        self: _T,
        fig: Optional[FigureProtocol] = None,
        name: Optional[Union[str, int]] = None,
        extensions: Optional[str] = None,
        tight_layout: bool = True,
        metadata: Optional[PdfMetadataDict] = None,
        **kwargs,
    ) -> _T:
        """Save the figure with the filename (...)_FIG_name.

        If name is None, use (...)_FIG1, (...)_FIG2.
        pdf is used by default if no extension is provided in name
        """
        self._figure_last_name = str(name).lstrip("_") if name is not None else None

        fig_name = self._get_fig_name(name, extensions)
        full_fig_name = f"{self.filepath}_{fig_name}"
        if fig is None:
            from matplotlib import pyplot as plt

            fig = plt.gcf()

        if (self._save_fig_inside_h5 and kwargs.get("inside_h5", True)) or kwargs.get(
            "inside_h5", False
        ):
            try:
                raise NotImplementedError(
                    "save_fig_inside_h5 is not implemented for the moment."
                )
                # import pltsave

                # data = pltsave.dumps(fig).to_json()
                # self[f"figures/{fig_name}"] = data
                # self.save([f"figures/{fig_name}"])
            except Exception as error:
                logger.exception(
                    "Failed to save the figure inside h5 file due to %s", error
                )
        if tight_layout and hasattr(fig, "tight_layout"):
            fig.tight_layout()  # type: ignore
        if (self._save_interactive_fig and kwargs.get("interactive", True)) or kwargs.get("interactive", False):
            import pickle
            with open(full_fig_name+".pkl", "wb") as file:
                pickle.dump(fig, file)
        if metadata is None:
            fig.savefig(full_fig_name, **kwargs)
        else:
            if not full_fig_name.endswith(".pdf"):
                raise ValueError("Metadata can be added only to pdf files.")

            from matplotlib.backends.backend_pdf import PdfPages

            pdf_fig = PdfPages(full_fig_name)
            fig.savefig(pdf_fig, format="pdf", **kwargs)  # type: ignore
            metadata = metadata or {}
            if not isinstance(metadata.get("Subject", ""), str):
                metadata["Subject"] = json.dumps(metadata.get("Subject"))

            if not isinstance(metadata.get("Keywords", ""), str):
                metadata["Keywords"] = json.dumps(metadata.get("Keywords"))

            pdf_metadata = pdf_fig.infodict()
            pdf_metadata.update(metadata)
            pdf_fig.close()

        self._figure_saved = True

        return self

    def _get_fig_name(
        self, name: Optional[Union[str, int]] = None, extensions: Optional[str] = None
    ) -> str:
        """Get the name of the figure depending on the suffix.

        If name is not specified, suffix is `FIG1.pdf`, `FIG2.pdf`, etc.
        If name like `123`, the suffix is `FIG123.pdf`.
        If name like `abc`, the suffix is `FIG_abc.pdf`
        """
        assert self.filepath, "You must set self.filepath before saving"

        if extensions is None:
            extensions = "pdf"
        elif extensions.startswith("."):
            extensions = extensions[1:]

        if name is None:
            self._fig_index += 1
            name = f"{self._fig_index}.{extensions}"
        else:
            if not isinstance(name, str):
                name = str(name)
            if not name.isnumeric() and name[0] != "_":
                name = "_" + name
            if os.path.splitext(name)[-1] == "":
                name = f"{name}.{extensions}"

        return "FIG" + name

    def parse_config(
        self, config_files: Optional[Tuple[str, ...]] = None
    ) -> "ConfigFile":
        """Parse config files. If `config_files` are not provided takes `default_config_files`."""

        config_files = config_files or self._default_config_files

        if not isinstance(config_files, tuple):
            config_files = tuple(config_files)
        if hash(config_files) in self._parsed_configs:
            return self._parsed_configs[hash(config_files)]

        config_data = sum(
            (self.parse_config_file(config_file) for config_file in config_files),
            ConfigFile(),
        )

        self._parsed_configs[hash(config_files)] = config_data

        return config_data

    @property
    def cfg(self) -> "ConfigFile":
        return self.parse_config()

    def parse_config_values(
        self, keys: List[str], config_files: Optional[Tuple[str, ...]] = None
    ) -> List[utils.title_parsing.ValueForPrint]:
        config_data = self.parse_config(config_files=config_files)
        if not isinstance(keys, (list, tuple)):
            raise ValueError("Keys must be a list of strings.")
        keys_with_values = []
        for key in keys:
            key_value, key_units, key_format = utils.title_parsing.parse_get_format(key)
            if key_value == "filename" or key_value == "file" or key_value == "f":
                filename = os.path.split(self.filepath)[-1]
                keys_with_values.append(
                    utils.title_parsing.ValueForPrint(
                        key_value, filename, key_units, key_format
                    )
                )
            elif key_value in self:
                keys_with_values.append(
                    utils.title_parsing.ValueForPrint(
                        key_value, self[key_value], key_units, key_format
                    )
                )
            elif key_value in config_data:
                keys_with_values.append(
                    utils.title_parsing.ValueForPrint(
                        key_value, config_data[key_value], key_units, key_format
                    )
                )
            else:
                logger.warning("key %s not found and cannot be parsed", key_value)

        return keys_with_values

    def parse_config_str(
        self,
        values: List[str],
        max_length: Optional[int] = None,
        config_files: Optional[Tuple[str, ...]] = None,
    ) -> str:
        """Parse the configuration files.

        Returns: key1=value1, key2=value2, ...
        """
        max_length = max_length or self._default_parse_config_str_max_length
        keys_with_values = self.parse_config_values(values, config_files=config_files)
        return utils.title_parsing.format_title(keys_with_values, max_length=max_length)

    def parse_config_file(self, config_file_name: str, /) -> ConfigFile:
        if config_file_name in self._parsed_configs:
            return self._parsed_configs[config_file_name]

        if "configs" not in self:
            raise KeyError("The is no config files saved within AnalysisManager")

        if config_file_name not in self["configs"]:
            original_config_name = config_file_name
            for possible_name in self["configs"]:
                if possible_name.startswith(config_file_name):
                    config_file_name = possible_name
                    break
            else:
                raise ValueError(
                    f"Cannot find config with name '{config_file_name}'. "
                    f"Possible configs file are {tuple(self['configs'].keys())}"
                )

            if config_file_name in self._parsed_configs:
                self._parsed_configs[original_config_name] = self._parsed_configs[
                    config_file_name
                ]
                return self._parsed_configs[config_file_name]

        else:
            original_config_name = None

        from ..parsing import parse_str

        file_content = self["configs"][config_file_name]
        config_data = ConfigFile(parse_str(file_content), file_content)
        self._parsed_configs[config_file_name] = config_data
        if original_config_name is not None:
            self._parsed_configs[original_config_name] = config_data

        # print("e", self._parsed_configs.keys())

        return config_data

    def set_default_config_files(self, config_files: Union[str, Tuple[str, ...]], /):
        self._default_config_files = (
            (config_files,) if isinstance(config_files, str) else tuple(config_files)
        )

    def get_analysis_code(
        self,
        name: str = "default",
        /,
        update_code: bool = True,
        replace: Optional[dict] = None,
    ) -> str:
        code: Optional[dict] = self.get("analysis_cells")
        if code is None:
            raise ValueError(
                f"There is no field 'analysis_cells' inside the data file. "
                f"Possible keys are {tuple(self.keys())}."
            )

        # if isinstance(code, bytes):
        #     code = code.decode()
        if name not in code:
            raise KeyError(
                f"Cannot get cell '{name}'. Possible cells are: {tuple(code.keys())}"
            )

        code_str: str = code[name]
        if update_code:
            code_str = code_str.replace(
                "aqm.analysis_cell()", f"aqm.analysis_cell('{self.filepath}')"
            )
        if replace is not None:
            for key, value in replace.items():
                code_str = code_str.replace(key, value)
        return code_str

    def open_figs(self) -> list:
        figures = []

        for figure_key in self.get("figures", []):
            import pltsave

            figure_code = self["figures"][figure_key]
            figure = pltsave.loads(figure_code)
            figures.append(figure)
        return figures

        # raise NotImplementedError(
        # "Not implemented for the moment. If you want to open an old figure. Use open_old_figs function")

    def pull(self, force_pull: bool = False):
        self._reset_attrs()
        return super().pull(force_pull)

    @property
    def figure_saved(self):
        return self._figure_saved

    @property
    def figure_last_name(self) -> Optional[str]:
        return self._figure_last_name

    @property
    def filepath(self) -> str:
        filepath = super().filepath
        assert filepath is not None
        return filepath
