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
import numpy as numpy
import argparse
from matplotlib import pyplot as plt

from reader import DEVICE_TYPE_SUBSTRATE, meta_data_row, readFile
from writer import write_to_file

locale.setlocale(locale.LC_ALL, '')

INPUT_FILE_A = 'chiplet_cost1.csv'
INPUT_FILE_B = 'chiplet_cost2.csv'

def filter_metadata_row(input):
    return filter(lambda row: meta_data_row(row) == False, input)

def calculate_assy_scrap(input, numberOfYears = 5):
    mat_costs = []
    for year in range(1, numberOfYears + 1):
        mat_cost_col = f'MatCostYr{year}'
        mat_cost_yr = list(map(lambda row: row[mat_cost_col], filter_metadata_row(input)))
        mat_costs.append(mat_cost_yr)

    assy = []
    assy_yield = []
    numOfAssemblySteps = int(input[0]['AssemblySteps'])
    for i in range(1, numOfAssemblySteps + 1):
        assy_col = f'AssemblySeq{i}'
        # only the assembly sequence with dimension should be considered
        assy_i = list(map(lambda row: int(row[assy_col]) if float(row['DimensionX']) > 0 and float(row['DimensionY']) > 0 else 0, filter_metadata_row(input)))
        assy.append(assy_i)

        # assy and assy_per_step_yield should have same column numbers
        # if assy_yield is provided, then do not calculate it
        input_assy_yield = input[0][f'AssyYield{i}']
        assy_yield_i = float(input_assy_yield) if input_assy_yield else float(input[0][f'AssyPerStepYield{i}']) ** sum(assy_i)
        assy_yield.append(assy_yield_i)

    assy_scraps = []

    for i in range(0, numberOfYears):
        mat_cost = mat_costs[i]
        assy_len = len(assy)
        assy_scrap = 0

        for j in range(0, assy_len):
            assy_j = assy[j]
            assy_yield_j = assy_yield[j]
            assy_scrap += numpy.dot(mat_cost, assy_j) * (1 - assy_yield_j)

        assy_scraps.append(assy_scrap)

    return assy_scraps


def calculate_nre(input, numOfYrs):
    nre = [0] * numOfYrs
    nre[0] = sum(list(map(lambda input: float(input['NRE($)'] or '0'), input)))
    return nre


def calculate_total_mask_set_cost(input, numOfYears):
    mask_costs = [0] * numOfYears
    mask_costs[0] = sum(list(map(lambda input: float(input['MaskSetCost'] or '0'), input)))
    return mask_costs


def calculate_cost(input, colName, numberOfYears = 5):
    costs = []
    for year in range(1, numberOfYears + 1):
        cost_col = colName + str(year)
        total_cost = sum(list(map(lambda row: 0 if meta_data_row(row) else row[cost_col], input)))
        costs.append(total_cost)

    return costs


def calculate_misc_cost(input, numberOfYears = 5):
    misc_costs = []
    substrate_row = list(filter(lambda row: row['DeviceType'] == DEVICE_TYPE_SUBSTRATE, input))[0]
    for year in range (1, numberOfYears + 1):
        package_assy_cost = float(input[0][f'PackageAssemblyCostYr{year}($)'] or '0')
        forecast_demand = int(substrate_row[f'ForecastDemandYr{year}'])
        misc_cost = package_assy_cost * forecast_demand
        misc_costs.append(misc_cost)

    return misc_costs


def calculate_total_cost(input, misc_costs, assy_scraps, total_mat_costs, total_quality_costs, total_op_costs, total_ip_costs, test_costs):
    years = len(total_mat_costs)
    total_nre = calculate_nre(input, years)
    total_mask_cost = calculate_total_mask_set_cost(input, years)
    total_costs = []

    substrate_row = list(filter(lambda row: row['DeviceType'] == DEVICE_TYPE_SUBSTRATE, input))[0]
    # make sure all inputs are of same length
    for i in range(0, years):
        # calculate substrate cost
        yield_adjusted_fup = substrate_row[f'ForecastUnitPriceYr{i + 1}($)']
        subs_demand = int(substrate_row[f'ForecastDemandYr{i + 1}'])
        subs_cost = yield_adjusted_fup * subs_demand

        fpty = float(input[0][f'FinalPackageTestYieldYr{i + 1}'])
        slt = float(input[0][f'SLTYieldYr{i + 1}'])
   
        total_cost = misc_costs[i] + test_costs[i] + total_mask_cost[i] + total_nre[i] + assy_scraps[i] + (1 + (1 - fpty) + (1 - slt) * fpty) * (total_mat_costs[i] + subs_cost) + total_op_costs[i] + total_ip_costs[i] + total_quality_costs[i]
        total_costs.append(total_cost)

    return total_costs


