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

import math
from operator import mod
from scipy.special import comb

import numpy as np
from params import Params

# Yield model names
MURPHY_MODEL = 'Murphy'
BOSE_EINSTEIN_MODEL = 'Bose Einstein'

# Device Type
DEVICE_TYPE_SUBSTRATE = 'Substrate'

params = Params(1, 1)

def validate(reads, template, years):
    input_headers = set(reads[0].keys())
    template_headers = set(template[0].keys())

    missing_columns = template_headers - input_headers
    if len(missing_columns) > 0:
        raise Exception(f"Following columns are missing, please use the template file inside input folder: {missing_columns}")
    
    assembly_steps = int(reads[0]['AssemblySteps'])
    for assembly_step in range(1, assembly_steps + 1):
        validate_col(input_headers, f'AssyPerStepYield{assembly_step}')
        validate_col(input_headers, f'AssyYield{assembly_step}')
        validate_col(input_headers, f'AssemblySeq{assembly_step}')

    for year in range(1, years + 1):
        validate_col(input_headers, f'SubstrateUnitPriceYr{year}($)')
        validate_col(input_headers, f'SubstrateUnitPriceYr{year}($)')
        validate_col(input_headers, f'DefectDensityYr{year}(Defects/cm^2)')
        validate_col(input_headers, f'WaferYieldYr{year}')
        validate_col(input_headers, f'ForecastUnitPriceYr{year}($)')
        validate_col(input_headers, f'ForecastDemandYr{year}')
        validate_col(input_headers, f'PackageAssemblyCostYr{year}($)')
        validate_col(input_headers, f'FinalPackageTestCostYr{year}($)')
        validate_col(input_headers, f'FinalPackageTestYieldYr{year}')
        validate_col(input_headers, f'SLTCostYr{year}($)')
        validate_col(input_headers, f'SLTYieldYr{year}')
        validate_col(input_headers, f'QualityYr{year}')
        validate_col(input_headers, f'OperatingUnitCostYr{year}($)')
        validate_col(input_headers, f'IpInterfaceCostYr{year}($)')
        validate_col(input_headers, f'IpInterfaceCostYr{year}($)')
        validate_col(input_headers, f'IpInterfaceCostAspYr{year}')
        

def validate_col(columns, column):
    if column not in columns:
        raise Exception(f"Following columns are missing, please use the template file inside input folder: {column}")


def cleanse(reads, args):
    input = []
    # Update the params values
    params.num_of_steps = args['steps']
    params.num_of_simulations = args['simulations']

    years = args['years']
    for row in reads:
        # Calculations not required for metadata row
        if meta_data_row(row):
            for year in range(1, years + 1):
                row[f'AspYr{year}($)'] = get_asp(row, year)
            input.append(row)
            continue

        row['EffA'] = calculate_effective_area(input, row)

        # GDPW
        row['GDPW'] = calculate_gdpw(row)

        row['ProbeCost($)'] = float(
            row['ProbeCost($)']) if row['ProbeCost($)'] else calculate_probe_cost(row)

        for year in range(1, years + 1):
            # Wafer price
            row[f'WaferPriceYr{year}($)'] = calculate_wafer_price(row, year)
            # Wafer Yield
            row[f'WaferYieldYr{year}'] = calculate_wafer_yield(row, input[0], year)

            # Forecast Unit Price ($) per die
            row[f'ForecastUnitPriceYr{year}($)'] = calculate_forcast_unit_price(row, year)

            row[f'ForecastDemandYr{year}'] = calculate_forcast_demand(row, year)
            # total operating cost
            forecast_demand = row[f'ForecastDemandYr{year}']
            op_unit_cost = float(row[f'OperatingUnitCostYr{year}($)'])
            row[f'OpCostYr{year}'] =  forecast_demand * op_unit_cost

            # Total IP Interface Cost
            # Total_Ip_Cost = IP_Cost + (IP_Pct_per_ASP * ASP) / 100 * FD
            ip_cost = float(row[f'IpInterfaceCostYr{year}($)'])
            ip_cost_per_asp = float(row[f'IpInterfaceCostAspYr{year}'])
            asps = input[0][f'AspYr{year}($)']
            row[f'TotalIpInterfaceCostYr{year}'] =  calculate_total_ip_cost(ip_cost, ip_cost_per_asp, forecast_demand, asps)

            # Material Cost
            # MatCost = FUP * FD
            forecast_unit_prices = row[f'ForecastUnitPriceYr{year}($)']
            row[f'MatCostYr{year}'] = calculate_mat_cost(forecast_unit_prices, forecast_demand)

            # Field Quality Cost
            field_quality_fr = float(row[f'QualityYr{year}'])
            row[f'QualityCostYr{year}'] = calculate_quality_cost(field_quality_fr, forecast_unit_prices, forecast_demand)

            # mask set cost and nre
            row[f'MaskCost{year}'] = get_mask_set_cost(row, year)
            # row[f'Nre{year}'] = get_nre(row, year)

            # test cost
            row[f'TestCost{year}'] = get_test_cost(input, row[f'WaferYieldYr{year}'])
        input.append(row)

    return input

