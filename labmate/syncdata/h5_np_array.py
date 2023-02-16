import os
from typing import Optional
import numpy as np
import h5py


class SyncNp():
    def __new__(cls, data):
        return data.view(H5NpArray)


class H5NpArray(np.ndarray):
    __filename__: Optional[str] = None
    __filekey__: Optional[str] = None
    __should_not_be_converted__ = True
    __save_on_edit__: bool = False
    __last_changes__: Optional[list] = None

    def __init__filepath__(self, *, filepath: str, filekey: str, save_on_edit: bool = False, **_):
        # if not save_on_edit:
        #     raise ValueError("Cannot use H5NpArray is save_on_edit=False")

        self.__filename__ = filepath
        self.__filekey__ = filekey
        self.__save_on_edit__ = save_on_edit
        self.__last_changes__ = []
        self.save(just_update=False)

    # def __getitem__(self, __key):
    #     return self.data.__getitem__(__key)

    def __setitem__(self, __key, __value):
        if self.__last_changes__ is None:
            self.__last_changes__ = []
        self.__last_changes__.append(__key)

        super().__setitem__(__key, __value)

        if self.__save_on_edit__:
            self.save(just_update=True)

    def save(self, just_update=True):
        # print(f"saving locally with {just_update=} {self.__last_changes__}")

        if self.__last_changes__ is None:
            return self

        if not self.__filename__ or not self.__filekey__:
            raise ValueError("Cannot save changes without filename and filekey provided")

        if not os.path.exists(os.path.dirname(self.__filename__)):
            os.makedirs(os.path.dirname(self.__filename__), exist_ok=True)

        if not just_update:
            with h5py.File(self.__filename__, 'a') as file:
                file[self.__filekey__] = np.asarray(self)
                # file.require_dataset(
                # self.__filekey__, shape=self.shape, dtype=self.dtype, exact=True)[:] = np.asarray(self)

        for key in self.__last_changes__:
            with h5py.File(self.__filename__, 'a') as file:
                if self.__filekey__ not in file.keys():
                    file.create_dataset(self.__filekey__, shape=self.data.shape)
                file[self.__filekey__][key] = self[key]  # type: ignore
                # file.require_dataset(
                # self.__filekey__, shape=self.shape, dtype=self.dtype, exact=False)[key] = self[key]

        self.__last_changes__ = []
        return self
