import os
import shutil

from labmate.acquisition_notebook import AcquisitionAnalysisManager
from labmate.display import logger as display_logger

from .utils import DATA_DIR, TEST_DIR, LogTest, ShellEmulator, aqm_logger


class AcquisitionAnalysisIpyDisplayTest(LogTest):
    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, save_on_edit=True, shell=shell
        )  # type: ignore
        self.aqm.set_default_config_files(("config.txt",))

        # self.config = (os.path.join(TEST_DIR, "data/config.txt"))
        self.config = TEST_DIR / "data" / "config.txt"
        self.aqm.set_config_file(str(self.config))
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.save_acquisition(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.aqm.analysis_cell()

    def assert_logs_for_float(self, logs, link_text=None, after_text=None):
        if link_text:
            self.assert_logs(logs, f">{link_text}<", 20)
        if after_text:
            self.assert_logs(logs, f"</a> {after_text}", 20)
        self.assert_logs(logs, "data/config.txt:7", 20)

    def test_display_param_link_error(self):
        with self.assertLogs(aqm_logger) as captured:
            self.aqm.display_param_link("nonexistent_param")
        self.assert_logs(captured.records, "nonexistent_param", 30)

    def test_display_param_link_only_param(self):
        with self.assertLogs(display_logger) as captured:
            self.aqm.display_param_link("float")
        self.assert_logs_for_float(captured.records, "float")

    def test_display_param_link_param_with_after_text(self):
        with self.assertLogs(display_logger) as captured:
            self.aqm.display_param_link("float = ", "same_value")
        self.assert_logs_for_float(captured.records, "float = ", "same_value")

    def test_display_param_link_list_of_param(self):
        with self.assertLogs(display_logger) as captured:
            self.aqm.display_param_link(["float = ", "int = "])
        self.assert_logs_for_float(captured.records, "float = ")

    def test_display_param_link_list_of_param_with_text(self):
        with self.assertLogs(display_logger) as captured:
            self.aqm.display_param_link(
                [("float = ", "some_float_value"), ("int = ", "some_int_value")]
            )
        self.assert_logs_for_float(captured.records, "float = ", "some_float_value")

    def test_display_param_link_list_with_title(self):
        with self.assertLogs(display_logger) as captured:
            self.aqm.display_param_link(
                [("float = ", "some_float_value"), ("int = ", "some_int_value")],
                title="this_is_title",
            )
        self.assert_logs_for_float(captured.records, "float = ", "some_float_value")
        self.assert_logs(captured.records, "this_is_title", 20)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
