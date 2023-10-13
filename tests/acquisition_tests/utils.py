import os
import logging
import unittest
from labmate.acquisition_notebook.acquisition_analysis_manager import logger as aqm_logger
from labmate.path import Path

TEST_DIR = Path(os.path.dirname(__file__))
DATA_DIR = Path(os.path.join(TEST_DIR, "tmp_test_data"))
DATA_FILE_PATH = Path(os.path.join(DATA_DIR, "some_data.h5"))

logging.basicConfig(level=logging.WARNING, force=True)
logging.StreamHandler().setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

aqm_logger.setLevel(logging.WARNING)


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
        return {"content": {"code": self.internal_data}}

    @property
    def last_execution_result(self):
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
        self.next_input = code


class LocalFig:
    def __init__(self):
        self.fig_saved = False

    def savefig(self, fname, **kwds):
        del fname, kwds
        self.fig_saved = True


class FunctionToRun:
    def __init__(self):
        self.function_run = 0

    def func(self):
        self.function_run += 1


class LogTest(unittest.TestCase):
    def check_logs(self, logs, msg, level):
        return any((msg in log.message and log.levelno >= level) for log in logs)

    def assert_logs(self, logs, msg=None, level=None):
        if isinstance(msg, list):
            for msg_ in msg:
                self.assert_logs(logs, msg_, level)
            return

        if msg:
            level = level if level is not None else 30

            self.assertTrue(
                self.check_logs(logs, msg, level),
                msg=f"No '{msg}' at level {level} inside: {[(l.message, l.levelno) for l in logs]}",
            )

        else:
            msg = "External variable used"
            level = level or 0
            self.assertFalse(
                self.check_logs(logs, msg, level),
                msg=f"There is '{msg}' inside: {[f'{log.levelno}:{log.message}' for log in logs]}",
            )
