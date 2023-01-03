import os
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union
import logging

from .acquisition_data import NotebookAcquisitionData

from ..utils import get_timestamp
from ..json_utils import json_read, json_write


class AcquisitionTmpData(NamedTuple):
    """Temporary data that stores inside temp.json"""
    experiment_name: str
    time_stamp: str
    cell: Optional[str] = None
    configs: Dict[str, str] = {}
    directory: Optional[str] = None


def check_subdir(parent_dir: Union[str, Path], directory: Union[str, Path]) -> str:
    """Check whether directory exists in parent directory. Creates if not.
    Returns final path."""
    path = os.path.join(parent_dir, directory)
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info("Directory was created. Path is %s", str(path))
    return path


def check_directory(path: Union[str, Path]) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


class AcquisitionManager:
    """AcquisitionManager"""
    acquisition_cell_init_code: Optional[str] = None
    acquisition_cell_end_code: Optional[str] = None
    last_acquisition_saved: bool = False

    _data_directory = None
    config_files = []

    _current_acquisition = None
    _current_filepath = None

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None):

        self.acquisition_cell_init_code = ""
        self.acquisition_cell_end_code = ""
        self._current_acquisition = None

        if data_directory is not None:
            self.data_directory = data_directory
        elif "ACQUISITION_DIR" in os.environ:
            self.data_directory = os.environ["ACQUISITION_DIR"]
        if self.data_directory is None:
            raise ValueError("No data directory specified")
        self.temp_file_path = os.path.join(self.data_directory, 'temp.json')

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
        check_directory(value)
        self._data_directory = value

    def get_data_directory_and_verify(self):
        data_directory = self.data_directory
        if data_directory is None:
            raise ValueError("You should set self.data_directory")
        return data_directory

    def set_config_file(self, *filenames: str) -> None:
        self.config_files = [Path(file) for file in filenames]
        for config_file in self.config_files:
            if not config_file.exists():
                raise ValueError(f"Configuration file at {config_file} does not exist")

    def get_exp_dir_path(self, experiment_name: str, data_directory: Optional[str] = None) -> str:
        data_directory = data_directory or self.data_directory
        if data_directory is None:
            raise ValueError("You should specify data_directory before")
        return check_subdir(data_directory, experiment_name)

    def get_exp_file_path(self, dic: AcquisitionTmpData) -> str:
        filename = f'{dic.time_stamp}_{dic.experiment_name}'
        directory = self.get_exp_dir_path(dic.experiment_name, data_directory=dic.directory)
        return os.path.join(directory, filename)

    @staticmethod
    def get_temp_data(path) -> Optional[AcquisitionTmpData]:
        if not os.path.exists(path):
            return None
        return AcquisitionTmpData(**json_read(path))

    def create_new_acquisition(self, experiment_name: str, cell: Optional[str] = None):
        self._current_acquisition = None
        configs: Dict[str, str] = {}
        for config_file in self.config_files:
            if not config_file.is_file():
                raise ValueError(f"Config file should be a file. Cannot save directory. Path: {config_file.absolute()}")
            with open(config_file, 'r') as file:  # pylint: disable=W1514
                configs[config_file.name] = file.read()

        dic = AcquisitionTmpData(experiment_name=experiment_name,
                                 time_stamp=get_timestamp(),
                                 cell=cell,
                                 configs=configs,
                                 directory=self.get_data_directory_and_verify())

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
    def current_filepath(self) -> str:
        filepath = self.current_acquisition.filepath
        if filepath is None:
            raise ValueError("No filepath specified")
        return filepath

    def get_ongoing_acquisition(self, replace: Optional[bool] = False):
        current_acquisition_param = self.get_temp_data(self.temp_file_path)
        assert current_acquisition_param is not None, \
            "You should create a new acquisition. It will create temp.json file."
        filepath = self.get_exp_file_path(current_acquisition_param)
        configs = current_acquisition_param.configs
        cell = current_acquisition_param.cell
        return NotebookAcquisitionData(
            filepath=filepath,
            configs=configs,
            cell=cell,
            replace=replace)

    def save_acquisition(self, **kwds):
        acq_data = self.current_acquisition
        acq_data.update(**kwds)
        acq_data.save()

        acq_data.save_config_files()
        acq_data.save_cell()

        self.last_acquisition_saved = True


def save_acquisition(**kwds):
    return AcquisitionManager.save_acquisition(**kwds)
