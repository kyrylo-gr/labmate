import os
from typing import List, Optional
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ..acquisition_utils import AcquisitionManager, AnalysisManager


class AcquisitionNotebookManager(AcquisitionManager):

    am: Optional[AnalysisManager] = None
    analysis_cell = None
    is_old_data = False

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
        return self.am

    @property
    def d(self):
        return self.data

    def save_fig(self, *arg, **kwds):
        if self.am is None:
            raise ValueError('No data set')
        return self.am.save_fig(*arg, **kwds)

    def save_acquisition(self, **kwds):
        super().save_acquisition(**kwds)
        self.load_am()

    def load_am(self, filename: Optional[str] = None):
        filename = filename or self.current_filepath
        if not os.path.exists(filename.rstrip('.h5') + '.h5'):
            raise ValueError(f"Cannot load data from {filename}")
        self.am = AnalysisManager(filename, self.analysis_cell)


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
        experiment_name = line.strip()

        self.aqm.new_acquisition(
            name=experiment_name, cell=cell)

        # print(id(self.aqm), self.aqm.current_filepath, acquisition.filepath)

        # if os.path.exists("init_acquisition_cell.py",):
        #     with open("init_acquisition_cell.py", 'r') as f:
        #         init_code = f.read()
        #     cell = init_code + cell

        self.shell.run_cell(cell)

    @cell_magic
    def analysis_cell(self, line, cell):
        if len(line):  # getting old data
            filename = line.strip("'").strip('"')
            self.aqm.is_old_data = True
        else:
            filename = self.aqm.current_filepath
            self.aqm.is_old_data = False
        print("analysis_cell")

        self.aqm.analysis_cell = cell

        filename = filename.rstrip('.h5') + '.h5'
        if os.path.exists(filename):
            self.aqm.load_am(filename)
        else:
            if self.aqm.is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self.aqm.am = None

        self.shell.run_cell(cell)


def load_ipython_extension(*, aqm, shell):
    magic = AcquisitionMagic(aqm, shell=shell)
    shell.register_magics(magic)
