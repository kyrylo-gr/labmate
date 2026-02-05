# pylint: disable=W0611
"""Utils for testing."""

import logging
import unittest

# from dh5.path import Path
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

from labmate.acquisition_notebook.acquisition_analysis_manager import (  # noqa: F401
    logger as aqm_logger,
)


TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "tmp_test_data"
DATA_FILE_PATH = DATA_DIR / "some_data.h5"

logging.basicConfig(level=logging.WARNING, force=True)
logging.StreamHandler().setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

# aqm_logger.setLevel(logging.WARNING)


class ShellEmulator:
    """This is emulation of a Figure class.

    The only goal of this class is to save something with savefig method.
    """

    last_success = True
    last_cell = "aqm.acquisition_cell('abc')"

    def __init__(self, internal_data: str = "shell_emulator_data"):
        """Create Shell Emulator.

        Args:
            internal_data (str, optional): Any custom data. Defaults to "shell_emulator_data".
        """
        self.internal_data = internal_data
        self.next_input = ""

    def get_parent(self):
        """Emulate shell from ipython. Return dict with code."""
        return {"content": {"code": self.internal_data}}

    @property
    def last_execution_result(self):
        """Emulate shell from ipython. Return info about last execution."""
        from labmate.attrdict import AttrDict

        return AttrDict(
            {
                "info": {
                    "raw_cell": self.last_cell,
                },
                "success": self.last_success,
            }
        )

    def set_next_input(self, code):
        """Set self.next_input to code."""
        self.next_input = code


class LocalFig:
    """Emulate Figure behaviour.

    The only parameter is fig_saved, which is False by default.
    It changes its value when savefig method is called.
    """

    def __init__(self):
        """Set self.fig_saved to False."""
        self.fig_saved = False

    def savefig(self, fname, **kwds):
        """Change self.fig_saved to True."""
        del fname, kwds
        self.fig_saved = True


class FunctionToRun:
    """Emulate Function behaviour."""

    def __init__(self):
        """Set self.function_run counter to 0."""
        self.function_run = 0

    def func(self):
        """Increase self.function_run counter by 1."""
        self.function_run += 1


class LogTest(unittest.TestCase):
    """Helper with log checks."""

    def check_logs(self, logs, msg, level) -> bool:
        """Check if `msg` is in `logs` messages at level >= `level`.

        Args:
            logs (logs): Logs captured by assertLogs(aqm_logger).
            msg (str): Message to look for.
            level (_type_): Minimal accepting level of the provided message.

        Returns:
            If message was found.
        """
        return any((msg in log.message and log.levelno >= level) for log in logs)

    def assert_logs(
        self,
        logs,
        msg: Optional[Union[str, List[str]]] = None,
        level: Optional[int] = None,
    ):
        """Assert that `msg` is in `logs` messages at level >= `level`.

        Args:
            logs (logs): Logs captured by assertLogs(aqm_logger).
            msg (str | list, optional): expected message or list of them. If nothing is provided,
                then it assert that there are no messages at `level` or higher.
            level (int, optional): Minimal accepting level of the provided message(s).
                Defaults to 30 (INFO level).
        """
        if isinstance(msg, list):
            for msg_ in msg:
                self.assert_logs(logs, msg_, level)
            return

        if msg:
            level = level if level is not None else 30

            self.assertTrue(
                self.check_logs(logs, msg, level),
                msg=f"No '{msg}' at level {level} inside: "
                f"{[f'{log.levelno}:{log.message}' for log in logs]}",
            )

        else:
            msg = "External variable used"
            level = level or 0
            self.assertFalse(
                self.check_logs(logs, msg, level),
                msg=f"There is '{msg}' inside: {[f'{log.levelno}:{log.message}' for log in logs]}",
            )


def compare_np_array(array1: Union[list, np.ndarray], array2: Union[list, np.ndarray]):
    """Return the sum of absolute difference between two arrays."""
    return np.abs(np.array(array1) - np.array(array2)).sum()  # type: ignore
