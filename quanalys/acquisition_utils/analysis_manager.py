import logging
import os
from typing import Optional, Union

from matplotlib import pyplot as plt
from matplotlib.figure import Figure


from .analysis_loop import AnalysisLoop

from ..syncdata import SyncData


class AnalysisManager(SyncData):
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
    if "ANALYSIS_DIRECTORY" in os.environ:
        analysis_directory = os.environ["ANALYSIS_DIRECTORY"]
    else:  # if None, then put analysis in the same folder as data (recommended)
        analysis_directory = None

    def __init__(self,
                 filepath: str,
                 cell: Optional[str] = None,
                 save_files: bool = False,
                 save_on_edit: bool = True):

        if filepath is None:
            raise ValueError("You must specify filepath")

        super().__init__(filepath=filepath, overwrite=False, read_only=False, save_on_edit=save_on_edit)
        self.lock_data()

        self._save_files = save_files

        self._fig_index = 0
        self._figure_saved = False
        self._parsed_configs = {}

        for key, value in self.items():
            if isinstance(value, dict) and value.get("__loop_shape__", None) is not None:
                self._update(**{key: AnalysisLoop(value)})

        self._analysis_cell = cell

        if cell is not None:
            self.unlock_data('analysis_cell')\
                .update(analysis_cell=cell).lock_data('analysis_cell')

        self.save_analysis_cell()

    def save_analysis_cell(self, cell: Optional[str] = None):
        if not self._save_files:
            return

        cell = cell or self._analysis_cell

        if cell is None or cell == "":
            logging.debug("Cell is not set. Nothing to save")
            return

        assert self.filepath, "You must set self.filepath before saving"

        with open(self.filepath + '_ANALYSIS_CELL.py', 'w', encoding="UTF-8") as file:
            file.write(cell)

    def save_fig(self, fig: Optional[Figure] = None, name: Optional[Union[str, int]] = None):
        """saves the figure with the filename (...)_FIG_name
          If name is None, use (...)_FIG1, (...)_FIG2.
          pdf is used by default if no extension is provided in name"""

        full_fig_name = self.get_fig_name(name)

        if fig is not None:
            fig.savefig(full_fig_name)
        else:
            plt.savefig(full_fig_name)

        self._figure_saved = True

    def get_fig_name(self, name: Optional[Union[str, int]] = None) -> str:
        """
        If name is not specified, suffix is `FIG1.pdf`, `FIG2.pdf`, etc.
        If name like `123`, the suffix is `FIG123.pdf`.
        If name like `abc`, the suffix is `FIG_abc.pdf` """
        assert self.filepath, "You must set self.filepath before saving"

        if name is None:
            self._fig_index += 1
            name = f'{self._fig_index}.pdf'
        else:
            if not isinstance(name, str):
                name = str(name)
            if not name.isnumeric() and name[0] != '_':
                name = "_" + name
            if os.path.splitext(name)[-1] == '':
                name = name + ".pdf"

        return self.filepath + '_FIG' + name

    def parse_config(self, config_name: str = "config"):
        if config_name in self._parsed_configs:
            return self._parsed_configs[config_name]

        if 'configs' not in self:
            raise ValueError("The is no config files save within AnalysisManager")

        if config_name not in self['configs']:
            original_config_name = config_name
            for possible_name in self['configs']:
                if possible_name.startswith(config_name):
                    config_name = possible_name
                    break
            else:
                raise ValueError(f"Cannot find config with name {config_name}. \
                    Possible configs file are {self['configs'].keys()}")

            if config_name in self._parsed_configs:
                self._parsed_configs[original_config_name] = self._parsed_configs[config_name]
                return self._parsed_configs[config_name]
        else:
            original_config_name = None

        from ..utils import parse_str
        config_data = parse_str(self['configs'][config_name])
        self._parsed_configs[config_name] = config_data
        if original_config_name is not None:
            self._parsed_configs[original_config_name] = config_data

        return config_data

    @property
    def figure_saved(self):
        return self._figure_saved
