import os
import shutil

from labmate.acquisition_notebook import AcquisitionAnalysisManager

from .utils import DATA_DIR, LogTest, ShellEmulator, aqm_logger


class LintingTest(LogTest):
    cell_text = "this is a analysis cell"
    experiment_name = "abc"

    x, y = [1, 2, 3], [4, 5, 6]

    def setUp(self):
        shell = ShellEmulator(self.cell_text)
        self.aqm = AcquisitionAnalysisManager(
            DATA_DIR, use_magic=False, save_files=False, save_on_edit=True, shell=shell
        )  # type: ignore
        self.turn_on_linting()

    def turn_on_linting(self):
        self.aqm.linting(allowed_variables=["aqm", "plt", "func"])

    def run_test(self, cell=""):
        cell = self.remove_tabs(cell)
        self.aqm.acquisition_cell(self.experiment_name)
        with self.assertLogs(aqm_logger) as captured:
            self.aqm.analysis_cell(cell=cell)
        return captured

    @staticmethod
    def remove_tabs(code: str):
        tabs = " " * (code.find("aqm"))
        return code.replace(tabs, "")

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
        self.assert_logs(logs.records, ["x", "y"], 30)

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
        self.assert_logs(logs.records, ["x1", "x2", "x3", "x4"])

    def test_lint_lambda_function(self):
        code = """\
        aqm.analysis_cell()
        f = lambda x, y: x + y - 5
        f = lambda x : x - 5
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def test_lint_lambda_function_wrong(self):
        code = """\
        aqm.analysis_cell()
        f = lambda x, y: x + y - 5*x1
        """
        logs = self.run_test(code)
        self.assert_logs(logs.records, ["x1"])

    def test_lint_save_fig_twice(self):
        code = """\
        aqm.analysis_cell()

        aqm.save_fig("name1")
        aqm.save_fig("name2")

        aqm.save_fig(name="name1")
        aqm.save_fig(name="name2")

        aqm.save_fig("name1")
        aqm.save_fig(name="name2")

        """
        logs = self.run_test(code)
        self.assert_logs(logs.records)

    def lint_save_fig_twice_wrong_cascade(self, code):
        logs = self.run_test(code)
        self.assert_logs(logs.records, ["save_fig"])

    def test_lint_save_fig_twice_wrong_1(self):
        code = """\
        aqm.save_fig("name1")
        aqm.save_fig("name1")
        """
        return self.lint_save_fig_twice_wrong_cascade(code)

    def test_lint_save_fig_twice_wrong_2(self):
        code = """\
        aqm.save_fig(name="name1")
        aqm.save_fig(name="name1")
        """
        return self.lint_save_fig_twice_wrong_cascade(code)

    def test_lint_save_fig_twice_wrong_3(self):
        code = """\
        aqm.save_fig("name1")
        aqm.save_fig(name="name1")
        """
        return self.lint_save_fig_twice_wrong_cascade(code)

    def test_lint_save_fig_twice_wrong_4(self):
        code = """\
        aqm.save_fig(fig, name="name1")
        aqm.save_fig(fig, name="name1")
        """
        return self.lint_save_fig_twice_wrong_cascade(code)

    def test_lint_save_fig_twice_wrong_5(self):
        code = """\
        aqm.save_fig(fig)
        aqm.save_fig(fig)
        """
        return self.lint_save_fig_twice_wrong_cascade(code)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)


class LintingByFileTest(LintingTest):
    def turn_on_linting(self):
        variables = ["aqm", "plt", "func"]
        filename = os.path.join(self.aqm.data_directory, "lint.py")
        with open(filename, "w", encoding="utf-8") as file:
            for var in variables:
                file.write(f"{var}=None\n")

        self.aqm.linting(init_file=filename)
