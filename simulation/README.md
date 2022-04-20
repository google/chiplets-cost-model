### Installation
1. python3 required
2. pip3 installation required (User Guide - pip3)[https://pip.pypa.io/en/latest/user_guide/#requirements-files]
2. Install required dependencies by running

```
pip3 install -r requirements.txt
```

### Running analysis
1. Provide input files in `inputs` directory. Use `input_template.csv` to create the input files. The name should be `data_option1.csv` and `data_option2.csv`
2. Run `python3 cost_analyzer.py --years <num of years> --reps <num of reps> --simulations <num of simulations>`

For example to run simulation for 5 years, 500 values randomly normally distributed and 8000 simulations:

```
python3 cost_analyzer.py --years 5 --reps 500 --simulations 8000
```

3. Look for output in `outputs` directory. 
4. In case of simulation, the unit cost difference distribution is available in `cost_diff_summary.png` for all `t`. They are available individually with `CostDiffYr{t}.png` as well.
Also, the Stochastic Analysis summary is available in `stochastic_analysis.csv` with Worst Case (5% probability), Average (50% Probability) and Best Case (5% Probability)


### Run unit tests

```
python3 -m unittest
```