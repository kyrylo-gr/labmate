import numpy as np
import matplotlib.pyplot as plt
import json, h5py, datetime, os, glob
from IPython.core.magic import register_cell_magic
from collections import OrderedDict



@register_cell_magic
def acquisition_cell(line, cell):
    """
    Place this magic function at the beginning of acquisition cell %%acquisition_cell experiment_name:
    This does several things:
     1. creates a unique timestamp corresponding to the measurement.
     2. saves in a temporary file the current content of the CONFIG_FILES to be backed-up
    """
    experiment_name = line
    AcquisitionManager.create_new_acquisition(experiment_name, cell)

    new_cell = AcquisitionManager.acquisition_cell_init_code
    new_cell += cell
    new_cell += AcquisitionManager.acquisition_cell_end_code
    get_ipython().run_cell(new_cell)

    if not AcquisitionManager._last_acquisition_saved:
        print("BEWARE: ongoing acquisition was not saved yet!")


class AcquisitionManager(object):
    acquisition_cell_init_code =  ""
    acquisition_cell_end_code = ""
    _last_acquisition_saved = False
    temp_file = os.path.join(os.path.split(__file__)[0], 'temp.json')

    if "ACQUISITION_DIR" in os.environ:
        data_directory = os.environ["ACQUISITION_DIR"]
    else:
        data_directory = None
    if "ACQUISITION_CONFIG_FILES" in os.environ:
        config_files = os.environ["ACQUISITION_CONFIG_FILES"].split(",")
    else:
        config_files = []

    def _get_timestamp():
        x = datetime.datetime.now()
        return x.strftime("%Y-%m-%d_%H-%M-%S_")

    def set_config_files(*filenames):
        AcquisitionManager.config_files = filenames

    def _make_exp_directory(experiment_name):
        directory = os.path.join(AcquisitionManager.data_directory, experiment_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print('directory created')
        return directory

    def _get_temp_dict():
        with open(os.path.join(os.path.split(__file__)[0], "temp.json"), 'r') as f:
            dic = json.load(f)
        return dic

    def _get_fullpath_from_temp_dict(dic):
        time_stamp = dic["time_stamp"]
        experiment_name = dic["experiment_name"]
        filename = time_stamp + '%s' % (experiment_name)
        directory = AcquisitionManager._make_exp_directory(experiment_name)
        return os.path.join(directory, filename)

    def get_ongoing_acquisition():
        dic = AcquisitionManager._get_temp_dict()
        fullpath = AcquisitionManager._get_fullpath_from_temp_dict(dic)
        configs = dic["configs"]
        cell = dic['cell']
        return AcquisitionData(fullpath, configs, cell)


    def create_new_acquisition(experiment_name, cell):
        configs = dict()
        for config_file in AcquisitionManager.config_files:
            with open(config_file, 'r') as f:
                config_content = f.read()
            configs[p.name] = config_content
        dic = dict(cell=cell,
                   experiment_name=experiment_name,
                   time_stamp=AcquisitionManager._get_timestamp(),
                   configs=configs)

        # save timestamp
        with open(AcquisitionManager.temp_file, "w") as f:
            json.dump(dic, f)

class AcquisitionData(object):
    def __init__(self, fullpath, configs, cell):
        self.fullpath = fullpath.rstrip('.h5')
        self.configs = configs
        self.cell = cell
        self.kwds = {}

    def add_kwds(self, **kwds):
        loop_kwds = {key: value for key, value in kwds.items() if isinstance(value, AcquisitionLoop)}
        for key, value in loop_kwds.items():
            kwds.pop(key)
            for loop_key, loop_data in value.data.items():
                kwds[key + '/' + loop_key] = loop_data
            kwds[key + '/__loop_shape__'] = value.loop_shape
        self.kwds.update(kwds)

    def save_config_files(self):
        for name in self.configs.keys():
            with open(self.fullpath + '_' + name, 'w') as f:
                f.write(self.configs[name])

    def save_cell(self):
        with open(self.fullpath + '_CELL.py', 'w') as f:
            f.write(self.cell)

    def save_data(self):
        with h5py.File(self.fullpath + '.h5', 'w') as f:
            print("saving to h5", self.fullpath + '.h5')
            for key, value in self.kwds.items():
                dset = f.create_dataset(key, data=value)


class AnalysisManager(object):
    if "ANALYSIS_DIRECTORY" in os.environ:
        analysis_directory = os.environ["ANALYSIS_DIRECTORY"]
    else: # if None, then put analysis in the same folder as data (recommended)
        analysis_directory = None
    extra_cells = OrderedDict() # extra cells to backup with each analysis
    current_analysis = None
    analysis_cell_init_code = ""
    analysis_cell_end_code = ""

    def create_new_analysis(fullpath, cell):
        AnalysisManager.current_analysis = AnalysisData()
        AnalysisManager.current_analysis._load_from_h5(fullpath)
        AnalysisManager.current_analysis._cell = cell
        AnalysisManager.current_analysis._extra_cells = AnalysisManager.extra_cells
        AnalysisManager.current_analysis._erase_previous_analysis()
        AnalysisManager.current_analysis._save_analysis_cell()

@register_cell_magic
def register_extra_analysis_cell(line, cell):
    AnalysisManager.extra_cells[line] = cell

@register_cell_magic
def analysis_cell(line, cell):
    """
    Place this magic function at the beginning of a cell to do one of the following:
    To analyze the data that were just saved:
      - %%analysis_cell
    To analyze an old dataset:
      - %%analysis_cell path/to/old/filename.h5
    """
    if len(line)==0:
        fullpath = AcquisitionManager.get_ongoing_acquisition().fullpath
    else: # loading old data
        fullpath = line
        fullpath = fullpath.strip("'")
        fullpath = fullpath.strip('"')

    AnalysisManager.create_new_analysis(fullpath, cell)
    new_cell = AnalysisManager.analysis_cell_init_code
    new_cell += cell
    new_cell += AnalysisManager.analysis_cell_end_code
    get_ipython().run_cell(new_cell)
    if not AnalysisManager.current_analysis._figure_saved:
        print("no figure was saved during data analysis, did you forget data.save_fig() ?")


class AcquisitionLoop(object):
    def __init__(self):
        self.loop_shape = []  # length of each loop level
        self.current_loop = 0  # stores the current loop level we are in
        self.data_level = {}  # for each keyword, indicates at which loop_level it is scanned
        self._data_flatten = {}

    def __call__(self, iterable):
        self.current_loop += 1
        if self.current_loop > len(self.loop_shape):
            self.loop_shape.append(len(iterable))
        else:
            assert (len(iterable) == self.loop_shape[self.current_loop - 1])
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
    def data(self):
        data_reshape = {}
        for key in self._data_flatten.keys():
            data_reshape[key] = np.array(self._data_flatten[key]).reshape(self._reshape_tuple(key))
        return data_reshape

    def append_data(self, **kwds):
        for key in kwds.keys():
            if not key in self.data_level:  # if key was never scanned, notice that it is scanned at the current level
                self.data_level[key] = self.current_loop
            else:  # otherwise make sure that key was previously scanned at the current loop level
                assert (self.data_level[key] == self.current_loop)
            if not key in self._data_flatten:
                self._data_flatten[key] = [kwds[key]]
            else:
                self._data_flatten[key].append(kwds[key])




class AnalysisLoop(object):
    def __init__(self, data=None, loop_shape=None):
        self.data = data
        self.loop_shape = loop_shape

    def _load_from_h5(self, h5group):
        self.loop_shape = h5group['__loop_shape__'][()]
        self.data = {key: h5group[key][()] for key in h5group if key!='__loop_shape__'}

    def __iter__(self):
        for index in range(self.loop_shape[0]):
            child_kwds = {}
            for key in self.data.keys():
                if len(self.data[key]) == 1:
                    child_kwds[key] = self.data[key][0]
                else:
                    child_kwds[key] = self.data[key][index]
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

    def _load_from_h5(self, fullpath):
        self._fullpath = fullpath.rstrip('.h5')
        with h5py.File(self._fullpath + '.h5', 'r') as f:
            for key in f.keys():
                if isinstance(f[key], h5py.Group):
                    loop = AnalysisLoop()
                    loop._load_from_h5(f[key])
                    self[key] = loop
                else:
                    self[key] = f[key][()]

    def __setitem__(self, key, val):
        super(AnalysisData, self).__setitem__(key, val)
        setattr(self, key, val)

    def update(self, *args, **kwds):
        """
        Make sure the update method works the same as for a dict, but also that
        the keys are appended to the object
        """
        if len(args)>1:
            raise ValueError("usage: update([E,] **F)")
        if len(args)==1:
            dic_or_iterable = args[0]
            if hasattr(dic_or_iterable, 'keys'):
                for key in ddic_or_iterableic.keys():
                    self[key] = dic_or_iterable[key]
            else:
                for key, value in dic_or_iterable:
                    self[key] = dic_or_iterable[key]
        for key in kwds:
            self[key] = kwds[key]

    def save_fig(self, fig, name=None):
        """saves the figure with the filename (...)_FIG_name
          If name is None, use (...)_FIG1, (...)_FIG2.
          pdf is used by default if no extension is provided in name"""
        if name is None:
            self._fig_index += 1
            name = str(self._fig_index) + '.pdf'
        elif os.path.splitext(name)[-1]=='' or \
                os.path.splitext(name)[-1][1] in '0123456789': # No extension
            name = '_' + name + '.pdf'
        full_fig_name = self._fullpath + '_FIG' + name
        print("saving fig", full_fig_name)
        plt.savefig(full_fig_name)
        self._figure_saved = True

    def _erase_previous_analysis(self):
        for filename in glob.glob(self._fullpath + '_ANALYSIS_*'):
            os.remove(filename)
        for filename in glob.glob(self._fullpath + '_FIG*'):
            os.remove(filename)

    def _save_analysis_cell(self):
        with open(self._fullpath + '_ANALYSIS_CELL.py', 'w') as f:
            f.write(self._cell)
        if len(AnalysisManager.extra_cells)>0:
            with open(self.fullpath + '_ANALYSIS_EXTRA_CELLS.py', 'w') as f:
                for key, val in AnalysisManager.extra_cells.items():
                    f.write(val)




