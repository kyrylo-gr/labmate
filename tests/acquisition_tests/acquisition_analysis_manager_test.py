import os
import shutil
import unittest

from dh5 import DH5

from labmate.acquisition import AnalysisData
from labmate.acquisition_notebook import AcquisitionAnalysisManager

from .analysis_data_test import AnalysisDataParceTest
from .utils import DATA_DIR, TEST_DIR, FunctionToRun, LocalFig, ShellEmulator


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
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=shell
        )  # type: ignore

    def check_xy_values(self):
        sd = DH5(self.aqm.aq.filepath)
        self.check_2_list(sd["x"], self.x)
        self.check_2_list(sd["y"], self.y)

    def check_2_list(self, lst1, lst2):
        self.assertEqual(len(lst1), len(lst2))
        for v1, v2 in zip(lst1, lst2):
            self.assertEqual(v1, v2)

    def create_acquisition_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)

    def create_analysis_cell(self):
        self.aqm.analysis_cell()

    def create_data_and_check(self):
        self.aqm.aq["x"] = self.x
        self.aqm.aq["y"] = self.y
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

        sd = DH5(self.aqm.aq.filepath)
        self.assertEqual(sd.get("acquisition_cell"), self.cell_text)

    def test_analysis_cell_saved(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.aqm.save_analysis_cell()

        sd = DH5(self.aqm.aq.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text)

    def test_analysis_cell_fig_saved(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        fig = LocalFig()
        self.aqm.save_fig(fig)

        sd = DH5(self.aqm.aq.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text)
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
        self.check_2_list(self.aqm.current_analysis["x"], self.x)
        self.check_2_list(self.aqm.current_analysis["y"], self.y)

    def test_analysis_after_restart(self):
        self.create_acquisition_cell()
        self.create_data_and_check()
        self.setUp()

        self.create_analysis_cell()

        self.assertIsNotNone(self.aqm.current_analysis)
        assert self.aqm.current_analysis
        self.check_2_list(self.aqm.current_analysis["x"], self.x)
        self.check_2_list(self.aqm.current_analysis["y"], self.y)

    def test_useful_flag_after_save_acquisition(self):
        self.create_acquisition_cell()
        self.assertEqual(self.aqm.aq.get("useful"), False)
        self.aqm.aq["x"] = self.x
        self.assertEqual(self.aqm.aq.get("useful"), False)
        self.aqm.save_acquisition()
        self.assertEqual(self.aqm.aq.get("useful"), True)

    def test_useful_flag_after_analysis_cell(self):
        self.create_acquisition_cell()
        self.assertEqual(self.aqm.aq.get("useful"), False)
        self.aqm.aq["x"] = self.x
        self.assertEqual(self.aqm.aq.get("useful"), False)
        self.create_analysis_cell()
        self.assertEqual(self.aqm.d.get("useful"), True)

    def test_error_on_last_execution(self):
        self.aqm.shell.last_success = False  # type: ignore
        with self.assertRaises(ChildProcessError):
            self.create_acquisition_cell()
            self.create_analysis_cell()
        self.aqm.shell.last_success = True  # type: ignore

    def test_setitem(self):
        self.create_acquisition_cell()
        self.aqm["x"] = "abc"
        self.create_analysis_cell()
        self.assertEqual(self.aqm.d.get("x"), "abc")

    def test_setitem_in_analysis(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        with self.assertRaises(ValueError):
            self.aqm["x"] = "abc"

    def test_setitem_before_acquisition(self):
        self.tearDownClass()
        self.setUp()
        with self.assertRaises(ValueError):
            self.aqm["x"] = "abc"

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
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=False, shell=shell
        )  # type: ignore

    def check_xy_values(self):
        sd = DH5(self.aqm.aq.filepath)
        self.check_2_list(sd["x"], self.x)
        self.check_2_list(sd["y"], self.y)

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
        self.assertFalse(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="H5 file was created. But it should not.",
        )

    def test_file_does_not_exist_on_add_data(self):
        self.create_acquisition_cell()

        self.aqm.aq["x"] = self.x
        self.aqm.aq["y"] = self.y

        self.aqm.aq.update(z=self.x)

        self.aqm.aq.pop("z")

        self.assertFalse(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="H5 file was created. But it should not.",
        )

    def test_file_exist_on_save_acquisition(self):
        self.create_acquisition_cell()

        self.aqm.save_acquisition()
        self.assertTrue(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="After running save_acquisition h5 file should exist",
        )

    def test_file_exist_on_save_acquisition_with_data(self):
        self.create_acquisition_cell()

        self.aqm.aq["x"] = self.x
        self.aqm.aq["y"] = self.y

        self.aqm.save_acquisition()

        self.assertTrue(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="After running save_acquisition h5 file should exist",
        )

        self.check_xy_values()

        assert self.aqm.current_analysis

        self.assertEqual(
            self.aqm.current_analysis.get("acquisition_cell"), self.cell_text
        )

    def test_save_acquisition_creates_am(self):
        self.create_acquisition_cell()
        self.assertIsNone(self.aqm.current_analysis)
        self.aqm.save_acquisition()
        self.assertIsNotNone(self.aqm.current_analysis)
        self.assertEqual(self.aqm.d.get("useful"), True)

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

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(
            sd.get("analysis_cells", {}).get("default"),
            self.cell_text,
            msg=f"Key saved {sd.keys()}, \
            aqm._analysis_cell_str='{self.aqm._analysis_cell_str}'",  # pylint: disable=W0212
        )

    def test_run_analysis_before_saving_check_cell(self):
        self.create_acquisition_cell()
        self.create_analysis_cell()
        self.assertFalse(
            os.path.exists(self.aqm.current_filepath + ".h5"),
            msg="H5 file was created. But analysis_cell should not create it.",
        )
        self.aqm.save_acquisition()
        self.assertEqual(
            DH5(self.aqm.aq.filepath).get("acquisition_cell"), self.cell_text
        )

    def test_save_inside_analysis_data(self):
        self.create_acquisition_cell()
        self.aqm.save_acquisition(x=self.x)
        self.assertEqual(self.aqm.aq.get("useful"), True)
        self.create_analysis_cell()

        self.aqm.d["y"] = self.y
        data = DH5(self.aqm.aq.filepath)
        self.assertFalse("y" in data)
        self.assertEqual(data["useful"], True)
        self.aqm.d.save()
        self.check_2_list(DH5(self.aqm.aq.filepath).get("y"), self.y)

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
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=None
        )  # type: ignore

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

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text2)

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

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("abc"), self.cell_text2)

    def tearDown(self) -> None:
        file = self.aqm.d.filepath + ".h5"
        if os.path.exists(file):
            os.remove(file)


