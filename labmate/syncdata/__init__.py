"""SyncData module. Main class is SyncData. It's a dictionary that is synchronized with .h5 file.

Also this module contains h5py_utils that allows to save and load dict from a h5 file.

Examples:
---------
>>> from labmate.syncdata import SyncData
>>> data = SyncData("some_file.h5", mode='w')
>>> data["some_key"] = "some_value"
>>> data.save()

>>> data = SyncData("some_file.h5", mode='r')
>>> data["some_key"] # -> "some_value"
>>> data["some_key"] = "some_other_value" # -> KeyError: Cannot change value in read mode

"""


# flake8: noqa: F401
from .syncdata_class import SyncData
