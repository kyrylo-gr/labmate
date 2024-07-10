import unittest

from labmate.utils.title_parsing import ValueForPrint, format_title, parse_get_format


class UnitsFormatTest(unittest.TestCase):
    """Test utils format function."""

    def test_parse_get_format_3args(self):
        self.assertTupleEqual(
            parse_get_format("speed__km/s__2f"), ("speed", "km/s", "2f")
        )

    def test_parse_get_format_2args(self):
        self.assertTupleEqual(parse_get_format("speed__km/s"), ("speed", "km/s", None))

        self.assertTupleEqual(parse_get_format("speed__2e"), ("speed", None, "2e"))

    def test_parse_get_format_1arg(self):
        self.assertTupleEqual(parse_get_format("speed"), ("speed", None, None))

    def test_parse_get_format_errors(self):
        self.assertTupleEqual(
            parse_get_format("speed__km/s__2f__abc"), ("speed", "km/s", "2f")
        )

    def test_format_title_working(self):
        values = [
            ValueForPrint("speed", 123.12345, "m/s", ".2f"),
            ValueForPrint("distance", 234.4321, "meters", None),
            ValueForPrint("time", 5432, None, ".1e"),
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


if __name__ == "__main__":
    unittest.main()