def calculate_quality_cost(field_quality_fr, forecast_unit_prices, forecast_demands):
    return forecast_unit_prices * forecast_demands * (field_quality_fr/1000000)

def calculate_mat_cost(forecast_unit_prices, forecast_demands):
    return forecast_unit_prices * forecast_demands

def calculate_total_ip_cost(ip_cost, ip_cost_per_asp, demands, asps):
    return (asps * ip_cost_per_asp) * demands + ip_cost

def calculate_wafer_price(row, year):
    if row['DeviceType'] == DEVICE_TYPE_SUBSTRATE:
        return get_transformed_matrix(0)

    if year == 1:
        if "-" not in row['WaferPriceYr1($)']:
            return get_transformed_matrix(float(row['WaferPriceYr1($)']))
        
        return get_normal_distribution(row['WaferPriceYr1($)'])

    wf_col = f'WaferPriceYr{year}($)'
    if row[wf_col]:
        if "-" not in row[wf_col]:
            return get_transformed_matrix(float(row[wf_col]))
        
        return get_normal_distribution(row[wf_col])
    
    wafer_prices = row[f'WaferPriceYr{year - 1}($)']
    discount_rate = float(row['WaferPriceAnnualDiscountFactor(%)'])
    return wafer_prices * (1 - discount_rate/100)

def calculate_forcast_demand(row, year):
    fd = row[f'ForecastDemandYr{year}']
    if "-" not in fd:
        return get_transformed_matrix(int(fd))
    
    return get_normal_distribution(row[f'ForecastDemandYr{year}'])


def calculate_effective_area(input, row):
    # EffA = (L + ss ) x (W + ss ) + rec_area * rec_spares Effective Area of each die
    L = float(row['DimensionX'])
    W = float(row['DimensionY'])
    ss = float(row['SawStreet(mm)'])
    rec_spares = int(input[0]['RecSpares'])
    rec_area = int(input[0]['RecArea'])
    return (L + ss) * (W + ss) + rec_area * rec_spares


def meta_data_row(row):
    device_type = row['DeviceType']
    return device_type is None or device_type == ''

# GDPW = ((Wfr - 6) * PI * (Wfr / (4 * EffA) - 1 / sqrt(2 * EffA)))
def calculate_gdpw(row):
    if float(row['DimensionX']) == 0 or float(row['DimensionY']) == 0:
        return 0
    wfr = float(row['WaferSize(mm)'])
    return round((wfr - 6) * math.pi * ((wfr / (4 * row['EffA'])) - (1 / math.sqrt(2 * row['EffA']))), 0)


def calculate_probe_cost(row):
    if row['DeviceType'] == DEVICE_TYPE_SUBSTRATE:
        return 0

    return float(row['ProberRate($/hr)']) * ((float(row['Insrtn1']) / 3600) / float(row['Sites1']) + (float(row['Insrtn2']) / 3600) / float(row['Sites2']))


def calculate_wafer_yield(row, metadata, year):
    wafer_yield = row[f'WaferYieldYr{year}']
    if wafer_yield:
        if "-" not in wafer_yield:
            return get_transformed_matrix(float(wafer_yield))
        
        return get_normal_distribution(wafer_yield)
    
    model = get_yield_model(metadata)
    defect_density = get_defect_density(row[f'DefectDensityYr{year}(Defects/cm^2)'])
    model_yield_fn = calculate_murphy_yield if model == MURPHY_MODEL else calculate_bose_einstein_yield
    model_yield = model_yield_fn(row, defect_density)
    rec_yield = calculate_rec_yield(metadata, defect_density)
    
    return model_yield + rec_yield


def calculate_murphy_yield(row, defect_density):
    return ((1 - math.exp(-defect_density * row['EffA'] * 0.01)) / (defect_density * row['EffA'] * 0.01)) ** 2


def calculate_bose_einstein_yield(row, defect_density):
    return (1.0 / (1 + defect_density * row['EffA'] * 0.01)) ** int(row['N'])


# Yield Adjusted Forcast Unit Price
# For Device Type = Active, FUP = Pwafer / (GDPW * WaferYield) + ProbeCost
# For Device Type = Substrace, FUP = SubsCost = SubsUnitPrice/WaferYield
def calculate_forcast_unit_price(row, year):
    fup = row[f'ForecastUnitPriceYr{year}($)']
    if fup:
        return get_transformed_matrix(float(fup))
    
    return calculate_substrate_fup(row, year) if row['DeviceType'] == DEVICE_TYPE_SUBSTRATE else calculate_active_fup(row, year) + row['ProbeCost($)']


