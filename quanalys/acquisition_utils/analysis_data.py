import os
from typing import Any, Dict, Iterable, Optional
from . import h5py_utils


def editing(func):
    def run_func_and_clean_precalculated_results(self, *args, **kwargs):
        self._last_data_saved = False  # pylint: disable=W0212
        func(self, *args, **kwargs)
        self._clean_precalculated_results()  # pylint: disable=W0212
        if self._save_on_edit:  # pylint: disable=W0212
            self.save(just_update=True)

    return run_func_and_clean_precalculated_results


class AnalysisData:
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """
    _repr: Optional[str] = None
    _default_attr = ['get', 'items', 'keys', 'pop', 'update', 'values', 'save']
    _last_data_saved: bool = False
    _filepath: Optional[str] = None

    def __init__(self,
                 filepath: Optional[str] = None,
                 save_on_edit: bool = False,
                 read_only: Optional[bool] = None,
                 overwrite: Optional[bool] = None):
        """This class should not contain any not local attributes.
        Look in __setattr__() to see why it would not work."""

        self._data = {}
        self._attrs = set()
        self._last_update = set()
        self._save_on_edit = save_on_edit

        if read_only is None:
            read_only = (save_on_edit is False and not overwrite) and filepath is not None

        # print(read_only)

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
                    self._load_from_h5(filepath)
            elif read_only:
                raise ValueError(f"Cannot open file in read_only mode if file {filepath} does not exist")

            if not read_only:
                self._filepath = filepath

    def _load_from_h5(self, filepath: str):
        data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5")
        self._update(**data)

    def _clean_precalculated_results(self):
        self._repr = None

    def __add_key(self, key):
        self._attrs.add(key)
        self._last_update.add(key)

    def __del_key(self, key):
        self._attrs.remove(key)
        self._last_update.add(key)

    @editing
    def update(self, **kwds: Dict[str, Any]):
        # print("Updating")
        for key in kwds:
            if self._read_only:
                raise TypeError("Cannot set a read-only attribute")
            self.__add_key(key)
        self._data.update(**kwds)

    def _update(self, **kwds: Dict[str, Any]):
        for key in kwds:
            self._attrs.add(key)
        self._data.update(**kwds)

    @editing
    def pop(self, key: str):
        if self._read_only:
            raise TypeError("Cannot set a read-only attribute")
        self.__del_key(key)
        self._data.pop(key)

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self._data.get(key, default)

    def __getitem__(self, __key: str) -> Any:
        return self._data.__getitem__(__key)

    @editing
    def __setitem__(self, __key: str, __value: Any):
        if self._read_only:
            raise TypeError("Cannot set a read-only attribute")
        self.__add_key(__key)
        return self._data.__setitem__(__key, __value)

    def __delitem__(self, key: str):
        return self.pop(key)

    def __getattr__(self, __name: str) -> Any:
        """Will be called if __getattribute__ does not work"""
        # print(f"custom getting attribute {__name}")
        if __name in self._data:
            return self.get(__name)
        raise AttributeError(f"No attribute {__name} found in AnalysisData")

    def __setattr__(self, __name: str, __value: Any) -> None:
        """Call every time you set an attribute."""
        if __name.startswith('_'):
            return object.__setattr__(self, __name, __value)
        return self.__setitem__(__name, __value)

    def __delattr__(self, __name: str) -> None:
        if __name in self._data:
            return self.__delitem__(__name)
        return object.__delattr__(self, __name)

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def keys(self):
        return self._data.keys()

    def _get_repr(self):
        if self._repr is None:
            self._repr = h5py_utils.output_dict_structure(self._data)

    def __repr__(self):
        self._get_repr()
        if self._last_data_saved:
            pass
        return f"AnalysisData: \n {self._repr}\nmode: {'r' if self._read_only else 'w'}"

    def __contains__(self, item):
        return item in self._data

    def __dir__(self) -> Iterable[str]:
        return list(self._attrs) + self._default_attr

    def save(self, just_update: bool = False, filepath: Optional[str] = None):
        if self._read_only:
            raise ValueError("Cannot save opened in a read-only mode. Should reopen the file")

        self._last_data_saved = True
        last_update, self._last_update = self._last_update, set()

        filepath = self._check_if_filepath_was_set(filepath, self._filepath)

        if just_update is False:
            return h5py_utils.save_dict(
                filename=filepath + '.h5',
                data=self._data)

        return h5py_utils.save_dict(
            filename=filepath + '.h5',
            data={key: self._data.get(key, None) for key in last_update})

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
        return self._filepath

    def _asdict(self):
        return self._data
