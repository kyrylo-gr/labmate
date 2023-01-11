from IPython.core.magic import Magics, magics_class, cell_magic
from .acquisition_notebook_manager import AcquisitionNotebookManager


@magics_class
class AcquisitionMagic(Magics):

    def __init__(self, aqm: AcquisitionNotebookManager, shell, **kwargs):
        if shell is None:
            raise ValueError("Not shell specified")
        self.shell = shell
        self.aqm = aqm
        super().__init__(shell, **kwargs)

    @cell_magic
    def acquisition_cell(self, line, cell):
        """Create new_acquisition with the name provided"""
        experiment_name = line.strip()

        self.aqm.acquisition_cell(experiment_name, cell)

        self.shell.run_cell(cell)

    @cell_magic
    def analysis_cell(self, line, cell):
        """If file is provided, opens this file to aqm.data.
        Otherwise, opens to aqm.data the filename from last acquisition."""

        if len(line):  # getting old data
            line = line.strip("'").strip('"')
        else:
            line = None

        self.aqm.analysis_cell(line, cell)

        self.shell.run_cell(cell)


def load_ipython_extension(*, aqm, shell):
    magic = AcquisitionMagic(aqm, shell=shell)
    shell.register_magics(magic)
