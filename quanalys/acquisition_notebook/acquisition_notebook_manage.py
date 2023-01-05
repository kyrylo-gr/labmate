import os
from typing import List, Optional
from IPython import get_ipython

from ..acquisition_utils import AcquisitionManager, AnalysisManager


class AcquisitionNotebookManager(AcquisitionManager):

    am: Optional[AnalysisManager] = None
    analysis_cell_str = None
    is_old_data = False

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None,
                 save_files: bool = False,
                 use_magic: bool = True):

        self.shell = get_ipython()
        self._save_files = save_files

        if use_magic:
            from .acquisition_magic_class import load_ipython_extension
            load_ipython_extension(aqm=self, shell=self.shell)

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
        self.am = AnalysisManager(filename, self.analysis_cell_str, save_files=self._save_files)

    def acquisition_cell(self, name: str, cell: Optional[str] = None):
        self.analysis_cell_str = None
        self.am = None

        if cell is None and self.shell is not None:
            cell = self.shell.get_parent()['content']['code']

        self.new_acquisition(name=name, cell=cell)

    def analysis_cell(self, filename: Optional[str] = None, cell: Optional[str] = None):
        if cell is None and self.shell is not None:
            cell = self.shell.get_parent()['content']['code']
            # self.shell.get_local_scope(1)['result'].info.raw_cell  # type: ignore

        if filename:  # getting old data
            self.is_old_data = True
            self.analysis_cell_str = None
        else:
            filename = self.current_filepath
            self.is_old_data = False
            self.analysis_cell_str = cell

        filename = filename.rstrip('.h5') + '.h5'

        if os.path.exists(filename):
            self.load_am(filename)
        else:
            if self.is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self.am = None
