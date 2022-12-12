import os
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Union
import glob
import logging
from collections import OrderedDict
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .utils import get_timestamp
from .json_utils import json_read, json_write


class AcquisitionTmpData(NamedTuple):
    """Temporary data that stores inside temp.json"""
    experiment_name: str
    time_stamp: str
    cell: Optional[str] = None
    configs: Dict[str, str] = {}
    directory: Optional[str] = None


class AcquisitionManager():
    """AcquisitionManager"""
    
    @classmethod
    def __init__(cls):
        cls.acquisition_cell_init_code: str = ""
        cls.acquisition_cell_end_code: str = ""
        cls.last_acquisition_saved: bool = False
        cls.temp_file_path = os.path.join(os.path.dirname(__file__), 'temp.json')

        if "ACQUISITION_DIR" in os.environ:
            cls.data_directory = os.environ["ACQUISITION_DIR"]
        else:
            cls.data_directory = None
        if "ACQUISITION_CONFIG_FILES" in os.environ:
            cls.config_files = [Path(file) for file in os.environ["ACQUISITION_CONFIG_FILES"].split(",")]
        else:
            cls.config_files = []

    @classmethod
    def set_config_file(cls, *filenames: str) -> None:
        cls.config_files = [Path(file) for file in filenames]

    @classmethod
    def get_exp_dir_path(cls, experiment_name: str, data_directory: Optional[str] = None) -> str:
        data_directory = data_directory or cls.data_directory
        # print(f"data_directory = {data_directory}")
        assert data_directory is not None, "You should specify data_directory before"
        directory = os.path.join(data_directory, experiment_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info("Directory was created. Path is %s", directory)
        return directory

    @staticmethod
    def get_temp_data(path) -> Optional[AcquisitionTmpData]:
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "temp.json")):
            return None
        return AcquisitionTmpData(**json_read(path))

    @classmethod
    def get_exp_file_path(cls, dic: AcquisitionTmpData) -> str:
        filename = f'{dic.time_stamp}_{dic.experiment_name}'
        directory = cls.get_exp_dir_path(dic.experiment_name, data_directory=dic.directory)
        return os.path.join(directory, filename)

    @classmethod
    def get_ongoing_acquisition(cls):
        current_acquisition_param = cls.get_temp_data(cls.temp_file_path)
        assert current_acquisition_param is not None, \
            "You should create a new acquisition. It will create temp.json file."
        fullpath = cls.get_exp_file_path(current_acquisition_param)
        configs = current_acquisition_param.configs
        cell = current_acquisition_param.cell
        return AcquisitionData(
            fullpath=fullpath,
            configs=configs,
            cell=cell)

    @classmethod
    def get_data_directory(cls):
        if cls.data_directory is not None:
            return cls.data_directory
        params_from_last_acquisition = cls.get_temp_data(cls.temp_file_path)
        assert params_from_last_acquisition is not None, "You should set cls.data_directory"
        return params_from_last_acquisition.directory
    
    @classmethod
    def create_new_acquisition(cls, experiment_name: str, cell: Optional[str] = ""):
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
        json_write(cls.temp_file_path, dic._asdict())    
            
    @classmethod
    def save_acquisition(cls, **kwds):
        acq = cls.get_ongoing_acquisition()
        acq.add_kwds(**kwds)
        acq.save_config_files()
        acq.save_cell()
        acq.save_data()
        cls.last_acquisition_saved = True


