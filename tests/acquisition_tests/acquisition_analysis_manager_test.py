import logging
import os
import shutil

import unittest

from labmate.acquisition_notebook import AcquisitionAnalysisManager
from labmate.acquisition_notebook.acquisition_analysis_manager import logger as aqm_logger
# from quanalys.acquisition import AcquisitionManager, AnalysisManager
from labmate.syncdata import SyncData
from .analysis_data_test import AnalysisDataParceTest

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")

logging.basicConfig(level=logging.WARNING, force=True)
logging.StreamHandler().setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

aqm_logger.setLevel(logging.WARNING)


class AcquisitionAnalysisManagerTest(unittest.TestCase):
    """Test of AcquisitionAnalysisManager.

    It mainly checks what acquisition_cell and analysis_cell do
    """

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

    def test_data_none(self):
        with self.assertRaises(ValueError):
            _ = self.aqm.data

    def test_aq_equal_current_acquisition(self):
        self.create_acquisition_cell()
        self.assertEqual(id(self.aqm.aq), id(self.aqm.current_acquisition))

    def test_d_equal_data(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.assertEqual(id(self.aqm.d), id(self.aqm.data))

    def test_analysis_cell_check_name(self):
        self.create_acquisition_cell()
        self.aqm.analysis_cell(acquisition_name="abc")

    def test_analysis_cell_check_name_wrong(self):
        self.create_acquisition_cell()
        with self.assertRaises(ValueError):
            self.aqm.analysis_cell(acquisition_name="wrong")

    def test_analysis_cell_check_name_re(self):
        self.create_acquisition_cell()
        self.aqm.analysis_cell(acquisition_name="^[a-z]*$")

    def test_analysis_cell_check_name_re_wrong(self):
        self.create_acquisition_cell()
        with self.assertRaises(ValueError):
            self.aqm.analysis_cell(acquisition_name="^[a-b]*$")

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
            sd.get("analysis_cells", {}).get('default'), self.cell_text)

    def test_analysis_cell_fig_saved(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        fig = LocalFig()
        self.aqm.save_fig(fig)

        sd = SyncData(self.aqm.aq.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('default'), self.cell_text)
        self.assertTrue(fig.fig_saved)

    def test_fig_only_saved(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        fig = LocalFig()
        self.aqm.save_fig_only(fig)
        self.assertTrue(fig.fig_saved)

    def test_get_analysis_code(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.aqm.save_analysis_cell()
        self.aqm.analysis_cell(self.aqm.d.filepath)
        code = self.aqm.get_analysis_code()
        self.assertEqual(code, self.cell_text)
        self.assertEqual(self.aqm.shell.next_input, self.cell_text)  # type: ignore

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

    def test_error_on_last_execution(self):
        self.aqm.shell.last_success = False  # type: ignore
        with self.assertRaises(ChildProcessError):
            self.create_acquisition_cell()
            self.create_analysis_cell()
        self.aqm.shell.last_success = True  # type: ignore

    def test_setitem(self):
        self.create_acquisition_cell()
        self.aqm['x'] = "abc"
        self.create_analysis_cell()
        self.assertEqual(self.aqm.d.get('x'), "abc")

    def test_setitem_in_analysis(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        with self.assertRaises(ValueError):
            self.aqm['x'] = "abc"

    def test_setitem_before_acquisition(self):
        self.tearDownClass()
        self.setUp()
        with self.assertRaises(ValueError):
            self.aqm['x'] = "abc"

    def test_acquisition_cell_prerun_hook(self):
        func_class = FunctionToRun()
        self.assertFalse(func_class.function_run)
        self.aqm.acquisition_cell(self.experiment_name, prerun=func_class.func)
        self.assertTrue(func_class.function_run)

    def test_acquisition_cell_prerun_hook_default(self):
        func_class = FunctionToRun()
        self.aqm.set_acquisition_cell_prerun_hook(func_class.func)
        self.assertFalse(func_class.function_run)
        self.create_acquisition_cell()
        self.assertTrue(func_class.function_run)

    def test_analysis_cell_prerun_hook(self):
        func_class = FunctionToRun()
        self.create_acquisition_cell()
        self.assertFalse(func_class.function_run)
        self.aqm.analysis_cell(prerun=func_class.func)
        self.assertTrue(func_class.function_run)

    def test_analysis_cell_prerun_hook_multi(self):
        func_class = FunctionToRun()
        func_class2 = FunctionToRun()
        self.create_acquisition_cell()
        self.assertFalse(func_class.function_run)
        self.aqm.analysis_cell(prerun=[func_class.func, func_class2.func])
        self.assertEqual(func_class.function_run, 1)
        self.assertEqual(func_class2.function_run, 1)

    def test_analysis_cell_prerun_hook_default(self):
        func_class = FunctionToRun()
        self.aqm.set_analysis_cell_prerun_hook(func_class.func)
        self.create_acquisition_cell()
        self.assertFalse(func_class.function_run)
        self.aqm.analysis_cell()
        self.assertTrue(func_class.function_run)

    def test_analysis_cell_prerun_hook_default_multi(self):
        func_class = FunctionToRun()
        func_class2 = FunctionToRun()
        self.aqm.set_analysis_cell_prerun_hook([func_class.func, func_class2.func])
        self.create_acquisition_cell()
        self.aqm.analysis_cell()
        self.assertEqual(func_class.function_run, 1)
        self.assertEqual(func_class2.function_run, 1)

    def test_analysis_cell_prerun_hook_default_mixed(self):
        func_class = FunctionToRun()
        func_class2 = FunctionToRun()
        func_class3 = FunctionToRun()
        self.aqm.set_analysis_cell_prerun_hook([func_class.func, func_class2.func])
        self.create_acquisition_cell()
        self.aqm.analysis_cell(prerun=func_class3.func)
        self.assertEqual(func_class.function_run, 1)
        self.assertEqual(func_class2.function_run, 1)
        self.assertEqual(func_class3.function_run, 1)

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
            sd.get("analysis_cells", {}).get('default'), self.cell_text,
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

    def test_wrong_name(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        with self.assertRaises(ValueError):
            self.aqm.analysis_cell("wrong", cell="none")

    def test_current_acquisition_not_none(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(cell="none")
        self.assertIsNotNone(self.aqm.current_acquisition)

    def test_current_acquisition_none(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell="none")
        self.assertIsNone(self.aqm.current_acquisition)

    def test_analysis_cell_after_old_data_loaded(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell="none")
        self.aqm.analysis_cell(cell="none")
        self.assertIsNotNone(self.aqm.d)

    def test_change_analysis_cell_for_old_data_specified(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell=self.cell_text2)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('default'), self.cell_text2)

    def test_change_analysis_cell_for_old_data_explicit_cell(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell="none")
        self.aqm.save_analysis_cell()

    def test_change_analysis_cell_for_old_data_explicit_named(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell(self.aqm.aq.filepath, cell="none")
        self.aqm.save_analysis_cell(name="abc")

    def test_change_analysis_cell_for_old_data_explicit_named_specified_cell(self):
        self.aqm.acquisition_cell(self.experiment_name, cell="none")
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell(name="abc", cell=self.cell_text2)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('abc'), self.cell_text2)

    def tearDown(self) -> None:
        file = self.aqm.d.filepath + '.h5'
        if os.path.exists(file):
            os.remove(file)


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
            sd.get("analysis_cells", {}).get('default'), self.cell_text)

    def test_change_analysis_cell_for_old_data(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('default'), self.cell_text)

    def test_change_analysis_cell_for_old_data_only_name(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath.rsplit('/', 1)[-1])  # type: ignore

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('default'), self.cell_text)

    def test_change_analysis_cell_for_old_data_explicit_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell()

        sd = SyncData(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get('default'), self.cell_text2)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class LintingTest(unittest.TestCase):
    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=True,
            shell=shell)  # type: ignore
        self.turn_on_linting()

    def turn_on_linting(self):
        self.aqm.linting(allowed_variables=['aqm', 'plt', 'func'])

    def run_test(self, cell=""):
        cell = self.remove_tabs(cell)
        self.aqm.acquisition_cell(self.experiment_name)
        with self.assertLogs(aqm_logger) as captured:
            self.aqm.analysis_cell(cell=cell)
        return captured

    @staticmethod
    def remove_tabs(code: str):
        tabs = " "*(code.find("aqm"))
        return code.replace(tabs, "")

    def check_logs(self, logs, msg, level):
        for log in logs:
            if msg in log.message and log.levelno >= level:
                return True
        return False

    def assert_logs(
            self, logs, msg=None, level=None):
        if isinstance(msg, list):
            for msg_ in msg:
                self.assert_logs(logs, msg_, level)
            return

        if msg:
            level = level if level is not None else 30

            self.assertTrue(self.check_logs(logs, msg, level),
                            msg=f"No '{msg}' at level {level} inside: {logs}")
        else:
            msg = "External variable used"
            level = level or 0
            self.assertFalse(
                self.check_logs(logs, msg, level),
                msg=f"There is '{msg}' inside: {[f'{log.levelno}:{log.message}' for log in logs]}")

    def test_lint_standard(self):
        code = """\
        aqm.analysis_cell()
        func()
        func = "a"
        plt.plot(aqm.d.x, aqm.d.y)
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_save_acquisition_simple(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")    
        if aqm.current_acquisition is not None:
            x, y = fetch_new_data() # noqa
            aqm.save_acquisition(x=x, y=y, const=const)
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_save_acquisition_wrong(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")    
        if aqm.current_acquisition is not None:
            x, y = fetch_new_data() # noqa
            aqm.save_acquisition(x=x, y=y, const=const)
        plt.plot(x, y)
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records, ['x', 'y'], 30)

    def test_lint_save_acquisition_right(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")    
        if aqm.current_acquisition is not None:
            x, y = fetch_new_data() # noqa
            aqm.save_acquisition(x=x, y=y, const=const)
        plt.plot(aqm.d.x, aqm.d.y)
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_save_acquisition_class(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")    
        if aqm.current_acquisition is not None:
            x, y = fetch_new_data() # noqa
            aqm.save_acquisition(x=x, cls1=cls.func1(), cls2=cls.func2, cls3=cls.func3.func4())
        plt.plot(aqm.d.x, aqm.d.y)
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_import(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")
        import some_import
        some_import()
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_import_star(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")
        from some_import import *
        some_import()
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records, "some_import")

    def test_lint_import_from(self):
        code = """\
        aqm.analysis_cell("2023_02_21__10_39_48__sine_qm")
        from some_import import some_func
        some_func()
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_def_function(self):
        code = """\
        aqm.analysis_cell()
        def abc1(p1, /, p2, p3=2, *, p4=3, p5: int=4) -> int:
            return p1 + p2 + p3 + p4 + p5
        def abc2(p1, p2):
            return p1
        def abc3(p1=3):
            return p1
        def abc4():
            return 0
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_def_function_wrong(self):
        code = """\
        aqm.analysis_cell()
        def abc1(p1, /, p2, p3=2, *, p4=3, p5: int=4) -> int:
            return p1 + p2 + p3 + p4 + p5*x1
        def abc2(p1, p2):
            return p1*x2
        def abc3(p1=3):
            return p1*x3
        def abc4():
            return x4
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records, ['x1', 'x2', 'x3', 'x4'])

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class LintingByFileTest(LintingTest):
    def turn_on_linting(self):
        variables = ['aqm', 'plt', 'func']
        filename = os.path.join(self.aqm.data_directory, "lint.py")
        with open(filename, "w", encoding="utf-8") as file:
            for var in variables:
                file.write(f"{var}=None\n")

        self.aqm.linting(init_file=filename)


class AcquisitionAnalysisManagerParceTest(AnalysisDataParceTest):
    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False,
            save_on_edit=True,
            shell=shell)  # type: ignore

        self.config = (os.path.join(TEST_DIR, "data/config.txt"))
        self.aqm.set_config_file(self.config)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq.update(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.aqm.analysis_cell()
        self.ad = self.aqm

    def set_data(self, key, value):
        self.ad.d[key] = value

    def test_parse_config(self):
        """This right way to save configuration files.

        They should be set before creating a new acquisition.
        """
        self.aqm.set_default_config_files(("config.txt",))
        data = self.aqm.cfg
        self.compare_config(data=data)


class ShellEmulator:
    """This is emulation of a Figure class.

    The only goal of this class is to save something with savefig method.
    """

    last_success = True
    last_cell = "aqm.acquisition_cell('abc')"

    def __init__(self, internal_data: str = "shell_emulator_data"):
        self.internal_data = internal_data
        self.next_input = ""

    def get_parent(self):
        return {'content': {
            'code': self.internal_data
        }}

    @property
    def last_execution_result(self):
        from labmate.attrdict import AttrDict
        return AttrDict(
            {'info': {'raw_cell': self.last_cell, },
             'success': self.last_success})

    def set_next_input(self, code):
        self.next_input = code


class LocalFig:
    def __init__(self):
        self.fig_saved = False

    def savefig(self, fname, **kwds):
        del fname, kwds
        self.fig_saved = True


class FunctionToRun():
    def __init__(self):
        self.function_run = 0

    def func(self):
        self.function_run += 1


if __name__ == '__main__':
    unittest.main()
