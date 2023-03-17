"""
This is the general tests that verify the front-end implementation.
So there is not tests on internal logic of the code. It's just a
verification of the api. So as soon as saving and opening works,
everything is good.
"""

import os
import shutil

import unittest

import numpy as np

from labmate.syncdata import SyncData
from labmate.syncdata import h5py_utils

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")
DATA_FILE_PATH = os.path.join(DATA_DIR, "some_data.h5")


class WithoutSavingTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""

    def setUp(self):
        self.data_smart = SyncData()
        self.data_dict = {}

    # @staticmethod
    def assertNpListEqual(self, d1, d2):
        self.assertTrue(np.all(d1 == d2),
                        msg=f"Arrays are not equal.\n d1 = {d1}.\n d2 = {d2}")

    @staticmethod
    def create_random_data(size=100):
        return list(np.random.randint(0, 100, size))

    def compare(self):
        self.compare_dict(self.data_smart, self.data_dict)  # noqa

    def compare_dict(self, d1, d2):
        self.assertSetEqual(
            set(d1.keys()), set(d2.keys()))

        for key in d1.keys():
            self.assertTrue(np.all(d1[key] == d2[key]))

    def apply_func(self, func, *args, **kwds):
        getattr(self.data_dict, func)(*args, **kwds)
        getattr(self.data_smart, func)(*args, **kwds)

    def test_init_empty(self):
        data_dict = {}
        data_smart = SyncData({})
        self.compare_dict(data_smart, data_dict)  # noqa

    def test_init_dict(self):
        data_dict = {'a': [1, 2, 3], 'b': [1, 2, 3]}
        data_smart = SyncData(data_dict)
        self.compare_dict(data_smart, data_dict)  # noqa

    def test_asdict(self):
        data_dict = {'a': [1, 2, 3], 'b': [1, 2, 3]}
        data_smart = SyncData(data_dict)
        d = data_smart.asdict()
        data_smart2 = SyncData(d)
        self.compare_dict(data_smart, data_smart2)

    def test_update_kwds(self):
        self.apply_func("update", a=self.create_random_data())
        self.apply_func("update", b=self.create_random_data())

        self.compare()

    def test_update_dict(self):
        # self.data_dict.update(data)
        # self.data_smart.update(data)
        # self.apply_func("update", )
        self.apply_func("update", {'a': self.create_random_data()})
        self.apply_func("update", {'b': self.create_random_data()})
        self.apply_func("update", {
            'd': self.create_random_data(),
            'c': self.create_random_data()})

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

    def test_get_dict(self):
        data = self.create_random_data()
        self.apply_func("update", data_to_get=data)
        self.assertNpListEqual(
            self.data_dict.get("data_to_get"),  # type: ignore
            self.data_smart.get_dict("data_to_get"))  # type: ignore
        self.assertNpListEqual(
            self.data_dict.get("data_to_get"), data)  # type: ignore

        data = {'a': 1, 'b': 2}
        self.data_smart['dict'] = data
        self.assertIsInstance(
            self.data_smart.get_dict("dict"), dict)
        self.assertDictEqual(
            self.data_smart.get_dict("dict", {}), data)

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

    def test_setitem_tuple_dict(self):
        data = self.create_random_data()
        self.data_smart['a3'] = {}
        self.data_smart['a3', 'b'] = data

        self.assertNpListEqual(
            self.data_smart['a3']['b'], data)
        self.assertNpListEqual(
            self.data_smart['a3', 'b'], data)

    def test_setitem_tuple_list(self):
        data = self.create_random_data()
        self.data_smart['a3'] = data.copy()
        self.data_smart['a3'][0] = 5000
        # print(data)
        # print(self.data_smart['a3'])
        data[0] = 5000
        self.assertNpListEqual(
            self.data_smart['a3'], data)

    def test_delitem(self):
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a1=self.create_random_data())
        self.compare()

        del self.data_dict['a2']
        del self.data_smart['a2']

        self.compare()

    def test_getattr(self):
        data = self.create_random_data()
        self.data_smart['a3'] = data

        self.assertNpListEqual(self.data_smart.a3, data)

    def test_getattr_int(self):
        data = self.create_random_data()
        data2 = self.create_random_data()
        self.data_smart['3'] = data

        self.assertNpListEqual(self.data_smart.i3, data)
        self.data_smart['i3'] = data2
        self.assertNpListEqual(self.data_smart.i3, data2)
        self.assertNpListEqual(self.data_smart['3'], data)

    def test_attributeError(self):
        with self.assertRaises(AttributeError):
            _ = self.data_smart.no_exists

    def test_setattr(self):
        data = self.create_random_data()
        self.data_smart.a4 = data

        self.assertNpListEqual(self.data_smart.a4, data)

    def test_delattr(self):
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a1=self.create_random_data())
        self.compare()

        del self.data_dict['a2']
        del self.data_smart.a2  # type: ignore  # noqa

        self.compare()

    def test_items(self):
        self.apply_func("update", a1=self.create_random_data())

        self.compare_dict(
            dict(self.data_dict.items()),
            dict(self.data_smart.items()))

    def test_items_iter(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())

        data_dict = self.data_dict

        for k, v in self.data_smart.items():
            # self.assertTrue(k in ('a1', 'a2'))
            self.assertTrue(np.all(data_dict[k] == v))

    def test_keys(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a3=self.create_random_data())

        self.assertSetEqual(
            set(self.data_dict.keys()),
            set(self.data_smart.keys())
        )

    def test_iter(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())

        keys = [k for k in self.data_smart]

        for k in ('a1', 'a2'):
            self.assertTrue(k in keys)

    def test_values(self):
        self.apply_func("update", a1=self.create_random_data())
        self.apply_func("update", a2=self.create_random_data())
        self.apply_func("update", a3=self.create_random_data())
        # print(np.all(np.array(list(self.data_dict.values())) == np.array(list(self.data_smart.values()))))
        self.assertNpListEqual(
            np.array(list(self.data_dict.values())),
            np.array(list(self.data_smart.values()))
        )

    def test_repr(self):
        class Test:
            """Random class"""
            __should_not_be_converted__ = True

            def asdict(self):
                return {}

        data = self.create_random_data()
        self.data_smart['ab1'] = data
        self.data_smart['ab2'] = 123
        self.data_smart['ab3'] = 123.45
        self.data_smart['ab4'] = {"a": 567, "b": {"c": {"d": {"e": {"f": "g"}}}}}
        self.data_smart['ab5'] = Test()
        rep = repr(self.data_smart)
        for key in ['ab1', 'ab2', 'ab3', 'ab4', 'ab5']:
            self.assertIn(key, rep)

        self.assertIn('Test', rep)

    def test_keys_tree(self):
        data = self.create_random_data()
        self.data_smart['ab1'] = data
        self.data_smart['ab2'] = 123
        self.data_smart['ab2'] = {"a": 567, "b": {"c": "d"}}
        rep = self.data_smart.keys_tree()
        self.assertIn('ab1', rep)
        self.assertIn('ab2', rep)
        self.assertIn('a', rep.get('ab2', {}))  # type: ignore
        self.assertIn('b', rep.get('ab2', {}))  # type: ignore
        self.assertIn('c', rep.get('ab2', {}).get('b', {}))  # type: ignore

    def test_str(self):
        self.data_smart['ab1'] = 1
        self.data_smart['ab2'] = 2
        string = str(self.data_smart)
        self.assertIn('ab1', string)
        self.assertIn('ab2', string)

    def test_dir(self):
        data = self.create_random_data()
        self.data_smart['abc1234'] = data
        self.data_smart['abc1235'] = data
        d = dir(self.data_smart)
        for k in self.data_smart.keys():
            self.assertIn(k, d)


