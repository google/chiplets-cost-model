"""
 Copyright 2022 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

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
