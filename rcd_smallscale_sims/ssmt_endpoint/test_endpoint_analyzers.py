from rcd_smallscale_sims.ssmt_endpoint.get_endpoints import *

import sys
import numpy as np
import pandas as pd
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser

from simtools.Utilities.Experiments import retrieve_experiment

exp_id = "a9fbc42e-7368-ea11-a2c5-c4346bcb1550"
years_to_include = 4

if __name__ == "__main__":
    run_analyzers_and_save_output(exp_id, years_to_include)