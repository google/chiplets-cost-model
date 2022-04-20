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

from preprocessor import calculate_bose_einstein_yield, calculate_rec_yield, wafer_sort_test_cost, slt_test_cost, final_test_cost


class TestReader(unittest.TestCase):
    def test_bose_einstein_yield(self):
        row = {'EffA': 378.14, 'N': '2'}

        yield_yr = calculate_bose_einstein_yield(row, 0.1)

        self.assertEqual(52.65, round(yield_yr * 100, 2))

    def test_calculate_rec_yield(self):
        metadata = {'RecBaseline': '32', 'RecSpares': '0', 'RecArea': '10'}
        
        rec_yield = calculate_rec_yield(metadata, 0.1)

        self.assertEqual(0.72498, round(rec_yield, 6))

    def test_wafer_sort_test_cost(self):
        input = [{'WSa($/hr)':'150', 'WSh($/hr)': '50', 'WSci': '2', 'WSdi': '15', 'WSxi': '0.8', 'WSri': '2'}]
        yield_i = 0.7

        cost = wafer_sort_test_cost(input, yield_i)

        self.assertEqual(2.400, round(cost, 3))
    
    def test_final_test_cost(self):
        input = [{'FTa($/hr)':'250', 'FTh($/hr)': '250', 'FTdi': '25', 'FTxi': '0.9', 'WSxi': '0.8', 'FTri': '0', 'FTci': '1'}]
        yield_i = 0.8

        cost = final_test_cost(input, yield_i)

        self.assertEqual(3.472, round(cost, 3))
    
    def test_slt_test_cost(self):
        input = [{'SLTa($/hr)':'30', 'SLTh($/hr)': '80', 'SLTdi': '360', 'FTxi': '0.9'}]
        yield_i = 0.8

        cost = slt_test_cost(input, yield_i)

        self.assertEqual(9.020, round(cost, 3))


if __name__ == '__main__':
    unittest.main()
