import unittest

from labmate.attrdict import AttrDict

DATA = {"int": 123, "float": 123.23, "param_1": "value_1", "param_2": "value_2"}


class AttrDictMainTest(unittest.TestCase):
    """Test utils format function."""

    def setUp(self) -> None:
        self.data = AttrDict(DATA)

    def test_dict_equal(self):
        self.assertDictEqual(self.data, DATA)

    def test_has_attr(self):
        for key in DATA:
            self.assertTrue(hasattr(self.data, key))

    def test_find(self):
        key_value_found = self.data.find("param")
        self.assertIsNotNone(key_value_found)
        assert key_value_found
        self.assertTupleEqual(key_value_found, ("param_1", "value_1"))

    def test_find_list(self):
        key_value_found = self.data.find(["param", "int"])
        self.assertListEqual(key_value_found, [("param_1", "value_1"), ("int", 123)])

    def test_find_all(self):
        key_value_found = self.data.find_all("param")
        self.assertListEqual(
            key_value_found, [("param_1", "value_1"), ("param_2", "value_2")]
        )

    def test_find_all_list(self):
        key_value_found = self.data.find_all(["param", "int"])
        self.assertListEqual(
            key_value_found,
            [[("param_1", "value_1"), ("param_2", "value_2")], [("int", 123)]],
        )

    def test_output_1(self):
        out = self.data.output(["int__m/s__.3f"])
        self.assertEqual("int = 123.000 (m/s)", out)

    def test_output_2(self):
        out = self.data.output(["int__m/s__.3f", "param_1__V"])
        self.assertEqual("int = 123.000 (m/s); param_1 = value_1 (V)", out)

    def test_output_str_end(self):
        out = self.data.output(["int__m/s__.3f", "param_1__V"], max_length=10)
        self.assertEqual("int = 123.000 (m/s)\nparam_1 = value_1 (V)", out)


if __name__ == "__main__":
    unittest.main()