class AcquisitionData():
    """TODO"""
    def __init__(self, fullpath: str, configs: Dict[str, str], cell: Optional[str]):
        self.fullpath = fullpath.rstrip('.h5')
        self.configs = configs
        self.cell = cell
        self.kwds: Dict[str, Union[List, np.ndarray, dict]] = {}
        self.last_data_saved = False

    def add_kwds(self, **kwds):
        self.last_data_saved = False
        # print(f"Adding keyword {kwds}")
        # for key, value in kwds.items():
        #     print(value.__class__.__name__)
        #     print(value.__class__.__name__ == "AcquisitionLoop")
        #     return value
        loop_kwds = {key: value for key, value in kwds.items() if value.__class__.__name__ == "AcquisitionLoop"}
        # print(f"Adding loop {loop_kwds}")
        for key, value in loop_kwds.items():
            # print("Inside loop")
            kwds.pop(key)
            # print(value.data)
            for loop_key, loop_data in value.data.items():
                kwds[f'{key}/{loop_key}'] = loop_data
            kwds[key + '/__loop_shape__'] = value.loop_shape
        self.kwds.update(kwds)

    def save_config_files(self):
        for name in self.configs.keys():
            with open(self.fullpath + '_' + name, 'w', encoding="utf-8") as file:
                file.write(self.configs[name])

    def save_cell(self):
        if self.cell is None:
            return
        with open(self.fullpath + '_CELL.py', 'w', encoding="utf-8") as file:
            file.write(self.cell)

    def save_data(self):  # TODO: save dict
        # print(self.kwds)
        with h5py.File(self.fullpath + '.h5', 'w') as file:
            logging.info("saving to h5 at %s", self.fullpath + '.h5')
            for key, value in self.kwds.items():
                file.create_dataset(key, data=value)
        self.last_data_saved = True


class AnalysisManager:
    """TODO"""
    if "ANALYSIS_DIRECTORY" in os.environ:
        analysis_directory = os.environ["ANALYSIS_DIRECTORY"]
    else:  # if None, then put analysis in the same folder as data (recommended)
        analysis_directory = None
    extra_cells = OrderedDict()  # extra cells to backup with each analysis
    analysis_cell_init_code = ""
    analysis_cell_end_code = ""

    @classmethod
    def __init__(cls, fullpath, cell: Optional[str] = None):
        cls.current_analysis = AnalysisData()
        cls.current_analysis._load_from_h5(fullpath)
        cls.current_analysis._cell = cell
        cls.current_analysis._extra_cells = AnalysisManager.extra_cells
        cls.current_analysis._erase_previous_analysis()
        cls.current_analysis._save_analysis_cell()

    @classmethod
    @property
    def figure_saved(cls) -> bool:
        return (cls.current_analysis._figure_saved is True) if cls.current_analysis else False


class AcquisitionLoop(object):
    """TODO"""
    def __init__(self):
        self.loop_shape: List[int] = []  # length of each loop level
        self.current_loop = 0  # stores the current loop level we are in
        self.data_level = {}  # for each keyword, indicates at which loop_level it is scanned
        self._data_flatten = {}

    def __call__(self, iterable):
        self.current_loop += 1
        if self.current_loop > len(self.loop_shape):
            self.loop_shape.append(len(iterable))
        else:
            assert len(iterable) == self.loop_shape[self.current_loop - 1]
        for i in iterable:
            yield i  # for body executes here

        self.current_loop -= 1

    def atomic_data_shape(self, key):
        return np.shape(self._data_flatten[key][0])

    def _reshape_tuple(self, key):
        tuple_shape = [1] * len(self.loop_shape)
        tuple_shape += self.atomic_data_shape(key)
        if self.data_level[key] > 0:
            for loop_index in range(self.data_level[key]):
                tuple_shape[loop_index] = self.loop_shape[loop_index]
        return tuple_shape

    @property
    def data(self) -> Dict[str, Any]:
        data_reshape = {}
        for key, data_flatten in self._data_flatten.items():
            data_flatten = np.array(data_flatten).flatten()
            expected_len = np.prod(self._reshape_tuple(key))
            if expected_len < len(data_flatten):
                # print(key, expected_len, len(data_flatten))
                data_flatten = data_flatten[-expected_len:]
                
            data_reshape[key] = np.pad(data_flatten, (0, expected_len-len(data_flatten))).reshape(
                self._reshape_tuple(key))
        return data_reshape

    def append_data(self, level=0, **kwds):
        current_loop = self.current_loop + level

        for key, value in kwds.items():
            if key not in self.data_level:  # if key was never scanned, notice that it is scanned at the current level
                self.data_level[key] = current_loop
            else:  # otherwise make sure that key was previously scanned at the current loop level
                assert self.data_level[key] == current_loop

            if key not in self._data_flatten:
                self._data_flatten[key] = [value]
            else:
                # print()
                self._data_flatten[key].append(value)


