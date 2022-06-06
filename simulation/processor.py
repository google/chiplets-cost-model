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

import numpy as np
from preprocessor import cleanse
from preprocessor import DEVICE_TYPE_SUBSTRATE, meta_data_row
from writer import create_row, write_to_file

def calculate_summary(read, args):
    years = args.years
    input = cleanse(read, args)

    operating_cost = calculate_cost(input, 'OpCostYr', years)
    ip_interface_cost = calculate_cost(input, 'TotalIpInterfaceCostYr', years)
    misc_cost = calculate_misc_cost(input, years)
    # print(misc_costA)
    # [array([[2000000., 2000000., .. to num of simulation.],
    #     to num of REPS
    #    [2000000., 2000000., 2000000., 2000000., 2000000.]]), 
    #  array([[3000000., 3000000., to num of simulation.],
    #     to num of REPS
    #   ]), 
    #  to num of years
    # ]

    quality_cost = calculate_cost(input, 'QualityCostYr', years)
    material_cost = calculate_cost(input, 'MatCostYr', years)
    nre = calculate_nre_cost(input, years)
    asp = calculate_asp(input, years)
    mask_cost = calculate_cost(input, 'MaskCost', years)
    assy_scrap = calculate_assy_scrap(input, years)
    subs_cost = calculate_substrate_cost(input, years)
    test_cost = calculate_cost(input, 'TestCost', years)
    total_cost = calculate_total_cost(input, years, misc_cost, assy_scrap, material_cost,
                                           quality_cost, operating_cost, ip_interface_cost, 
                                           mask_cost, nre, subs_cost, test_cost)

    total_unit_cost_arr = calculate_total_unit_cost(input, total_cost, years)
    # Preparing values for summary output
    return {
        'operating_costs': find_xy_mean(operating_cost),
        'ip_interface_costs': find_xy_mean(ip_interface_cost),
        'misc_costs': find_xy_mean(misc_cost),
        'quality_costs': find_xy_mean(quality_cost),
        'material_costs': find_xy_mean(material_cost),
        'assy_scraps': find_xy_mean(assy_scrap),
        'total_costs': find_xy_mean(total_cost),
        'total_unit_cost_arr': total_unit_cost_arr,
        'total_unit_costs': find_xy_mean(total_unit_cost_arr), 
        'mask_costs': mask_cost,
        'nre': nre,
        'asp': asp
    }


def filter_metadata_row(input):
    return filter(lambda row: meta_data_row(row) == False, input)

def calculate_assy_scrap(input, years=5):

    assy = []
    assy_yield = []
    numOfAssemblySteps = int(input[0]['AssemblySteps'])
    #  we create 2D matrix of assemby seq of (i x assembly_steps)
    # [[ 1. 1 . . . to i]
    #  [ 1. 1 . . . to i]
    #  [ 1. 1 . . . to i]
    #   . . . to num of assembly steps
    #  [ 1. 1 . . . to i]]
    for i in range(1, numOfAssemblySteps + 1):
        assy_col = f'AssemblySeq{i}'
        # only the assembly sequence with dimension should be considered
        assy_i = list(map(lambda row: int(row[assy_col]) if float(row['DimensionX']) > 0 and float(
            row['DimensionY']) > 0 else 0, filter_metadata_row(input)))
        assy.append(assy_i)

        # assy and assy_per_step_yield should have same column numbers
        # if assy_yield is provided, then do not calculate it
        input_assy_yield = input[0][f'AssyYield{i}']
        assy_yield_i = float(input_assy_yield) if input_assy_yield else float(
            input[0][f'AssyPerStepYield{i}']) ** sum(assy_i)
        assy_yield.append(assy_yield_i)

    assy_scraps = []

    for year in range(1, years + 1):
        #  we create 3D matrix of material cost for each die (i x NUM_OF_REPS x NUM_OF_SIMULATIONS)
        # [[[ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.], [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.]
        #   [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.], [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.]
        #    ..... to NUM of REPS],
        #  [[ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.], [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.]
        #   [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.], [ 3493250. 4863525. . . to NUM_OF_SIMULATIONS 22089000.]
        #    ..... to NUM of REPS]
        #  ... to i ]
        
        mat_cost_col = f'MatCostYr{year}'
        mat_cost = list(map(lambda row: row[mat_cost_col], filter_metadata_row(input)))
        assy_scrap_t = []
        # for each assembly sequence, find sum product and add to find scrap cost for given time t
        for j in range(0, len(assy)):
            assy_j = assy[j]
                # [ 1. 1 . . . to NUM_OF_REPS 0.], [ 1. 1 . . . to NUM_OF_REPS 0.] ... to i
            assy_yield_j = assy_yield[j]
            assy_scrap_j = sum(list(mat_cost[k] * assy_seq for (k, assy_seq) in enumerate(assy_j))) * (1 - assy_yield_j)
            assy_scrap_t.append(assy_scrap_j)

        assy_scraps.append(sum(assy_scrap_t))

    return assy_scraps


def calculate_cost(input, colName, years=5):
    costs = []
    for year in range(1, years + 1):
        cost_t = sum(list(map(lambda row: row[colName + str(year)], filter_metadata_row(input))))
        costs.append(cost_t)

    return costs


def get_substrate_row(input):
    return list(filter(lambda row: row['DeviceType'] == DEVICE_TYPE_SUBSTRATE, input))[0]


