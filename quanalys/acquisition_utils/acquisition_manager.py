import os
from pathlib import Path
from typing import Dict, NamedTuple, Optional, Union
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


class AcquisitionManager:
    """AcquisitionManager"""
    acquisition_cell_init_code: Optional[str] = None
    acquisition_cell_end_code: Optional[str] = None
    last_acquisition_saved: bool = False
    temp_file_path = os.path.join(os.path.dirname(__file__), 'temp.json')

    data_directory = None
    config_files = []

    _current_acquisition = None
    _current_filepath = None

    @classmethod
    def __init__(cls):
        cls.acquisition_cell_init_code = ""
        cls.acquisition_cell_end_code = ""
        cls._current_acquisition = None

        if "ACQUISITION_DIR" in os.environ:
            cls.data_directory = os.environ["ACQUISITION_DIR"]
        if "ACQUISITION_CONFIG_FILES" in os.environ:
            cls.config_files = [Path(file) for file in os.environ["ACQUISITION_CONFIG_FILES"].split(",")]

    @classmethod
    def set_config_file(cls, *filenames: str) -> None:
        cls.config_files = [Path(file) for file in filenames]

    @classmethod
    def get_exp_dir_path(cls, experiment_name: str, data_directory: Optional[str] = None) -> str:
        data_directory = data_directory or cls.data_directory
        if data_directory is None:
            raise ValueError("You should specify data_directory before")
        return check_subdir(data_directory, experiment_name)

    @classmethod
    def get_exp_file_path(cls, dic: AcquisitionTmpData) -> str:
        filename = f'{dic.time_stamp}_{dic.experiment_name}'
        directory = cls.get_exp_dir_path(dic.experiment_name, data_directory=dic.directory)
        return os.path.join(directory, filename)

    @staticmethod
    def get_temp_data(path) -> Optional[AcquisitionTmpData]:
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "temp.json")):
            return None
        return AcquisitionTmpData(**json_read(path))

    @classmethod
    def get_data_directory(cls):
        if cls.data_directory is not None:
            return cls.data_directory
        params_from_last_acquisition = cls.get_temp_data(cls.temp_file_path)
        assert params_from_last_acquisition is not None, "You should set cls.data_directory"
        return params_from_last_acquisition.directory

    @classmethod
    def create_new_acquisition(cls, experiment_name: str, cell: Optional[str] = None):
        cls._current_acquisition = None
        configs: Dict[str, str] = {}
        for config_file in cls.config_files:
            assert config_file.is_file(), "Config file should be a file. Cannot save directory."
            with open(config_file, 'r') as file:  # pylint: disable=W1514
                configs[config_file.name] = file.read()

        dic = AcquisitionTmpData(experiment_name=experiment_name,
                                 time_stamp=get_timestamp(),
                                 cell=cell,
                                 configs=configs,
                                 directory=cls.get_data_directory())

        # save timestamp
        # print(dic._asdict())
        json_write(cls.temp_file_path, dic._asdict())

        cls._current_acquisition = cls.get_ongoing_acquisition(replace=True)

    @classmethod
    @property
    def current_acquisition(cls):
        if cls._current_acquisition is None:
            cls._current_acquisition = cls.get_ongoing_acquisition()
        return cls._current_acquisition

    @classmethod
    def get_ongoing_acquisition(cls, replace: Optional[bool] = False):
        current_acquisition_param = cls.get_temp_data(cls.temp_file_path)
        assert current_acquisition_param is not None, \
            "You should create a new acquisition. It will create temp.json file."
        filepath = cls.get_exp_file_path(current_acquisition_param)
        configs = current_acquisition_param.configs
        cell = current_acquisition_param.cell
        return NotebookAcquisitionData(
            filepath=filepath,
            configs=configs,
            cell=cell,
            replace=replace)

    @classmethod
    def save_acquisition(cls, **kwds):
        acq_data = cls.current_acquisition
        acq_data.update(**kwds)
        acq_data.save_config_files()
        acq_data.save_cell()
        acq_data.save()
        cls.last_acquisition_saved = True


def save_acquisition(**kwds):
    return AcquisitionManager.save_acquisition(**kwds)
