

#  Bbondo

import pandas as pd
import sys

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from dtk.interventions.habitat_scale import scale_larval_habitats
from dtk.interventions.input_EIR import add_InputEIR
from dtk.vector.species import set_species_param
from simtools.ModBuilder import ModBuilder, ModFn
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter

base = '../../'
sys.path.append(base + 'src/analysis/')
sys.path.append(base + 'src/sims/')
sys.path.append(base + 'inputs/grid_csv/')

from build_zambia_cb import ZambiaConfigBuilder
from zambia_helpers import *

# RUN PARAMETERS:
# base = "C:/Users/jsuresh/Projects/malaria-zm-kariba/gridded_sims/"
dropbox_user='jsuresh'
# catch_number = 1
# catch_list = get_catchment_list(dropbox_user=dropbox_user)
# catch = catch_list[catch_number]
catch = "chiyabi"

base = "../../"
sim_start_year = 2010
# Sim ends on July 1, 2016:
sim_duration_days = 365*(2016-sim_start_year) + 182
num_cores = 2


samples_per_iteration = 32
sim_runs_per_param_set = 2
max_iterations = 7
priority = "AboveNormal"
coreset = "emod_abcd"
sigma_r = 0.02

experiment_name = "{}_combos".format(catch)
resume = False



[params, burnin_params] = load_params_from_rank0_burnin()



zm = ZambiaConfigBuilder(sim_start_year=sim_start_year, sim_duration_days=sim_duration_days, dropbox_user=dropbox_user, num_cores=num_cores)
cb = zm.cb
cd = catch_specific_params(cb, catch)


arab_constant_rescale = pow(10, arab_constant) / pow(10, burnin_params['arab_constant_scale'])
arab_rainfall_rescale = pow(10, arab_rainfall) / pow(10, burnin_params['arab_rainfall_scale'])
funest_spline_rescale = pow(10, funest_spline) / pow(10, burnin_params['funest_spline_scale'])
funest_veg_rescale = pow(10, funest_veg) / pow(10, burnin_params['funest_veg_scale'])

scale_larval_habitats(cb,
                      pd.DataFrame({
                          'CONSTANT.arabiensis': [arab_constant_rescale],
                          'TEMPORARY_RAINFALL.arabiensis': [arab_rainfall_rescale],
                          'LINEAR_SPLINE.funestus': [funest_spline_rescale],
                          'WATER_VEGETATION.funestus': [funest_veg_rescale]
                      }),
                      start_day=0)

# Add interventions
# zm.add_all_interventions(cb, catch)
zm.add_reports_for_likelihood_analyzers(cb, catch, filter_duration_days=sim_duration_days)



# Draw from serialized file (from rank0 burnin):
if catch == "bbondo":
    cb.update_params({
        "Serialized_Population_Path": "//internal.idm.ctr/IDM/Home/jsuresh/input/kariba_gridded_sims",
        'Serialized_Population_Filenames': ['{}_2010.dtk'.format(catch)]
    })
else:
    cb.update_params({
        "Serialized_Population_Path": "//internal.idm.ctr/IDM/Home/jsuresh/input/kariba_gridded_sims",
        'Serialized_Population_Filenames': ['{}_2010-000.dtk'.format(catch),'{}_2010-001.dtk'.format(catch)]
    })

# # Drop EIR in regional node by a factor of 10 at beginning of 2014: this will overwrite previous EIR intervention
monthly_profile = [0.21, 0.28, 0.43, 0.65, 0.84, 1.21, 1.24, 1.04, 0.84, 0.57, 0.29, 0.17]
EIR_scale_factor = 0.1
EIR_start_day = 365 * (2014-sim_start_year)
add_InputEIR(cb,
             monthlyEIRs=[x * EIR_scale_factor for x in monthly_profile],
             nodes={'class': 'NodeSetNodeList', 'Node_List': [100000]},
             start_day=EIR_start_day)


if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC","priority",priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []


    # if num_seeds > 1:
    #     new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    #     modlists.append(new_modlist)
    #
    # new_modlist = [ModFn(catch_specific_params, catch_i) for catch_i in list(range(56))]
    # modlists.append(new_modlist)
    #
    # builder = ModBuilder.from_combos(*modlists)


    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name)
                                # exp_builder=builder)
