from typing import List, Optional
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ..acquisition_utils import AcquisitionManager, AnalysisManager


class AcquisitionNotebookManager(AcquisitionManager):

    am: Optional[AnalysisManager] = None

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None):
        load_ipython_extension(aqm=self, shell=get_ipython())
        super().__init__(
            data_directory=data_directory,
            config_files=config_files)

    @property
    def data(self):
        if self.am is None:
            raise ValueError('No data set')
        return self.am.data

    def save_fig(self, *arg, **kwds):
        if self.am is None:
            raise ValueError('No data set')
        return self.am.save_fig(*arg, **kwds)


@magics_class
class AcquisitionMagic(Magics):

    def __init__(self, aqm: AcquisitionNotebookManager, shell=None, **kwargs):
        shell = shell or get_ipython()
        if shell is None:
            raise ValueError("Not shell specified")
        self.shell = shell
        self.aqm = aqm
        super().__init__(shell, **kwargs)

    @cell_magic
    def acquisition_cell(self, line, cell):
        experiment_name = line
        self.aqm.create_new_acquisition(experiment_name, cell)
        self.shell.run_cell(cell)

    @cell_magic
    def analysic_cell(self, line, cell):
        if len(line):  # getting old
            filename = line.strip("'").strip('"')
        else:
            filename = self.aqm.current_filepath
        print("analysic_cell")

        self.aqm.am = AnalysisManager(filename, cell)
        self.shell.run_cell(cell)


def load_ipython_extension(*, aqm, shell):
    magic = AcquisitionMagic(aqm, shell=shell)
    shell.register_magics(magic)