def calculate_substrate_cost(input, numOfYears):
    substrate_costs = []
    substrate_row = get_substrate_row(input)
    for year in range(1, numOfYears + 1):
        yield_adjusted_fup = substrate_row[f'ForecastUnitPriceYr{year}($)']
        subs_demand = substrate_row[f'ForecastDemandYr{year}']
        substrate_costs.append(yield_adjusted_fup * subs_demand)

    return substrate_costs

def calculate_misc_cost(input, years=5):
    misc_costs = []
    substrate_row = get_substrate_row(input)
    for year in range(1, years + 1):
        package_assy_cost = float(
            input[0][f'PackageAssemblyCostYr{year}($)'] or '0')
        forecast_demand = substrate_row[f'ForecastDemandYr{year}']
        misc_costs.append(forecast_demand * package_assy_cost)

    return misc_costs


def calculate_total_cost(input, years, misc_costs, assy_scraps, total_mat_costs, total_quality_costs, total_op_costs, total_ip_interface_costs, mask_costs, nre, subs_costs, test_costs):
    # make sure all inputs are of same length
    total_costs = []
    
    for i in range(0, years):
        fpty = float(input[0][f'FinalPackageTestYieldYr{i + 1}'])
        slt = float(input[0][f'SLTYieldYr{i + 1}'])
        total_cost = misc_costs[i] + test_costs[i] + mask_costs[i] + assy_scraps[i] + (
                total_mat_costs[i] + subs_costs[i]) * (1 + (1 - fpty) + (1 - slt) * fpty) + total_op_costs[i] + total_quality_costs[i] + total_ip_interface_costs[i] + nre[i]
        total_costs.append(total_cost)

    return total_costs


def cost_contribution(costs, total):
    contribution = []
    for i in range(0, len(costs)):
        contribution.append(costs[i] / total[i])

    return contribution


def calculate_total_unit_cost(input, total_costs, numOfYrs):
    total_unit_costs = []

    for year in range(1, numOfYrs + 1):
        total_cost_t = total_costs[year - 1]
        demands = input[1][f'ForecastDemandYr{year}']
        total_unit_costs.append(total_cost_t / demands)

    return total_unit_costs


def calculate_unit_cost_contribution(total_unit_cost, cost_contribution):
    unit_cost_contribution = []
    for i in range(0, len(total_unit_cost)):
        unit_cost_contribution.append(
            total_unit_cost[i] * cost_contribution[i])

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


def calculate_asp(input, numOfYears):
    asps = []
    for year in range(1, numOfYears + 1):
        asp = input[0][f'AspYr{year}($)']
        asps.append(asp.mean())

    return asps

def calculate_nre_cost(input, numOfYears):
    nre = [0] * numOfYears
    nre[0] = sum(list(map(lambda row: float(row['NRE($)'] or '0'), input)))
    return nre

def find_xy_mean(lst):
    return np.average(find_x_mean(lst), axis = 1)

def find_y_mean(lst):
    return list(map(lambda arr: arr.mean(axis = 1), lst))

def find_x_mean(lst):
    return list(map(lambda arr: arr.mean(axis = 0), lst))


def write_summary(summaryA, summaryB, years):

    material_costsA = summaryA['material_costs']
    material_costsB = summaryB['material_costs']

    mask_costsA = summaryA['mask_costs']
    mask_costsB = summaryB['mask_costs']

    nreA = summaryA['nre']
    nreB = summaryB['nre']

    assy_scrapsA = summaryA['assy_scraps']
    assy_scrapsB = summaryB['assy_scraps']

    quality_costsA = summaryA['quality_costs']
    quality_costsB = summaryB['quality_costs']

    operating_costsA = summaryA['operating_costs']
    operating_costsB = summaryB['operating_costs']

    ip_interface_costsA = summaryA['ip_interface_costs']
    ip_interface_costsB = summaryB['ip_interface_costs']

    misc_costsA = summaryA['misc_costs']
    misc_costsB = summaryB['misc_costs']

    total_costsA = summaryA['total_costs']
    total_costsB = summaryB['total_costs']

    summary = []
    summary.append(create_row('Material($)', material_costsA, material_costsB, years))
    summary.append(create_row('Mask Set($)', mask_costsA, mask_costsB, years))
    summary.append(create_row('NRE($)', nreA, nreB, years))
    summary.append(create_row('KGD($)', assy_scrapsA, assy_scrapsB, years))
    summary.append(create_row('Quality($)', quality_costsA, quality_costsB, years))
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
        mask_costsA, total_costsA), cost_contribution(mask_costsB, total_costsB), years))
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

    total_unit_costA = summaryA['total_unit_costs']
    total_unit_costB = summaryB['total_unit_costs']

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

    aspA = summaryA['asp']
    aspB = summaryA['asp']
    gross_marginsA = calculate_gross_margin(total_unit_costA, aspA)
    gross_marginsB = calculate_gross_margin(total_unit_costB, aspB)
    # print(gross_marginsA)
    # print(gross_marginsB)
    summary.append(create_row('Gross Margin($)',
                   gross_marginsA, gross_marginsB, years))
    summary.append(create_row('Gross Margin(%)', calculate_gross_margin_percent(
        gross_marginsA, aspA), calculate_gross_margin_percent(gross_marginsB, aspB), years))
    
    total_unit_cost_diff = np.array(summaryB['total_unit_cost_arr']) - np.array(summaryA['total_unit_cost_arr'])
    # print(find_xy_mean(total_unit_cost_diff))
    summary.append(create_row('Cost Difference', find_xy_mean(total_unit_cost_diff), [
                   ''] * years, years))
    write_to_file(summary, years)