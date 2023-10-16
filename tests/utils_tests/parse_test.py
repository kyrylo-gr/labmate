import unittest

from labmate.utils.parse import parse_get_format, ValueForPrint, format_title, ParsedValue


class UnitsFormatTest(unittest.TestCase):
    """Test utils format function."""

    def test_parse_get_format_3args(self):
        self.assertTupleEqual(parse_get_format("speed__km/s__2f"), ("speed", "km/s", "2f"))

    def test_parse_get_format_2args(self):
        self.assertTupleEqual(parse_get_format("speed__km/s"), ("speed", "km/s", None))

        self.assertTupleEqual(parse_get_format("speed__2e"), ("speed", None, "2e"))

    def test_parse_get_format_1arg(self):
        self.assertTupleEqual(parse_get_format("speed"), ("speed", None, None))

    def test_parse_get_format_errors(self):
        self.assertTupleEqual(parse_get_format("speed__km/s__2f__abc"), ("speed", "km/s", "2f"))

    def test_format_title_working(self):
        values = [
            ValueForPrint("speed", 123.12345, "m/s", "2f"),
            ValueForPrint("distance", 234.4321, "meters", None),
            ValueForPrint("time", 5432, None, "1e"),
        ]
        txt = format_title(values, max_length=40)
        self.assertIn("speed = ", txt)
        self.assertIn("123.12", txt)
        self.assertIn("(m/s)", txt)

        self.assertIn("distance = ", txt)
        self.assertIn("234.4321", txt)
        self.assertNotIn("()", txt)

        self.assertIn("time = ", txt)
        self.assertIn("5.4e+03", txt)

        self.assertLessEqual(max(len(t) for t in txt.split("\n")), 40)


class ParsedValueOperationTest(unittest.TestCase):
    """Test ParsedValue operations."""

    v1 = 2
    v2 = 3

    def setUp(self) -> None:
        self.pv1 = ParsedValue("abc", self.v1)
        self.pv2 = ParsedValue("abc2", self.v2)
        return super().setUp()

    def answer(self, method):
        try:
            res = getattr(self.v1, method)(self.v2)
            if res == NotImplemented:
                raise TypeError
        except TypeError:
            return getattr(self.v2, method)(self.v1)

    def test_add(self):
        self.assertEqual(self.pv1 + self.pv2, self.v1 + self.v2)

    def test_radd(self):
        self.assertEqual(self.pv2 + self.pv1, self.v2 + self.v1)

    def test_sub(self):
        self.assertEqual(self.pv1 - self.pv2, self.v1 - self.v2)

    def test_rsub(self):
        self.assertEqual(self.pv2 - self.pv1, self.v2 - self.v1)

    def test_mul(self):
        self.assertEqual(self.pv1 * self.pv2, self.v1 * self.v2)

    def test_rmul(self):
        self.assertEqual(self.pv2 * self.pv1, self.v2 * self.v1)

    def test_truediv(self):
        self.assertEqual(self.pv1 / self.pv2, self.v1 / self.v2)

    def test_pow(self):
        self.assertEqual(self.pv1**self.pv2, self.v1**self.v2)

    def test_eq(self):
        self.assertEqual(self.pv1 == self.pv2, self.v1 == self.v2)

    def test_ne(self):
        self.assertEqual(self.pv1 != self.pv2, self.v1 != self.v2)

    def test_abs(self):
        self.assertEqual(abs(self.pv1), abs(self.v1))
        self.assertEqual(abs(self.pv2), abs(self.v2))

    def test_format(self):
        self.assertEqual(f"{self.pv1:.0f}", f"{self.v1:.0f}")
        self.assertEqual(f"{self.pv1:.2f}", f"{self.v1:.2f}")
        self.assertEqual(f"{self.pv1:.3e}", f"{self.v1:.3e}")

    def test_floatdiv(self):
        self.assertEqual(self.pv1 // self.pv2, self.v1 // self.v2)

    def test_mod(self):
        self.assertEqual(self.pv1 % self.pv2, self.v1 % self.v2)

    def test_lt(self):
        self.assertEqual(self.pv1 < self.pv2, self.v1 < self.v2)

    def test_gt(self):
        self.assertEqual(self.pv1 > self.pv2, self.v1 > self.v2)

    def test_le(self):
        self.assertEqual(self.pv1 <= self.pv2, self.v1 <= self.v2)

    def test_ge(self):
        self.assertEqual(self.pv1 >= self.pv2, self.v1 >= self.v2)

    def unpack(self):
        original, value = self.pv1
        self.assertEqual(original, "abc")
        self.assertEqual(value, self.v1)


class ComplexTests:
    def test_floatdiv(self):
        return

    def test_mod(self):
        return

    def test_lt(self):
        return

    def test_gt(self):
        return

    def test_le(self):
        return

    def test_ge(self):
        return


class ParsedValueLeftOperationTest(ParsedValueOperationTest):
    """Test ParsedValue operations."""

    def setUp(self) -> None:
        self.pv1 = ParsedValue("abc", self.v1)
        self.pv2 = self.v2
        return super().setUp()


class ParsedValueLeftComplexOperationTest(ComplexTests, ParsedValueLeftOperationTest):
    """Test ParsedValue operations."""

    v1 = 2
    v2 = 3 + 1j * 6


class ParsedValueRightOperationTest(ParsedValueOperationTest):
    """Test ParsedValue operations."""

    def setUp(self) -> None:
        self.pv1 = self.v1
        self.pv2 = ParsedValue("abc", self.v2)
        return super().setUp()


class ParsedValueRightComplexOperationTest(ComplexTests, ParsedValueRightOperationTest):
    """Test ParsedValue operations."""

    v1 = 2
    v2 = 3 + 1j * 6


if __name__ == "__main__":
    unittest.main()
