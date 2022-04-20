
# Simulation parameters
# In case if Monte Carlo analysis is required, then pass params in args while 
# running scripts as:
# `python3 cost_analyzer.py --years 5 --reps 10 --simulations 20`

class Params(object):
    def __init__(self, reps, simulations):
        self.num_of_reps = reps
        self.num_of_simulations = simulations

    def __str__(self):
        return f"reps: {self.num_of_reps}, simulations: {self.num_of_simulations}"