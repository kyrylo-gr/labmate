import logging
import os
from typing import List, Optional, Union

from matplotlib import pyplot as plt
from matplotlib.figure import Figure


from .analysis_loop import AnalysisLoop

from ..syncdata import SyncData
from ..path import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


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
    if "ANALYSIS_DIRECTORY" in os.environ:
        analysis_directory = os.environ["ANALYSIS_DIRECTORY"]
    else:  # if None, then put analysis in the same folder as data (recommended)
        analysis_directory = None

    _figure_last_name = None
    _figure_saved = False
    _fig_index = 0

    def __init__(self,
                 filepath: Union[str, Path],
                 cell: Optional[str] = None,
                 save_files: bool = False,
                 save_on_edit: bool = True,
                 save_fig_inside_h5: bool = True):

        if filepath is None:
            raise ValueError("You must specify filepath")

        super().__init__(filepath=str(filepath), overwrite=False, read_only=False, save_on_edit=save_on_edit)
        self.lock_data()

        self._save_files = save_files
        self._save_fig_inside_h5 = save_fig_inside_h5

        self.reset_am()

        for key, value in self.items():
            if isinstance(value, dict) and value.get("__loop_shape__", None) is not None:
                self._update({key: AnalysisLoop(value)})

        self._analysis_cell = cell

        if cell is not None:
            self.unlock_data('analysis_cell')\
                .update({'analysis_cell': cell}).lock_data('analysis_cell')

        self.save_analysis_cell()

    def reset_am(self):
        self._fig_index = 0
        self._figure_saved = False
        self._parsed_configs = {}

    def save_analysis_cell(self, cell: Optional[str] = None, cell_name: Optional[str] = None):
        cell_name = "analysis_cell" + ("" if cell_name is None else f"_{cell_name}")
        cell = cell or self._analysis_cell
        if cell is None or cell == "":
            logging.debug("Cell is not set. Nothing to save")
            return

        self.unlock_data(cell_name)\
            .update({cell_name: cell}).lock_data(cell_name).save([cell_name])

        if self._save_files:
            assert self.filepath, "You must set self.filepath before saving"
            with open(self.filepath + '_ANALYSIS_CELL.py', 'w', encoding="UTF-8") as file:
                file.write(cell)

    def save_fig(self,
                 fig: Optional[Figure] = None,
                 name: Optional[Union[str, int]] = None,
                 **kwargs):
        """saves the figure with the filename (...)_FIG_name
          If name is None, use (...)_FIG1, (...)_FIG2.
          pdf is used by default if no extension is provided in name"""

        self._figure_last_name = str(name).lstrip('_') if name is not None else None

        fig_name = self.get_fig_name(name)
        full_fig_name = f'{self.filepath}_{fig_name}'

        if fig is not None:
            if self._save_fig_inside_h5 and kwargs.get("pickle", True):
                try:
                    import pickle
                    import codecs
                    pickled = codecs.encode(pickle.dumps(fig), "base64").decode()
                    self[f"figures/{fig_name}"] = pickled
                    self.save([f"figures/{fig_name}"])
                except Exception as error:
                    logger.warning("Failed to pickle the figure due to %s", error)

            fig.savefig(full_fig_name, **kwargs)
        else:
            plt.savefig(full_fig_name, **kwargs)

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

        return 'FIG' + name

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

    def get_analysis_code(self, update_code: bool = True) -> str:
        code = self.get('analysis_cell')
        if code is None:
            raise ValueError('There is no field `analysis_cell` inside the data file.')

        if isinstance(code, bytes):
            code = code.decode()

        if update_code:
            code = code.replace("aqm.analysis_cell()", f"aqm.analysis_cell('{self.filepath}')")
        return code

    def get_analysis_fig(self) -> List[Figure]:
        figures = []
        # print(self.get("figures"))

        for figure_key in self.get("figures", []):  # pylint: disable=E1133
            # print(figure_key)
            import pickle
            import codecs
            figure_code = self['figures'][figure_key]
            if isinstance(figure_code, str):
                figure_code = figure_code.encode()
            figure: Figure = pickle.loads(codecs.decode(figure_code, 'base64'))
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
