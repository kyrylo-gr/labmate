from typing import Optional
import numpy as np
import h5py


class H5NpArray:
    _filename: Optional[str] = None
    _filekey: Optional[str] = None
    should_not_be_converted = True

    def __init__(self, *arg, **kwargs):
        self.data = np.array(*arg, **kwargs)

    def __init__filepath__(self, *, filepath: str, filekey: str, save_on_edit: bool = False, **_):
        if not save_on_edit:
            raise ValueError("Cannot use H5NpArray is save_on_edit=False")

        self._filename = filepath
        self._filekey = filekey

    def __getitem__(self, __key):
        return self.data.__getitem__(__key)

    def __setitem__(self, __key, __value):
        # print(f"{self._filename=} {self._filekey=}")
        if self._filename and self._filekey:
            with h5py.File(self._filename, 'a') as file:
                if self._filekey not in file.keys():
                    file.create_dataset(self._filekey, shape=self.data.shape)
                file.require_dataset(
                    self._filekey, shape=self.data.shape, dtype=self.data.dtype, exact=True)[__key] = __value

        self.data.__setitem__(__key, __value)

    def __repr__(self) -> str:
        return "H5NpArray:" + self.data.__repr__()

    def _asdict(self):
        return self.data
