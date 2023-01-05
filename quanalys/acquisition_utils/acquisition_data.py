from typing import Dict, Optional

from ..syncdata import SyncData


class NotebookAcquisitionData(SyncData):
    """It's a SyncData that has information about the configs file and the cell.
    `configs` is a list of the paths to the files that saved by `save_config_files` function.
    `cell` is a str. It saves using `save_cell` function that will save it to `..._CELL.py` file"""

    def __init__(self,
                 filepath: str,
                 configs: Optional[Dict[str, str]] = None,
                 cell: Optional[str] = None,
                 overwrite: Optional[bool] = True,
                 save_on_edit: bool = True):

        super().__init__(filepath=filepath, save_on_edit=save_on_edit, read_only=False, overwrite=overwrite)

        self['configs'] = configs
        self['cell'] = cell

    def save_config_files(self, configs: Optional[Dict[str, str]] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self._filepath)
        configs = configs or self['configs']
        if configs is None:
            return
        for name, value in configs.items():
            with open(filepath + '_' + name, 'w', encoding="utf-8") as file:
                file.write(value)

    def save_cell(self, cell: Optional[str] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        cell = cell or self['cell']
        if cell is None:
            return

        with open(filepath + '_CELL.py', 'w', encoding="utf-8") as file:
            file.write(cell)

    def save_additional_info(self):
        self.save_cell()
        self.save_config_files()
