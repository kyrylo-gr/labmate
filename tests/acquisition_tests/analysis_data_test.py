import os
import shutil

import unittest

from dh5 import DH5
from labmate.acquisition import AcquisitionManager, AnalysisData
from labmate.acquisition.acquisition_manager import read_config_files

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class AnalysisDataTest(unittest.TestCase):
    """Test that AnalysisManagerTest should perform as dictionary."""

    analysis_cell = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq.update(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.ad = AnalysisData(self.aqm.current_filepath, cell=self.analysis_cell)

    def test_nothing(self):
        with self.assertRaises(ValueError):
            AnalysisData(None)  # type: ignore

    def test_open_read_mode(self):
        self.assertEqual(self.ad.get("x", [])[0], 1)  # pylint: disable=E1136
        with self.assertRaises(KeyError, msg="Data is not locked"):
            self.ad["x"] = 2

        self.ad["z"] = 3

        sd = DH5(self.ad.filepath)
        self.assertEqual(sd.get("z"), 3)

    def test_analysis_cell(self):
        sd = DH5(self.aqm.aq.filepath)
        analysis_cell = sd.get("analysis_cells", {}).get("default")
        # if isinstance(analysis_cell, bytes):
        #     analysis_cell = analysis_cell.decode()
        self.assertEqual(analysis_cell, self.analysis_cell)

    def test_get_analysis_code(self):
        self.ad = AnalysisData(self.aqm.current_filepath, cell="none")
        code = self.ad.get_analysis_code()
        self.assertEqual(code, self.analysis_cell)

    def test_analysis_cell_file(self):
        self.ad = AnalysisData(self.aqm.current_filepath, cell=self.analysis_cell, save_files=True)
        with open(
            self.aqm.current_filepath + "_ANALYSIS_CELL_default.py", encoding="utf-8"
        ) as file:
            code = file.readline()
        self.assertEqual(code, self.analysis_cell)

    def test_save_fig(self):
        fig = SimpleSaveFig()
        self.ad.save_fig(fig)  # type: ignore

        self.assertTrue(
            os.path.exists(
                os.path.join(
                    DATA_DIR, self.experiment_name, self.aqm.current_filepath + "_FIG1.pdf"
                )
            )
        )

    def test_save_fig_given_number(self):
        fig = SimpleSaveFig()
        self.ad.save_fig(fig, 123)  # type: ignore

        self.assertTrue(
            os.path.exists(
                os.path.join(
                    DATA_DIR, self.experiment_name, self.aqm.current_filepath + "_FIG123.pdf"
                )
            )
        )

    def test_save_fig_given_name(self):
        fig = SimpleSaveFig()
        self.ad.save_fig(fig, "abc")  # type: ignore

        self.assertTrue(
            os.path.exists(
                os.path.join(
                    DATA_DIR, self.experiment_name, self.aqm.current_filepath + "_FIG_abc.pdf"
                )
            )
        )

    def test_save_fig_tight_layout(self):
        fig = SimpleSaveFigWithTightLayout()
        self.ad.save_fig(fig, "a")  # type: ignore

        self.assertTrue(
            os.path.exists(
                os.path.join(
                    DATA_DIR, self.experiment_name, self.aqm.current_filepath + "_FIG_a.pdf"
                )
            )
        )

        self.assertTrue(fig.tighted_layout)

    def test_save_fig_tight_layout_false(self):
        fig = SimpleSaveFigWithTightLayout()
        self.ad.save_fig(fig, "a", tight_layout=False)  # type: ignore

        self.assertTrue(
            os.path.exists(
                os.path.join(
                    DATA_DIR, self.experiment_name, self.aqm.current_filepath + "_FIG_a.pdf"
                )
            )
        )

        self.assertFalse(fig.tighted_layout)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class AnalysisDataParceTest(unittest.TestCase):
    """Test that AnalysisManagerTest should perform as dictionary."""

    analysis_cell = "this is a analysis cell"
    experiment_name = "abc"

    def setUp(self):
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
        self.aqm = AcquisitionManager(DATA_DIR)

        self.aqm.set_config_file(self.config)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq.update(x=[1, 2, 3], y=[[1, 2], [3, 4], [4, 5]])
        self.ad = AnalysisData(self.aqm.current_filepath, cell=self.analysis_cell)

    def compare_config(self, file="config.txt", data=None):
        # self.ad = AnalysisData(self.aqm.current_filepath)
        if data is None:
            data = self.ad.parse_config_file(file)

        self.assertEqual(data["int"], 123)
        self.assertEqual(data.int, 123)  # type: ignore
        self.assertEqual(data["int_underscore"], 213020)
        self.assertEqual(data["wrong_int"], "123 213")
        self.assertEqual(data["div_int"], "123 // 4")
        self.assertEqual(data["negative_int"], -123)
        self.assertEqual(data["float"], 123.45)
        self.assertEqual(data["negative_float"], -123.45)
        self.assertEqual(data["wrong_float"], "123.321.213")
        self.assertEqual(data["exp"], 1e5)
        self.assertEqual(data["negative_exp"], -1e5)
        self.assertEqual(data["wrong_exp"], "1e3ef")
        self.assertEqual(data["wrong_exp2"], "1e3e22")
        self.assertEqual(data["int_with_comment"], 123)
        self.assertFalse("commented_value" in data)
        self.assertFalse("tab_variable" in data)

    def test_parse_file(self):
        """This is no an obvious way to save config files."""
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name)
        self.aqm.aq["configs"] = read_config_files([self.config[0]])

        self.ad = AnalysisData(self.aqm.current_filepath)
        # print(self.ad.parse_config("config.txt"))
        self.compare_config()

    def test_parse_file_error_name(self):
        """Error if the name of the config file is wrong."""
        with self.assertRaises(ValueError):
            self.ad.parse_config_file("abc")

    def test_parse_file_error_file(self):
        """Error when there are no config files."""
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name + "2")

        self.ad = AnalysisData(self.aqm.current_filepath)

        with self.assertRaises((ValueError, KeyError)):
            self.ad.parse_config_file("abc")

    def test_parse_file_pushing_from_begging(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.compare_config()

    def test_parse_file_pushing_from_begging_small_name(self):
        """Name of the config file no full but begging is right."""
        self.compare_config("conf")

    def test_parse_file_the_same_name(self):
        """Name of the config file no full but begging is right."""
        self.compare_config("config.txt")
        self.compare_config("config.txt")

    def test_parse_file_with_second_short_name(self):
        """Name of the config file no full but begging is right."""
        self.compare_config("config.txt")
        self.compare_config("conf")

    def test_parse_config(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.ad.set_default_config_files(("config.txt",))
        data = self.ad.parse_config()
        self.compare_config(data=data)

    def test_parse_config_twice(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.ad.set_default_config_files(("config.txt",))
        data = self.ad.parse_config()
        self.compare_config(data=data)

        data = self.ad.parse_config()
        self.compare_config(data=data)

    def test_parse_config_list(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        data = self.ad.parse_config(["config.txt"])  # type: ignore
        self.compare_config(data=data)

    def test_parse_config_default_list(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.ad.set_default_config_files(["config.txt"])  # type: ignore
        data = self.ad.parse_config()
        self.compare_config(data=data)

    def set_data(self, key, value):
        self.ad[key] = value

    def test_parse_config_str(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.ad.set_default_config_files(("config.txt",))
        self.set_data("in_self_data", 789)
        data = self.ad.parse_config_str(["int", "int_underscore", "in_self_data"])
        self.assertIn("int", data)
        self.assertIn("123", data)

        self.assertIn("int_underscore", data)
        self.assertIn("213020", data)

        self.assertIn("in_self_data", data)
        self.assertIn("789", data)

    def test_eval_key(self):
        cfg = self.ad.parse_config_file("imported_config.py")

        self.assertDictEqual(cfg.eval_key("param_dict"), {"1": "123", "2": "456"})

    def test_eval_as_module(self):
        cfg = self.ad.parse_config_file("imported_config.py")
        self.assertEqual(cfg["param_int"], 1)
        self.assertEqual(cfg["param_float"], 2.5)
        self.assertEqual(cfg["param_float_link"], "param_float")
        cfg_module = cfg.eval_as_module()

        self.assertEqual(cfg_module.param_int, 1)
        self.assertEqual(cfg_module.param_float, 2.5)
        self.assertEqual(cfg_module.param_float_link, 2.5)

        self.assertDictEqual(cfg_module.param_dict, {"1": "123", "2": "456"})

    def test_parse_config_str_filename(self):
        """This right way to save configuration files.
        They should be set before creating a new acquisition.
        """
        self.ad.set_default_config_files(("config.txt",))
        data = self.ad.parse_config_str(["filename", "f", "file"])
        self.assertIn(f"file = {os.path.basename(self.aqm.current_filepath)}", data)
        self.assertIn(f"filename = {os.path.basename(self.aqm.current_filepath)}", data)
        self.assertIn(f"f = {os.path.basename(self.aqm.current_filepath)}", data)

    def test_parse_config_cfg(self):
        self.ad.set_default_config_files(("config.txt",))
        cfg = self.ad.cfg
        self.assertEqual(cfg["float"], 123.45)
        self.assertEqual(cfg.float, 123.45)  # type: ignore

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SimpleSaveFig:
    """This is emulation of a Figure class.
    The only goal of this class is to save something with savefig method.
    """

    def __init__(self, internal_data: str = "data"):
        """Init method with any custom internal_data that later can be accessed."""
        self.internal_data = internal_data

    def savefig(self, filepath: str):
        with open(filepath, mode="w", encoding="utf-8") as file:
            file.write(self.internal_data)


class SimpleSaveFigWithTightLayout(SimpleSaveFig):
    tighted_layout = False

    def tight_layout(self):
        self.tighted_layout = True


if __name__ == "__main__":
    unittest.main()
