from typing import Optional
from . import h5py_utils


class AnalysisData(dict):
    """
    This object is obtained by loading a dataset contained in a .h5 file.
    Datasets can be obtained as in a dictionary: e.g.
    data[freqs]
    """

    def __init__(self, filepath: Optional[str] = None):
        self._fig_index = 0
        self._figure_saved = False
        self._cell: Optional[str] = None
        self._extra_cells: Optional[dict] = None
        self.filepath = filepath
        if filepath is not None:
            self._load_from_h5(filepath)

    def _load_from_h5(self, filepath: str):
        data = h5py_utils.open_h5(filepath.rstrip(".h5") + ".h5")
        for key, value in data.items():
            self[key] = value

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

    def __setitem__(self, key, val):
        super().__setitem__(key, val)
        setattr(self, key, val)

    def update(self, *args, **kwds):
        """
        Make sure the update method works the same as for a dict, but also that
        the keys are appended to the object
        """
        if len(args) > 1:
            raise ValueError("usage: update([E,] **F)")
        if len(args) == 1:
            dic_or_iterable = args[0]
            if hasattr(dic_or_iterable, 'keys'):
                for key in dic_or_iterable.keys():
                    self[key] = dic_or_iterable[key]
            else:
                for key, value in dic_or_iterable:
                    self[key] = dic_or_iterable[key]

        for key, value in kwds.items():
            self[key] = value
