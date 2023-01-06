import os
import shutil

import unittest

from quanalys.acquisition_utils import AcquisitionManager
from quanalys.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class AcquisitionManagerTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""
    acquisition_cell = "this is a cell"
    experiment_name = "abc"

    def setUp(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name, self.acquisition_cell)

    def test_right_folder_was_created(self):
        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name)))

    def test_cell_saved(self):
        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(sd.get("acquisition_cell"), self.acquisition_cell)

    def test_cell_update(self):
        self.aqm.aq.update(x=2)

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(sd.get("x"), 2)

    def test_save_config(self):
        self.aqm.set_config_file(
            os.path.join(TEST_DIR, "data/line_config.txt"))
        self.aqm.new_acquisition(self.experiment_name, self.acquisition_cell)

        sd = SyncData(self.aqm.aq.filepath)

        self.assertEqual(
            sd.get("configs").get('line_config.txt'),  # type: ignore
            "this is a config file")

    def test_file_was_explicitly_saved_false(self):
        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(sd.get('useful'), False)

    def test_file_was_explicitly_saved_true(self):
        self.aqm.save_acquisition()
        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(sd.get('useful'), True)

    def test_save_acquisition(self):
        self.aqm.save_acquisition(x=5)

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(sd.get('useful'), True)
        self.assertEqual(sd.get("x"), 5)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == '__main__':
    unittest.main()
