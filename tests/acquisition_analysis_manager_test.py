import logging
import os
import shutil

import unittest

from labmate.acquisition_notebook import AcquisitionAnalysisManager
# from quanalys.acquisition_utils import AcquisitionManager, AnalysisManager
from labmate.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")

logging.basicConfig(level=logging.WARNING, force=True)
logging.StreamHandler().setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)


class AcquisitionAnalysisManagerTest(unittest.TestCase):
    """Test of AcquisitionAnalysisManager.
    It mainly checks what acquisition_cell and analysis_cell do"""

    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=True,
            shell=shell)  # type: ignore

    def check_xy_values(self):
        sd = SyncData(self.aqm.aq.filepath)
        self.check_2_list(sd['x'], self.x)
        self.check_2_list(sd['y'], self.y)

    def check_2_list(self, lst1, lst2):
        self.assertEqual(len(lst1), len(lst2))
        for v1, v2 in zip(lst1, lst2):
            self.assertEqual(v1, v2)

    def create_acquisition_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)

    def create_analysis_cell(self):
        self.aqm.analysis_cell()

    def create_data_and_check(self):
        self.aqm.aq['x'] = self.x
        self.aqm.aq['y'] = self.y
        self.check_xy_values()

    def test_current_filepath(self):
        self.create_acquisition_cell()
        self.assertEqual(str(self.aqm.current_filepath), self.aqm.aq.filepath)

    def test_aq_equal_current_acquisition(self):
        self.create_acquisition_cell()
        self.assertEqual(id(self.aqm.aq), id(self.aqm.current_acquisition))

    def test_d_equal_data(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.assertEqual(id(self.aqm.d), id(self.aqm.data))

    def test_acquisition_cell_saved(self):
        self.create_acquisition_cell()

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(
            sd.get("acquisition_cell"), self.cell_text)

    def test_analysis_cell_saved(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.aqm.save_analysis_cell()

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text)

    def test_simple_acq_cell(self):
        self.create_acquisition_cell()
        self.aqm.save_acquisition(x=self.x, y=self.y)

        self.check_xy_values()

    def test_simple_acq_cell2(self):
        self.create_acquisition_cell()
        self.create_data_and_check()

    def test_no_tmp_file(self):
        self.tearDownClass()
        self.create_acquisition_cell()
        self.create_data_and_check()

    def test_analysis(self):
        self.create_acquisition_cell()
        self.create_data_and_check()

        self.assertIsNone(self.aqm.current_analysis)

        self.create_analysis_cell()
        self.assertIsNotNone(self.aqm.current_analysis)
        assert self.aqm.current_analysis
        self.check_2_list(self.aqm.current_analysis['x'], self.x)
        self.check_2_list(self.aqm.current_analysis['y'], self.y)

    def test_analysis_after_restart(self):
        self.create_acquisition_cell()
        self.create_data_and_check()
        self.setUp()

        self.create_analysis_cell()

        self.assertIsNotNone(self.aqm.current_analysis)
        assert self.aqm.current_analysis
        self.check_2_list(self.aqm.current_analysis['x'], self.x)
        self.check_2_list(self.aqm.current_analysis['y'], self.y)

    def test_useful_flag_after_save_acquisition(self):
        self.create_acquisition_cell()
        self.assertEqual(self.aqm.aq.get('useful'), False)
        self.aqm.aq['x'] = self.x
        self.assertEqual(self.aqm.aq.get('useful'), False)
        self.aqm.save_acquisition()
        self.assertEqual(self.aqm.aq.get('useful'), True)

    def test_useful_flag_after_analysis_cell(self):
        self.create_acquisition_cell()
        self.assertEqual(self.aqm.aq.get('useful'), False)
        self.aqm.aq['x'] = self.x
        self.assertEqual(self.aqm.aq.get('useful'), False)
        self.create_analysis_cell()
        self.assertEqual(self.aqm.d.get('useful'), True)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class AcquisitionAnalysisManagerWithSaveOnEditOffTest(unittest.TestCase):
    """Check AcquisitionAnalysisManager with save_on_edit = False."""

    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=False,
            shell=shell)  # type: ignore

    def check_xy_values(self):
        sd = SyncData(self.aqm.aq.filepath)
        self.check_2_list(sd['x'], self.x)
        self.check_2_list(sd['y'], self.y)

    def check_2_list(self, lst1, lst2):
        self.assertEqual(len(lst1), len(lst2))
        for v1, v2 in zip(lst1, lst2):
            self.assertEqual(v1, v2)

    def create_acquisition_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)

    def create_analysis_cell(self):
        self.aqm.analysis_cell()

    def test_file_does_not_exist_on_new_cell(self):
        self.create_acquisition_cell()
        self.assertFalse(os.path.exists(self.aqm.current_filepath + ".h5"),
                         msg="H5 file was created. But it should not.")

    def test_file_does_not_exist_on_add_data(self):
        self.create_acquisition_cell()

        self.aqm.aq['x'] = self.x
        self.aqm.aq['y'] = self.y

        self.aqm.aq.update(z=self.x)

        self.aqm.aq.pop('z')

        self.assertFalse(os.path.exists(self.aqm.current_filepath + ".h5"),
                         msg="H5 file was created. But it should not.")

    def test_file_exist_on_save_acquisition(self):
        self.create_acquisition_cell()

        self.aqm.save_acquisition()
        self.assertTrue(os.path.exists(self.aqm.current_filepath + ".h5"),
                        msg="After running save_acquisition h5 file should exist")

    def test_file_exist_on_save_acquisition_with_data(self):
        self.create_acquisition_cell()

        self.aqm.aq['x'] = self.x
        self.aqm.aq['y'] = self.y

        self.aqm.save_acquisition()

        self.assertTrue(os.path.exists(self.aqm.current_filepath + ".h5"),
                        msg="After running save_acquisition h5 file should exist")

        self.check_xy_values()

        assert self.aqm.current_analysis

        self.assertEqual(
            self.aqm.current_analysis.get("acquisition_cell"), self.cell_text)

    def test_save_acquisition_creates_am(self):
        self.create_acquisition_cell()
        self.assertIsNone(self.aqm.current_analysis)
        self.aqm.save_acquisition()
        self.assertIsNotNone(self.aqm.current_analysis)
        self.assertEqual(self.aqm.d.get('useful'), True)

    def test_run_analysis_before_saving(self):
        self.create_acquisition_cell()
        self.assertIsNone(self.aqm.current_analysis)
        self.create_analysis_cell()
        self.assertIsNone(self.aqm.current_analysis)
        self.aqm.save_acquisition()
        self.assertIsNotNone(self.aqm.current_analysis)

    def test_analysis_cell_saved(self):
        self.create_acquisition_cell()
        self.aqm.save_acquisition()
        self.create_analysis_cell()
        self.aqm.save_analysis_cell()

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text,
            msg=f"Key saved {sd.keys()}, \
            aqm._analysis_cell_str='{self.aqm._analysis_cell_str}'")  # pylint: disable=W0212

    def test_run_analysis_before_saving_check_cell(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.assertFalse(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="H5 file was created. But analysis_cell should not create it.")
        self.aqm.save_acquisition()
        self.assertEqual(
            SyncData(self.aqm.aq.filepath).get("acquisition_cell"), self.cell_text)

    def test_save_inside_analysis_data(self):
        self.create_acquisition_cell()
        self.aqm.save_acquisition(x=self.x)
        self.assertEqual(self.aqm.aq.get("useful"), True)
        self.create_analysis_cell()

        self.aqm.d['y'] = self.y
        data = SyncData(self.aqm.aq.filepath)
        self.assertFalse('y' in data)
        self.assertEqual(data['useful'], True)
        self.aqm.d.save()
        self.check_2_list(SyncData(self.aqm.aq.filepath).get('y'), self.y)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class OldDataLoadTestsWithNoShell(unittest.TestCase):
    cell_text = "this is a analysis cell"
    cell_text2 = "this is the second analysis cell"

    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=True,
            shell=None)  # type: ignore

    def test_current_acquisition_not_none(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.assertIsNotNone(self.aqm.current_acquisition)

    def test_current_acquisition_none(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.assertIsNone(self.aqm.current_acquisition)

    def test_analysis_cell_after_old_data_loaded(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.analysis_cell()
        self.assertIsNotNone(self.aqm.d)

    def test_change_analysis_cell_for_old_data_specified(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell=self.cell_text2)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text2)

    def test_change_analysis_cell_for_old_data_explicit_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell()

    def test_change_analysis_cell_for_old_data_explicit_named(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell(name="abc")

    def test_change_analysis_cell_for_old_data_explicit_named_specified_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell(name="abc", cell=self.cell_text2)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cell_abc"), self.cell_text2)


class OldDataLoadWithShellTests(OldDataLoadTestsWithNoShell):

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=True,
            shell=shell)  # type: ignore

    def test_change_analysis_cell_for_new_data(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text)

    def test_change_analysis_cell_for_old_data(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text)

    def test_change_analysis_cell_for_old_data_explicit_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell()

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cell"), self.cell_text2)

    def tearDown(self) -> None:
        file = self.aqm.d.filepath + '.h5'
        if os.path.exists(file):
            os.remove(file)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class ShellEmulator:
    """This is emulation of a Figure class.
    The only goal of this class is to save something with savefig method."""

    def __init__(self, internal_data: str = "shell_emulator_data"):
        self.internal_data = internal_data

    def get_parent(self):
        return {'content': {
            'code': self.internal_data
        }}


if __name__ == '__main__':
    unittest.main()
