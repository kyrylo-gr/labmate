import os
import shutil
import unittest
from concurrent.futures import Future
from unittest.mock import Mock, patch

from labmate.acquisition import AcquisitionManager
from labmate.acquisition.acquisition_data import NotebookAcquisitionData
from labmate.acquisition.backend import AcquisitionBackend

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")


class MockBackend(AcquisitionBackend):
    """Mock backend for testing."""

    def __init__(self):
        """Initialize mock backend with call tracking."""
        self.save_snapshot_called = False
        self.load_snapshot_called = False
        self.save_snapshot_acquisition = None
        self.load_snapshot_acquisition = None

    def save_snapshot(self, acquisition: NotebookAcquisitionData) -> None:
        """Track that save_snapshot was called."""
        self.save_snapshot_called = True
        self.save_snapshot_acquisition = acquisition

    def load_snapshot(self, acquisition: NotebookAcquisitionData) -> None:
        """Track that load_snapshot was called."""
        self.load_snapshot_called = True
        self.load_snapshot_acquisition = acquisition


class BackendTest(unittest.TestCase):
    """Test backend scheduling methods in AcquisitionManager."""

    experiment_name = "test_backend"

    def setUp(self):
        """Set up test fixtures."""
        self.aqm = AcquisitionManager(DATA_DIR)
        self.aqm.new_acquisition(self.experiment_name, cell="none")

    def test_schedule_backend_save_no_backend(self):
        """Test that _schedule_backend_save returns None when backend is None."""
        self.aqm._backend = None
        result = self.aqm._schedule_backend_save(self.aqm.current_acquisition)
        self.assertIsNone(result)

    def test_schedule_backend_load_no_backend(self):
        """Test that _schedule_backend_load returns None when backend is None."""
        self.aqm._backend = None
        result = self.aqm._schedule_backend_load(self.aqm.current_acquisition)
        self.assertIsNone(result)

    def test_schedule_backend_save_single_backend(self):
        """Test that _schedule_backend_save calls backend.save_snapshot."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        future = self.aqm._schedule_backend_save(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        self.assertIsInstance(future, Future)
        assert future is not None

        # Wait for the future to complete
        future.result(timeout=5)

        # Verify backend was called
        self.assertTrue(mock_backend.save_snapshot_called)
        self.assertEqual(
            mock_backend.save_snapshot_acquisition, self.aqm.current_acquisition
        )

    def test_schedule_backend_load_single_backend(self):
        """Test that _schedule_backend_load calls backend.load_snapshot."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        future = self.aqm._schedule_backend_load(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        self.assertIsInstance(future, Future)
        assert future is not None

        # Wait for the future to complete
        future.result(timeout=5)

        # Verify backend was called
        self.assertTrue(mock_backend.load_snapshot_called)
        self.assertEqual(
            mock_backend.load_snapshot_acquisition, self.aqm.current_acquisition
        )

    def test_schedule_backend_save_multiple_backends(self):
        """Test that _schedule_backend_save calls all backends."""
        mock_backend1 = MockBackend()
        mock_backend2 = MockBackend()
        self.aqm._backend = (mock_backend1, mock_backend2)

        future = self.aqm._schedule_backend_save(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        self.assertIsInstance(future, Future)
        assert future is not None
        # Wait for the future to complete
        future.result(timeout=5)

        # Verify both backends were called
        self.assertTrue(mock_backend1.save_snapshot_called)
        self.assertTrue(mock_backend2.save_snapshot_called)
        self.assertEqual(
            mock_backend1.save_snapshot_acquisition, self.aqm.current_acquisition
        )
        self.assertEqual(
            mock_backend2.save_snapshot_acquisition, self.aqm.current_acquisition
        )

    def test_schedule_backend_load_multiple_backends(self):
        """Test that _schedule_backend_load calls all backends."""
        mock_backend1 = MockBackend()
        mock_backend2 = MockBackend()
        self.aqm._backend = (mock_backend1, mock_backend2)

        future = self.aqm._schedule_backend_load(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        self.assertIsInstance(future, Future)
        assert future is not None

        # Wait for the future to complete
        future.result(timeout=5)

        # Verify both backends were called
        self.assertTrue(mock_backend1.load_snapshot_called)
        self.assertTrue(mock_backend2.load_snapshot_called)
        self.assertEqual(
            mock_backend1.load_snapshot_acquisition, self.aqm.current_acquisition
        )
        self.assertEqual(
            mock_backend2.load_snapshot_acquisition, self.aqm.current_acquisition
        )

    def test_schedule_backend_save_executor_shutdown(self):
        """Test that executor is shut down after save completes."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        future = self.aqm._schedule_backend_save(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        assert future is not None
        # Wait for the future to complete
        future.result(timeout=5)

        # Verify executor is shut down (future should be done)
        self.assertTrue(future.done())

    def test_schedule_backend_load_executor_shutdown(self):
        """Test that executor is shut down after load completes."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        future = self.aqm._schedule_backend_load(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        assert future is not None

        # Wait for the future to complete
        future.result(timeout=5)

        # Verify executor is shut down (future should be done)
        self.assertTrue(future.done())

    def test_schedule_backend_save_backend_none_after_submit(self):
        """Test that save_snapshot handles backend being None after submit."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        # Patch to simulate backend becoming None after executor submit
        original_save = mock_backend.save_snapshot

        def save_with_none_check(acquisition):
            self.aqm._backend = None
            original_save(acquisition)

        mock_backend.save_snapshot = save_with_none_check

        future = self.aqm._schedule_backend_save(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        assert future is not None
        # Wait for the future to complete
        future.result(timeout=5)

        # Verify backend was still called before it became None
        self.assertTrue(mock_backend.save_snapshot_called)

    def test_schedule_backend_load_backend_none_after_submit(self):
        """Test that load_snapshot handles backend being None after submit."""
        mock_backend = MockBackend()
        self.aqm._backend = (mock_backend,)

        # Patch to simulate backend becoming None after executor submit
        original_load = mock_backend.load_snapshot

        def load_with_none_check(acquisition):
            self.aqm._backend = None
            original_load(acquisition)

        mock_backend.load_snapshot = load_with_none_check

        future = self.aqm._schedule_backend_load(self.aqm.current_acquisition)
        self.assertIsNotNone(future)
        assert future is not None
        # Wait for the future to complete
        future.result(timeout=5)

        # Verify backend was still called before it became None
        self.assertTrue(mock_backend.load_snapshot_called)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory once all tests finished."""
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == "__main__":
    unittest.main()
