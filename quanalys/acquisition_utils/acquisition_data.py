import logging
import os
from typing import Dict, List, Optional, Protocol, Union, Any
import numpy as np

from . import h5py_utils


class ClassWithAsdict(Protocol):
    """Any class with predefined `_asdict` attribute.
    `_asdict` class should return a dictionary with only list and dict.
    It should not be a dict of other classes"""

    def _asdict(self, *args, **kwargs) -> dict:
        ...


def editing(func):
    def run_func_and_save_results(self, *args, **kwargs):
        self.last_data_saved = False
        self.called_inside_edit = True
        func(self, *args, **kwargs)
        if self.save_on_edit:
            self.save(just_update=True)
        self.called_inside_edit = False

    return run_func_and_save_results


class AcquisitionData:
    """TODO"""
    called_inside_edit = False
    save_on_edit = False
    last_data_saved = False

    def __init__(self, filepath: Optional[str] = None, replace: Optional[bool] = None):
        self.filepath = filepath.rstrip('.h5') if filepath is not None else None
        self.data: Dict[str, Union[List, np.ndarray, dict]] = {}

        self.last_update = set()
        self.__keys = set()

        if self.filepath is not None:
            if os.path.exists(self.filepath+'.h5'):
                if replace is None:
                    raise ValueError("""File with the same name already exists. So you
                        should explicitly provide what to do with it. Set `replace=True`
                        to replace file. Set `replace=False` if you want to open existing
                        file and work with it.""")
                if replace:
                    os.remove(self.filepath + '.h5')
                else:
                    self.data = h5py_utils.open_h5(self.filepath + '.h5')
                    for key in self.data:
                        self.__keys.add(key)

    def __add_key(self, key):
        self.last_update.add(key)
        self.__keys.add(key)

    def __del_key(self, key):
        self.last_update.add(key)
        self.__keys.remove(key)

    @editing
    def update(self, **kwds: Dict[str, Union[list, np.ndarray, dict, ClassWithAsdict]]):
        for key, value in kwds.items():
            self.__add_key(key)
            # print(key, hasattr(value, '_asdict'), "u")
            if hasattr(value, '_asdict'):
                kwds[key] = value._asdict()  # type: ignore

        self.data.update(kwds)

    @editing
    def pop(self, key: str):
        self.__del_key(key)
        self.data.pop(key)

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Optional[Any]:
        return self.data.get(key, None)

    def __setitem__(self, key: str, value: Any):
        return self.update(**{key: value})

    def __delitem__(self, key: str):
        return self.pop(key)

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def keys(self):
        return tuple(self.__keys)

    def save(self, just_update: bool = False, filepath: Optional[str] = None):
        # print("Saving")
        self.last_data_saved = True
        last_update = self.last_update
        self.last_update = set()
        filepath = self._check_if_filepath_was_set(filepath, self.filepath)
        if just_update is False:
            if self.called_inside_edit is False:  # if command was explicitly called
                logging.info("saving to h5 at %s", filepath + '.h5')
            # print(f"saving to {filepath} from zero")
            return h5py_utils.save_dict(
                filename=filepath + '.h5',
                data=self.data)

        return h5py_utils.save_dict(
            filename=filepath + '.h5',
            data={key: self.data.get(key, None) for key in last_update})

    @staticmethod
    def _check_if_filepath_was_set(filepath: Optional[str], filepath2: Optional[str]) -> str:
        """
        Returns path to the file with filename, but without extension."""
        filepath = filepath or filepath2
        if filepath is None:
            raise ValueError("Should provide filepath or set self.filepath before saving")
        filepath = filepath.rstrip('.h5')
        return filepath


class NotebookAcquisitionData(AcquisitionData):
    """TODO"""

    def __init__(self,
                 filepath: str,
                 configs: Optional[Dict[str, str]] = None,
                 cell: Optional[str] = None,
                 replace: Optional[bool] = True):
        super().__init__(filepath=filepath, replace=replace)

        self.configs = configs
        self.cell = cell

    def save_config_files(self, configs: Optional[Dict[str, str]] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self.filepath)
        configs = configs or self.configs
        if configs is None:
            return
        for name, value in configs.items():
            with open(filepath + '_' + name, 'w', encoding="utf-8") as file:
                file.write(value)

    def save_cell(self, cell: Optional[str] = None, filepath: Optional[str] = None):
        filepath = self._check_if_filepath_was_set(filepath, self.filepath)

        cell = cell or self.cell
        if cell is None:
            return

        with open(filepath + '_CELL.py', 'w', encoding="utf-8") as file:
            file.write(cell)
