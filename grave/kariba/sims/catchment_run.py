import pandas as pd
import sys

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from dtk.interventions.input_EIR import add_InputEIR
from dtk.vector.species import set_species_param
from simtools.ModBuilder import ModBuilder, ModFn
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from simtools.Utilities.Experiments import retrieve_experiment

base = '../../'
sys.path.append(base + 'src/analysis/')
sys.path.append(base + 'src/sims/')
sys.path.append(base + 'inputs/grid_csv/')

from build_zambia_cb import ZambiaConfigBuilder
from zambia_helpers import *
from zambia_calib_site import zambia_calib_site

# RUN PARAMETERS:
# base = "C:/Users/jsuresh/Projects/malaria-zm-kariba/gridded_sims/"
dropbox_user='jsuresh'
# catch_number = 1
# catch_list = get_catchment_list(dropbox_user=dropbox_user)
# catch = catch_list[catch_number]
catch = "chiyabi"
experiment_name = "chiyabi_maxinfecsweep_v2_oldimmunity"

base = "../../"
sim_start_year = 1954 #2010 - 7*8 (7 climate data years)
# Sim ends on Jan 1, 2014:
sim_duration_days = 365*(2014-sim_start_year)
num_cores = 8
num_seeds = 4

priority = "Highest"
coreset = "emod_abcd" #"emod_32cores"


milen_larval_params = load_milen_larval_params(catch)






zm = ZambiaConfigBuilder(sim_start_year=sim_start_year, sim_duration_days=sim_duration_days, dropbox_user=dropbox_user, num_cores=num_cores)
cb = zm.cb
cd = catch_specific_params(cb, catch)

set_species_param(cb,
                  'arabiensis',
                  'Larval_Habitat_Types', {
                      # "CONSTANT": 10.**sample['arab_constant_scale'],
                      "CONSTANT": 10.**6.5,
                      "TEMPORARY_RAINFALL": 10.**11
                  })

# Funestus
set_species_param(cb,
                  'funestus',
                  'Larval_Habitat_Types', {
                      "LINEAR_SPLINE": {
                          "Capacity_Distribution_Number_Of_Years": 1,
                          "Capacity_Distribution_Over_Time": {
                              "Times": [
                                  0.0,
                                  30.417,
                                  60.833,
                                  91.25,
                                  121.667,
                                  152.083,
                                  182.5,
                                  212.917,
                                  243.333,
                                  273.75,
                                  304.167,
                                  334.583
                              ],
                              "Values": [
                                  0.0,
                                  0.0,
                                  0.0,
                                  0.2,
                                  0.8,
                                  1.0,
                                  1.0,
                                  1.0,
                                  0.5,
                                  0.2,
                                  0.0,
                                  0.0
                              ]
                          },
                          "Max_Larval_Capacity": 10.**8.97
                          # "Max_Larval_Capacity": 10.**sample['arab_rainfall_scale'] * sample['spline_rainfall_ratio']
                          # "Max_Larval_Capacity": 10.**sample['funest_spline_scale']
                      },
                      # "WATER_VEGETATION": 10.**sample['funest_veg_scale']
                      "WATER_VEGETATION": 10.**5.5
                  })



# Add interventions
zm.add_all_interventions(cb, catch)
zm.add_reports_for_likelihood_analyzers(cb, catch, filter_duration_days=(365*4))

# This is a burnin, so we want to serialize our population at 2010-01-01:
serialize_year = 2010
serialization_write_time = (serialize_year - sim_start_year) * 365
cb.update_params({"Serialization_Time_Steps": [serialization_write_time]})

if catch == "chiyabi":
    cb.set_input_collection("ba932ab1-46b8-e811-a2c0-c4346bcb7275")
    cb.set_exe_collection("2fd1a56e-56b5-e811-a2c0-c4346bcb7275")
    cb.set_dll_collection("2cd1a56e-56b5-e811-a2c0-c4346bcb7275")

# # Drop EIR in regional node by a factor of 10 at beginning of 2014: this will overwrite previous EIR intervention
# monthly_profile = [0.21, 0.28, 0.43, 0.65, 0.84, 1.21, 1.24, 1.04, 0.84, 0.57, 0.29, 0.17]
# EIR_scale_factor = 0.1
# EIR_start_day = 365 * (2014-sim_start_year)
# add_InputEIR(cb,
#              monthlyEIRs=[x * EIR_scale_factor for x in monthly_profile],
#              nodes={'class': 'NodeSetNodeList', 'Node_List': [100000]},
#              start_day=EIR_start_day)




if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []

    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Max_Individual_Infections', seed) for seed in range(3,7)]
    modlists.append(new_modlist)

    if num_seeds > 1:
        new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
        modlists.append(new_modlist)

    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)
