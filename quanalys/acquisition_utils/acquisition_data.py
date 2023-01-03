from typing import Dict, Optional

from .analysis_data import AnalysisData


class AcquisitionData(AnalysisData):
    """TODO"""

    def __init__(self,
                 filepath: Optional[str] = None,
                 overwrite: Optional[bool] = None):
        super().__init__(
            filepath=filepath, save_on_edit=True, read_only=False, overwrite=overwrite)


class NotebookAcquisitionData(AcquisitionData):
    """TODO"""

    def __init__(self,
                 filepath: str,
                 configs: Optional[Dict[str, str]] = None,
                 cell: Optional[str] = None,
                 overwrite: Optional[bool] = True):
        super().__init__(filepath=filepath, overwrite=overwrite)

        self.configs = configs
        self.cell = cell

    def save_config_files(self, configs: Optional[Dict[str, str]] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self._filepath)
        configs = configs or self.configs
        if configs is None:
            return
        for name, value in configs.items():
            with open(filepath + '_' + name, 'w', encoding="utf-8") as file:
                file.write(value)

    def save_cell(self, cell: Optional[str] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        cell = cell or self.cell
        if cell is None:
            return

        with open(filepath + '_CELL.py', 'w', encoding="utf-8") as file:
            file.write(cell)
