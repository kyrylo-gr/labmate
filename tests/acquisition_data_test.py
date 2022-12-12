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

from quanalys.acquisition_utils import AcquisitionData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")


class WithoutSavingTest(unittest.TestCase):
    """Test that AcquisitionData should perform as dictionary"""

    def setUp(self):
        self.adata = AcquisitionData()
        self.data = {}

    def test_adding(self):
        lst = list(range(100))
        self.adata['a1'] = lst[:50]
        self.adata.update(a2=lst[50:])

        self.assertListEqual(lst[:50], self.adata.get('a1'))  # type: ignore
        self.assertListEqual(lst[50:], self.adata['a2'])   # type: ignore
        
        self.assertSetEqual(set(self.adata.keys()), set(('a1', 'a2')))

    def test_deleting(self):
        lst = list(range(100))
        self.adata['a1'] = lst[:50]
        self.adata.update(a2=lst[50:])
        
        self.assertSetEqual(
            self.adata.last_update,
            set(('a1', 'a2'))
        )
        
        self.adata.last_update = set()

        del self.adata['a1']
        self.assertTupleEqual(self.adata.keys(), ('a2',))
        
        self.adata.pop('a2')
        self.assertTupleEqual(self.adata.keys(), tuple())
        
        self.assertSetEqual(
            self.adata.last_update,
            set(('a1', 'a2'))
        )

        self.assertIsNone(self.adata['a1'])
        self.assertIsNone(self.adata['a2'])


if __name__ == '__main__':
    unittest.main()