def create_row(category, option1, option2, numOfYr):
    row = {'CostCategory': category}

    for year in range(1, numOfYr + 1):
        col_name = f'ChipletYr{year}'
        row[col_name] = option1[year - 1]

    for year in range(1, numOfYr + 1):
        col_name = f'2SocChipsYr{year}'
        row[col_name] = option2[year - 1]

    return row


def cost_contribution(costs, total):
    contribution = []
    for i in range(0, len(costs)):
        contribution.append(costs[i] / total[i])

    return contribution


def calculate_total_unit_cost(input, total_cost, numOfYrs):
    total_unit_costs = []

    for year in range(1, numOfYrs + 1):
        total_unit_costs.append(total_cost[year - 1]/ int(input[1][f'ForecastDemandYr{year}']))

    return total_unit_costs


def calculate_unit_cost_contribution(total_unit_cost, cost_contribution):
    unit_cost_contribution = []
    for i in range(0, len(total_unit_cost)):
        unit_cost_contribution.append(total_unit_cost[i] * cost_contribution[i])

    return unit_cost_contribution


def calculate_gross_margin(total_unit_costs, asps):
    gross_margins = []
    for i in range(0, len(total_unit_costs)):
        gross_margins.append(asps[i] - total_unit_costs[i])

    return gross_margins


def calculate_gross_margin_percent(gross_margins, asps):
    gross_margin_percent = []
    for i in range(0, len(gross_margins)):
        gross_margin_percent.append(gross_margins[i] / asps[i])

    return gross_margin_percent


def calculate_cost_difference(unit_costsB, unit_costsA):
    if len(unit_costsA) != len(unit_costsB):
        raise Exception('Length for unit costs should be the same')

    diff = []
    for i in range(0, len(unit_costsA)):
        diff.append(unit_costsB[i] - unit_costsA[i])

    return diff


def calculate_asp(input, numOfYears):
    asps = []
    for year in range(1, numOfYears + 1):
        aspCol = f'AspYr{year}($)'
        asps.append(float(input[0][aspCol]))

    return asps


def plot_graph(numOfYears, costsA, costsB, title):
    x = numpy.arange(1, numOfYears + 1)
    plt.title(title)
    plt.xlabel('Year')
    plt.ylabel('Cost($)')
    plt.plot(x, costsA, color = 'r', label = 'Option 1 (Chiplet)')
    plt.plot(x, costsB, color = 'g', label = 'Option 2 (2 SOC Chips)')
    plt.legend()
    plt.savefig('outputs/' + title.lower().replace(" ", "_") + '.png')
    plt.clf()


