"""SyncData class is a dictionary that is synchronized with .h5 file."""
from typing import Any, Dict, Iterable, Literal, Optional, Set, TypeVar, Union, overload

import logging
import os
from pathlib import Path
from functools import wraps

from . import h5py_utils
from .data_transformation import transform_to_possible_formats
from .dict_structure import get_keys_structure, output_dict_structure

from .types import DICT_OR_LIST_LIKE


def editing(func):
    """If a function changes the data it should be saved.
    It's a wrapper for such function.
    """

    @wraps(func)
    def run_func_and_clean_precalculated_results(self, *args, **kwargs):
        self._last_data_saved = False  # pylint: disable=W0212
        res = func(self, *args, **kwargs)
        self._clean_precalculated_results()  # pylint: disable=W0212
        if self._save_on_edit:  # pylint: disable=W0212
            self.save(only_update=True)
        return res

    return run_func_and_clean_precalculated_results


_T = TypeVar("_T")


class NotLoaded:
    """Internal class for data that has not been loaded yet."""

    def __init__(self):
        pass

    def __str__(self) -> str:
        return """This key is not loaded. If you see this message,
                it means that you accessed the key not via SyncData object"""

    def __repr__(self) -> str:
        return """This key is not loaded"""


class SyncData:
    """Dict that is synchronized with .h5 file.

    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]

    This class should not contain any not local attributes.
    Look in __setattr__() to see why it would not work.
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
    __should_not_be_converted__ = True

    def __init__(
        self,
        filepath_or_data: Optional[Union[str, dict, Path]] = None,
        /,
        mode: Optional[Literal['r', 'w', 'a', 'w=', 'a=']] = None,
        *,
        filepath: Optional[Union[str, Path]] = None,
        save_on_edit: bool = False,
        read_only: Optional[Union[bool, Set[str]]] = None,
        overwrite: Optional[bool] = None,
        data: Optional[dict] = None,
        open_on_init: Optional[bool] = None,
        **kwds,
    ):
        """SyncData.

        Args:
            filepath_or_data (str|dict, optional): either filepath, either data as dict.
            filepath (str|Path, optional): filepath to load. Defaults to None.
            save_on_edit (bool, optional): do you what to save file every time it edited. Defaults to False.
            read_only (bool, optional): opens file in read_only mode, i.e. it cannot be modified.
                Defaults to (save_on_edit is False && overwrite is False) and filepath is set.
            overwrite (Optional[bool], optional):
                If file exists, it should be explicitly precised.
                By default raises an error if file exist.
            data (Optional[dict], optional):
                Data to load. If data provided, file . Defaults to None.
            open_on_init (Optional[bool], optional): open_on_init. Defaults to True.

        """
        if mode is not None:
            if mode.startswith('w'):
                read_only = False
                overwrite = True
            elif mode.startswith('a'):
                read_only = False
                overwrite = False
            elif mode == 'r':
                read_only = True
            if mode.endswith('='):
                save_on_edit = True

        if filepath_or_data is not None and hasattr(filepath_or_data, "keys"):
            if not isinstance(filepath_or_data, dict):
                filepath_or_data = {key: filepath_or_data[key] for key in filepath_or_data.keys()}  # type: ignore
            data = data or filepath_or_data

        if isinstance(filepath_or_data, (str, Path)):
            filepath = filepath or filepath_or_data

        if filepath and not isinstance(filepath, str):
            filepath = str(filepath)

        self._data: Dict[str, Any] = data or {}
        self._keys: Set[str] = set(self._data.keys())
        self._last_update = set()
        self._save_on_edit = save_on_edit
        self._classes_should_be_saved_internally = set()
        self._key_prefix: Optional[str] = kwds.get("key_prefix")

        if read_only is None:
            read_only = (save_on_edit is False and not overwrite) and filepath is not None

        if open_on_init is False and overwrite is True:
            raise ValueError("Cannot overwrite file and open_on_init=False mode")
        self._open_on_init = (
            open_on_init if open_on_init is not None else (None if self._data else True)
        )
        self._unopened_keys = set()

        # if keep_up_to_data and read_only is True:
        # raise ValueError("Cannot open file in read-only and keep_up_to_data=True mode")
        # self._keep_up_to_data = keep_up_to_data

        self._read_only = read_only
        if filepath is not None:
            filepath = filepath if filepath.endswith('.h5') else filepath + '.h5'

            if (overwrite or save_on_edit) and read_only:
                raise ValueError("""Cannot open file in read_only mode and overwrite it.""")

            if os.path.exists(filepath):
                if overwrite is None and not read_only:
                    raise ValueError(
                        "File with the same name already exists. So you should explicitly "
                        "provide what to do with it. Set `overwrite=True` to replace file. "
                        "Set `overwrite=False` if you want to open existing file and work with it."
                    )

                if overwrite and not read_only:
                    os.remove(filepath)

                if read_only or (not read_only and not overwrite):
                    if self._open_on_init:
                        self._load_from_h5(filepath)
                    elif self._open_on_init is False:
                        self._keys = h5py_utils.keys_h5(filepath, key_prefix=self._key_prefix)
                        self._unopened_keys.update(self._keys)

            elif read_only:
                raise ValueError(
                    f"Cannot open file in read_only mode if file {filepath} does not exist"
                )

            # if not read_only:
            self._filepath = filepath

    def __init__filepath__(self, *, filepath: str, filekey: str, save_on_edit: bool = False, **_):
        self._filepath = filepath
        self._key_prefix = filekey
        self._save_on_edit = save_on_edit

    def _load_from_h5(
        self, filepath: Optional[str] = None, key: Optional[Union[str, Set[str]]] = None
    ):
        filepath = filepath or self._filepath
        if filepath is None:
            raise ValueError("Filepath is not specified. So cannot load_h5")
        filepath = filepath if filepath.endswith('.h5') else filepath + '.h5'
        data = h5py_utils.open_h5(filepath, key=key, key_prefix=self._key_prefix)
        self._file_modified_time = os.path.getmtime(filepath)
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
        return (self._read_only) and (self._read_only is True or key in self._read_only)

    @editing
    def update(self, __m: Optional[dict] = None, **kwds: 'DICT_OR_LIST_LIKE'):
        if __m is not None:
            kwds.update(__m)

        for key in kwds:  # pylint: disable=C0206
            if self.__check_read_only_true(key):
                raise KeyError(f"Cannot set a read-only '{key}' attribute")
            self.__add_key(key)
            kwds[key] = transform_to_possible_formats(kwds[key])

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
            raise KeyError(f"Cannot pop a read-only '{key}' attribute")
        self.__del_key(key)
        # self.pull(auto=True)
        if key not in self._unopened_keys:
            self._data.pop(key)
            return self

    @overload
    def get_dict(self, __key: str) -> Any:
        """Return element as a dict. Return None if not found."""

    @overload
    def get_dict(self, __key: str, __default: _T) -> Union[Any, _T]:
        """With default value provided."""

    def get_dict(self, key: str, default: Any = None):
        return self.__get_data__(key, default)

    @overload
    def get(self, __key: str) -> Any:
        """Return element as a SyncData class if it's dict. Return None if not found."""

    @overload
    def get(self, __key: str, __default: _T) -> Union[Any, _T]:
        """With default value provided."""

    def get(self, key: str, default: Any = None):
        data = self.__get_data__(key, default)
        if isinstance(data, dict) and data:
            return SyncData(filepath=self._filepath, data=data, key_prefix=key)
        return data

    def __getitem__(self, __key: Union[str, tuple]):
        if isinstance(__key, tuple):
            return self.__getitem__(__key[0]).__getitem__(__key[1:] if len(__key) > 2 else __key[1])
        return self.__get_data_or_raise__(__key)
        # return self._data.__getitem__(__key)

    @editing
    def __setitem__(self, __key: Union[str, tuple], __value: 'DICT_OR_LIST_LIKE') -> None:
        if isinstance(__key, tuple):
            self.__add_key(__key[0])
            return self.__getitem__(__key[0]).__setitem__(
                __key[1:] if len(__key) > 2 else __key[1], __value
            )

        if self.__check_read_only_true(__key):
            raise KeyError(f"Cannot set a read-only '{__key}' attribute")

        self.__add_key(__key)
        __value = transform_to_possible_formats(__value)

        if self._read_only is not True:
            if hasattr(__value, "save"):
                self._classes_should_be_saved_internally.add(__key)

            if hasattr(__value, "__init__filepath__") and self._filepath:
                key = __key if self._key_prefix is None else f"{self._key_prefix}/{__key}"
                __value.__init__filepath__(  # type: ignore
                    filepath=self._filepath, filekey=key, save_on_edit=self._save_on_edit
                )

            if hasattr(__value, '__post__init__'):
                __value.__post__init__()  # type: ignore

        self.__set_data__(__key, __value)
        return None

    def __delitem__(self, key: str):
        self.pop(key)

    def __getattr__(self, __name: str):
        """Call if __getattribute__ does not work."""
        if len(__name) > 1 and __name[0] == 'i' and __name[1:].isdigit() and __name not in self:
            __name = __name[1:]
        if __name in self:
            data = self.get(__name)
            # if isinstance(data, dict) and data:
            #     return SyncData(filepath=self._filepath, data=data, key_prefix=__name)
            return data
        raise AttributeError(f"No attribute {__name} found in SyncData")

    def __setattr__(self, __name: str, __value: 'DICT_OR_LIST_LIKE') -> None:
        """Call every time you set an attribute."""
        if __name.startswith('_'):
            return object.__setattr__(self, __name, __value)

        if isinstance(vars(self.__class__).get(__name), property):
            return object.__setattr__(self, __name, __value)
        return self.__setitem__(__name, __value)

    def __delattr__(self, __name: str) -> None:
        if __name in self:
            return self.__delitem__(__name)
        return object.__delattr__(self, __name)

    @overload
    def __get_data__(self, __key: str) -> Optional[None]:
        """Return None if the data doesn't contain key."""

    @overload
    def __get_data__(self, __key: str, __default: _T) -> Union[Any, _T]:
        """Return default value if the data doesn't contain key."""

    def __get_data__(self, __key: str, __default: Any = None):
        if __key in self._unopened_keys:
            self._load_from_h5(key=__key)
        data = self._data.get(__key, __default)
        if isinstance(data, NotLoaded):
            self._load_from_h5(key=__key)
            data = self._data.get(__key, __default)
        return data

    def __get_data_or_raise__(self, __key):
        # self.pull(auto=True)
        if __key in self._unopened_keys:
            self._load_from_h5(key=__key)
        data = self._data.__getitem__(__key)
        if isinstance(data, NotLoaded):
            self._load_from_h5(key=__key)
            data = self._data.__getitem__(__key)
        return data

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

    def keys(self) -> Set[str]:
        # self.pull(auto=True)
        return self._keys.copy().union(self._unopened_keys.copy())

    def keys_tree(self) -> Dict[str, Optional[dict]]:
        """Tree of the keys. Used for h5viewer."""
        structure = get_keys_structure(self._data)

        for key in self._unopened_keys:
            structure[key] = None
        return structure

    def __iter__(self):
        return iter(self.keys())

    def _get_repr(self):
        # self.pull(auto=True)
        if self._repr is None:
            additional_info = (
                {key: " (r)" for key in self._read_only}
                if isinstance(self._read_only, set)
                else None
            )
            self._repr = output_dict_structure(self._data, additional_info=additional_info) + (
                f"\nUnloaded keys: {self._unopened_keys}" if self._unopened_keys else ""
            )

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
        return (item in self._data) or (item in self._unopened_keys)

    def __dir__(self) -> Iterable[str]:
        return list(self._keys) + self._default_attr

    def save(
        self,
        only_update: Union[bool, Iterable[str]] = True,
        filepath: Optional[str] = None,
        force: Optional[bool] = None,
    ):
        if force is True:
            only_update = False
        if self._read_only is True:
            raise ValueError("Cannot save opened in a read-only mode. Should reopen the file")
        if isinstance(only_update, Iterable):
            last_update = self._last_update.intersection(only_update)
            self._last_update = self._last_update.difference(only_update)
        else:
            last_update, self._last_update = self._last_update, set()

        if len(self._last_update) == 0:
            self._last_data_saved = True

        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        if only_update is False:
            if self._read_only is False:
                data_to_save = self._data
            else:
                data_to_save = {
                    key: value
                    for key, value in self._data.items()
                    if key not in self._read_only or key in last_update
                }
            data_to_save.update(
                {
                    key: None
                    for key in last_update
                    if (key not in self._data) and not self.__check_read_only_true(key)
                }
            )

            self.__h5py_utils_save_dict_with_retry(filepath=filepath, data=data_to_save)

            return self

        for key in last_update:
            if key in self._classes_should_be_saved_internally:
                obj = self._data[key]
                if hasattr(obj, 'save'):
                    self._data[key].save(only_update=only_update)
                else:
                    self._classes_should_be_saved_internally.remove(key)

        self.__h5py_utils_save_dict_with_retry(
            filepath=filepath,
            data={
                key: self._data.get(key)
                for key in last_update
                if key not in self._classes_should_be_saved_internally
            },
        )

        return self

    def __h5py_utils_save_dict_with_retry(self, filepath: str, data: dict):
        # print("open", time.time(), self._raise_file_locked_error)
        for i in range(self._retry_on_file_locked_error):
            try:
                # print("_raise_file_locked_error", self._raise_file_locked_error, list(data.keys()))
                self._file_modified_time = h5py_utils.save_dict(
                    filename=filepath + '.h5', data=data, key_prefix=self._key_prefix
                )
                return
            except h5py_utils.FileLockedError as error:
                if self._raise_file_locked_error:
                    raise error
                logging.info("File is locked. waiting 2s and %d more retrying.", i)
                from ..utils import async_utils

                async_utils.sleep(1)

        raise h5py_utils.FileLockedError(
            f"Even after {self._retry_on_file_locked_error} data was not saved"
        )

    @staticmethod
    def _check_if_filepath_was_set(filepath: Optional[str], filepath2: Optional[str]) -> str:
        """Return path to the file with filename, but without extension."""
        filepath = filepath or filepath2
        if filepath is None:
            raise ValueError("Should provide filepath or set self.filepath before saving")
        filepath = (filepath.rsplit('.h5', 1)[0]) if filepath.endswith('.h5') else filepath
        return filepath

    @property
    def filepath(self):
        return None if self._filepath is None else (self._filepath.rsplit('.h5', 1)[0])

    @filepath.setter
    def filepath(self, value: str):
        if not isinstance(value, str):
            value = str(value)
        self._filepath = value if value.endswith('.h5') else value + '.h5'

    @property
    def filename(self) -> Optional[str]:
        filepath = self.filepath
        if filepath is None:
            return None
        return os.path.basename(filepath)

    @property
    def save_on_edit(self):
        return self._save_on_edit

    def asdict(self):
        return self._data

    def pull_available(self):
        if self.filepath is None:
            raise ValueError("Cannot pull from file if it's not been set")
        file_modified = os.path.getmtime(self.filepath + '.h5')
        return self._file_modified_time != file_modified

    def pull(self, force_pull: bool = False):
        if self.filepath is None:
            raise ValueError("Cannot pull from file if it's not been set")

        if force_pull or self.pull_available():
            logging.debug('File modified so it will be reloaded.')
            self._data = {}
            self._keys = set()
            self._clean_precalculated_results()
            self._load_from_h5()

        return self

    @overload
    def close_key(self, key: None = None, every: Literal[True] = True):
        """Close every opened key so it could be collected by the garbage collector afterwards."""

    @overload
    def close_key(self, key: Iterable[str]):
        """Close every key provided so it could be collected by the garbage collector afterwards."""

    @overload
    def close_key(self, key: str):
        """Close the key so it could be collected by the garbage collector afterwards."""

    def close_key(
        self,
        key: Optional[Union[str, Iterable[str]]] = None,
        every: Optional[Literal[True]] = None,
    ):
        """Close the key so it could be collected by the garbage collector afterwards.

        Args:
            key (str | Iterable[str], optional): key or keys that should be closed. Defaults to None.
            every (True, optional): put to True if all keys should be closed. Defaults to None.

        Raises:
            ValueError: if both key and every are not provided.

        Returns:
            self.__class__: Self
        """
        if every is True:
            for k in self.keys():
                self.close_key(k)
            return self
        elif key is None:
            raise ValueError("Should provide key or every=True.")

        if not isinstance(key, str):
            for k in key:
                self.close_key(k)
            return self

        if key not in self._unopened_keys:
            self._data.pop(key)
        self._unopened_keys.add(key)

        return self
