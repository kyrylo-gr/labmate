import logging
import os
from typing import List, Literal, Optional, Protocol, Tuple, Union


from .analysis_loop import AnalysisLoop

from ..syncdata import SyncData
from .config_file import ConfigFile
from ..path import Path
from .. import utils


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class FigureProtocol(Protocol):
    def savefig(self, fname, **kwds):
        """Save the figure to a file."""


class AnalysisData(SyncData):
    """AnalysisManager is subclass of SyncData.

    It opens the filepath and immediately looks every existing keys.
    So that you can add and modify a new key, but cannot change old keys.

    Also if `cell` was provided, it will save it to h5 file and
    to _ANALYSIS_CELL.py file into the same directory.

    Use case are the same as for the SyncData except additional
    `save_fig` method.

    Example 1:
    ```
    data = AnalysisManager(filepath)
    print(data.x)
    data.fit_results = [1,2,3]
    ```
    """

    _figure_last_name = None
    _figure_saved = False
    _fig_index = 0

    def __init__(
        self,
        filepath: Union[str, Path],
        cell: Optional[str] = "none",
        save_files: bool = False,
        save_on_edit: bool = True,
        save_fig_inside_h5: bool = False,
    ):
        if filepath is None:
            raise ValueError("You must specify filepath")

        super().__init__(filepath=str(filepath), overwrite=False, read_only=False, save_on_edit=save_on_edit)
        self.lock_data()

        self._save_files = save_files

        # if save_fig_inside_h5 is True:
        #     raise NotImplementedError(
        #         """We stop using pickle as it's not consistent between systems.
        #         before the better solution found this functionality is deprecated.""")
        self._save_fig_inside_h5 = save_fig_inside_h5

        self._default_config_files: Tuple[str, ...] = tuple()

        self.reset_am()

        for key, value in self.items():
            if isinstance(value, dict) and value.get("__loop_shape__") is not None:
                self._update({key: AnalysisLoop(value)})

        self._analysis_cell = cell

        # if cell is not None:
        #     self.unlock_data('analysis_cell')\
        #         .update({'analysis_cell': cell}).lock_data('analysis_cell')

        self.save_analysis_cell()

    def reset_am(self):
        self._fig_index = 0
        self._figure_saved = False
        self._parsed_configs = {}

    def save_analysis_cell(self, cell: Optional[Union[str, Literal['none']]] = None, cell_name: Optional[str] = None):
        cell = cell or self._analysis_cell
        if cell == "none":
            return
        cell_name = cell_name or "default"
        cell_name_key = f"analysis_cells/{cell_name}"

        if cell is None or cell == "":
            logger.warning("Analysis cell is not set. Nothing to save")
            return

        self.unlock_data(cell_name_key).update({cell_name_key: cell}).lock_data(cell_name_key).save([cell_name_key])

        if self._save_files:
            assert self.filepath, "You must set self.filepath before saving"
            with open(self.filepath + f'_ANALYSIS_CELL_{cell_name}.py', 'w', encoding="UTF-8") as file:
                file.write(cell)

    def save_fig(
        self,
        fig: Optional[FigureProtocol] = None,
        name: Optional[Union[str, int]] = None,
        extensions: Optional[str] = None,
        tight_layout: bool = True,
        **kwargs,
    ):
        """Save the figure with the filename (...)_FIG_name.

        If name is None, use (...)_FIG1, (...)_FIG2.
        pdf is used by default if no extension is provided in name
        """
        self._figure_last_name = str(name).lstrip('_') if name is not None else None

        fig_name = self._get_fig_name(name, extensions)
        full_fig_name = f'{self.filepath}_{fig_name}'
        if fig is None:
            from matplotlib import pyplot as plt

            fig = plt.gcf()

        if (self._save_fig_inside_h5 and kwargs.get("inside_h5", True)) or kwargs.get("inside_h5", False):
            try:
                # import pickle
                # import codecs
                # pickled = codecs.encode(pickle.dumps(fig), "base64").decode()
                import pltsave

                data = pltsave.dumps(fig).to_json()
                self[f"figures/{fig_name}"] = data
                self.save([f"figures/{fig_name}"])
            except Exception as error:
                logger.exception("Failed to save the figure inside h5 file due to %s", error)
        if tight_layout and hasattr(fig, "tight_layout"):
            fig.tight_layout()  # type: ignore
        fig.savefig(full_fig_name, **kwargs)

        self._figure_saved = True

    def _get_fig_name(self, name: Optional[Union[str, int]] = None, extensions: Optional[str] = None) -> str:
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
            name = f'{self._fig_index}.{extensions}'
        else:
            if not isinstance(name, str):
                name = str(name)
            if not name.isnumeric() and name[0] != '_':
                name = "_" + name
            if os.path.splitext(name)[-1] == '':
                name = f"{name}.{extensions}"

        return 'FIG' + name

    def parse_config(self, config_files: Optional[Tuple[str, ...]] = None) -> ConfigFile:
        # if isinstance(config_files, str):
        #     logging.warning("""Function `parse_config` changed its behavior.
        #                     Old parse_config function now calls `parse_config_file`.""")
        #     return self.parse_config_file(config_files)  # type: ignore

        config_files = config_files or self._default_config_files

        if not isinstance(config_files, tuple):
            config_files = tuple(config_files)
        if hash(config_files) in self._parsed_configs:
            return self._parsed_configs[hash(config_files)]

        config_data = sum((self.parse_config_file(config_file) for config_file in config_files), ConfigFile())

        self._parsed_configs[hash(config_files)] = config_data

        return config_data

    @property
    def cfg(self) -> 'ConfigFile':
        return self.parse_config()

    def parse_config_values(
        self, keys: List[str], config_files: Optional[Tuple[str, ...]] = None
    ) -> List[utils.parse.ValueForPrint]:
        config_data = self.parse_config(config_files=config_files)
        if not isinstance(keys, (list, tuple)):
            raise ValueError("Keys must be a list of strings.")
        keys_with_values = []
        for key in keys:
            key_value, key_units, key_format = utils.parse.parse_get_format(key)
            if key_value == "filename" or key_value == "file" or key_value == "f":
                filename = os.path.split(self.filepath)[-1]
                keys_with_values.append(utils.parse.ValueForPrint(key_value, filename, key_units, key_format))
            elif key_value in config_data:
                keys_with_values.append(
                    utils.parse.ValueForPrint(key_value, config_data[key_value], key_units, key_format)
                )
            elif key_value in self:
                keys_with_values.append(utils.parse.ValueForPrint(key_value, self[key_value], key_units, key_format))
            else:
                logger.warning("key %s not found and cannot be parsed", key_value)

        return keys_with_values

    def parse_config_str(
        self, values: List[str], max_length: Optional[int] = 60, config_files: Optional[Tuple[str, ...]] = None
    ) -> str:
        """Parse the configuration files.

        Returns: key1=value1, key2=value2, ...
        """
        keys_with_values = self.parse_config_values(values, config_files=config_files)
        return utils.parse.format_title(keys_with_values, max_length=max_length)

    def parse_config_file(self, config_file_name: str, /) -> ConfigFile:
        if config_file_name in self._parsed_configs:
            return self._parsed_configs[config_file_name]

        if 'configs' not in self:
            raise KeyError("The is no config files saved within AnalysisManager")

        if config_file_name not in self['configs']:
            original_config_name = config_file_name
            for possible_name in self['configs']:
                if possible_name.startswith(config_file_name):
                    config_file_name = possible_name
                    break
            else:
                raise ValueError(
                    f"Cannot find config with name '{config_file_name}'. "
                    f"Possible configs file are {tuple(self['configs'].keys())}"
                )

            if config_file_name in self._parsed_configs:
                self._parsed_configs[original_config_name] = self._parsed_configs[config_file_name]
                return self._parsed_configs[config_file_name]

        else:
            original_config_name = None

        from ..utils.parse import parse_str

        file_content = self['configs'][config_file_name]
        config_data = ConfigFile(parse_str(file_content), file_content)
        self._parsed_configs[config_file_name] = config_data
        if original_config_name is not None:
            self._parsed_configs[original_config_name] = config_data

        # print("e", self._parsed_configs.keys())

        return config_data

    def set_default_config_files(self, config_files: Union[str, Tuple[str, ...]], /):
        self._default_config_files = (config_files,) if isinstance(config_files, str) else tuple(config_files)

    def get_analysis_code(self, name: str = "default", /, update_code: bool = True) -> str:
        code: Optional[dict] = self.get('analysis_cells')
        if code is None:
            raise ValueError(
                f"There is no field 'analysis_cells' inside the data file. " f"Possible keys are {tuple(self.keys())}."
            )

        # if isinstance(code, bytes):
        #     code = code.decode()
        if name not in code:
            raise KeyError(f"Cannot get cell '{name}'. Possible cells are: {tuple(code.keys())}")

        code_str: str = code[name]
        if update_code:
            code_str = code_str.replace("aqm.analysis_cell()", f"aqm.analysis_cell('{self.filepath}')")
        return code_str

    def open_figs(self) -> list:
        figures = []

        for figure_key in self.get("figures", []):
            import pltsave

            figure_code = self['figures'][figure_key]
            figure = pltsave.loads(figure_code)
            figures.append(figure)
        return figures

        # raise NotImplementedError(
        # "Not implemented for the moment. If you want to open an old figure. Use open_old_figs function")

    def open_old_figs(self) -> list:
        figures = []
        # print(self.get("figures"))

        for figure_key in self.get("figures", []):  # pylint: disable=E1133
            # print(figure_key)
            import pickle
            import codecs

            figure_code = self['figures'][figure_key]
            if isinstance(figure_code, str):
                figure_code = figure_code.encode()
            figure = pickle.loads(codecs.decode(figure_code, 'base64'))
            figures.append(figure)
        return figures

    def pull(self, force_pull: bool = False):
        self.reset_am()
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
