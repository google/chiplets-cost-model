import unittest

from reader import calculate_bose_einstein_yield, calculate_rec_yield


class TestReader(unittest.TestCase):
    def test_bose_einstein_yield(self):
        row = {'EffA': 378.14, 'N': '2'}

        yield_yr = calculate_bose_einstein_yield(row, 0.1)

        self.assertEqual(52.65, round(yield_yr * 100, 2))

    def test_calculate_rec_yield(self):
        input = [{'RecBaseline': '3', 'RecSpares': '2', 'RecArea': '1'}]
        rec_yield = calculate_rec_yield(input, 0.1)

        self.assertEqual(0.015, round(rec_yield, 3))


if __name__ == '__main__':
    unittest.main()
