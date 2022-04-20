import csv
import math
from operator import mod
from scipy.special import comb

# Yield model names
MURPHY_MODEL = 'Murphy'
BOSE_EINSTEIN_MODEL = 'Bose Einstein'
DEVICE_TYPE_SUBSTRATE = 'Substrate'

def readFile(fileName, numOfYears):
    input = []
    with open('inputs/' + fileName) as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Calculations not required for metadata row
            if meta_data_row(row):
                input.append(row)
                continue

            # Wafer price
            for year in range(1, numOfYears + 1):
                col = f'WaferPriceYr{year}($)'
                if col not in row:
                    raise Exception(f'Column {col} does not exists! Make sure number of year matches columns')

                row[col] = calculate_wafer_price(row, year)

            row['EffA'] = calculate_effective_area(input, row)

            # GDPW
            row['GDPW'] = calculate_gdpw(row)

            row['ProbeCost($)'] = float(
                row['ProbeCost($)']) if row['ProbeCost($)'] else calculate_probe_cost(row)

            # Wafer Yield
            for year in range(1, numOfYears + 1):
                wafer_col = f'WaferYieldYr{year}'
                dd_col = f'DefectDensityYr{year}(Defects/cm^2)'
                if wafer_col not in row or dd_col not in row:
                    raise Exception('Column does not exists! Make sure number of year matches columns')

                row[wafer_col] = calculate_wafer_yield(row, row[wafer_col], input, float(row[dd_col] or '0'))
                row[f'TestCostYr{year}'] = get_test_cost(input, row[wafer_col])

            # Forecast Unit Price ($) per die
            for year in range(1, numOfYears + 1):
                col = f'ForecastUnitPriceYr{year}($)'
                if col not in row:
                    raise Exception('Column does not exists! Make sure number of year matches columns')

                row[col] = calculate_forcast_unit_price(row, row[col], year)

            # total operating cost
            for year in range(1, numOfYears + 1):
                forecast_demand = int(row[f'ForecastDemandYr{year}'])
                op_unit_cost = float(row[f'OperatingUnitCostYr{year}($)'])
                row[f'OpCostYr{year}'] = op_unit_cost * forecast_demand

            # Total IP Interface Cost
            # Total_Ip_Cost = IP_Cost + (IP_Pct_per_ASP * ASP) / 100 * FD
            for year in range(1, numOfYears + 1):
                total_ip_cost_col = f'TotalIpInterfaceCostYr{year}'
                ip_cost = float(row[f'IpInterfaceCostYr{year}($)'])
                ip_cost_per_asp = float(row[f'IpInterfaceCostAspYr{year}'])
                fd = int(row[f'ForecastDemandYr{year}'])
                asp = get_asp_cost(input, row, f'AspYr{year}($)')
                row[total_ip_cost_col] = ip_cost + (ip_cost_per_asp * asp) * fd

            # Material Cost
            # MatCost = FUP * FD
            for year in range(1, numOfYears + 1):
                mat_cost_col = f'MatCostYr{year}'
                fup = float(row[f'ForecastUnitPriceYr{year}($)'])
                fd = float(row[f'ForecastDemandYr{year}'])
                row[mat_cost_col] = fup * fd

            # Field Quality Cost
            for year in range(1, numOfYears + 1):
                qual_cost_col = f'QualityCostYr{year}'
                field_quality_fr = float(row[f'QualityYr{year}'])
                fup = float(row[f'ForecastUnitPriceYr{year}($)'])
                fd = int(row[f'ForecastDemandYr{year}'])
                row[qual_cost_col] = (field_quality_fr/1000000) * fup * fd

            input.append(row)

    # test cost are not done in sheet
    # Ask Mudashir
    return input


def calculate_wafer_price(row, year):
    if row['DeviceType'] == DEVICE_TYPE_SUBSTRATE:
        return 0
    
    if year == 1:
        return float(row['WaferPriceYr1($)'])

    wafer_price = float(row[f'WaferPriceYr{year - 1}($)'])   
    discount_rate = float(row['WaferPriceAnnualDiscountFactor(%)'])
    return wafer_price * (1 - discount_rate/100)


def calculate_effective_area(input, row):
    # EffA = (L + ss ) x (W + ss ) Effective Area of each die
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


def calculate_wafer_yield(row, wafer_yield, input, defect_density):
    if wafer_yield:
        return float(wafer_yield)

    model = get_yield_model(input, row)
    model_yield = calculate_murphy_yield(row, defect_density) if model == MURPHY_MODEL else calculate_bose_einstein_yield(row, defect_density)
    return model_yield + calculate_rec_yield(input, defect_density)


def calculate_murphy_yield(row, defect_density):
    return ((1 - math.exp(-defect_density * row['EffA'] * 0.01)) / (defect_density * row['EffA'] * 0.01)) ** 2


def calculate_bose_einstein_yield(row, defect_density):
    return (1.0 / (1 + defect_density * row['EffA'] * 0.01)) ** int(row['N'])


# Yield Adjusted Forcast Unit Price
# For Device Type = Active, FUP = Pwafer / (GDPW * WaferYield) + ProbeCost
# For Device Type = Substrace, FUP = SubsCost = SubsUnitPrice/WaferYield
def calculate_forcast_unit_price(row, forecast_unit_force_price, year):
    if forecast_unit_force_price:
        return float(forecast_unit_force_price)

    return calculate_substrate_fup(row, year) if row['DeviceType'] == DEVICE_TYPE_SUBSTRATE else calculate_active_fup(row, year) + row['ProbeCost($)']


def calculate_active_fup(row, year):
    gdpw = row['GDPW']
    if gdpw == 0:
        return 0
    pWafer = float(row[f'WaferPriceYr{year}($)'])
    pYield = float(row[f'WaferYieldYr{year}'])
    return  pWafer/ int(gdpw * pYield)


def calculate_substrate_fup(row, year):
    subs_unit_price = float(row[f'SubstrateUnitPriceYr{year}($)'] or '0')
    subs_yield = float(row[f'WaferYieldYr{year}'])
    return subs_unit_price/subs_yield


def get_asp_cost(input, row, asp_col):
    return float(input[0][asp_col] if input else row[asp_col])


def get_yield_model(input, row):
    model = input[0]['YieldModel'] if input else row['YieldModel']

    if model != MURPHY_MODEL and model != BOSE_EINSTEIN_MODEL:
        raise Exception('Yield model should be one of Murphy or Bose Einstein')

    return model


def calculate_rec_yield(input, dd):
    k = int(input[0]['RecSpares'])
    n = int(input[0]['RecBaseline']) + int(input[0]['RecSpares'])
    p = int(input[0]['RecArea']) / 100 * dd
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
