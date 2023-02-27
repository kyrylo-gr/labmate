import os
import shutil

import unittest

from labmate.acquisition import AcquisitionManager
from labmate.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class AcquisitionManagerTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""
    acquisition_cell = "this is a cell"
    experiment_name = "abc"

    def setUp(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name)

    def load_data(self):
        return SyncData(self.aqm.aq.filepath)

    def test_right_folder_was_created(self):
        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name)))

    def test_right_folder_was_created_environment(self):
        os.environ['ACQUISITION_DIR'] = DATA_DIR
        self.aqm = AcquisitionManager()
        experiment_name = "abc1"
        self.aqm.new_acquisition(experiment_name)
        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, experiment_name)))
        del os.environ['ACQUISITION_DIR']

    def test_no_dir_provided_restore_from_cache(self):
        with self.assertRaises(ValueError):
            self.aqm = AcquisitionManager()

    def test_create_init_analyse_file(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        with open(os.path.join(DATA_DIR, "random.py"), 'w', encoding="utf-8") as file:
            file.write(self.acquisition_cell)

        self.aqm.set_init_analyse_file(os.path.join(DATA_DIR, "random.py"))
        self.aqm.new_acquisition(self.experiment_name)
        with open(os.path.join(DATA_DIR, self.experiment_name, "init_analyse.py"), 'r', encoding='utf-8') as file:
            code = file.read()
        self.assertEqual(code, self.acquisition_cell)

    def test_no_cell(self):
        sd = self.load_data()
        self.assertNotIn("acquisition_cell", sd)

    def test_cell_saved(self):
        self.aqm.new_acquisition(self.experiment_name, self.acquisition_cell)
        sd = self.load_data()
        self.assertEqual(sd.get("acquisition_cell"), self.acquisition_cell)

    def test_cell_update(self):
        self.aqm.aq.update(x=2)

        sd = self.load_data()
        self.assertEqual(sd.get("x"), 2)

    def test_save_config(self):
        self.aqm.set_config_file(
            os.path.join(TEST_DIR, "data/line_config.txt"))
        self.aqm.new_acquisition(self.experiment_name, self.acquisition_cell)

        sd = self.load_data()

        self.assertEqual(
            sd.get("configs", {}).get('line_config.txt'),
            "this is a config file")

    def test_save_config2(self):
        self.aqm.set_config_file(
            [os.path.join(TEST_DIR, "data/line_config.txt"),
             os.path.join(TEST_DIR, "data/line_config2.txt")])
        self.aqm.new_acquisition(self.experiment_name, self.acquisition_cell)

        sd = self.load_data()

        self.assertEqual(
            sd.get("configs", {}).get('line_config.txt'),
            "this is a config file")

        self.assertEqual(
            sd.get("configs", {}).get('line_config2.txt'),
            "this is a config file2")

    def test_save_config_environment(self):
        self.aqm = AcquisitionManager(DATA_DIR, config_files=[os.path.join(TEST_DIR, "data/line_config.txt"),
                                                              os.path.join(TEST_DIR, "data/line_config2.txt")])

        self.aqm.new_acquisition(self.experiment_name)

        sd = self.load_data()

        self.assertEqual(
            sd.get("configs", {}).get('line_config.txt'),
            "this is a config file")

        self.assertEqual(
            sd.get("configs", {}).get('line_config2.txt'),
            "this is a config file2")

    def test_save_config_param(self):
        os.environ['ACQUISITION_CONFIG_FILES'] = ",".join(
            [os.path.join(TEST_DIR, "data/line_config.txt"),
             os.path.join(TEST_DIR, "data/line_config2.txt")])
        self.setUp()

        sd = self.load_data()

        self.assertEqual(
            sd.get("configs", {}).get('line_config.txt'),
            "this is a config file")

        self.assertEqual(
            sd.get("configs", {}).get('line_config2.txt'),
            "this is a config file2")

    def test_file_was_explicitly_saved_false(self):
        sd = self.load_data()
        self.assertEqual(sd.get('useful'), False)

    def test_file_was_explicitly_saved_true(self):
        self.aqm.save_acquisition()

        sd = self.load_data()
        self.assertEqual(sd.get('useful'), True)

    def test_save_acquisition(self):
        self.aqm.save_acquisition(x=5, y=6)

        sd = self.load_data()
        self.assertEqual(sd.get('useful'), True)
        self.assertEqual(sd.get("x"), 5)
        self.assertEqual(sd.get("y"), 6)

    def test_current_experiment_name(self):
        self.assertEqual(self.aqm.current_experiment_name, self.experiment_name)

    def test_current_filepath(self):
        self.assertEqual(str(self.aqm.aq.filepath), str(self.aqm.current_filepath))

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == '__main__':
    unittest.main()