def calculate_active_fup(row, year):
    gdpw = row['GDPW']
    if gdpw == 0:
        return 0
    pWafer = row[f'WaferPriceYr{year}($)']
    pYield = row[f'WaferYieldYr{year}']
    return pWafer / (pYield * gdpw)


def calculate_substrate_fup(row, year):
    subs_unit_price = get_transformed_matrix(float(row[f'SubstrateUnitPriceYr{year}($)'] or '0'))
    subs_yield = row[f'WaferYieldYr{year}']
    return subs_unit_price/subs_yield


def get_defect_density(dd):
    if "-" not in dd:
        return get_transformed_matrix(float(dd))
    return get_normal_distribution(dd)


def get_asp(row, year):
    asp = row[f'AspYr{year}($)']
    if "-" not in asp:
        return get_transformed_matrix(float(asp))
    
    return get_normal_distribution(row[f'AspYr{year}($)'])


def get_yield_model(metadata):
    model = metadata['YieldModel']

    if model != MURPHY_MODEL and model != BOSE_EINSTEIN_MODEL:
        raise Exception('Yield model should be one of Murphy or Bose Einstein')

    return model


def get_nre(row, year):
    nre = row['NRE($)']
    if year > 1 or nre is None or nre == '':
        return 0.0
    if "-" in nre:
        return get_normal_distribution(nre)
    return get_transformed_matrix(float(nre))


def get_mask_set_cost(row, year):
    if year > 1:
        return 0.0
    return float(row['MaskSetCost'] or '0')


def calculate_rec_yield(metadata, dd):
    k = int(metadata['RecSpares'])
    n = int(metadata['RecBaseline']) + int(metadata['RecSpares'])
    p = int(metadata['RecArea']) / 100 * dd
    return comb(n, k) * p**k * (1 - p)**(n - k)

def wafer_sort_test_cost(input, yield_i):
    ws_a = float(input[0]['WSa($/hr)']) # Wafer sort automated test equipment loaded rate
    ws_h = float(input[0]['WSh($/hr)']) # Wafer sort prober loaded rate ($/hr)
    ws_ci = float(input[0]['WSci'])     # Wafer Sort insertion per unit
    ws_di = float(input[0]['WSdi'])     # Probe (Wafer Sort) time duration per insertion
    ws_xi = float(input[0]['WSxi'])     # Wafer sort test coverage
    ws_ri = float(input[0]['WSri'])     # Wafer sort retest attempts for failing unit
    return ((ws_a + ws_h) / 3600) * (ws_di * ws_ci + (1 - yield_i * ws_xi) * ws_di * ws_ri)

def final_test_cost(input, yield_i):
    ft_a = float(input[0]['FTa($/hr)']) 
    ft_h = float(input[0]['FTh($/hr)']) # final test handler loaded rate
    ws_xi = float(input[0]['WSxi'])     # Wafer sort test coverage
    ft_xi = float(input[0]['FTxi'])
    ft_di = float(input[0]['FTdi'])
    ft_ri = float(input[0]['FTri'])
    ft_ci = float(input[0]['FTci'])
    return ((ft_a + ft_h) / 3600) * (ft_ci * ft_di + (1 - yield_i * (ws_xi - ft_xi)) * (ft_ri * ft_di))

def slt_test_cost(input, yield_i):
    slt_a = float(input[0]['SLTa($/hr)']) 
    slt_h = float(input[0]['SLTh($/hr)']) # final test handler loaded rate
    slt_di = float(input[0]['SLTdi'])   # system level test duration per unit
    ftx_i = float(input[0]['FTxi'])
    return ((slt_a + slt_h) / 3600) * (slt_di * (yield_i + (1 - yield_i) * (1 - ftx_i)))

def get_test_cost(input, yield_i):
    return wafer_sort_test_cost(input, yield_i) + final_test_cost(input, yield_i) + slt_test_cost(input, yield_i)

def get_normal_distribution(range_val):
    first, second = range_val.split("-")
    low, high = float(first), float(second)
    avg = (low + high) / 2
    sd = avg / 10
    return np.random.normal(avg, sd, size = (params.num_of_steps, params.num_of_simulations))

def get_transformed_matrix(val):
    return np.array([[val] * params.num_of_simulations] * params.num_of_steps)

def simulation(input, years):
    for row in input:
        if meta_data_row(row):
            for year in range(1, years + 1):
                asp = row[f'AspYr{year}($)']
                if "-" in asp:
                    return True

        for year in range(1, years + 1):
            dd = row[f'DefectDensityYr{year}(Defects/cm^2)']
            wafer_yield = row[f'WaferYieldYr{year}']
            wafer_price = row[f'WaferPriceYr{year}($)']
            forecast_demad = row[f'ForecastDemandYr{year}']

            if "-" in dd or "-" in wafer_yield or "-" in wafer_price or "-" in forecast_demad:
                return True
    return False