class AnalysisLoop():
    """TODO"""
    def __init__(self, data=None, loop_shape: Optional[List[int]] = None):
        self.data = data
        self.loop_shape = loop_shape

    @classmethod
    def load_from_h5(cls, h5group):
        loop = cls()
        loop.loop_shape = h5group['__loop_shape__'][()]
        loop.data = AnalysisData()
        loop.data.update(**{key: h5group[key][()] for key in h5group if key != '__loop_shape__'})
        return loop

    def __iter__(self):
        assert self.data is not None, "Data should be set before iterating over it"
        assert self.loop_shape is not None, "loop_shape should be set before iterating over it"
        for index in range(self.loop_shape[0]):
            child_kwds = {}
            for key, value in self.data.items():
                if len(value) == 1:
                    child_kwds[key] = value[0]
                else:
                    child_kwds[key] = value[index]

            if len(self.loop_shape) > 1:
                yield AnalysisLoop(child_kwds, loop_shape=self.loop_shape[1:])
            else:
                child = AnalysisData()
                child.update(**child_kwds)
                yield child


class AnalysisData(dict):
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """

    def __init__(self):
        self._fig_index = 0
        self._figure_saved = False
        self._cell: Optional[str] = None
        self._extra_cells: Optional[dict] = None
        self.filepath: Optional[str] = None

    def _load_from_h5(self, fullpath: str):
        if os.path.dirname(fullpath) == '' and \
                AcquisitionManager.data_directory is not None:  # only filename (no path provided)
            experiment_name = fullpath[20:].rstrip('.h5')  # strip timestamp
            fullpath = os.path.join(AcquisitionManager.data_directory, experiment_name, fullpath)
        self.filepath = fullpath.rstrip('.h5')
        with h5py.File(self.filepath + '.h5', 'r') as file:
            for key, value in file.items():
                if isinstance(value, h5py.Group):
                    self[key] = AnalysisLoop.load_from_h5(value)
                else:
                    self[key] = value[()]

    def __setitem__(self, key, val):
        super(AnalysisData, self).__setitem__(key, val)
        setattr(self, key, val)

    def update(self, *args, **kwds):
        """
        Make sure the update method works the same as for a dict, but also that
        the keys are appended to the object
        """
        if len(args) > 1:
            raise ValueError("usage: update([E,] **F)")
        if len(args) == 1:
            dic_or_iterable = args[0]
            if hasattr(dic_or_iterable, 'keys'):
                for key in dic_or_iterable.keys():
                    self[key] = dic_or_iterable[key]
            else:
                for key, value in dic_or_iterable:
                    self[key] = dic_or_iterable[key]

        for key, value in kwds.items():
            self[key] = value

    def save_fig(self, fig: Optional[Figure] = None, name=None):
        """saves the figure with the filename (...)_FIG_name
          If name is None, use (...)_FIG1, (...)_FIG2.
          pdf is used by default if no extension is provided in name"""
        assert self.filepath, "You must set self.filepath before saving"
        if name is None:
            self._fig_index += 1
            name = str(self._fig_index) + '.pdf'
        elif os.path.splitext(name)[-1] == '' or \
                os.path.splitext(name)[-1][1] in '0123456789':  # No extension
            name = '_' + name + '.pdf'
        full_fig_name = self.filepath + '_FIG' + name
        print("saving fig", full_fig_name)
        if fig is not None:
            fig.savefig(full_fig_name)
        else:
            plt.savefig(full_fig_name)

        self._figure_saved = True

    def _erase_previous_analysis(self):
        assert self.filepath, "You must set self.filepath before saving"
        for filename in glob.glob(self.filepath + '_ANALYSIS_*'):
            os.remove(filename)
        for filename in glob.glob(self.filepath + '_FIG*'):
            os.remove(filename)

    def _save_analysis_cell(self):
        if self._cell is None:
            logging.debug("Cell is not set. Nothing to save")
            return
        
        assert self.filepath, "You must set self.filepath before saving"
        
        with open(self.filepath + '_ANALYSIS_CELL.py', 'w', encoding="UTF-8") as file:
            file.write(self._cell)

        # if len(AnalysisManager.extra_cells) > 0:
        #     with open(self.filepath + '_ANALYSIS_EXTRA_CELLS.py', 'w', encoding="UTF-8") as file:
        #         for key, val in AnalysisManager.extra_cells.items():
        #             file.write(val)


def save_acquisition(**kwds):
    return AcquisitionManager.save_acquisition(**kwds)


def load_acquisition():
    return AnalysisManager.current_analysis
