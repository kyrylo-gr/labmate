from __future__ import annotations

from matplotlib.figure import Figure
import logging
from typing import Any, List, Optional, Union
from ..utils import lstrip_int
from ..acquisition_utils import AcquisitionManager, AnalysisData
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AcquisitionAnalysisManager(AcquisitionManager):
    """

    ### Init:
    ```
    aqm = AcquisitionAnalysisManager("tmp_data/", use_magic=False, save_files=False)
    aqm.set_config_file("configuration.py")
    ```
    ### acquisition_cell:
    ```
    aqm.acquisition_cell('simple_sine')
    ...
    aqm.save_acquisition(x=x, y=y)
    ```

    ### analysis_cell:
    ```
    aqm.analysis_cell()
    ...
    plt.plot(aqm.d.x, aqm.d.y)
    aqm.save_fig()
    ```

    """
    _analysis_data: Optional[AnalysisData] = None
    _analysis_cell_str = None
    is_old_data = False
    _last_fig_name = None

    def __init__(self,
                 data_directory: Optional[str] = None, *,
                 config_files: Optional[List[str]] = None,
                 save_files: bool = False,
                 use_magic: bool = False,
                 save_on_edit: bool = True,
                 save_on_edit_analysis: Optional[bool] = None,
                 save_fig_inside_h5: bool = True,
                 shell: Any = False):
        """

        Args:
            data_directory (Optional[str], optional):
                Path to data_directory. Should be explicitly set here or as environ parameter.
            config_files (Optional[List[str]], optional):
                List of paths to config files. Defaults to empty.
            save_files (bool, optional):
                True to additionally save config files and the cells to files. Defaults to False.
                So all information is saved inside the h5 file.
            use_magic (bool, optional):
                True to register the magic cells. Defaults to False.
            save_on_edit (bool. Defaults to True):
                True to save data for every change.
            save_on_edit_analysis (bool. Defaults to same as save_on_edit):
                save_on_edit parameter for AnalysisManager i.e. data inside analysis_cell
            shell (InteractiveShell | None, optional. Defaults to False):
                could be provided or explicitly set to None. Defaults to get_ipython().
        """
        if shell is False or shell is True:  # behavior by default shell
            from IPython import get_ipython
            self.shell = get_ipython()
        else:  # if any shell is provided. even None
            self.shell = shell

        if use_magic:
            from .acquisition_magic_class import load_ipython_extension
            load_ipython_extension(aqm=self, shell=self.shell)

        if save_on_edit_analysis is None:
            save_on_edit_analysis = save_on_edit

        self._save_on_edit_analysis = save_on_edit_analysis
        self._save_fig_inside_h5 = save_fig_inside_h5

        super().__init__(
            data_directory=data_directory,
            config_files=config_files,
            save_files=save_files,
            save_on_edit=save_on_edit)

    @property
    def current_acquisition(self):
        if self.is_old_data:
            return None
        return super().current_acquisition

    @property
    def current_analysis(self):
        return self._analysis_data

    @property
    def data(self):
        if self._analysis_data is None:
            raise ValueError('No data set')
        return self._analysis_data

    @property
    def d(self):  # pylint: disable=invalid-name
        return self.data

    def save_fig(self,
                 fig: Optional[Figure] = None,
                 name: Optional[Union[str, int]] = None, **kwds):
        if self._analysis_data is None:
            raise ValueError('No data set')

        return self._analysis_data.save_fig(fig=fig, name=name, **kwds)

    def save_analysis_cell(self, name: Optional[str] = None):
        if self._analysis_data is None:
            raise ValueError('No data set')

        if name is None:
            name = self._analysis_data.figure_last_name

        cell = get_current_cell(self.shell)
        self._analysis_data.save_analysis_cell(cell, name)

    def save_fig_and_analysis_cell(self,
                                   fig: Optional[Figure] = None,
                                   name: Optional[Union[str, int]] = None, **kwds):

        self.save_fig(fig=fig, name=name, **kwds)
        self.save_analysis_cell(name=str(name))

    def save_acquisition(self, **kwds):
        super().save_acquisition(**kwds)
        self.load_analysis_data()
        return self

    def load_analysis_data(self, filename: Optional[str] = None):
        filename = filename or str(self.current_filepath)
        if not os.path.exists(filename.rstrip('.h5') + '.h5'):
            raise ValueError(f"Cannot load data from {filename}")

        self._analysis_data = AnalysisData(
            filename, cell=self._analysis_cell_str,
            save_files=self._save_files, save_on_edit=self._save_on_edit_analysis,
            save_fig_inside_h5=self._save_fig_inside_h5)

        self._analysis_data.unlock_data('useful').update(**{'useful': True}).lock_data('useful')

        if self._save_on_edit_analysis is False:
            self._analysis_data.save()

        return self._analysis_data

    def acquisition_cell(self, name: str, cell: Optional[str] = None) -> AcquisitionAnalysisManager:
        self._analysis_cell_str = None
        self._analysis_data = None

        if cell is None and self.shell is not None:
            cell = get_current_cell(self.shell)

        self.new_acquisition(name=name, cell=cell)

        logger.info(os.path.basename(self.current_filepath))

        return self

    def analysis_cell(self, filename: Optional[str] = None, cell: Optional[str] = None) -> AcquisitionAnalysisManager:
        if cell is None and self.shell is not None:
            cell = get_current_cell(self.shell)
            # self.shell.get_local_scope(1)['result'].info.raw_cell  # type: ignore

        if filename:  # getting old data
            self.is_old_data = True
            self._analysis_cell_str = None
            filename = self.get_full_filename(filename)
        else:
            self.is_old_data = False
            filename = str(self.current_filepath)
            self._analysis_cell_str = cell

        logger.info(os.path.basename(filename))

        if os.path.exists(filename.rstrip('.h5') + '.h5'):
            self.load_analysis_data(filename)
        else:
            if self.is_old_data:
                raise ValueError(f"Cannot load data from {filename}")
            self._analysis_data = None
        return self

    def get_analysis_code(self, look_inside: bool = True) -> str:
        if self._analysis_data is None:
            raise ValueError('No data set')

        code = self._analysis_data.get_analysis_code(update_code=look_inside)

        if self.shell is not None:
            self.shell.set_next_input(code)  # type: ignore
        return code

    def get_analysis_fig(self) -> List[Figure]:
        if self._analysis_data is None:
            raise ValueError('No data set')

        return self._analysis_data.get_analysis_fig()

    def get_full_filename(self, filename) -> str:
        if '/' in filename or '\\' in filename:
            return filename

        filename = filename.rstrip('.h5')

        name_with_prefix = lstrip_int(filename)
        if name_with_prefix:
            suffix = name_with_prefix[1]
            return os.path.join(self.get_data_directory(), suffix, filename)
        return filename

    def parse_config(self, config_name: str = "config"):
        if self._analysis_data is None:
            raise ValueError('No data set')

        return self._analysis_data.parse_config(config_name)


def get_current_cell(shell: Any):
    return shell.get_parent()['content']['code']
