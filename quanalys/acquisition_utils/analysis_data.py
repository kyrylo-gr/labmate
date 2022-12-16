from typing import Any, Dict, Optional
from . import h5py_utils


class AnalysisData:
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """

    def __init__(self, filepath: Optional[str] = None):
        self._data = {}
        self.filepath = filepath
        if filepath is not None:
            self._load_from_h5(filepath)

    def _load_from_h5(self, filepath: str):
        self._data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5")
        # print("load", self._data)
        # if os.path.dirname(filepath) == '' and \
        #         AcquisitionManager.data_directory is not None:  # only filename (no path provided)
        #     experiment_name = filepath[20:].rstrip('.h5')  # strip timestamp
        #     filepath = os.path.join(AcquisitionManager.data_directory, experiment_name, filepath)
        # self.filepath = filepath.rstrip('.h5')
        # with h5py.File(self.filepath + '.h5', 'r') as file:
        #     for key, value in file.items():
        #         if isinstance(value, h5py.Group):
        #             self[key] = AnalysisLoop.load_from_h5(value)
        #         else:
        #             self[key] = value[()]

    # def update(self, *args, **kwds):
    #     """
    #     Make sure the update method works the same as for a dict, but also that
    #     the keys are appended to the object
    #     """
    #     if len(args) > 1:
    #         raise ValueError("usage: update([E,] **F)")
    #     if len(args) == 1:
    #         dic_or_iterable = args[0]
    #         if hasattr(dic_or_iterable, 'keys'):
    #             for key in dic_or_iterable.keys():
    #                 self[key] = dic_or_iterable[key]
    #         else:
    #             for key, value in dic_or_iterable:
    #                 self[key] = dic_or_iterable[key]

    #     for key, value in kwds.items():
    #         self[key] = value

    def update(self, **kwds: Dict[str, Any]):
        self._data.update(kwds)
        for key, value in kwds.items():
            setattr(self, key, value)

    def pop(self, key: str):
        self._data.pop(key)

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self._data.get(key, default)

    def __getitem__(self, __key: str) -> Optional[Any]:
        return self._data.__getitem__(__key)

    def __setitem__(self, __key: str, __value: Any):
        # print("set item", __key, __value)
        setattr(self, __key, __value)
        return self._data.__setitem__(__key, __value)

    def __delitem__(self, key: str):
        return self.pop(key)

    def __delattr__(self, __name: str) -> None:
        if __name in self._data:
            self.__delitem__(__name)
        super().__delattr__(__name)

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def keys(self):
        return self._data.keys()
