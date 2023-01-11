import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Union
from . import h5py_utils
from .h5_np_array import H5NpArray
from ..utils import async_utils


def editing(func):
    def run_func_and_clean_precalculated_results(self, *args, **kwargs):
        self._last_data_saved = False  # pylint: disable=W0212
        res = func(self, *args, **kwargs)
        self._clean_precalculated_results()  # pylint: disable=W0212
        if self._save_on_edit:  # pylint: disable=W0212
            self.save(just_update=True)
        return res

    return run_func_and_clean_precalculated_results


def check_data_up_to_date(func):
    """It will verify is the data was updated externally
    and load the data if it was. Checks at most once a minute"""

    def verify_file_modif_load_if_needed(self, *args, **kwargs):
        self.pull(auto=True)
        res = func(self, *args, **kwargs)
        return res

    return verify_file_modif_load_if_needed


class SyncData:
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """
    _repr: Optional[str] = None
    _default_attr = ['get', 'items', 'keys', 'pop', 'update', 'values', 'save']
    _last_data_saved: bool = False
    _filepath: Optional[str] = None
    _read_only: Union[bool, Set[str]]
    _raise_file_locked_error: bool = False
    _retry_on_file_locked_error: int = 5
    _last_time_data_checked: float = 0
    _file_modified_time: float = 0

    def __init__(self,
                 filepath_or_data: Optional[Union[str, dict, Path]] = None, /, *,
                 filepath: Optional[Union[str, Path]] = None,
                 save_on_edit: bool = False,
                 read_only: Optional[Union[bool, Set[str]]] = None,
                 overwrite: Optional[bool] = None,
                 data: Optional[dict] = None,
                 open_on_init: bool = True):
        """This class should not contain any not local attributes.
        Look in __setattr__() to see why it would not work."""

        if isinstance(filepath_or_data, dict):
            # print("Data given")
            data = data or filepath_or_data

        if isinstance(filepath_or_data, (str, Path)):
            # print("Filepath given")
            filepath = filepath or filepath_or_data

        if filepath and not isinstance(filepath, str):
            filepath = str(filepath)

        self._data: Dict[str, Any] = data or {}
        self._keys: Set[str] = set(self._data.keys())
        self._last_update = set()
        self._save_on_edit = save_on_edit
        self._classes_should_be_saved_internally = set()

        if read_only is None:
            read_only = (save_on_edit is False and not overwrite) and filepath is not None

        if open_on_init is False and overwrite is True:
            raise ValueError("Cannot overwrite file and open_on_init=False mode")
        self._open_on_init = open_on_init
        self._unopened_keys = set()

        # if keep_up_to_data and read_only is True:
        # raise ValueError("Cannot open file in read-only and keep_up_to_data=True mode")
        # self._keep_up_to_data = keep_up_to_data

        self._read_only = read_only
        if filepath is not None:
            filepath = filepath.rstrip('.h5') + '.h5'

            if (overwrite or save_on_edit) and read_only:
                raise ValueError("""Cannot open file in read_only mode and overwrite it.""")

            if os.path.exists(filepath):
                if overwrite is None and not read_only:
                    raise ValueError("File with the same name already exists. So you\
                        should explicitly provide what to do with it. Set `overwrite=True`\
                        to replace file. Set `overwrite=False` if you want to open existing\
                        file and work with it.")

                if overwrite and not read_only:
                    os.remove(filepath)

                if read_only or (not read_only and not overwrite):
                    if open_on_init:
                        self._load_from_h5(filepath)
                    else:
                        self._keys = h5py_utils.keys_h5(filepath.rstrip(".h5") + ".h5")
                        self._unopened_keys.update(self._keys)

            elif read_only:
                raise ValueError(f"Cannot open file in read_only mode if file {filepath} does not exist")

            # if not read_only:
            self._filepath = filepath

    def _load_from_h5(self, filepath: Optional[str] = None, key: Optional[Union[str, Set[str]]] = None):
        filepath = filepath or self._filepath
        if filepath is None:
            raise ValueError("Filepath is not specified. So cannot load_h5")
        data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5", key=key)
        self._file_modified_time = os.path.getmtime(filepath.rstrip(".h5") + ".h5")
        self._update(data)

    def lock_data(self, keys: Optional[Iterable[str]] = None):
        if self._read_only is True:
            raise ValueError("Cannot lock specific data and everything is locked by read_only mode")
        if not isinstance(self._read_only, set):
            self._read_only = set()
        if keys is None:
            keys = self.keys()
        elif isinstance(keys, str):
            keys = (keys,)

        for key in keys:
            self._read_only.add(key)

        self._clean_precalculated_results()
        return self

    def unlock_data(self, remove_keys: Optional[Iterable[str]] = None):
        if self._read_only is True:
            raise ValueError("Cannot unlock is global read_only mode was set to True")
        if isinstance(self._read_only, set):
            if remove_keys is None:
                self._read_only = False
            else:
                if isinstance(remove_keys, str):
                    remove_keys = (remove_keys,)
                for key in remove_keys:
                    if key in self._read_only:
                        self._read_only.remove(key)

        self._clean_precalculated_results()
        return self

    def _clean_precalculated_results(self):
        self._repr = None

    def __add_key(self, key):
        self._keys.add(key)
        self._last_update.add(key)

    def __del_key(self, key):
        self._keys.remove(key)
        self._last_update.add(key)

    def __check_read_only_true(self, key):
        return self._read_only and \
            (self._read_only is True or key in self._read_only)

    @editing
    def update(self, __m: Optional[dict] = None, **kwds: h5py_utils.DICT_OR_LIST_LIKE):
        if __m is not None:
            kwds.update(__m)

        for key in kwds:  # pylint: disable=C0206
            if self.__check_read_only_true(key):
                raise TypeError(f"Cannot set a read-only '{key}' attribute")
            self.__add_key(key)
            kwds[key] = h5py_utils.transform_to_possible_formats(kwds[key])

        # self.pull(auto=True)
        self._data.update(**kwds)
        return self

    def _update(self, __m: Optional[dict] = None, **kwds: Any):
        """Update only internal data and attributes.
        Can be modified in read_only mode. Did not change a file."""
        if __m is not None:
            kwds.update(__m)

        for key in kwds:
            self._keys.add(key)
            self._unopened_keys.discard(key)

        self._data.update(kwds)

    @editing
    def pop(self, key: str):
        if self.__check_read_only_true(key):
            raise TypeError(f"Cannot pop a read-only '{key}' attribute")
        self.__del_key(key)
        # self.pull(auto=True)
        if key not in self._unopened_keys:
            self._data.pop(key)
        return self

    def get(self, key: str, default: Optional[Any] = None):
        return self.__get_data__(key, default)

    def __getitem__(self, __key: Union[str, tuple]):
        if isinstance(__key, tuple):
            return self.__getitem__(__key[0]).__getitem__(
                __key[1:] if len(__key) > 2 else __key[1])
        return self.__get_data_or_raise__(__key)
        # return self._data.__getitem__(__key)

    @editing
    def __setitem__(self, __key: Union[str, tuple], __value: h5py_utils.DICT_OR_LIST_LIKE) -> None:
        if isinstance(__key, tuple):
            self.__add_key(__key[0])
            return self.__getitem__(__key[0]).__setitem__(
                __key[1:] if len(__key) > 2 else __key[1], __value)

        if self.__check_read_only_true(__key):
            raise TypeError(f"Cannot set a read-only '{__key}' attribute")

        self.__add_key(__key)
        __value = h5py_utils.transform_to_possible_formats(__value)

        if hasattr(__value, "save"):
            self._classes_should_be_saved_internally.add(__key)

        if hasattr(__value, "__init__filepath__"):
            if self._filepath is None:
                raise ValueError("Cannot run __init__filepath__ with file unspecified")

            __value.__init__filepath__(  # type: ignore
                filepath=self._filepath, filekey=__key, save_on_edit=self._save_on_edit)
        self.__set_data__(__key, __value)

    def __delitem__(self, key: str):
        self.pop(key)

    def __getattr__(self, __name: str):
        """Will be called if __getattribute__ does not work"""
        if len(__name) >= 2 and __name[0] == 'i' and \
                __name[1:].isdigit() and __name not in self.keys():
            __name = __name[1:]
        if __name in self.keys():
            data = self.get(__name)
            if isinstance(data, dict) and data:
                return SyncData(data)
            return data
        raise AttributeError(f"No attribute {__name} found in SyncDatas")

    def __setattr__(self, __name: str, __value: h5py_utils.DICT_OR_LIST_LIKE) -> None:
        """Call every time you set an attribute."""
        if __name.startswith('_'):
            return object.__setattr__(self, __name, __value)
        return self.__setitem__(__name, __value)

    def __delattr__(self, __name: str) -> None:
        if __name in self.keys():
            return self.__delitem__(__name)
        return object.__delattr__(self, __name)

    def __get_data__(self, __key: str, __default=None):
        if __key in self._unopened_keys:
            self._load_from_h5(key=__key)
        return self._data.get(__key, __default)

    def __get_data_or_raise__(self, __key):
        # self.pull(auto=True)
        if __key in self._unopened_keys:
            self._load_from_h5(key=__key)
        return self._data.__getitem__(__key)

    def __set_data__(self, __key: str, __value):
        # self.pull(auto=True)
        return self._data.__setitem__(__key, __value)

    def items(self):
        # self.pull(auto=True)
        if self._unopened_keys:
            self._load_from_h5(key=self._unopened_keys)
        return self._data.items()

    def values(self):
        # self.pull(auto=True)
        if self._unopened_keys:
            self._load_from_h5(key=self._unopened_keys)
        return self._data.values()

    def keys(self):
        # self.pull(auto=True)
        return self._keys

    def __iter__(self):
        return iter(self.keys())

    def _get_repr(self):
        # self.pull(auto=True)
        if self._repr is None:
            additional_info = {key: " (r)" for key in self._read_only} if isinstance(self._read_only, set) else None
            self._repr = h5py_utils.output_dict_structure(self._data, additional_info=additional_info) + \
                (f"\nUnloaded keys: {self._unopened_keys}" if self._unopened_keys else "")

    def __repr__(self):
        self._get_repr()

        not_saved = '' if self._last_data_saved or self._read_only is True else " (not saved)"
        mode = 'r' if self._read_only is True else 'w' if self._read_only is False else 'rw'
        mode = 'l' if self._filepath is None and self._read_only is not True else mode
        not_saved = '' if mode == 'l' else not_saved

        return f"{type(self).__name__} ({mode}){not_saved}: \n {self._repr}"

    def __str__(self):
        return self.__repr__()

    def __contains__(self, item):
        return item in self.keys()

    def __dir__(self) -> Iterable[str]:
        return list(self._keys) + self._default_attr

    def save(self, just_update: bool = False, filepath: Optional[str] = None):
        # print(f"saving globally with {just_update=}")
        if self._read_only is True:
            raise ValueError("Cannot save opened in a read-only mode. Should reopen the file")

        self._last_data_saved = True
        last_update, self._last_update = self._last_update, set()

        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        if just_update is False:
            if self._read_only is False:
                data_to_save = self._data
            else:
                data_to_save = {key: value for key, value in self._data.items()
                                if key not in self._read_only or key in last_update}
            self.__h5py_utils_save_dict_with_retry(filepath=filepath, data=data_to_save)

            return self

        for key in last_update:
            if key in self._classes_should_be_saved_internally:
                obj = self._data[key]
                if hasattr(obj, 'save'):
                    self._data[key].save(just_update=just_update)
                else:
                    self._classes_should_be_saved_internally.remove(key)
        self.__h5py_utils_save_dict_with_retry(
            filepath=filepath,
            data={key: self._data.get(key, None) for key in last_update
                  if key not in self._classes_should_be_saved_internally})

        return self

    def __h5py_utils_save_dict_with_retry(self, filepath: str, data: dict):
        # print("open", time.time(), self._raise_file_locked_error)
        for i in range(self._retry_on_file_locked_error):
            try:
                # print("_raise_file_locked_error", self._raise_file_locked_error, list(data.keys()))
                self._file_modified_time = h5py_utils.save_dict(
                    filename=filepath + '.h5',
                    data=data
                )
                return
            except h5py_utils.FileLockedError as error:
                if self._raise_file_locked_error:
                    raise error
                logging.info("File is locked. waiting 2s and %d more retrying.", i)
                async_utils.sleep(2)

        raise h5py_utils.FileLockedError(
            f"Even after {self._retry_on_file_locked_error} data was not saved")

    @staticmethod
    def _check_if_filepath_was_set(filepath: Optional[str], filepath2: Optional[str]) -> str:
        """
        Returns path to the file with filename, but without extension."""
        filepath = filepath or filepath2
        if filepath is None:
            raise ValueError("Should provide filepath or set self.filepath before saving")
        filepath = filepath.rstrip('.h5')
        return filepath

    @property
    def filepath(self):
        return None if self._filepath is None else self._filepath.rstrip('.h5')

    def _asdict(self):
        return self._data

    def h5nparray(self, data) -> H5NpArray:
        return data.view(H5NpArray)

    def create_item_as_instance(self, cls, key, *args, **kwds):
        self[key] = cls(*args, **kwds)

    def pull(self, force_pull: bool = False):
        # if self._keep_up_to_data is False or self._file_modified_time == 0:
        # return

        if self.filepath is None:
            raise ValueError("Cannot pull from file if it's not been set")

        # if auto:
        #     now = time.time()
        #     if (now-self._last_time_data_checked) < 1:
        #         return
        #     self._last_time_data_checked = now

        file_modified = os.path.getmtime(self.filepath + '.h5') if force_pull is False else 0

        if self._file_modified_time != file_modified or force_pull:
            logging.info('File modified so it will be reloaded.')
            # if key is None:
            self._data = {}
            self._keys = set()
            self._clean_precalculated_results()
            self._load_from_h5()

        return self

    def _update_data_from_file(self):
        pass
