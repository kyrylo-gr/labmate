import shutil
import unittest
import warnings
from pathlib import Path
from typing import Any

from labmate.acquisition import AcquisitionManager
from labmate.acquisition.acquisition_data import NotebookAcquisitionData
from labmate.acquisition.hooks import LifecycleHooks


TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "tmp_hooks_test_data"


class LifecycleHooksTest(unittest.TestCase):
    """Lifecycle hook dispatch on AcquisitionManager."""

    experiment_name = "test_hooks"

    def setUp(self):
        self.hooks = LifecycleHooks()
        self.am = AcquisitionManager(DATA_DIR, hooks=self.hooks)
        self.am.new_acquisition(self.experiment_name, cell="none")

    def test_dispatch_acquisition_saved_no_listeners(self):
        self.am.hooks.dispatch_acquisition_saved(self.am.current_acquisition)

    def test_dispatch_acquisition_data_loaded_no_listeners(self):
        self.am.hooks.dispatch_acquisition_data_loaded(self.am.current_acquisition)

    def test_dispatch_acquisition_saved_calls_listener(self):
        called = {}

        def on_save(acq: NotebookAcquisitionData, **_kwargs: Any) -> None:
            called["acq"] = acq

        self.am.hooks.add_acquisition_saved(on_save)
        self.am.hooks.dispatch_acquisition_saved(self.am.current_acquisition)
        self.assertIs(called["acq"], self.am.current_acquisition)

    def test_dispatch_acquisition_data_loaded_calls_listener(self):
        called = {}

        def on_loaded(acq: NotebookAcquisitionData, **_kwargs: Any) -> None:
            called["acq"] = acq

        self.am.hooks.add_acquisition_data_loaded(on_loaded)
        self.am.hooks.dispatch_acquisition_data_loaded(self.am.current_acquisition)
        self.assertIs(called["acq"], self.am.current_acquisition)

    def test_dispatch_acquisition_saved_multiple_listeners(self):
        called = []

        def a(acq: NotebookAcquisitionData, **_kwargs: Any) -> None:
            called.append("a")

        def b(acq: NotebookAcquisitionData, **_kwargs: Any) -> None:
            called.append("b")

        self.am.hooks.add_acquisition_saved(a)
        self.am.hooks.add_acquisition_saved(b)
        self.am.hooks.dispatch_acquisition_saved(self.am.current_acquisition)
        self.assertEqual(called, ["a", "b"])

    def test_dispatch_analysis_data_loading_runs_in_order(self):
        paths = []
        h5_path = str(DATA_DIR / "x.h5")

        def log_path(p: str, **_kwargs: Any) -> None:
            paths.append(p)

        self.hooks.add_analysis_data_loading(log_path)
        self.hooks.add_analysis_data_loading(lambda p, **_kw: paths.append(p + "_2"))
        self.hooks.dispatch_analysis_data_loading(h5_path)
        self.assertEqual(paths, [h5_path, h5_path + "_2"])

    def test_dispatch_analysis_cell_ready(self):
        seen = []

        self.hooks.add_analysis_cell_ready(lambda **_kw: seen.append(1))
        self.hooks.add_analysis_cell_ready(lambda **_kw: seen.append(2))
        self.hooks.dispatch_analysis_cell_ready()
        self.assertEqual(seen, [1, 2])

    def test_set_analysis_cell_ready_replaces(self):
        seen = []
        self.hooks.set_analysis_cell_ready(lambda **_kw: seen.append("a"))
        self.hooks.set_analysis_cell_ready(lambda **_kw: seen.append("b"))
        self.hooks.dispatch_analysis_cell_ready()
        self.assertEqual(seen, ["b"])

    def test_add_hook_without_var_keyword_warns(self):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            hooks = LifecycleHooks()

            def cb(_acq: NotebookAcquisitionData) -> None:
                pass

            hooks.add_acquisition_saved(cb)
            self.assertEqual(len(recorded), 1)
            self.assertTrue(issubclass(recorded[0].category, FutureWarning))

    def test_add_hook_with_var_keyword_no_warning(self):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            hooks = LifecycleHooks()

            def cb(_acq: NotebookAcquisitionData, **_kwargs: Any) -> None:
                pass

            hooks.add_acquisition_saved(cb)
            self.assertEqual(len(recorded), 0)

    def test_set_analysis_cell_ready_warns_per_callback(self):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            hooks = LifecycleHooks()
            hooks.set_analysis_cell_ready([lambda: None, lambda: None])
            self.assertEqual(len(recorded), 2)

    def test_dispatch_forwards_kwargs_only_when_callback_accepts_var_keyword(self):
        hooks = LifecycleHooks()
        received_legacy = []
        received_modern = []

        def legacy(acq: NotebookAcquisitionData) -> None:
            received_legacy.append({"acq": acq, "kwargs": {}})

        def modern(acq: NotebookAcquisitionData, **kwargs: Any) -> None:
            received_modern.append({"acq": acq, "kwargs": kwargs})

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            hooks.add_acquisition_saved(legacy)

        hooks.add_acquisition_saved(modern)
        acq = self.am.current_acquisition
        hooks.dispatch_acquisition_saved(acq, reason="x", stage=1)

        self.assertEqual(len(received_legacy), 1)
        self.assertIs(received_legacy[0]["acq"], acq)
        self.assertEqual(received_legacy[0]["kwargs"], {})

        self.assertEqual(len(received_modern), 1)
        self.assertIs(received_modern[0]["acq"], acq)
        self.assertEqual(received_modern[0]["kwargs"], {"reason": "x", "stage": 1})

    def test_dispatch_cell_ready_forwards_kwargs(self):
        hooks = LifecycleHooks()
        seen = []

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            hooks.add_analysis_cell_ready(lambda: seen.append("legacy"))

        hooks.add_analysis_cell_ready(lambda **kwargs: seen.append(kwargs))
        hooks.dispatch_analysis_cell_ready(flags=2)
        self.assertEqual(seen, ["legacy", {"flags": 2}])

    @classmethod
    def tearDownClass(cls):
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == "__main__":
    unittest.main()
