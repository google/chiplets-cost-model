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

from cost_analyzer import calculate_assy_scrap


class TestReader(unittest.TestCase):
    def test_assy_scrap_cost(self):
        input = [
            {
                'DeviceType': '',
                'AssemblySteps': '7',
                'AssyPerStepYield1': '0.99',
                'AssyPerStepYield2': '0.99',
                'AssyPerStepYield3': '0.99',
                'AssyPerStepYield4': '0.99',
                'AssyPerStepYield5': '0.98',
                'AssyPerStepYield6': '0.99',
                'AssyPerStepYield7': '0.95',
                'AssyYield1': '',
                'AssyYield2': '',
                'AssyYield3': '',
                'AssyYield4': '',
                'AssyYield5': '',
                'AssyYield6': '',
                'AssyYield7': '',
            },
            {
                'DeviceType': 'Substrate',
                'DimensionX': '68.5',
                'DimensionY': '68.5',
                'MatCostYr1': 10204081.63,
                'MatCostYr2': 14878000.40,
                'MatCostYr3': 22222222.22,
                'MatCostYr4': 78125000.00,
                'MatCostYr5': 74360499.70,
                'AssemblySeq1': '0',
                'AssemblySeq2': '0',
                'AssemblySeq3': '0',
                'AssemblySeq4': '0',
                'AssemblySeq5': '0',
                'AssemblySeq6': '0',
                'AssemblySeq7': '1',
            },
            {
                'DeviceType': 'Active',
                'DimensionX': '68.5',
                'DimensionY': '68.5',
                'MatCostYr1': 157969593.24,					
                'MatCostYr2': 197670554.29,
                'MatCostYr3': 240957514.71,
                'MatCostYr4': 700308744.26,
                'MatCostYr5': 568219101.94,
                'AssemblySeq1': '0',
                'AssemblySeq2': '0',
                'AssemblySeq3': '0',
                'AssemblySeq4': '0',
                'AssemblySeq5': '0',
                'AssemblySeq6': '0',
                'AssemblySeq7': '1',
            }
        ]
        expected_assy_scrap = [16396933.299825005, 20723484.082275007, 25660024.35067501, 75897290.06535003, 62651511.15990003]
        
        assy_scrap = calculate_assy_scrap(input, 5)

        self.assertAlmostEqual(assy_scrap, expected_assy_scrap)


if __name__ == '__main__':
    unittest.main()
