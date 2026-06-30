import unittest

from normalizers.phone import normalize_phone


class PhoneNormalizationTest(unittest.TestCase):
    def test_normalize_phone_to_e164(self):
        self.assertEqual(normalize_phone("+1 (650) 253-0000"), "+16502530000")

    def test_invalid_phone_returns_none(self):
        self.assertIsNone(normalize_phone("123"))


if __name__ == "__main__":
    unittest.main()
