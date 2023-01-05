import os
import shutil
# import shutil

import unittest

import numpy as np

from quanalys.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class H5NpArraySaveOnEditTest(unittest.TestCase):
    """Saving different type of variables inside h5"""

    def setUp(self):
        self.sd = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        self.size = (100, 1000)
        self.check = np.zeros(shape=self.size)
        self.sd['test'] = self.sd.h5nparray(self.check)

    def compare(self):
        self.assertTrue(self.compare_np_array(
            self.check, self.sd['test']))

        sd = SyncData(DATA_FILE_PATH)

        self.assertTrue(self.compare_np_array(
            self.check, sd['test']))

    @staticmethod
    def compare_np_array(a1, a2):
        return np.all(a1 == a2)

    @staticmethod
    def create_random_data(size=1000):
        return np.random.randint(0, 100, size)

    def test_zeros(self):
        self.compare()

    def test_horizontal_change(self):
        data = self.create_random_data(self.size[1])
        self.sd['test'][1, :] = data
        self.check[1, :] = data

        self.compare()

    def test_vertical_change(self):
        data = self.create_random_data(self.size[0])
        self.sd['test'][:, 2] = data
        self.check[:, 2] = data

        self.compare()

    def test_for_data(self):
        for i in range(self.size[0]):
            data = self.create_random_data(self.size[1])
            self.sd['test'][i, :] = data
            self.check[i, :] = data

        self.compare()

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class H5NpArrayTest(H5NpArraySaveOnEditTest):
    def setUp(self):
        self.sd = SyncData(DATA_FILE_PATH, save_on_edit=False, overwrite=True)
        self.size = (100, 1000)
        self.check = np.zeros(shape=self.size)
        self.sd['test'] = self.sd.h5nparray(self.check)

    def compare(self):
        self.sd['test'].save(just_update=True)  # pylint: disable=E1101 # type: ignore
        return super().compare()


class H5NpArrayGlobalSaveTest(H5NpArraySaveOnEditTest):

    def compare(self):
        self.sd.save()
        return super().compare()


if __name__ == '__main__':
    unittest.main()