class OldDataLoadWithShellTests(OldDataLoadTestsWithNoShell):
    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=shell
        )  # type: ignore

    def test_change_analysis_cell_for_new_data(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        sd = DH5(self.aqm.aq.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text)

    def test_change_analysis_cell_for_old_data(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text)

    def test_change_analysis_cell_for_old_data_only_name(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.save_analysis_cell()

        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath.rsplit("/", 1)[-1])  # type: ignore

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text)

    def test_change_analysis_cell_for_old_data_explicit_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)
        self.aqm.save_acquisition(x=self.x)
        self.aqm.analysis_cell()
        self.aqm.shell = ShellEmulator(self.cell_text2)
        self.aqm.analysis_cell(self.aqm.aq.filepath)
        self.aqm.save_analysis_cell()

        sd = DH5(self.aqm.d.filepath)
        self.assertEqual(sd.get("analysis_cells", {}).get("default"), self.cell_text2)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class AcquisitionAnalysisManagerParceTest(AnalysisDataParceTest):
    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=shell
        )  # type: ignore
        self.aqm.set_default_config_files(("config.txt",))

        # self.config = (os.path.join(TEST_DIR, "data/config.txt"))
        self.config = (
            os.path.join(
                TEST_DIR,
                "data/config.txt",
            ),
            os.path.join(
                TEST_DIR,
                "data/imported_config.py",
            ),
        )
        self.aqm.set_config_file(self.config)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.save_acquisition(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.aqm.analysis_cell()
        self.ad = self.aqm

    def set_data(self, key, value):
        self.ad.d[key] = value

    def test_parse_config_cfg(self):
        """This right way to save configuration files.

        They should be set before creating a new acquisition.
        """
        data = self.aqm.cfg
        self.compare_config(data=data)

    def test_parse_config_default_config_load(self):
        """This right way to save configuration files.

        They should be set before creating a new acquisition.
        """
        cfg = AnalysisData(self.aqm.current_filepath).cfg
        self.assertEqual(cfg["float"], 123.45)
        self.assertEqual(cfg.float, 123.45)  # type: ignore


class LoadCreateIndependentFilesTest(unittest.TestCase):
    """Test load_file, create_acquisition.."""

    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=shell
        )  # type: ignore

    def check_xy_values(self, file=None):
        if file is None:
            file = self.aqm.aq.filepath
        sd = DH5(file)
        self.check_2_list(sd["x"], self.x)
        self.check_2_list(sd["y"], self.y)

    def check_2_list(self, lst1, lst2):
        self.assertEqual(len(lst1), len(lst2))
        for v1, v2 in zip(lst1, lst2):
            self.assertEqual(v1, v2)

    def create_acquisition_cell(self):
        self.aqm.acquisition_cell(self.experiment_name)

    def create_analysis_cell(self):
        self.aqm.analysis_cell()

    def test_create_acquisition_with_name(self):
        self.create_acquisition_cell()
        aq = self.aqm.create_acquisition("test_item")
        aq["x"], aq["y"] = self.x, self.y
        self.check_xy_values(aq.filepath)

    def test_create_acquisition_without_name(self):
        self.create_acquisition_cell()
        aq = self.aqm.create_acquisition()
        aq["x"], aq["y"] = self.x, self.y
        self.check_xy_values(aq.filepath)

    def test_load_file_by_filename(self):
        self.create_acquisition_cell()
        aq = self.aqm.create_acquisition()
        aq["x"], aq["y"] = self.x, self.y

        data = self.aqm.load_file(aq.filename)
        self.check_2_list(data["x"], self.x)
        self.check_2_list(data["y"], self.y)

    def test_load_file_by_filepath(self):
        self.create_acquisition_cell()
        aq = self.aqm.create_acquisition()
        aq["x"], aq["y"] = self.x, self.y

        data = self.aqm.load_file(aq.filepath)
        self.check_2_list(data["x"], self.x)
        self.check_2_list(data["y"], self.y)

    def test_for_loop(self):
        self.create_acquisition_cell()
        files = []
        for i in range(5):
            aq = self.aqm.create_acquisition("list_item")
            aq.save_acquisition(
                x=self.x, y=self.y, i=i, parent=self.aqm.current_filepath.str
            )  # optional, but good to keep a trace of the files

            files.append(aq.filepath)
            self.aqm["files"] = files

        self.create_analysis_cell()
        for i, file in enumerate(self.aqm.data.files):
            data = self.aqm.load_file(file)
            self.check_2_list(data["x"], self.x)
            self.check_2_list(data["y"], self.y)
            self.assertEqual(data["i"], i)

    def test_for_loop_without_name(self):
        self.create_acquisition_cell()
        files = []
        for i in range(5):
            aq = self.aqm.create_acquisition()
            aq.save_acquisition(
                x=self.x, y=self.y, i=i, parent=self.aqm.current_filepath.str
            )  # optional, but good to keep a trace of the files

            files.append(aq.filepath)
            self.aqm["files"] = files

        self.aqm.save_acquisition()

        self.create_analysis_cell()
        for i, file in enumerate(self.aqm.data.files):
            data = self.aqm.load_file(file)
            self.check_2_list(data["x"], self.x)
            self.check_2_list(data["y"], self.y)
            self.assertEqual(data["i"], i)


if __name__ == "__main__":
    unittest.main()