def main(numOfYears):
    print('Starting to read ' + INPUT_FILE_A)
    inputA = readFile(INPUT_FILE_A, numOfYears)
    print('Completead reading ' + INPUT_FILE_A)
    print('################')

    print('Starting to read ' + INPUT_FILE_B)
    inputB = readFile(INPUT_FILE_B, numOfYears)
    print('Completead reading ' + INPUT_FILE_B)

    print('Starting analysis...')
    operating_costsA = calculate_cost(inputA, 'OpCostYr', numOfYears)
    operating_costsB = calculate_cost(inputB, 'OpCostYr', numOfYears)

    ip_interface_costsA = calculate_cost(inputA, 'TotalIpInterfaceCostYr', numOfYears)
    ip_interface_costsB = calculate_cost(inputB, 'TotalIpInterfaceCostYr', numOfYears)

    misc_costsA = calculate_misc_cost(inputA, numOfYears)
    misc_costsB = calculate_misc_cost(inputB, numOfYears)

    quality_costsA = calculate_cost(inputA, 'QualityCostYr', numOfYears)
    quality_costsB = calculate_cost(inputB, 'QualityCostYr', numOfYears)

    material_costsA = calculate_cost(inputA, 'MatCostYr', numOfYears)
    material_costsB = calculate_cost(inputB, 'MatCostYr', numOfYears)

    test_costA = calculate_cost(inputA, 'TestCostYr', numOfYears)
    test_costB = calculate_cost(inputB, 'TestCostYr', numOfYears)
    assy_scrapsA = calculate_assy_scrap(inputA, numOfYears)
    total_costsA = calculate_total_cost(inputA, misc_costsA, assy_scrapsA, material_costsA, quality_costsA, operating_costsA, ip_interface_costsA, test_costA)
    print(total_costsA)
    assy_scrapsB = calculate_assy_scrap(inputB, numOfYears)
    total_costsB = calculate_total_cost(inputB, misc_costsB, assy_scrapsB, material_costsB, quality_costsB, operating_costsB, ip_interface_costsB, test_costB)
    print(total_costsB)
    nreA = calculate_nre(inputA, numOfYears)
    nreB = calculate_nre(inputB, numOfYears)

    mask_costA = calculate_total_mask_set_cost(inputA, numOfYears)
    mask_costB = calculate_total_mask_set_cost(inputB, numOfYears)

    summary = []
    summary.append(create_row('Material($)', material_costsA, material_costsB, numOfYears))
    summary.append(create_row('Mask Set($)', mask_costA, mask_costB, numOfYears))
    summary.append(create_row('NRE($)', nreA, nreB, numOfYears))
    summary.append(create_row('KGD($)', assy_scrapsA, assy_scrapsB, numOfYears))
    summary.append(create_row('Quality($)', quality_costsA, quality_costsB, numOfYears))
    summary.append(create_row('Operating Cost($)', operating_costsA, operating_costsB, numOfYears))
    summary.append(create_row('IP Interface Cost($)', ip_interface_costsA, ip_interface_costsB, numOfYears))
    summary.append(create_row('Misc Cost (Assy, Test)($)', misc_costsA, misc_costsB, numOfYears))
    summary.append(create_row('Total($)', total_costsA, total_costsB, numOfYears))

    # % of Total Cost Contribution
    summary.append(create_row('Material(%)', cost_contribution(material_costsA, total_costsA), cost_contribution(material_costsB, total_costsB), numOfYears))
    summary.append(create_row('Mask Set(%)', cost_contribution(mask_costA, total_costsA), cost_contribution(mask_costB, total_costsB), numOfYears))
    summary.append(create_row('NRE(%)', cost_contribution(nreA, total_costsA), cost_contribution(nreB, total_costsB), numOfYears))
    summary.append(create_row('KGD(%)', cost_contribution(assy_scrapsA, total_costsA), cost_contribution(assy_scrapsB, total_costsB), numOfYears))
    summary.append(create_row('Quality(%)', cost_contribution(quality_costsA, total_costsA), cost_contribution(quality_costsB, total_costsB), numOfYears))
    summary.append(create_row('Operating Cost(%)', cost_contribution(operating_costsA, total_costsA), cost_contribution(operating_costsB, total_costsB), numOfYears))
    summary.append(create_row('IP Interface Cost($)(%)', cost_contribution(ip_interface_costsA, total_costsA), cost_contribution(ip_interface_costsB, total_costsB), numOfYears))
    summary.append(create_row('Misc Cost (Assy, Test)(%)', cost_contribution(misc_costsA, total_costsA), cost_contribution(misc_costsB, total_costsB), numOfYears))

    total_unit_costA = calculate_total_unit_cost(inputA, total_costsA, numOfYears)
    total_unit_costB = calculate_total_unit_cost(inputB, total_costsB, numOfYears)
    summary.append(create_row('Total Unit Cost($)', total_unit_costA, total_unit_costB, numOfYears))

    summary.append(create_row('Material Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(material_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(material_costsB, total_costsB)), numOfYears))
    summary.append(create_row('NRE Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(nreA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(nreB, total_costsB)), numOfYears))
    summary.append(create_row('KGD Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(assy_scrapsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(assy_scrapsB, total_costsB)), numOfYears))
    summary.append(create_row('Quality Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(quality_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(quality_costsB, total_costsB)), numOfYears))
    summary.append(create_row('Operating Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(operating_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(operating_costsB, total_costsB)), numOfYears))
    summary.append(create_row('IP Interface Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(ip_interface_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(ip_interface_costsB, total_costsB)), numOfYears))
    summary.append(create_row('Misc Total Unit Cost($)', calculate_unit_cost_contribution(total_unit_costA, cost_contribution(misc_costsA, total_costsA)), calculate_unit_cost_contribution(total_unit_costB, cost_contribution(misc_costsB, total_costsB)), numOfYears))

    aspA = calculate_asp(inputA, numOfYears)
    aspB = calculate_asp(inputB, numOfYears)
    gross_marginsA = calculate_gross_margin(total_unit_costA, aspA)
    gross_marginsB = calculate_gross_margin(total_unit_costB, aspB)

    summary.append(create_row('Gross Margin($)', gross_marginsA, gross_marginsB, numOfYears))
    summary.append(create_row('Gross Margin(%)', calculate_gross_margin_percent(gross_marginsA, aspA), calculate_gross_margin_percent(gross_marginsB, aspB), numOfYears))
    summary.append(create_row('Cost Difference', calculate_cost_difference(total_unit_costB, total_unit_costA), [''] * numOfYears, numOfYears))
    write_to_file(summary, numOfYears)

    # plot graph
    plot_graph(numOfYears, total_costsA, total_costsB, 'Total Cost')
    plot_graph(numOfYears, total_unit_costA, total_unit_costB, 'Total Unit Cost')
    print('Completed analysis')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('T', type = int, help = 'Total number of years of forecast')
    args = parser.parse_args()
    print('Total Number of years for forecast: ', args.T)
    main(args.T)
    print('Completed the analysis')
