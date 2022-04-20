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
from preprocessor import DEVICE_TYPE_SUBSTRATE, meta_data_row


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