class SavingOnEditTest(WithoutSavingTest):
    """Testing that SyncData saves the data on edit.
    Testing with simple data"""

    def setUp(self):
        self.data_smart = SyncData(
            filepath=DATA_FILE_PATH, overwrite=True, save_on_edit=True)

    @property
    def data_dict(self):
        return h5py_utils.open_h5(DATA_FILE_PATH)

    def apply_func(self, func, *args, **kwds):
        getattr(self.data_smart, func)(*args, **kwds)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SavingManualTest(SavingOnEditTest):
    """Testing that SyncData saves the data after save function runs."""

    def setUp(self):
        self.data_smart = SyncData(
            filepath=DATA_FILE_PATH, overwrite=True, save_on_edit=False)

    @property
    def data_dict(self):
        self.data_smart.save(just_update=False)
        return h5py_utils.open_h5(DATA_FILE_PATH)


class SavingManualJustUpdateTest(SavingManualTest):
    """Testing that SyncData saves the data after save(just_update=True) function runs."""

    @property
    def data_dict(self):
        self.data_smart.save(just_update=True)
        return h5py_utils.open_h5(DATA_FILE_PATH)


class SavingOnEditWithReadonlyFieldTest(SavingOnEditTest):
    """Testing that SyncData saves the data after save(just_update=True) function runs."""

    def setUp(self):
        self.data_smart = SyncData(
            filepath=DATA_FILE_PATH, overwrite=True, save_on_edit=True)
        self.data_smart['a0'] = self.create_random_data()
        self.data_smart.lock_data('a0')


