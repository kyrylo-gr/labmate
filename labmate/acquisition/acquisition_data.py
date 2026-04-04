"""Module that contains NotebookAcquisitionData class."""

from typing import Dict, List, Optional, Union

from dh5 import DH5

from ..logger import logger
from ..utils.file_read import read_files


class NotebookAcquisitionData(DH5):
    """It's a DH5 that has information about the configs file and the cell.

    `configs` is a list of the paths to the files that saved by `save_config_files` function.
    `cell` is a str. It saves using `save_cell` function that will save it to `..._CELL.py` file
    """

    _current_step: int
    _cells: Dict[int, Optional[str]]

    def __init__(
        self,
        filepath: str,
        configs: Optional[Union[Dict[str, str], List[str]]] = None,
        cell: Optional[str] = "none",
        overwrite: Optional[bool] = True,
        save_on_edit: bool = True,
        save_files: bool = True,
        experiment_name: Optional[str] = None,
    ):
        """Create file.
        This class is a DH5 object that saves code and config files.

        Args:
            filepath (str): path to the file to be saved.
            configs (dict[str, str] | list[str], optional): List of the files to read or dictionary
             with a filename as a key and a value as the context of the file. Defaults to None.
            cell (str, optional): string of the cell to be saved under `acquisition_cell` key.
             Defaults to "none". If equals to None or empty string, then warning will be displayed.
            overwrite (bool, optional): True if the existed file should be overwritten.
             Defaults to True.
            save_on_edit (bool, optional): If file is saved every time any changes has made.
             Defaults to True. If False, the file should be saved either with method .save() or
             with method .save_acquisition(...).
            save_files (bool, optional): If config files should be saved as a files and not only
             inside h5 file. Defaults to True.
            experiment_name (Optional[str], optional): Completely optional property for
             external use. Never used internally. Defaults to None.
        """
        super().__init__(
            filepath=filepath,
            save_on_edit=save_on_edit,
            read_only=False,
            overwrite=overwrite,
        )

        if isinstance(configs, list):
            configs = read_files(configs)

        self._save_files = save_files

        self._config = configs
        self.save_configs()

        self._cells = {1: cell}
        self.save_cell(cell=cell, suffix="1")

        self.experiment_name = experiment_name
        self.current_step = 1

        self["useful"] = False

    def save_configs(
        self, configs: Optional[Dict[str, str]] = None, filepath: Optional[str] = None
    ):
        """Save the configuration files to the h5 file and possibly to files.

        If `save_files` during init was set to True, then it will create copy of the files near
         the h5 file.

        Args:
            configs (dict[str, str], optional): Dictionary that contains config files with keys as
             names of the files. Defaults to self._config that was set during init.
            filepath (str, optional): Path+file_prefix to the desired location, i.e. it should end
             with the file prefix to which the config file name and extension will be added. Needed
             if config files are saved as files. Defaults to save filepath as h5 file.
        """
        configs = configs or self._config
        if configs is None:
            return

        self["configs"] = configs

        if not self._save_files:
            return

        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        for name, value in configs.items():
            with open(filepath + "_" + name, "w", encoding="utf-8") as file:
                file.write(value)

    def save_cell(
        self,
        cell: Optional[str] = None,
        filepath: Optional[str] = None,
        suffix: Optional[str] = None,
    ):
        """Save the cell code to the h5 file and possibly to a file.

        If `save_files` during init was set to True, then it will create a '.py' file near
         the h5 file.

        Args:
            cel (str, optional): String that contains code of the cell. Defaults to self._cell that
             was set during init.
            filepath (str, optional): Needed if the code is saved as a file. Path+file_prefix to
             the desired location, i.e. it should end with the file prefix to which the suffix and
             'py' extension will be added. Defaults to save filepath as h5 file.
        """
        if cell == "none":
            return
        if cell is None or cell == "":
            logger.warning("Acquisition cell is not set. Nothing to save")
            return
        if suffix is not None:
            self[f"acquisition_cell/{suffix}"] = cell
        else:
            self["acquisition_cell/0"] = cell

        if not self._save_files:
            return

        filepath = self._check_if_filepath_was_set(filepath, self._filepath)
        with open(filepath + "_CELL.py", "w", encoding="utf-8") as file:
            file.write(cell)

    def save_cells(
        self,
        cells: Optional[Dict[int, Optional[str]]] = None,
        filepath: Optional[str] = None,
    ):
        """Save all sells that are provided or pushed into self._cells array."""
        cells = cells or self._cells
        # if len(cells) == 1:
        #     self.save_cell(cells.popitem()[1], filepath)
        #     return
        for i, cell in cells.items():
            self.save_cell(cell, filepath, suffix=str(i))

    def save_additional_info(self):
        """Save all additional information, i.e. cell code, configs. Put useful key to True."""
        self["useful"] = True

        if not self._save_files:
            return
        self.save_cells()
        self.save_configs()

    def save_acquisition(self, **kwds) -> "NotebookAcquisitionData":
        """Save kwds and all additional information (configs, code, ...)."""
        self.update(**kwds)
        self.save_additional_info()
        if self.save_on_edit is False:
            self.save()
        return self

    @property
    def current_step(self):
        """Return the current step of the acquisition."""
        return self._current_step

    @current_step.setter
    def current_step(self, value: int):
        self._current_step = value

    def set_cell(self, cell: Optional[str], step: Optional[int] = None):
        """Set the cell code."""
        if step is None:
            step = self.current_step
        self._cells[step] = cell
