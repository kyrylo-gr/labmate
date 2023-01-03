"""
This is the general tests that verify the front-end implementation.
So there is not tests on internal logic of the code. It's just a
verification of the api. So as soon as saving and opening works,
everything is good.
"""

import os
import shutil
# import shutil

import unittest

import numpy as np

from quanalys.acquisition_utils import AnalysisData
from quanalys.acquisition_utils import h5py_utils

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class WithoutSavingTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""

    def setUp(self):
        self.data_smart = AnalysisData()
        self.data_dict = {}

    @staticmethod
    def assertNpListEqual(d1, d2):
        return np.all(d1 == d2)

    @staticmethod
    def create_random_data(size=100):
        return list(np.random.randint(0, 100, size))

    def compare(self):
        self.compare_dict(self.data_smart._asdict(), self.data_dict)  # noqa

    def compare_dict(self, d1, d2):
        self.assertDictEqual(d1, d2)  # noqa

    def apply_func(self, func, *args, **kwds):
        getattr(self.data_dict, func)(*args, **kwds)
        getattr(self.data_smart, func)(*args, **kwds)

    def test_update(self):
        self.apply_func("update", a=self.create_random_data())
        self.apply_func("update", b=self.create_random_data())

        self.compare()

    def test_pop(self):
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("pop", 'a2')
        self.compare()

    def test_get(self):
        data = self.create_random_data()
        self.apply_func("update", data_to_get=data)
        self.assertNpListEqual(
            self.data_dict.get("data_to_get"),  # type: ignore
            self.data_smart.get("data_to_get"))  # type: ignore
        self.assertNpListEqual(
            self.data_dict.get("data_to_get"), data)  # type: ignore

    def test_getitem(self):
        data = self.create_random_data()
        self.apply_func("update", data_to_get=data)
        self.assertNpListEqual(
            self.data_dict['data_to_get'],
            self.data_smart['data_to_get'])

    def test_setitem(self):
        data = self.create_random_data()
        self.data_smart['a3'] = data

        self.assertNpListEqual(
            self.data_smart['a3'], data)

    def test_delitem(self):
        self.apply_func("update", a2=self.create_random_data())
        self.compare()

        del self.data_dict['a2']
        del self.data_smart['a2']

        self.compare()

    def test_getattr(self):
        data = self.create_random_data()
        self.data_smart['a3'] = data

        self.assertNpListEqual(self.data_smart.a3, data)

    def test_setattr(self):
        data = self.create_random_data()
        self.data_smart.a4 = data

        self.assertNpListEqual(self.data_smart.a4, data)

    def test_delattr(self):
        self.apply_func("update", a2=self.create_random_data())
        self.compare()

        del self.data_dict['a2']
        del self.data_smart.a2  # type: ignore  # noqa

        self.compare()

    def test_items(self):
        self.apply_func("update", a1=self.create_random_data())

        self.compare_dict(
            dict(self.data_dict.items()),
            dict(self.data_smart.items()))

    def test_keys(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a3=self.create_random_data())

        self.assertSetEqual(
            set(self.data_dict.keys()),
            set(self.data_smart.keys())
        )

    def test_values(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a3=self.create_random_data())

        self.assertNpListEqual(
            np.array(self.data_dict.values()),
            np.array(self.data_smart.values())
        )


class SavingOnEditTest(WithoutSavingTest):
    """Testing that AnalysisData saves the data on edit.
    Testing with simple data"""

    def setUp(self):
        self.data_smart = AnalysisData(
            filepath=DATA_FILE_PATH, overwrite=True, save_on_edit=True)
        # self.data_dict = {}

    @property
    def data_dict(self):
        return h5py_utils.open_h5(DATA_FILE_PATH)

    def compare_dict(self, d1, d2):
        self.assertSetEqual(
            set(d1.keys()), set(d2.keys()))

        for key in d1.keys():
            self.assertTrue(np.all(d1[key] == d2[key]))

    def apply_func(self, func, *args, **kwds):
        getattr(self.data_smart, func)(*args, **kwds)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class InitSetupTest(unittest.TestCase):
    """Tests mode and internal variable depending on different init setup"""

    def setUp(self):
        d = AnalysisData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        d['t'] = 3

    def test_with_nothing(self):
        d = AnalysisData()
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212

    def test_classical_read(self):
        d = AnalysisData(DATA_FILE_PATH)
        self.assertEqual(d._read_only, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_explicit_read(self):
        d = AnalysisData(DATA_FILE_PATH, read_only=True)
        self.assertEqual(d._read_only, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_impossible_read_save(self):
        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH, read_only=True, save_on_edit=True)

        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH, read_only=True, overwrite=True)

    def test_overwrite(self):
        d = AnalysisData(DATA_FILE_PATH, overwrite=True)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        with self.assertRaises(KeyError):
            d['t']

    def test_overwrite_write_mode(self):
        d = AnalysisData(DATA_FILE_PATH, overwrite=True, read_only=False)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        with self.assertRaises(KeyError):
            d['t']

    def test_open_to_save(self):
        d = AnalysisData(DATA_FILE_PATH, overwrite=False, read_only=False)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_raise_file_exist(self):
        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH, read_only=False)

        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH, read_only=False, save_on_edit=True)

        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH, save_on_edit=True)

    def test_open_to_save_with_save_on_edit(self):
        d = AnalysisData(DATA_FILE_PATH, overwrite=False, save_on_edit=True)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_no_file_exist_read_mode(self):
        os.remove(DATA_FILE_PATH)
        with self.assertRaises(ValueError):
            AnalysisData(DATA_FILE_PATH)

    def test_no_file_exist_save_mode(self):
        os.remove(DATA_FILE_PATH)
        d = AnalysisData(DATA_FILE_PATH, save_on_edit=True)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, True)  # pylint: disable=W0212

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class ReadModeTest(unittest.TestCase):
    """Test that no pos"""

    def setUp(self):
        d = AnalysisData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        d['t'] = 3

    def test_cannot_change_in_read_mode(self):
        d = AnalysisData(DATA_FILE_PATH)

        with self.assertRaises(TypeError):
            d['t'] = 2

        with self.assertRaises(TypeError):
            del d['t']

        with self.assertRaises(TypeError):
            d.pop('t')

        with self.assertRaises(TypeError):
            d.update(t=[2, 3])  # type: ignore

        with self.assertRaises(TypeError):
            d.t = 2

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SavingDifferentFormatTest(unittest.TestCase):
    """Saving different type of variables inside h5"""

    def setUp(self):
        self.data_smart = AnalysisData(
            filepath=DATA_FILE_PATH, overwrite=True, save_on_edit=True)

    def test_dict_save(self):
        pass

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == '__main__':
    unittest.main()
