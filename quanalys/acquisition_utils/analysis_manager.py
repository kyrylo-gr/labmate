from collections import OrderedDict
import glob
import logging
import os
# import h5py
from typing import Optional

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .acquisition_manager import AcquisitionManager

# from .acquisition_manager import AcquisitionManager

from .analysis_loop import AnalysisLoop

# def load_acquisition():
#     return AnalysisManager.current_analysis

from .analysis_data import AnalysisData


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
        # print(self.analysis_data._data)
        for key, value in self.analysis_data.items():
            if isinstance(value, dict) and value.get("__loop_shape__", None) is not None:
                # print("setting AnalysisLoop")
                self.analysis_data[key] = AnalysisLoop(value)
        self.cell = cell
        self.erase_previous_analysis()
        self.save_analysis_cell()

    def get_last_filepath(self) -> Optional[str]:
        return AcquisitionManager.current_filepath()

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

    def save_analysis_cell(self, cell: Optional[str] = None):
        cell = cell or self.cell
        if cell is None:
            logging.debug("Cell is not set. Nothing to save")
            return
        assert self.filepath, "You must set self.filepath before saving"

        if cell == "":
            logging.warning("Cell is set to empty string, probably something is wrong")

        with open(self.filepath + '_ANALYSIS_CELL.py', 'w', encoding="UTF-8") as file:
            file.write(cell)

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