class InitSetupTest(unittest.TestCase):
    """Tests mode and internal variable depending on different init setup"""

    def setUp(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        d['t'] = 3

    def test_with_nothing(self):
        d = SyncData()
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212

    def test_classical_read(self):
        d = SyncData(DATA_FILE_PATH)
        self.assertEqual(d._read_only, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_explicit_read(self):
        d = SyncData(DATA_FILE_PATH, read_only=True)
        self.assertEqual(d._read_only, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_impossible_read_save(self):
        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH, read_only=True, save_on_edit=True)

        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH, read_only=True, overwrite=True)

    def test_overwrite(self):
        d = SyncData(DATA_FILE_PATH, overwrite=True)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        with self.assertRaises(KeyError):
            _ = d['t']

    def test_overwrite_write_mode(self):
        d = SyncData(DATA_FILE_PATH, overwrite=True, read_only=False)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        with self.assertRaises(KeyError):
            _ = d['t']

    def test_open_to_save(self):
        d = SyncData(DATA_FILE_PATH, overwrite=False, read_only=False)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, False)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_raise_file_exist(self):
        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH, read_only=False)

        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH, read_only=False, save_on_edit=True)

        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH, save_on_edit=True)

    def test_open_to_save_with_save_on_edit(self):
        d = SyncData(DATA_FILE_PATH, overwrite=False, save_on_edit=True)
        self.assertEqual(d._read_only, False)  # pylint: disable=W0212
        self.assertEqual(d._save_on_edit, True)  # pylint: disable=W0212
        self.assertEqual(d['t'], 3)

    def test_no_file_exist_read_mode(self):
        os.remove(DATA_FILE_PATH)
        with self.assertRaises(ValueError):
            SyncData(DATA_FILE_PATH)

    def test_no_file_exist_save_mode(self):
        os.remove(DATA_FILE_PATH)
        d = SyncData(DATA_FILE_PATH, save_on_edit=True)
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
    """Test that no changes can be made in the read mode.
    And test the locking features"""

    def setUp(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        d['t'] = 3

    def test_global_readonly(self):
        # from labmate.utils.async_utils import sleep
        d = SyncData(DATA_FILE_PATH, read_only=True)

        with self.assertRaises(ValueError):
            d.lock_data()

        with self.assertRaises(ValueError):
            d.lock_data('t')

        with self.assertRaises(ValueError):
            d.unlock_data()

        with self.assertRaises(ValueError):
            d.unlock_data('t')

        with self.assertRaises(ValueError):
            d.save(just_update=True)

        with self.assertRaises(ValueError):
            d.save(just_update=False)

    def test_cannot_change_in_read_mode(self):
        d = SyncData(DATA_FILE_PATH)

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

    def test_lock_data_without_args(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        self.assertEqual(d['t'], 3)
        d['t2'] = 4
        d.lock_data()
        self.assertEqual(d['t'], 3)
        with self.assertRaises(TypeError):
            d['t'] = 2
        with self.assertRaises(TypeError):
            d['t2'] = 2

    def test_lock_data_with_str(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        d['t1'], d['t2'] = 3, 4

        d.lock_data('t2')

        self.assertEqual(d['t1'], 3)
        d['t1'] = 5
        self.assertEqual(d['t1'], 5)

        self.assertEqual(d['t2'], 4)
        with self.assertRaises(TypeError):
            d['t2'] = 2

    def test_lock_data_with_list(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        d['t1'], d['t2'] = 3, 4

        d.lock_data(['t1', 't2'])

        with self.assertRaises(TypeError):
            d['t1'] = 2
        with self.assertRaises(TypeError):
            d['t2'] = 2

    def test_unlock_data_with_str(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        d['t1'], d['t2'] = 3, 4
        d.lock_data()

        d.unlock_data('t1')
        d['t1'] = 5
        self.assertEqual(d['t1'], 5)

        with self.assertRaises(TypeError):
            d['t2'] = 2

    def test_unlock_data_everything(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        d['t1'], d['t2'] = 3, 4
        d.lock_data()

        d.unlock_data()
        d['t1'] = 5
        self.assertEqual(d['t1'], 5)

        d['t2'] = 2
        self.assertEqual(d['t2'], 2)

    def test_unlock_what_never_locked_or_exist(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=False)
        d.unlock_data()
        d.unlock_data("never_set")

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SavingOnEditDifferentFormatTest(unittest.TestCase):
    """Saving different type of variables inside h5"""

    def setUp(self):
        d = SyncData(DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        d['t'] = 3

    def compare_dict(self, d1, d2):
        self.assertSetEqual(
            set(d1.keys()), set(d2.keys()))

        for key in d1.keys():
            self.assertTrue(np.all(d1[key] == d2[key]))

    def create_file(self):
        return SyncData(
            DATA_FILE_PATH, save_on_edit=True, overwrite=False)

    def read_file(self, _):
        return SyncData(DATA_FILE_PATH)

    def test_np_array_save(self):
        data = np.linspace(0, 10, 100).reshape(10, 10)
        d = self.create_file().update(test=data)
        self.assertTrue(np.all(data == d['test']))
        d = self.read_file(d)
        self.assertTrue(np.all(data == d['test']))

    def test_dict_save(self):
        data = {'a': 5,
                'b': np.linspace(0, 10, 100),
                'c': list(range(100)),
                'd': np.linspace(0, 10, 100).reshape(10, 10)}

        d = self.create_file().update(t=data)
        self.compare_dict(d['t'], data)  # type: ignore

        d = self.read_file(d)
        self.compare_dict(d['t'], data)  # type: ignore

    def test_save_random_class(self):
        class Test:
            """Random class that cannot be saved"""

        d = self.create_file()

        with self.assertRaises(TypeError):
            d.update(**{'a': 5, 'b': Test()})
            d.save()

        self.assertEqual(d['t'], 3)
        self.assertEqual(d['a'], 5)

    def test_save_asdict_class(self):
        class Test:
            def asdict(self):
                return {'a': 5, 'b': 4}

        d = self.create_file()
        d['t'] = Test()

        self.assertEqual(d['t']['a'], 5)
        self.assertEqual(d['t']['b'], 4)

        d = self.read_file(d)

        self.assertEqual(d['t', 'a'], 5)
        self.assertEqual(d['t', 'b'], 4)

    def test_save_asarray(self):
        class Test:
            def asarray(self):
                return [1, 2, 3]

        d = self.create_file()
        d['t'] = Test()

        self.assertTrue(np.all(d['t'] == np.array([1, 2, 3])))

        d = self.read_file(d)

        self.assertTrue(np.all(d['t'] == np.array([1, 2, 3])))

    def test_save_tuple(self):
        d = self.create_file()
        d['t'] = (1, 2, 3)  # type: ignore

        self.assertTrue(np.all(d['t'] == np.array([1, 2, 3])))

        d = self.read_file(d)

        self.assertTrue(np.all(d['t'] == np.array([1, 2, 3])))

    def test_init__filepath(self):
        class Test:
            __should_not_be_converted__ = True
            inited = False

            def __init__filepath__(
                    self, *,
                    filepath: str,
                    filekey: str,
                    save_on_edit: bool = False, **_):
                del filepath, filekey, save_on_edit
                self.inited = True

            def asdict(self):
                return {'a': 5}

        d = self.create_file()
        d['t'] = Test()

        self.assertTrue(d['t'].inited)  # type: ignore  # pylint: disable=E1101

    def test_init_filepath_local(self):
        class Test:
            __should_not_be_converted__ = True
            inited = False

            def __init__filepath__(self, *args, **kwds):
                """should not be run"""

            def asdict(self):
                return {}

        d = SyncData()
        with self.assertRaises(ValueError):
            d['t'] = Test()

    @ classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class SavingManualDifferentFormatTest(SavingOnEditDifferentFormatTest):
    """Test to save different formats of data, when save_on_edit is False"""

    def create_file(self):
        return SyncData(
            DATA_FILE_PATH, save_on_edit=False, overwrite=False, read_only=False)

    def read_file(self, d):
        d.save()
        return SyncData(DATA_FILE_PATH)


class PullTest(unittest.TestCase):
    """Testing to open SyncData in write mode in 2 different kernel"""

    def test_pull(self):
        # from labmate.utils.async_utils import sleep
        sd1 = SyncData(
            DATA_FILE_PATH, save_on_edit=True, overwrite=True, read_only=False)
        sd1['b'] = 3
        sd2 = SyncData(
            DATA_FILE_PATH, overwrite=False, read_only=True)

        sd1['a'] = 1
        import time
        time.sleep(1)
        sd2.pull()
        self.assertTrue('a' in sd2)
        self.assertEqual(sd2['a'], 1)

    def test_force_pull(self):
        # from labmate.utils.async_utils import sleep
        sd1 = SyncData(
            DATA_FILE_PATH, save_on_edit=True, overwrite=True, read_only=False)
        sd1['a'] = 1
        sd2 = SyncData(
            DATA_FILE_PATH, overwrite=False, read_only=True)
        sd2._data = {}  # pylint: disable=protected-access

        sd2.pull(force_pull=True)
        self.assertTrue('a' in sd2)
        self.assertEqual(sd2['a'], 1)

    def test_pull_with_local(self):
        # from labmate.utils.async_utils import sleep
        sd1 = SyncData()
        with self.assertRaises(ValueError):
            sd1.pull()

        with self.assertRaises(ValueError):
            sd1.pull(force_pull=True)

        with self.assertRaises(ValueError):
            sd1.pull_available()

    @ classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class OpenOnInitTest(WithoutSavingTest):
    def setUp(self):
        if os.path.exists(DATA_FILE_PATH):
            os.remove(DATA_FILE_PATH)
        self.data_smart = SyncData(
            filepath=DATA_FILE_PATH, overwrite=False, save_on_edit=True, open_on_init=False)

    @ property
    def data_dict(self):
        return SyncData(DATA_FILE_PATH, open_on_init=False)

    def compare_dict(self, d1, d2):
        self.assertSetEqual(
            set(d1.keys()), set(d2.keys()))

        for key in d1.keys():
            self.assertTrue(np.all(d1[key] == d2[key]))

    def apply_func(self, func, *args, **kwds):
        getattr(self.data_smart, func)(*args, **kwds)

    def test_delitem(self):
        pass

    def test_delattr(self):
        pass

    def test_getitem2(self):
        data = self.create_random_data()
        self.data_smart['a'] = data

        sd = SyncData(DATA_FILE_PATH, open_on_init=False)
        self.assertDictEqual(sd._data, {})  # pylint: disable=protected-access
        self.assertSetEqual(sd.keys(), set(['a']))
        self.assertTrue(np.all(sd.get('a') == data))

    def test_setitem2(self):
        data = self.create_random_data()
        self.data_smart['a'] = data

        sd = SyncData(DATA_FILE_PATH, open_on_init=False, save_on_edit=True, overwrite=False)
        self.assertDictEqual(sd._data, {})  # pylint: disable=W0212
        self.assertSetEqual(sd.keys(), set(['a']))

        data = self.create_random_data()
        sd['a'] = data

        sd = SyncData(DATA_FILE_PATH, open_on_init=False)
        self.assertTrue(np.all(sd.get('a') == data))

    @ classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class RandomCasesTest(unittest.TestCase):
    """Testing to open SyncData in write mode in 2 different kernel"""

    def test_lockfile(self):
        # from labmate.utils.async_utils import sleep
        sd1 = SyncData(
            DATA_FILE_PATH, save_on_edit=True, overwrite=True)
        sd1['b'] = 3

        with self.assertRaises(h5py_utils.FileLockedError):
            sd1._retry_on_file_locked_error = 1  # pylint: disable=W0212
            with h5py_utils.LockFile(DATA_FILE_PATH):
                sd1['a'] = 2

        with self.assertRaises(h5py_utils.FileLockedError):
            sd1._raise_file_locked_error = True  # pylint: disable=W0212
            with h5py_utils.LockFile(DATA_FILE_PATH):
                sd1['a'] = 2

    def test_filename_without_extension(self):
        sd1 = SyncData(
            DATA_FILE_PATH[:-3], save_on_edit=True, overwrite=True)
        sd1['b'] = 3

        self.assertTrue(os.path.exists(DATA_FILE_PATH))

    def test_change_filename(self):
        sd1 = SyncData(
            DATA_FILE_PATH[:-3], save_on_edit=True, overwrite=True)
        sd1['b'] = 3

        sd1.filepath = DATA_FILE_PATH[:-3] + '2'
        sd1.save()

        sd1['c'] = 4
        sd2 = SyncData(DATA_FILE_PATH[:-3] + '2')
        self.assertEqual(sd2['b'], 3)
        self.assertEqual(sd2['c'], 4)

    @ classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == '__main__':
    unittest.main()
