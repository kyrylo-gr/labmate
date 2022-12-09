"""
This is the general tests that verify the front-end implementation.
So there is not tests on internal logic of the code. It's just a
verification of the api. So as soon as saving and opening works,
everything is good.
"""

import os
import shutil

import unittest
import numpy as np

from quanalys import AcquisitionManager, AnalysisManager

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")


class BasicTest(unittest.TestCase):
    """Test of saving simple data."""

    def setUp(self):
        AcquisitionManager.data_directory = DATA_DIR

    def test_simple_save(self):
        """Save and load the simplest list."""
        x = np.linspace(0, 20*np.pi, 101)
        y = np.sin(x)
        AcquisitionManager.save_acquisition(x=x, y=y)

        fullpath = AcquisitionManager.get_ongoing_acquisition().fullpath
        AnalysisManager(fullpath, "")

        data = AnalysisManager.current_analysis

        assert data is not None

        self.assertTrue(np.all(x == data.get('x')))
        self.assertTrue(np.all(y == data.get('y')))

    def test_open_old_file(self):
        pass
        # old_file_path = "./data/old_data_example.h5"

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        shutil.rmtree(os.path.join(os.path.dirname(__file__), DATA_DIR))

class LoopTest(unittest.TestCase):
    """Test of saving simple data."""

    def setUp(self):
        AcquisitionManager.data_directory = DATA_DIR

    def test_simple_save(self):
        """Save and load the simplest list."""
        x = np.linspace(0, 20*np.pi, 101)
        y = np.sin(x)
        AcquisitionManager.save_acquisition(x=x, y=y)

        fullpath = AcquisitionManager.get_ongoing_acquisition().fullpath
        AnalysisManager(fullpath, "")

        data = AnalysisManager.current_analysis

        assert data is not None

        self.assertTrue(np.all(x == data.get('x')))
        self.assertTrue(np.all(y == data.get('y')))

    def test_open_old_file(self):
        pass
        # old_file_path = "./data/old_data_example.h5"

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        shutil.rmtree(os.path.join(os.path.dirname(__file__), DATA_DIR))


if __name__ == '__main__':
    unittest.main()
