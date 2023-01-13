import os
import shutil

import unittest

from quanalys.acquisition_utils import AcquisitionManager, AnalysisManager
from quanalys.acquisition_utils.acquisition_manager import read_config_files
from quanalys.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class AnalysisManagerTest(unittest.TestCase):
    """Test that AnalysisManagerTest should perform as dictionary"""
    analysis_cell = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq.update(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.am = AnalysisManager(self.aqm.current_filepath, cell=self.analysis_cell)

    def test_open_read_mode(self):
        self.assertEqual(self.am.get('x', [])[0], 1)  # pylint: disable=E1136
        with self.assertRaises(TypeError, msg="Data is not locked"):
            self.am['x'] = 2

        self.am['z'] = 3

        sd = SyncData(self.am.filepath)
        self.assertEqual(sd.get('z'), 3)

    def test_analysis_cell(self):
        sd = SyncData(self.aqm.aq.filepath)
        analysis_cell = sd.get("analysis_cell")
        if isinstance(analysis_cell, bytes):
            analysis_cell = analysis_cell.decode()
        self.assertEqual(
            analysis_cell, self.analysis_cell)

    def test_save_fig(self):
        fig = SimpleSaveFig()
        self.am.save_fig(fig)  # type: ignore

        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name, self.aqm.current_filepath + '_FIG1.pdf')))

    def test_save_fig_given_number(self):
        fig = SimpleSaveFig()
        self.am.save_fig(fig, 123)  # type: ignore

        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name, self.aqm.current_filepath + '_FIG123.pdf')))

    def test_save_fig_given_name(self):
        fig = SimpleSaveFig()
        self.am.save_fig(fig, "abc")  # type: ignore

        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name, self.aqm.current_filepath + '_FIG_abc.pdf')))

    def test_parse_file(self):
        """This is no an obvious way to save config files"""
        config = (os.path.join(TEST_DIR, "data/config.txt"))
        self.aqm.aq['configs'] = read_config_files([config])

        self.am = AnalysisManager(self.aqm.current_filepath)
        # print(self.am.parse_config("config.txt"))
        self.compare_config()

    def test_parse_file_pushing_from_begging(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition."""
        config = (os.path.join(TEST_DIR, "data/config.txt"))

        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.set_config_file(config)
        self.aqm.new_acquisition(self.experiment_name)

        self.am = AnalysisManager(self.aqm.current_filepath)
        # print(self.am.parse_config("config.txt"))
        self.compare_config()

    def compare_config(self):
        self.am = AnalysisManager(self.aqm.current_filepath)
        data = self.am.parse_config("config.txt")

        self.assertEqual(data['int'], 123)
        self.assertEqual(data['int_underscore'], 213020)
        self.assertEqual(data['wrong_int'], "123 213")
        self.assertEqual(data['div_int'], "123 // 4")
        self.assertEqual(data['float'], 123.45)
        self.assertEqual(data['wrong_float'], "123.321.213")
        self.assertEqual(data['exp'], 1e5)
        self.assertEqual(data['wrong_exp'], "1e3ef")
        self.assertEqual(data['wrong_exp2'], "1e3e22")
        self.assertEqual(data['int_with_comment'], 123)
        self.assertFalse('commented_value' in data)
        self.assertFalse('tab_variable' in data)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SimpleSaveFig:
    """This is emulation of a Figure class.
    The only goal of this class is to save something with savefig method."""

    def __init__(self, internal_data: str = "data"):
        self.internal_data = internal_data

    def savefig(self, filepath: str):
        with open(filepath, mode="w", encoding="utf-8") as file:
            file.write(self.internal_data)


if __name__ == '__main__':
    unittest.main()
