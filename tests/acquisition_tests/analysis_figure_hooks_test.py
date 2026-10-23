"""Regression tests for figure notifications during current and old-data analysis."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dh5 import DH5

from labmate.acquisition import AnalysisData
from labmate.acquisition_notebook import AcquisitionAnalysisManager

from .utils import LocalFig


class FileFigure:
    """Write a figure sidecar without importing a plotting backend."""

    def savefig(self, fname, **kwargs):
        Path(fname).write_text("figure contents", encoding="utf-8")


class AnalysisFigureHooksTest(unittest.TestCase):
    """Keep existing callbacks compatible while notifying old-data integrations."""

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.aqm = AcquisitionAnalysisManager(
            directory.name, use_magic=False, shell=None, save_files=True
        )
        self.aqm.acquisition_cell("first", cell="none")
        self.aqm.save_acquisition(x=[1, 2, 3])
        self.legacy_events = []
        self.analysis_events = []
        self.aqm.hooks.add_figure_saved(
            lambda acquisition, **kwargs: self.legacy_events.append(acquisition)
        )
        self.aqm.hooks.add_analysis_figure_saved(
            lambda analysis, **kwargs: self.analysis_events.append(analysis)
        )

    def test_current_figure_notifies_both_hooks_once_with_original_objects(self):
        acquisition = self.aqm.current_acquisition
        analysis = self.aqm.data

        result = self.aqm.save_fig(fig=FileFigure(), name="fit.svg", cell="fit_code")

        self.assertIs(result, self.aqm)
        self.assertEqual(len(self.legacy_events), 1)
        self.assertIs(self.legacy_events[0], acquisition)
        self.assertEqual(len(self.analysis_events), 1)
        self.assertIs(self.analysis_events[0], analysis)
        self.assertIsInstance(self.analysis_events[0], AnalysisData)

    def test_reopened_figure_notifies_analysis_hook_without_current_acquisition(self):
        filepath = str(self.aqm.current_filepath)
        self.aqm.analysis_cell(filepath=filepath, cell="none")
        self.assertIsNone(self.aqm.current_acquisition)

        self.aqm.save_fig(fig=FileFigure(), name="fit.svg", cell="fit_code")

        self.assertEqual(self.legacy_events, [])
        self.assertEqual(len(self.analysis_events), 1)
        self.assertIs(self.analysis_events[0], self.aqm.data)
        self.assertEqual(str(self.analysis_events[0].filepath), filepath)

    def test_reopened_figure_uses_loaded_file_instead_of_another_active_acquisition(self):
        old_filepath = str(self.aqm.current_filepath)
        self.aqm.acquisition_cell("second", cell="none")
        self.aqm.save_acquisition(x=[4, 5, 6])
        active_filepath = str(self.aqm.current_filepath)
        self.aqm.analysis_cell(filepath=old_filepath, cell="none")

        self.aqm.save_fig(fig=FileFigure(), name="fit.svg", cell="fit_code")

        self.assertEqual(self.legacy_events, [])
        self.assertEqual(len(self.analysis_events), 1)
        self.assertEqual(str(self.analysis_events[0].filepath), old_filepath)
        self.assertNotEqual(str(self.analysis_events[0].filepath), active_filepath)

    def test_notification_runs_after_figure_and_analysis_cell_are_on_disk(self):
        seen = []

        def on_saved(analysis, **kwargs):
            figure_path = Path(str(analysis.filepath) + "_FIG_fit.svg")
            saved = DH5(analysis.filepath, "r")
            seen.append((figure_path.read_text(encoding="utf-8"), saved["analysis_cells"]["fit"]))

        self.aqm.hooks.add_analysis_figure_saved(on_saved)
        self.aqm.save_fig(fig=FileFigure(), name="fit", extensions="svg", cell="fit_code")

        self.assertEqual(seen, [("figure contents", "fit_code")])

    def test_figure_save_failure_does_not_notify_either_hook(self):
        figure = LocalFig()
        with self.assertRaisesRegex(OSError, "figure write failed"), patch.object(
            figure, "savefig", side_effect=OSError("figure write failed")
        ):
            self.aqm.save_fig(fig=figure, name="fit", cell="fit_code")

        self.assertEqual(self.legacy_events, [])
        self.assertEqual(self.analysis_events, [])

    def test_analysis_cell_save_failure_does_not_notify_either_hook(self):
        with self.assertRaisesRegex(OSError, "analysis write failed"), patch.object(
            AnalysisData, "save_analysis_cell", side_effect=OSError("analysis write failed")
        ):
            self.aqm.save_fig(fig=FileFigure(), name="fit.svg", cell="fit_code")

        self.assertEqual(self.legacy_events, [])
        self.assertEqual(self.analysis_events, [])

    def test_standalone_save_fig_only_does_not_notify_either_hook(self):
        self.aqm.save_fig_only(fig=FileFigure(), name="fit.svg")

        self.assertEqual(self.legacy_events, [])
        self.assertEqual(self.analysis_events, [])


if __name__ == "__main__":
    unittest.main()
