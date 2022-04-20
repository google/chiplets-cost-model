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
from re import S
import numpy as np
import pandas as pd
import seaborn as sns
import time
import multiprocessing as mp

import argparse
from reader import readFile
from preprocessor import cleanse, simulation, validate
from plotter import plot_df, plot_graph
from processor import calculate_cost, calculate_misc_cost, calculate_assy_scrap, calculate_substrate_cost, calculate_total_cost, calculate_total_unit_cost, cost_contribution, calculate_unit_cost_contribution, calculate_gross_margin, calculate_gross_margin_percent, calculate_asp, find_xy_mean, find_x_mean, calculate_nre_cost
from writer import create_row, write_to_file

sns.set_style('whitegrid')
locale.setlocale(locale.LC_ALL, '')

INPUT_FILE_A = 'data_option1.csv'
INPUT_FILE_B = 'data_option2.csv'
TEMPLATE_FILE = 'input_template.csv'


def main(args):
    print('Starting to read ' + INPUT_FILE_A)
    readA = readFile(INPUT_FILE_A)
    print('Completead reading ' + INPUT_FILE_A)
    print('################')

    print('Starting to read ' + INPUT_FILE_B)
    readB = readFile(INPUT_FILE_B)
    print('Completead reading ' + INPUT_FILE_B)

    print('Validating inputs against template...')
    years = args.years
    template = readFile(TEMPLATE_FILE)
    validate(readA, template, years)
    validate(readB, template, years)

    print('Running analysis...')

    start = time.time()

    # plot sensitivity graph if current run requires simulation
    requires_simulation = simulation(readA, years) or simulation(readB, years)

    inputA = cleanse(readA, args)
    inputB = cleanse(readB, args)
    operating_costA = calculate_cost(inputA, 'OpCostYr', years)
    operating_costB = calculate_cost(inputB, 'OpCostYr', years)

    ip_interface_costA = calculate_cost(
            inputA, 'TotalIpInterfaceCostYr', years)
    ip_interface_costB = calculate_cost(
            inputB, 'TotalIpInterfaceCostYr', years)

    misc_costA = calculate_misc_cost(inputA, years)
    # print(misc_costA)
    # [array([[2000000., 2000000., .. to num of simulation.],
    #     to num of REPS
    #    [2000000., 2000000., 2000000., 2000000., 2000000.]]), 
    #  array([[3000000., 3000000., to num of simulation.],
    #     to num of REPS
    #   ]), 
    #  to num of years
    # ]
    misc_costB = calculate_misc_cost(inputB, years)

    quality_costA = calculate_cost(inputA, 'QualityCostYr', years)
    quality_costB = calculate_cost(inputB, 'QualityCostYr', years)

    material_costA = calculate_cost(inputA, 'MatCostYr', years)
    material_costB = calculate_cost(inputB, 'MatCostYr', years)

    nreA = calculate_nre_cost(inputA, years)
    nreB = calculate_nre_cost(inputB, years)

    mask_costA = calculate_cost(inputA, 'MaskCost', years)
    mask_costB = calculate_cost(inputB, 'MaskCost', years)

    assy_scrapA = calculate_assy_scrap(inputA, years)
    assy_scrapB = calculate_assy_scrap(inputB, years)

    subs_costA = calculate_substrate_cost(inputA, years)
    subs_costB = calculate_substrate_cost(inputB, years)

    test_costA = calculate_cost(inputA, 'TestCost', years)
    test_costB = calculate_cost(inputB, 'TestCost', years)
    total_costA = calculate_total_cost(inputA, years, misc_costA, assy_scrapA, material_costA,
                                           quality_costA, operating_costA, ip_interface_costA, 
                                           mask_costA, nreA, subs_costA, test_costA)
    total_costB = calculate_total_cost(inputB, years, misc_costB, assy_scrapB, material_costB,
                                           quality_costB, operating_costB, ip_interface_costB, 
                                           mask_costB, nreB, subs_costB, test_costB)
    # Preparing values for summary output
    operating_costsA = find_xy_mean(operating_costA)
    operating_costsB = find_xy_mean(operating_costB)

    ip_interface_costsA = find_xy_mean(ip_interface_costA)
    ip_interface_costsB = find_xy_mean(ip_interface_costB)

    misc_costsA = find_xy_mean(misc_costA)
    misc_costsB = find_xy_mean(misc_costB)

    quality_costsA = find_xy_mean(quality_costA)
    quality_costsB = find_xy_mean(quality_costB)

    material_costsA = find_xy_mean(material_costA)
    material_costsB = find_xy_mean(material_costB)

    assy_scrapsA = find_xy_mean(assy_scrapA)
    assy_scrapsB = find_xy_mean(assy_scrapB)

    total_costsA = find_xy_mean(total_costA)
    total_costsB = find_xy_mean(total_costB)

    summary = []
    summary.append(create_row('Material($)', material_costsA,
                   material_costsB, years))
    summary.append(create_row(
        'Mask Set($)', mask_costA, mask_costB, years))
    summary.append(create_row('NRE($)', nreA, nreB, years))
    summary.append(create_row(
        'KGD($)', assy_scrapsA, assy_scrapsB, years))
    summary.append(create_row('Quality($)', quality_costsA,
                   quality_costsB, years))
    summary.append(create_row('Operating Cost($)',
                   operating_costsA, operating_costsB, years))
    summary.append(create_row('IP Interface Cost($)',
                   ip_interface_costsA, ip_interface_costsB, years))
    summary.append(create_row('Misc Cost (Assy, Test)($)',
                   misc_costsA, misc_costsB, years))
    summary.append(create_row(
        'Total($)', total_costsA, total_costsB, years))

    # % of Total Cost Contribution
    summary.append(create_row('Material(%)', cost_contribution(
        material_costsA, total_costsA), cost_contribution(material_costsB, total_costsB), years))
    summary.append(create_row('Mask Set(%)', cost_contribution(
        mask_costA, total_costsA), cost_contribution(mask_costB, total_costsB), years))
    summary.append(create_row('NRE(%)', cost_contribution(
        nreA, total_costsA), cost_contribution(nreB, total_costsB), years))
    summary.append(create_row('KGD(%)', cost_contribution(
        assy_scrapsA, total_costsA), cost_contribution(assy_scrapsB, total_costsB), years))
    summary.append(create_row('Quality(%)', cost_contribution(
        quality_costsA, total_costsA), cost_contribution(quality_costsB, total_costsB), years))
    summary.append(create_row('Operating Cost(%)', cost_contribution(
        operating_costsA, total_costsA), cost_contribution(operating_costsB, total_costsB), years))
    summary.append(create_row('IP Interface Cost($)(%)', cost_contribution(
        ip_interface_costsA, total_costsA), cost_contribution(ip_interface_costsB, total_costsB), years))
    summary.append(create_row('Misc Cost (Assy, Test)(%)', cost_contribution(
        misc_costsA, total_costsA), cost_contribution(misc_costsB, total_costsB), years))
    # print(summary)

    total_unit_costsA = calculate_total_unit_cost(inputA, total_costA, years)
    total_unit_costsB = calculate_total_unit_cost(inputB, total_costB, years)

    total_unit_costA = find_xy_mean(total_unit_costsA)
    total_unit_costB = find_xy_mean(total_unit_costsB)

    summary.append(create_row('Material Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        material_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(material_costsB, total_costsB)), years))
    summary.append(create_row('NRE Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        nreA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(nreB, total_costsB)), years))
    summary.append(create_row('KGD Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        assy_scrapsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(assy_scrapsB, total_costsB)), years))
    summary.append(create_row('Quality Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        quality_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(quality_costsB, total_costsB)), years))
    summary.append(create_row('Operating Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        operating_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(operating_costsB, total_costsB)), years))
    summary.append(create_row('IP Interface Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        ip_interface_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(ip_interface_costsB, total_costsB)), years))
    summary.append(create_row('Misc Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(
        misc_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(misc_costsB, total_costsB)), years))

    aspA = calculate_asp(inputA, years)
    aspB = calculate_asp(inputB, years)

    gross_marginsA = calculate_gross_margin(total_unit_costA, aspA)
    gross_marginsB = calculate_gross_margin(total_unit_costB, aspB)
    # print(gross_marginsA)
    # print(gross_marginsB)
    summary.append(create_row('Gross Margin($)',
                   gross_marginsA, gross_marginsB, years))
    summary.append(create_row('Gross Margin(%)', calculate_gross_margin_percent(
        gross_marginsA, aspA), calculate_gross_margin_percent(gross_marginsB, aspB), years))
    
    total_unit_cost_diff = np.array(total_unit_costsB) - np.array(total_unit_costsA)
    # print(find_xy_mean(total_unit_cost_diff))
    summary.append(create_row('Cost Difference', find_xy_mean(total_unit_cost_diff), [
                   ''] * years, years))
    write_to_file(summary, years)
    # plot graph
    plot_graph(years, total_costsA, total_costsB, 'Total Cost')
    plot_graph(years, total_unit_costA,
               total_unit_costB, 'Total Unit Cost')

    if requires_simulation:
        cost_diff_cols = []
        for year in range(1, years + 1):
            cost_diff_cols.append(f'CostDiffYr{year}')
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
    
    print()
    print(f'Time taken: {(time.time() - start)}sec')


if __name__ == "__main__":
    print("cpu ", mp.cpu_count())
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=int, required=True, help='Total number of years of forecast')
    parser.add_argument('--reps', type=int, default=1, help = 'Number of uniformly distributed values')
    parser.add_argument('--simulations', type=int, default=1, help = 'Number of simulations to run')
    args = parser.parse_args()
    print('Total Number of years for forecast: ', args.years)
    main(args)
    print('Completed the analysis')
