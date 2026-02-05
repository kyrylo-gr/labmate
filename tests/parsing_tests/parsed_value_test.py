import unittest

import matplotlib.pyplot as plt
import numpy as np

from labmate.parsing import ParsedValue


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


class ParsedValuePlotTest(unittest.TestCase):
    """Test ParsedValue plotting."""

    def setUp(self) -> None:
        self.x = np.linspace(0, 10, 100)
        self.y = np.sin(self.x)
        self.pv = ParsedValue("2*2", 4)
        return super().setUp()

    def test_plot(self):
        fig, ax = plt.subplots()
        ax.plot(self.x, self.y)
        ax.axvline(x=self.pv, color="red")
        plt.close(fig)

    # As "wrapper" is not installed or available, manually parameterize the test
    def test_plot_after_operation(self):
        operations = [lambda x: x + 20, lambda x: x * 2, lambda x: x - 10]
        for operation in operations:
            fig, ax = plt.subplots()
            ax.plot(self.x, self.y)
            ax.axvline(x=operation(self.pv), color="red")
            plt.close(fig)

    def test_plot_with_format(self):
        fig, ax = plt.subplots()
        ax.plot(self.x, self.y)
        ax.axvline(x=self.pv.value, color="red")
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
