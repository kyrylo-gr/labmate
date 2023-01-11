from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union
import logging

from .acquisition_data import NotebookAcquisitionData, read_config_files

from ..utils import get_timestamp
from ..json_utils import json_read, json_write


class AcquisitionTmpData(NamedTuple):
    """Temporary data that stores inside temp.json"""
    experiment_name: str
    time_stamp: str
    configs: Dict[str, str] = {}
    directory: Optional[str] = None


def check_subdir(parent_dir: Union[str, Path], directory: Union[str, Path]) -> str:
    """Check whether directory exists in parent directory. Creates if not.
    Returns final path."""
    path = os.path.join(parent_dir, directory)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logging.info("Directory was created. Path is %s", str(path))
    return path


def create_directory(path: Union[str, Path]) -> None:
    # if not os.path.exists(path):
    os.makedirs(path, exist_ok=True)


class AcquisitionManager:
    """AcquisitionManager"""

    _data_directory = None
    config_files = []

    _current_acquisition = None
    _current_filepath = None

    _save_files = False
    _save_on_edit = True

    cell: Optional[str] = None

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None,
                 save_files: Optional[bool] = None,
                 save_on_edit: Optional[bool] = None):

        if save_files is not None:
            self._save_files = save_files

        if save_on_edit is not None:
            self._save_on_edit = save_on_edit

        self._current_acquisition = None

        if data_directory is not None:
            self.data_directory = data_directory
        elif "ACQUISITION_DIR" in os.environ:
            self.data_directory = os.environ["ACQUISITION_DIR"]
        else:
            raise ValueError("No data directory specified")

        self.temp_file_path = os.path.join(self.data_directory, 'temp.json')  # type: ignore

        if config_files is not None:
            self.set_config_file(*config_files)
        elif "ACQUISITION_CONFIG_FILES" in os.environ:
            self.set_config_file(*os.environ["ACQUISITION_CONFIG_FILES"].split(","))

    @property
    def data_directory(self) -> Union[str, None]:
        if self._data_directory is not None:
            return self._data_directory
        params_from_last_acquisition = self.get_temp_data(self.temp_file_path)
        return params_from_last_acquisition.directory if \
            params_from_last_acquisition is not None else None

    @data_directory.setter
    def data_directory(self, value: str) -> None:
        create_directory(value)
        self._data_directory = value

    def get_data_directory(self):
        """Return data_directory or raise error if not set."""
        data_directory = self.data_directory
        if data_directory is None:
            raise ValueError("You should set self.data_directory")
        return data_directory

    def set_config_file(self, filename: Union[str, List[str]]) -> AcquisitionManager:
        """Set self.config_file to filename. Verify if exists.
        Only set config file for future acquisition and will not change current acquisition"""
        if isinstance(filename, str):
            filename = [filename]

        self.config_files = [file for file in filename]

        for config_file in self.config_files:
            if not os.path.exists(config_file):
                raise ValueError(f"Configuration file at {config_file} does not exist")

        return self

    def create_subdir(self, experiment_name: str, data_directory: Optional[str] = None) -> str:
        """Create a subdirectory inside data_directory"""
        data_directory = data_directory or self.get_data_directory()
        return check_subdir(data_directory, experiment_name)

    def create_path_from_tmp_data(self, dic: AcquisitionTmpData) -> str:
        return os.path.join(
            self.create_subdir(dic.experiment_name, data_directory=dic.directory),
            f'{dic.time_stamp}__{dic.experiment_name}')

    @staticmethod
    def get_temp_data(path) -> Optional[AcquisitionTmpData]:
        if not os.path.exists(path):
            return None
        return AcquisitionTmpData(**json_read(path))

    def new_acquisition(self, name: str, cell: Optional[str] = None):
        """Creates a new acquisition with the given experiment name"""
        self._current_acquisition = None
        self.cell = cell
        configs = read_config_files(self.config_files)

        dic = AcquisitionTmpData(experiment_name=name,
                                 time_stamp=get_timestamp(),
                                 configs=configs,
                                 directory=self.get_data_directory())

        json_write(self.temp_file_path, dic._asdict())

        self._current_acquisition = self.get_ongoing_acquisition(replace=True)

        return self.current_acquisition

    @property
    def current_acquisition(self):
        # print(2, cls._current_acquisition)
        if self._current_acquisition is None:
            self._current_acquisition = self.get_ongoing_acquisition()
            # print(3, cls._current_acquisition)
        return self._current_acquisition

    @property
    def aq(self):
        return self.current_acquisition

    @property
    def current_filepath(self) -> str:
        filepath = self.current_acquisition.filepath
        if filepath is None:
            raise ValueError("No filepath specified")
        return filepath

    def get_ongoing_acquisition(self, replace: Optional[bool] = False) -> NotebookAcquisitionData:
        current_acquisition_param = self.get_temp_data(self.temp_file_path)
        assert current_acquisition_param is not None, \
            "You should create a new acquisition. It will create temp.json file."
        filepath = self.create_path_from_tmp_data(current_acquisition_param)
        configs = current_acquisition_param.configs
        cell = self.cell

        return NotebookAcquisitionData(
            filepath=filepath,
            configs=configs,
            cell=cell,
            overwrite=replace,
            save_on_edit=self._save_on_edit,
            save_files=self._save_files)

    def save_acquisition(self, **kwds) -> AcquisitionManager:
        acq_data = self.current_acquisition
        acq_data.update(**kwds)
        acq_data.save_additional_info()
        if self._save_on_edit is False:
            acq_data.save()
        return self
