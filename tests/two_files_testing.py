import os
import subprocess

import numpy as np
from labmate.syncdata import SyncData
# from labmate.syncdata import FileLockedError
TEST_DIR = r'/Users/4cd87a/Documents/Projects/PhD/codes/acquisition_utils/tests/'
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = "/Users/4cd87a/Documents/Projects/PhD/codes/acquisition_utils/tests/tmp_test_data/some_data.h5"


big_array = np.zeros(shape=(5000, 10000))


write_long_data = subprocess.Popen(
    ["python", os.path.join(TEST_DIR, "save_long_data.py")],
    stdout=subprocess.PIPE)

sd = SyncData(DATA_FILE_PATH,
              read_only=False, save_on_edit=True,
              overwrite=False, open_on_init=False)

sd._raise_file_locked_error = True  # pylint: disable=protected-access

s = write_long_data.stdout.readline().decode().strip()  # type: ignore

print(s)
# while(s := write_long_data.stdout.readline().decode().strip()) != "start" or s != "":  # type: ignore
# print(s)

# print()


sd['param2'] = big_array

write_long_data.wait()
