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


# Simulation parameters
# In case if Monte Carlo analysis is required, then pass params in args 
# while running scripts as:
# `python3 cost_analyzer.py --years 5 --reps 10 --simulations 20`

class Params(object):
    def __init__(self, reps, simulations):
        self.num_of_reps = reps
        self.num_of_simulations = simulations

    def __str__(self):
        return f"reps: {self.num_of_reps}, simulations: {self.num_of_simulations}"