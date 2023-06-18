import os

from typing import Dict, List, NamedTuple, Optional, Tuple, Union
from ..path import Path

from .acquisition_data import NotebookAcquisitionData, read_config_files, read_file, eval_config_files

from ..utils import get_timestamp
from .. import json as jsn


class AcquisitionTmpData(NamedTuple):
    """Temporary data that stores inside temp.json."""

    experiment_name: str
    time_stamp: str
    configs: Dict[str, str] = {}
    directory: Optional[Union[str, Path]] = None

    def asdict(self):
        return self._asdict()  # pylint: disable=no-member


class AcquisitionManager:
    """AcquisitionManager."""

    _data_directory: Path
    config_files = []
    config_files_eval = {}

    _current_acquisition = None
    _current_filepath = None

    _save_files = False
    _save_on_edit = True
    _init_code = None

    cell: Optional[str] = None

    def __init__(
        self,
        data_directory: Optional[Union[str, Path]] = None,
        *,
        config_files: Optional[List[str]] = None,
        save_files: Optional[bool] = None,
        save_on_edit: Optional[bool] = None,
    ):
        if save_files is not None:
            self._save_files = save_files

        if save_on_edit is not None:
            self._save_on_edit = save_on_edit

        self._current_acquisition = None
        self._acquisition_tmp_data = None

        if data_directory is not None:
            self.data_directory = Path(data_directory)
        elif "ACQUISITION_DIR" in os.environ:
            self.data_directory = Path(os.environ["ACQUISITION_DIR"])
        else:
            raise ValueError("No data directory specified")

        self.temp_file_path = self.data_directory / 'temp.json'

        if config_files is not None:
            self.set_config_file(config_files)
        elif "ACQUISITION_CONFIG_FILES" in os.environ:
            self.set_config_file(os.environ["ACQUISITION_CONFIG_FILES"].split(","))

    @property
    def data_directory(self) -> Path:
        return self._data_directory

    @data_directory.setter
    def data_directory(self, directory: Path) -> None:
        self._data_directory = directory.makedirs()

    @property
    def acquisition_tmp_data(self) -> AcquisitionTmpData:
        acquisition_tmp_data = self._acquisition_tmp_data or self.get_temp_data(self.temp_file_path)
        if acquisition_tmp_data is None:
            raise ValueError("You should create a new acquisition. It will create temp.json file.")
        return acquisition_tmp_data

    @acquisition_tmp_data.setter
    def acquisition_tmp_data(self, dic: AcquisitionTmpData) -> None:
        jsn.write(self.temp_file_path, dic.asdict())
        self._acquisition_tmp_data = dic

    def __setitem__(self, __key: str, __value) -> None:
        self.aq[__key] = __value

    def set_config_file(self, filename: Union[str, List[str], Tuple[str, ...]]) -> 'AcquisitionManager':
        """Set self.config_file to filename. Verify if exists.
        Only set config file for future acquisition and will not change current acquisition"""
        if isinstance(filename, str):
            filename = [filename]

        self.config_files = list(filename)

        for config_file in self.config_files:
            if not os.path.exists(config_file):
                raise ValueError(f"Configuration file at {config_file} does not exist")

        return self

    def set_config_evaluation_module(self, file, module):
        if file not in self.config_files:
            raise ValueError("Configuration file should be specified before with set_config_file function")
        self.config_files_eval[os.path.basename(file)] = module

    def set_init_analyse_file(self, filename: Union[str, Path]) -> None:
        if not isinstance(filename, Path):
            filename = Path(filename)
        init = read_file(str(filename.absolute()))
        if init:
            self._init_code = init

    def create_path_from_tmp_data(self, dic: AcquisitionTmpData, ignore_existence: bool = False) -> 'Path':
        data_directory = dic.directory or self.data_directory
        experiment_path = Path(data_directory) / str(dic.experiment_name)
        if not experiment_path.exists():
            experiment_path.makedirs()
        if self._init_code and not os.path.exists(experiment_path / "init_analyse.py"):
            with open(experiment_path / "init_analyse.py", "w", encoding="utf-8") as file:
                file.write(self._init_code)
        filepath_original = filepath = experiment_path / f'{dic.time_stamp}__{dic.experiment_name}'
        if ignore_existence:
            return filepath

        index = 0
        while os.path.exists(filepath + '.h5'):
            filepath = filepath_original + f'__{index}'
            index += 1

        return filepath

    @staticmethod
    def get_temp_data(path: Path) -> Optional[AcquisitionTmpData]:
        if not os.path.exists(path):
            return None
        return AcquisitionTmpData(**jsn.read(path))

    def new_acquisition(
        self, name: str, cell: Optional[str] = None, save_on_edit: Optional[bool] = None
    ) -> NotebookAcquisitionData:
        """Create a new acquisition with the given experiment name."""
        self._current_acquisition = None
        self.cell = cell
        configs = read_config_files(self.config_files)
        if self.config_files_eval:
            configs = eval_config_files(configs, self.config_files_eval)

        dic = AcquisitionTmpData(
            experiment_name=name, time_stamp=get_timestamp(), configs=configs, directory=self.data_directory
        )

        self.acquisition_tmp_data = dic

        self._current_acquisition = self.get_acquisition(replace=True, save_on_edit=save_on_edit)

        return self.current_acquisition

    def create_acquisition(
        self, name: Optional[str] = None, cell: Optional[str] = None, save_on_edit: Optional[bool] = None
    ) -> NotebookAcquisitionData:
        """Create a new acquisition with the given experiment name."""
        configs = read_config_files(self.config_files)

        if self.config_files_eval:
            configs = eval_config_files(configs, self.config_files_eval)

        if name is None:
            name = self.current_experiment_name + '_item'

        dic = AcquisitionTmpData(
            experiment_name=name, time_stamp=get_timestamp(), configs=configs, directory=self.data_directory
        )

        filepath = self.create_path_from_tmp_data(dic)
        configs = configs if configs else None
        save_on_edit = save_on_edit if save_on_edit is not None else self._save_on_edit

        return NotebookAcquisitionData(
            filepath=str(filepath),
            configs=configs,
            cell=cell or self.cell,
            overwrite=False,
            save_on_edit=save_on_edit,
            save_files=self._save_files,
        )

    @property
    def current_acquisition(self) -> NotebookAcquisitionData:
        if self._current_acquisition is None:
            self._current_acquisition = self.get_acquisition()
        return self._current_acquisition

    @property
    def aq(self):  # pylint: disable=invalid-name
        return self.current_acquisition

    @property
    def current_filepath(self) -> Path:
        filepath = self.current_acquisition.filepath
        if filepath is None:
            raise ValueError("No filepath specified")
        return Path(filepath)

    @property
    def current_experiment_name(self) -> str:
        return self.acquisition_tmp_data.experiment_name  # self.current_acquisition.name

    def get_acquisition(
        self, replace: Optional[bool] = False, save_on_edit: Optional[bool] = None
    ) -> NotebookAcquisitionData:
        acquisition_tmp_data = self.acquisition_tmp_data
        filepath = self.create_path_from_tmp_data(acquisition_tmp_data, ignore_existence=True)
        configs = acquisition_tmp_data.configs
        configs = configs if configs else None
        cell = self.cell

        save_on_edit = save_on_edit if save_on_edit is not None else self._save_on_edit

        return NotebookAcquisitionData(
            filepath=str(filepath),
            configs=configs,
            cell=cell,
            overwrite=replace,
            save_on_edit=save_on_edit,
            save_files=self._save_files,
            experiment_name=acquisition_tmp_data.experiment_name,
        )

    def save_acquisition(self, **kwds) -> 'AcquisitionManager':
        acq_data = self.current_acquisition
        if acq_data is None:
            raise ValueError(
                "Cannot save data to acquisition as current acquisition is None. \n\
                Possibly because you have never run `acquisition_cell(..)` or it's an old data"
                ""
            )

        acq_data.update(**kwds)
        acq_data.save_additional_info()
        if acq_data.save_on_edit is False:
            acq_data.save()
        return self
