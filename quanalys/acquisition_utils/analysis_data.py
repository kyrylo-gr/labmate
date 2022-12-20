from typing import Any, Dict, Iterable, Optional
from . import h5py_utils


def editing(func):
    def run_func_and_clean_precalculated_results(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self._clean_precalculated_results()  # pylint: disable=W0212

    return run_func_and_clean_precalculated_results


class AnalysisData:
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """
    _repr: Optional[str] = None
    _default_attr = ['get', 'items', 'keys', 'pop', 'update', 'values']

    def __init__(self, filepath: Optional[str] = None):
        self._data = {}
        self._attrs = set()

        if filepath is not None:
            self._load_from_h5(filepath)

    def _load_from_h5(self, filepath: str):
        data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5")
        self.update(**data)

    def _clean_precalculated_results(self):
        self._repr = None

    @editing
    def update(self, **kwds: Dict[str, Any]):
        # print("Updating")
        self._data.update(**kwds)
        for key in kwds:
            # print(key, self._attrs)
            self._attrs.add(key)

    @editing
    def pop(self, key: str):
        self._data.pop(key)
        self._attrs.remove(key)

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self._data.get(key, default)

    def __getitem__(self, __key: str) -> Optional[Any]:
        return self._data.__getitem__(__key)

    @editing
    def __setitem__(self, __key: str, __value: Any):
        self._attrs.add(__key)
        return self._data.__setitem__(__key, __value)

    @editing
    def __delitem__(self, key: str):
        self._attrs.remove(key)
        return self.pop(key)

    def __getattr__(self, __name: str) -> Any:
        """Will be called if __getattribute__ does not work"""
        # print(f"custom getting attribute {__name}")
        if __name in self._data:
            return self.get(__name)
        raise AttributeError(f"No attribute {__name} found in AnalysisData")

    def __setattr__(self, __name: str, __value: Any) -> None:
        # print(f"custom settin {__name} {__value}")
        if __name.startswith('_'):
            return object.__setattr__(self, __name, __value)
        return self.__setitem__(__name, __value)

    @editing
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
        return f"AnalysisData: \n {self._repr}"

    def __contains__(self, item):
        return item in self._data

    def __dir__(self) -> Iterable[str]:
        return list(self._attrs) + self._default_attr
