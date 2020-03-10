
# Run endpoint analyzer on all runs in the suite, and collect ALL results into a single results CSV/dataframe
import sys
import numpy as np
import pandas as pd
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from simtools.Utilities.COMPSUtilities import exps_for_suite_id
from simtools.Utilities.Experiments import retrieve_experiment

if __name__ == "__main__":
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    suite_id = "5589873b-6ab8-e911-a2c1-c4346bcb1555"  # Gates Review
    suite_exps = exps_for_suite_id(suite_id=suite_id)


    for exp_dict in suite_exps:
        print(exp_dict.id)
        if str(exp_dict.id) == "1fd20dd2-d5b8-e911-a2c1-c4346bcb1555":
            print("SKIPPING BROKEN MOOMBA RUN exp id 1fd20dd2-d5b8-e911-a2c1-c4346bcb1555")
        else: #TESTING fixme
            print(exp_dict.id)
    #         exp = retrieve_experiment(exp_dict.id)
    #         print(exp)
    #         am.add_experiment(exp)
    #
    # am.analyze()
