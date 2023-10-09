import os
from typing import Optional
import numpy as np
import h5py


class SyncNp(np.ndarray):
    __filename__: Optional[str] = None
    __filekey__: Optional[str] = None
    __should_not_be_converted__ = True
    __save_on_edit__: bool = False
    __last_changes__: Optional[list] = None
    __should_initialized__: bool = False

    def __new__(cls, data):
        if isinstance(data, list):
            data = np.array(data)
        if isinstance(data, tuple):
            data = np.zeros(shape=data)
        if isinstance(data, SyncNp):
            return data
        data = data.view(cls)
        return data

    def __init__filepath__(self, *, filepath: str, filekey: str, save_on_edit: bool = False, **_):
        self.__filename__ = filepath
        self.__filekey__ = filekey
        self.__save_on_edit__ = save_on_edit
        if self.__last_changes__ is None:
            self.__last_changes__ = []
        self.__should_initialized__ = True
        if self.__save_on_edit__:  # or not self.__initialized__:
            self.save(only_update=False)

    def __setitem__(self, __key, __value):
        if self.__last_changes__ is None:
            self.__last_changes__ = []
        self.__last_changes__.append(__key)

        super().__setitem__(__key, __value)

        if self.__save_on_edit__:
            self.save(only_update=True)

    def save(self, only_update=True):
        if self.__last_changes__ is None:
            return self

        if not self.__filename__ or not self.__filekey__:
            raise ValueError("Cannot save changes without filename and filekey provided")

        if os.path.dirname(self.__filename__) and not os.path.exists(
            os.path.dirname(self.__filename__)
        ):
            os.makedirs(os.path.dirname(self.__filename__), exist_ok=True)

        if not only_update:
            self.__should_initialized__ = False
            with h5py.File(self.__filename__, "a") as file:
                if self.__filekey__ in file:
                    del file[self.__filekey__]
                file[self.__filekey__] = np.asarray(self)

        with h5py.File(self.__filename__, "a") as file:
            if self.__filekey__ not in file or self.__should_initialized__:
                if self.__filekey__ in file:
                    del file[self.__filekey__]
                file[self.__filekey__] = np.asarray(self)
                self.__should_initialized__ = False

            for key in self.__last_changes__:
                file[self.__filekey__][key] = self[key]  # type: ignore

        self.__last_changes__ = []
        return self

    def asarray(self):
        return self.view(np.ndarray)
