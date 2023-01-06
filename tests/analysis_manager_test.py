import os
import shutil

import unittest

from quanalys.acquisition_utils import AcquisitionManager, AnalysisManager
from quanalys.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class AcquisitionManagerTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""
    analysis_cell = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq.update(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.am = AnalysisManager(self.aqm.current_filepath, cell=self.analysis_cell)

    def test_open_read_mode(self):
        self.assertEqual(self.am.get('x')[0], 1)
        with self.assertRaises(TypeError, msg="Data is not locked"):
            self.am['x'] = 2

        self.am['z'] = 3

        sd = SyncData(self.am.filepath)
        self.assertEqual(sd.get('z'), 3)

    def test_analysis_cell(self):
        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.analysis_cell)

    def test_save_fig(self):
        fig = SimpleSaveFig()
        self.am.save_fig(fig)  # type: ignore

        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.experiment_name, self.aqm.current_filepath + '_FIG1.pdf')))

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SimpleSaveFig:
    def __init__(self, internal_data: str = "data"):
        self.internal_data = internal_data

    def savefig(self, filepath: str):
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(self.internal_data)


if __name__ == '__main__':
    unittest.main()
