import pandas as pd
import sys
import os

from simtools.ModBuilder import ModBuilder, ModFn
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

base = '../../'
sys.path.append(base + 'src/analysis/')
sys.path.append(base + 'src/sims/')
sys.path.append(base + 'inputs/grid_csv/')

from build_zambia_cb import ZambiaConfigBuilder
from zambia_helpers import *



# RUN PARAMETERS:
dropbox_user = "jsuresh"

dropbox_base = "C:/Users/{}/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/".format(dropbox_user)
input_base = os.path.join(dropbox_base,"inputs/catchments/")
base = "../../"
sim_start_year = 2014
sim_length_years = 1
num_cores = 1
num_seeds = 1
experiment_name = "kariba_local_migr_sweep"
priority = "Highest"
coreset = "emod_32cores"

zm = ZambiaConfigBuilder(sim_start_year=sim_start_year, sim_length_years=sim_length_years)
cb = zm.cb

# Add migration reports:
cb.params['Report_Event_Recorder'] = 1
cb.params["Report_Event_Recorder_Ignore_Events_In_List"] = 0
cb.params["Listed_Events"] = ["Bednet_Got_New_One", "Bednet_Using", "Bednet_Discarded"]
cb.params["Report_Event_Recorder_Events"] = ["Immigrating", "Emigrating"]

# load in inputs for this particular catchment
# run for 365 days

# def migr_test(cb, migr_testing):
#     if migr_testing:
#         cb.update_params({})
#     return {"migr_test": migr_testing}


# def set_x_local(cb, x_local):
#     cb.update_params({
#         'x_Local_Migration': x_local,
#         'x_Regional_Migration': 1.0
#     })



if __name__ == "__main__":
    modlists = []


    # if num_seeds > 1:
    #     new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    #     modlists.append(new_modlist)
    #
    # new_modlist = [ModFn(catch_specific_params, catch_i) for catch_i in list(range(56))]
    # modlists.append(new_modlist)
    #
    # builder = ModBuilder.from_combos(*modlists)

    catch_specific_params(cb, 1)


    SetupParser.init()
    SetupParser.set("HPC","priority",priority)
    SetupParser.set("HPC", "node_group", coreset)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name)
                                # exp_builder=builder)
