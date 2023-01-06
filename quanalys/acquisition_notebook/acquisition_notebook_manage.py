from __future__ import annotations
import os
from typing import List, Optional
from IPython import get_ipython

from ..acquisition_utils import AcquisitionManager, AnalysisManager
from ..utils import lstrip_int


class AcquisitionNotebookManager(AcquisitionManager):
    """

    ### Init:
    ```
    aqm = AcquisitionNotebookManager("tmp_data/", use_magic=False, save_files=False)
    aqm.set_config_file("configuration.py")
    ```
    ### acquisition_cell:
    ```
    aqm.acquisition_cell('simple_sine')
    ...
    aqm.save_acquisition(x=x, y=y)
    ```

    ### analysis_cell:
    ```
    aqm.analysis_cell()
    ...
    plt.plot(aqm.d.x, aqm.d.y)
    aqm.save_fig()
    ```

    """
    am: Optional[AnalysisManager] = None
    analysis_cell_str = None
    is_old_data = False

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None,
                 save_files: bool = False,
                 use_magic: bool = True):

        self.shell = get_ipython()
        self._save_files = save_files
        self._parsed_configs = {}

        if use_magic:
            from .acquisition_magic_class import load_ipython_extension
            load_ipython_extension(aqm=self, shell=self.shell)

        super().__init__(
            data_directory=data_directory,
            config_files=config_files)

    @property
    def data(self):
        if self.am is None:
            raise ValueError('No data set')
        return self.am

    @property
    def d(self):
        return self.data

    def save_fig(self, *arg, **kwds):
        if self.am is None:
            raise ValueError('No data set')
        return self.am.save_fig(*arg, **kwds)

    def save_acquisition(self, **kwds):
        super().save_acquisition(**kwds)
        self.load_am()

    def load_am(self, filename: Optional[str] = None):
        self._parsed_configs = {}
        filename = filename or self.current_filepath
        if not os.path.exists(filename.rstrip('.h5') + '.h5'):
            raise ValueError(f"Cannot load data from {filename}")
        self.am = AnalysisManager(filename, self.analysis_cell_str, save_files=self._save_files)
        return self.am

    def acquisition_cell(self, name: str, cell: Optional[str] = None) -> AcquisitionNotebookManager:
        self.analysis_cell_str = None
        self.am = None

        if cell is None and self.shell is not None:
            cell = self.shell.get_parent()['content']['code']

        print(os.path.basename(self.current_filepath))

        self.new_acquisition(name=name, cell=cell)
        return self

    def analysis_cell(self, filename: Optional[str] = None, cell: Optional[str] = None) -> AcquisitionNotebookManager:
        if cell is None and self.shell is not None:
            cell = self.shell.get_parent()['content']['code']
            # self.shell.get_local_scope(1)['result'].info.raw_cell  # type: ignore

        if filename:  # getting old data
            self.is_old_data = True
            self.analysis_cell_str = None
            filename = self.get_full_filename(filename)
        else:
            filename = self.current_filepath
            self.is_old_data = False
            self.analysis_cell_str = cell

        print(os.path.basename(filename))

        if os.path.exists(filename.rstrip('.h5') + '.h5'):
            self.load_am(filename)
        else:
            if self.is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self.am = None
        return self

    def get_analysis_code(self, look_inside: bool = True) -> str:
        if self.am is None:
            raise ValueError('No data set')

        code = self.am.get('analysis_cell')
        if code is None:
            raise ValueError('There is no field `analysis_cell` inside the data file.')

        if isinstance(code, bytes):
            code = code.decode()

        if look_inside:
            code = code.replace("aqm.analysis_cell()", f"aqm.analysis_cell('{self.am.filepath}')")

        if self.shell is not None:
            self.shell.set_next_input(code)
        return code

    def get_full_filename(self, filename) -> str:
        if '/' in filename or '\\' in filename:
            return filename

        name_with_prefix = lstrip_int(filename)
        if name_with_prefix:
            suffix = name_with_prefix[1]
            return os.path.join(self.get_data_directory(), suffix, filename)
        return filename

    def parse_config(self, config_name: str = "config"):
        if config_name in self._parsed_configs:
            return self._parsed_configs[config_name]

        if self.am is None:
            raise ValueError('No data set')

        if 'configs' not in self.am:
            raise ValueError("The is no config files save within AnalysisManager")

        if config_name not in self.am['configs']:
            original_config_name = config_name
            for possible_name in self.am['configs']:
                if possible_name.startswith(config_name):
                    config_name = possible_name
                    break
            else:
                raise ValueError(f"Cannot find config with name {config_name}. \
                    Possible configs file are {self.am['configs'].keys()}")

            if config_name in self._parsed_configs:
                self._parsed_configs[original_config_name] = self._parsed_configs[config_name]
                return self._parsed_configs[config_name]
        else:
            original_config_name = None

        from ..utils import parse_str
        config_data = parse_str(self.am['configs'][config_name])
        self._parsed_configs[config_name] = config_data
        if original_config_name is not None:
            self._parsed_configs[original_config_name] = config_data

        return config_data
