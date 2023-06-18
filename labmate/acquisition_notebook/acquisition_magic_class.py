"""This module provides the magic way for acquisition_analysis_manager usage.

It's very old method and should will be removed in the future.
"""

from IPython.core.magic import Magics, magics_class, cell_magic
from .acquisition_analysis_manager import AcquisitionAnalysisManager


@magics_class
class AcquisitionMagic(Magics):
    def __init__(self, aqm: AcquisitionAnalysisManager, shell, **kwargs):
        if shell is None:
            raise ValueError("Cannot use magic cells if a shell is not found.")
        self.shell = shell
        self.aqm = aqm
        super().__init__(shell, **kwargs)

    @cell_magic
    def acquisition_cell(self, line, cell):
        """Create new_acquisition with the name provided."""
        experiment_name = line.strip()

        self.aqm.acquisition_cell(experiment_name, cell=cell)

        self.shell.run_cell(cell)

    @cell_magic
    def analysis_cell(self, line, cell):
        """Open data if file is provided, otherwise open last acquisition."""
        if len(line):  # getting old data
            line = line.strip("'").strip('"')
        else:
            line = None

        self.aqm.analysis_cell(line, cell=cell)

        self.shell.run_cell(cell)


def load_ipython_extension(*, aqm, shell):
    magic = AcquisitionMagic(aqm, shell=shell)
    shell.register_magics(magic)
