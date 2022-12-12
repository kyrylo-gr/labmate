import logging
from typing import Dict, List, Optional, Union, Any
import numpy as np

from . import h5py_utils


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

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath.rstrip('.h5') if filepath is not None else None
        self.data: Dict[str, Union[List, np.ndarray, dict]] = {}

        self.last_update = set()
        self.__keys = set()

    def __add_key(self, key):
        self.last_update.add(key)
        self.__keys.add(key)

    def __del_key(self, key):
        self.last_update.add(key)
        self.__keys.remove(key)

    @editing
    def update(self, **kwds):
        loop_kwds = {key: value for key, value in kwds.items() if value.__class__.__name__ == "AcquisitionLoop"}
        # print(f"Adding loop {loop_kwds}")
        for key, value in loop_kwds.items():
            # print("Inside loop")
            kwds.pop(key)
            # print(value.data)
            for loop_key, loop_data in value.data.items():
                kwds[f'{key}/{loop_key}'] = loop_data
            kwds[key + '/__loop_shape__'] = value.loop_shape

        for key in kwds:
            self.__add_key(key)

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
        self.last_data_saved = True
        self.last_update = set()
        filepath = filepath or self.filepath
        assert filepath is not None, "Should provide filepath or set self.filepath to save"
        filepath = filepath.rstrip('.h5')
        if just_update is False:
            if self.called_inside_edit is False:  # if command was explicitly called
                logging.info("saving to h5 at %s", filepath + '.h5')
            return h5py_utils.save_dict(
                filename=filepath + '.h5',
                data=self.data)

        return h5py_utils.save_dict(
            filename=filepath + '.h5',
            data={key: self.data.get(key, None) for key in self.last_update})


class NotebookAcquisitionData(AcquisitionData):
    """TODO"""

    def __init__(self, filepath: str, configs: Dict[str, str], cell: Optional[str]):
        super().__init__(filepath=filepath)

        self.configs = configs
        self.cell = cell

    def save_config_files(self):
        for name in self.configs.keys():
            with open(self.filepath + '_' + name, 'w', encoding="utf-8") as file:
                file.write(self.configs[name])

    def save_cell(self):
        if self.cell is None:
            return
        with open(self.filepath + '_CELL.py', 'w', encoding="utf-8") as file:
            file.write(self.cell)
