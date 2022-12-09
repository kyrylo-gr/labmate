import logging
from IPython.core.magic import register_cell_magic

from .acquisition_utils import AcquisitionManager, AnalysisManager


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
    get_ipython().run_cell(new_cell)  # type: ignore # pylint: disable=E0602  # noqa: F821

    if not AcquisitionManager.last_acquisition_saved:
        logging.warning("BEWARE: ongoing acquisition was not saved yet!")


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
    if len(line):  # getting old
        fullpath = line.strip("'").strip('"')
    else:
        fullpath = AcquisitionManager.get_ongoing_acquisition().fullpath

    AnalysisManager(fullpath, cell)
    new_cell = AnalysisManager.analysis_cell_init_code
    new_cell += cell
    new_cell += AnalysisManager.analysis_cell_end_code
    get_ipython().run_cell(new_cell)  # type: ignore # pylint: disable=E0602  # noqa: F821

    if not AnalysisManager.figure_saved:
        logging.warning("no figure was saved during data analysis, did you forget data.save_fig() ?")
