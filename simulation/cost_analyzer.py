#!/usr/bin/env python3

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

import locale
from operator import contains
from re import S
import numpy as np
import pandas as pd
import seaborn as sns
import time
import multiprocessing as mp

from reader import readFile
from preprocessor import simulation, validate, read_params
from plotter import plot_df, plot_graph, plot_tornado
from processor import calculate_summary, find_x_mean, find_xy_mean, write_summary
from copy import deepcopy

sns.set_style('whitegrid')
locale.setlocale(locale.LC_ALL, '')

INPUT_FILE_A = 'data_option1.csv'
INPUT_FILE_B = 'data_option2.csv'
TEMPLATE_FILE = 'input_template.csv'


def take_read(read, col, years, type):
    def map_val(val):
        if "-" not in val:
            return val
        first, second = val.split("-")
        return first if type == 'High' else second

    def map_row(row):
        for year in range(1, years + 1):
            colName = col.replace("{year}", f'Yr{year}')
            row[colName] = map_val(row[colName])
        return row

    return list(map(lambda row: map_row(row), read))


def create_tornado_input(readA, readB, summaryA, summaryB, years, cols, args):
    tornado_input = []
    for i in range(0, years):
        tornado_input.append([])

    for col in cols:
        inputA_fd_high = take_read(deepcopy(readA), col, years, 'High')
        inputA_fd_low = take_read(deepcopy(readA), col, years, 'Low')
        summaryA_fd_high = calculate_summary(inputA_fd_high, args)
        summaryA_fd_low = calculate_summary(inputA_fd_low, args)
        total_ucd_high = find_xy_mean(np.array(summaryA_fd_high['total_unit_cost_arr']) - np.array(summaryB['total_unit_cost_arr']))
        total_ucd_low = find_xy_mean(np.array(summaryA_fd_low['total_unit_cost_arr']) - np.array(summaryB['total_unit_cost_arr']))
        for year in range(0, years):
            tornado_input[year].append({'name': f'Option1 {col}', 'high': total_ucd_high[year], 'low': total_ucd_low[year]})
        
        inputB_fd_high = take_read(deepcopy(readB), col, years, 'High')
        inputB_fd_low = take_read(deepcopy(readB), col, years, 'Low')
        summaryB_fd_high = calculate_summary(inputB_fd_high, args)
        summaryB_fd_low = calculate_summary(inputB_fd_low, args)
        total_ucd_high = find_xy_mean(np.array(summaryA['total_unit_cost_arr']) - np.array(summaryB_fd_high['total_unit_cost_arr']))
        total_ucd_low = find_xy_mean(np.array(summaryA['total_unit_cost_arr']) - np.array(summaryB_fd_low['total_unit_cost_arr']))
        for year in range(0, years):
            tornado_input[year].append({'name': f'Option2 {col}', 'high': total_ucd_high[year], 'low': total_ucd_low[year]})
    return tornado_input

