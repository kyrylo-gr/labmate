"""This file is used during the LockingOfSyncData.
It creates long data and occupies the file.

print("start") is a signal that file is started to be occupied.
"""

# from time import sleep
import smart_import  # noqa # type: ignore # pylint: disable=unused-import

import os
import numpy as np

from labmate.syncdata import SyncData
# from labmate.utils.async_utils import sleep

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")

if os.path.exists(DATA_FILE_PATH):
    os.remove(DATA_FILE_PATH)

big_array = np.zeros(shape=(10000, 5000))

# os.remove(DATA_FILE_PATH)
sd = SyncData(filepath=DATA_FILE_PATH,
              overwrite=True,
              read_only=False,
              save_on_edit=True)

# sd['param0'] = 1
# sd.save()
# sleep(.2)
print("start")
# sleep(.1)

sd['param1'] = big_array
# sd.save()
# with SyncData(DATA_FILE_PATH), 'a') as file:
#     file['array'] = big_array
print("end")
