from collections import OrderedDict
import glob
import logging
import os
# import h5py
from typing import List, Optional

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

# from .acquisition_manager import AcquisitionManager
from . import h5py_utils


# def load_acquisition():
#     return AnalysisManager.current_analysis


class AnalysisManager:
    """TODO"""
    if "ANALYSIS_DIRECTORY" in os.environ:
        analysis_directory = os.environ["ANALYSIS_DIRECTORY"]
    else:  # if None, then put analysis in the same folder as data (recommended)
        analysis_directory = None
    extra_cells = OrderedDict()  # extra cells to backup with each analysis
    analysis_cell_init_code = ""
    analysis_cell_end_code = ""

    fig_index = 0
    figure_saved = False

    def __init__(self,
                 filepath: Optional[str] = None,
                 cell: Optional[str] = None):
        filepath = filepath or self.get_last_filepath()
        if filepath is None:
            raise ValueError("Cannot find the last filepath from AcquisitionManager. You must specify filepath")
        self.filepath = filepath
        self.analysis_data = AnalysisData(filepath)
        self.cell = cell
        self.erase_previous_analysis()
        self.save_analysis_cell()

    def get_last_filepath(self) -> Optional[str]:
        return None

    def erase_previous_analysis(self):
        assert self.filepath, "You must set self.filepath before saving"
        for i, filename in enumerate(glob.glob(self.filepath + '_ANALYSIS_*')):
            logging.debug("Removing previous analysis file #%d", i)
            os.remove(filename)
        for i, filename in enumerate(glob.glob(self.filepath + '_FIG*')):
            logging.debug("Removing previous figure file #%d", i)
            os.remove(filename)
        self.fig_index = 0
        self.figure_saved = False

    def save_analysis_cell(self):
        if self.cell is None:
            logging.debug("Cell is not set. Nothing to save")
            return
        assert self.filepath, "You must set self.filepath before saving"

        with open(self.filepath + '_ANALYSIS_CELL.py', 'w', encoding="UTF-8") as file:
            file.write(self.cell)

    def save_fig(self, fig: Optional[Figure] = None, name=None):
        """saves the figure with the filename (...)_FIG_name
          If name is None, use (...)_FIG1, (...)_FIG2.
          pdf is used by default if no extension is provided in name"""
        assert self.filepath, "You must set self.filepath before saving"
        if name is None:
            self.fig_index += 1
            name = str(self.fig_index) + '.pdf'
        elif os.path.splitext(name)[-1] == '' or \
                os.path.splitext(name)[-1][1] in '0123456789':  # No extension
            name = '_' + name + '.pdf'
        full_fig_name = self.filepath + '_FIG' + name
        # print("saving fig", full_fig_name)
        if fig is not None:
            fig.savefig(full_fig_name)
        else:
            plt.savefig(full_fig_name)

        self.figure_saved = True

    # @classmethod
    # @property
    # def figure_saved(cls) -> bool:
    #     return (cls.current_analysis._figure_saved is True) if cls.current_analysis else False


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
        if self.data is None:
            raise ValueError("Data should be set before iterating over it")
        if self.loop_shape is None:
            raise ValueError("loop_shape should be set before iterating over it")

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

    def __init__(self, filepath: Optional[str] = None):
        self._fig_index = 0
        self._figure_saved = False
        self._cell: Optional[str] = None
        self._extra_cells: Optional[dict] = None
        self.filepath = filepath
        if filepath is not None:
            self._load_from_h5(filepath)

    def _load_from_h5(self, filepath: str):
        data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5")
        for key, value in data.items():
            self[key] = value

        # if os.path.dirname(filepath) == '' and \
        #         AcquisitionManager.data_directory is not None:  # only filename (no path provided)
        #     experiment_name = filepath[20:].rstrip('.h5')  # strip timestamp
        #     filepath = os.path.join(AcquisitionManager.data_directory, experiment_name, filepath)
        # self.filepath = filepath.rstrip('.h5')
        # with h5py.File(self.filepath + '.h5', 'r') as file:
        #     for key, value in file.items():
        #         if isinstance(value, h5py.Group):
        #             self[key] = AnalysisLoop.load_from_h5(value)
        #         else:
        #             self[key] = value[()]

    def __setitem__(self, key, val):
        super().__setitem__(key, val)
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