def main():
    print('Starting to read ' + INPUT_FILE_A)
    readA = readFile(INPUT_FILE_A)
    print('Completead reading ' + INPUT_FILE_A)
    print('################')

    print('Starting to read ' + INPUT_FILE_B)
    readB = readFile(INPUT_FILE_B)
    print('Completead reading ' + INPUT_FILE_B)

    print('Validating inputs against template...')
    years = read_params(readA, readB, {'name': 'NumOfYears', 'displayName': 'years'})

    print('Total Number of years for forecast: ', years)

    steps = read_params(readA, readB, {'name': 'NumOfSteps', 'displayName': 'steps'})
    simulations = read_params(readA, readB, {'name': 'NumOfSimulation', 'displayName': 'simulations'})
    
    template = readFile(TEMPLATE_FILE)
    validate(readA, template, years)
    validate(readB, template, years)

    print('Running analysis...')

    start = time.time()

    # plot sensitivity graph if current run requires simulation
    requires_simulation = simulation(readA, years) or simulation(readB, years)
    args = {'years': years, 'steps': steps, 'simulations': simulations}
 
    summaryA = calculate_summary(deepcopy(readA), args)
    summaryB = calculate_summary(deepcopy(readB), args)
    write_summary(summaryA, summaryB, years)
    # plot graph
    plot_graph(years, summaryA['total_costs'], summaryB['total_costs'], 'Total Cost')
    plot_graph(years, summaryA['total_unit_costs'], summaryB['total_unit_costs'], 'Total Unit Cost')

    if requires_simulation:
        cost_diff_cols = []
        for year in range(1, years + 1):
            cost_diff_cols.append(f'CostDiffYr{year}')
        total_unit_cost_diff = np.array(summaryB['total_unit_cost_arr']) - np.array(summaryA['total_unit_cost_arr'])
        df_data = np.transpose(find_x_mean(total_unit_cost_diff))
        total_unit_cost_diff_df = pd.DataFrame(
            data=df_data, columns=cost_diff_cols)
        print()

        # REPS = 50, SIM = 10_000
        #        CostDiffYr1  CostDiffYr2  CostDiffYr3  CostDiffYr4  CostDiffYr5
        # count     10000.00     10000.00     10000.00     10000.00     10000.00
        # mean        223.94       174.95       121.79        96.49        62.77
        # std          16.45        14.15        11.59         9.65         0.13
        # min         163.75       121.56        79.62        62.17        62.27
        # 5%          196.81       152.05       102.94        80.67        62.55
        # 50%         223.87       174.86       121.59        96.21        62.77
        # 95%         251.00       198.62       141.02       112.43        62.99
        # max         285.02       238.74       166.42       135.85        63.19

        # REPS = 100, SIM = 10_000
        #     CostDiffYr1  CostDiffYr2  CostDiffYr3  CostDiffYr4  CostDiffYr5
        # count     10000.00     10000.00     10000.00     10000.00     10000.00
        # mean        224.04       174.62       121.97        96.59        62.77
        # std          11.78        10.17         8.21         6.89         0.10
        # min         175.97       134.99        88.50        72.59        62.41
        # 5%          204.86       158.13       108.55        85.33        62.61
        # 50%         224.02       174.49       121.88        96.44        62.77
        # 95%         243.83       191.60       135.49       108.09        62.92
        # max         277.98       214.83       153.97       124.18        63.15

        # REPS = 100, SIM = 15_000
        #        CostDiffYr1  CostDiffYr2  CostDiffYr3  CostDiffYr4  CostDiffYr5
        # count     15000.00     15000.00     15000.00     15000.00     15000.00
        # mean        223.98       174.92       121.97        96.57        62.77
        # std          11.76        10.03         8.16         6.88         0.09
        # min         173.59       130.75        90.93        68.77        62.42
        # 5%          205.05       158.54       108.64        85.26        62.61
        # 50%         223.84       174.86       121.96        96.53        62.77
        # 95%         243.53       191.62       135.36       107.88        62.92
        # max         272.70       216.22       154.24       124.21        63.17

        # REPS = 100, SIM = 20_000
        #        CostDiffYr1  CostDiffYr2  CostDiffYr3  CostDiffYr4  CostDiffYr5
        # count     20000.00     20000.00     20000.00     20000.00     20000.00
        # mean        224.01       174.71       121.93        96.47        62.76
        # std          11.85        10.07         8.15         6.82         0.10
        # min         177.41       131.97        90.36        69.49        62.41
        # 5%          204.79       158.12       108.71        85.38        62.61
        # 50%         223.85       174.76       121.83        96.39        62.76
        # 95%         243.84       191.19       135.56       107.87        62.92
        # max         276.14       217.07       154.26       121.66        63.19

        total_unit_cost_diff_df.describe(percentiles=[0.05, 0.5, 0.95]).round(2).to_csv("outputs/stochastic_analysis.csv")
        # print(total_unit_cost_diff_df.describe(percentiles=[0.05, 0.5, 0.95]).round(2))
        plot_df(total_unit_cost_diff_df)

        # plot tornado chart
        # evaluate value for low for all years for a variable
        # [[{name: FD, low: 10, high: 40}, {name: Yield, low: 10, high: 40}], [{name: FD, low: 10, high: 40}], [{}]
        # FD as variable
        args['steps'] = 1
        args['simulations'] = 1
        tornado_input = create_tornado_input(deepcopy(readA), deepcopy(readB), summaryA, summaryB, years, ['ForecastDemand{year}', 'Asp{year}($)', 'WaferYield{year}', 'WaferPrice{year}($)', 'DefectDensity{year}(Defects/cm^2)'], args)
        plot_tornado(tornado_input)

    print()
    print(f'Time taken: {(time.time() - start)}sec')


if __name__ == "__main__":
    print("cpu ", mp.cpu_count())
    main()
    print('Completed the analysis')
