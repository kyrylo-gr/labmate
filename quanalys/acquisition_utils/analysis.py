from collections import OrderedDict
import glob
import logging
import os
import h5py
from typing import List, Optional

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .acquisition_manager import AcquisitionManager


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
        # print("saving fig", full_fig_name)
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


def load_acquisition():
    return AnalysisManager.current_analysis
