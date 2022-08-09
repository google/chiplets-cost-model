### Installation
1. python3 required
2. pip3 installation required (User Guide - pip3)[https://pip.pypa.io/en/latest/user_guide/#requirements-files]
2. Install required dependencies by running

```
pip3 install -r requirements.txt
```
### Running baseline analysis
1. Provide input files in `inputs` directory. `input_template.csv` can be used to create the input files, but `input_template.csv` shouldn't be updated directly - VERY IMPORTANT!! The input file name should be `data_option1.csv` and `data_option2.csv`
2. Run `python3 cost_analyzer.py`

For example to run simulation for 5 years, specify the values in input `params.csv` file:

```
NumOfYears,NumOfSteps,NumOfSimulation
5,1,1
```

3. Look for output in `outputs` directory. 


### Running Monte Carlo analysis
1. Provide input files in `inputs` directory. `input_template.csv` can be used to create the input files, but `input_template.csv` shouldn't be updated directly - VERY IMPORTANT!! The input file name should be `data_option1.csv` and `data_option2.csv`
2. Run `python3 cost_analyzer.py`

For example to run simulation for 5 years, 50 values randomly normally distributed for the range and 8000 simulations, specify the values in `params.csv` input file:

```
NumOfYears,NumOfSteps,NumOfSimulation
5,50,8000
```

3. Look for output in `outputs` directory. 
4. In case of simulation, the unit cost difference distribution is available in `cost_diff_summary.png` for all `t`. They are available individually with `CostDiffYr{t}.png` as well.
Also, the Stochastic Analysis summary is available in `stochastic_analysis.csv` with Worst Case (5% probability), Average (50% Probability) and Best Case (5% Probability)


### Run unit tests

```
python3 -m unittest
```