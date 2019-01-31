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
from zambia_calib_site import zambia_calib_site

# RUN PARAMETERS:
# base = "C:/Users/jsuresh/Projects/malaria-zm-kariba/gridded_sims/"
dropbox_user='jsuresh'
# catch_number = 1
# catch_list = get_catchment_list(dropbox_user=dropbox_user)
# catch = catch_list[catch_number]
catch = "bbondo"

base = "../../"
sim_start_year = 2010
# Sim ends on July 1, 2016:
sim_duration_days = 365*(2016-sim_start_year) + 182
num_cores = 2


samples_per_iteration = 32
sim_runs_per_param_set = 4
max_iterations = 7
priority = "AboveNormal"
coreset = "emod_abcd"
sigma_r = 0.02

experiment_name = "{}_old_immunity_calib".format(catch)
resume = False


def load_params_from_rank0_burnin():
    df = pd.read_csv("rank0_burnins.csv")
    df = df[df["catch"]==catch]

    arab_constant = 6.3 #df.loc[0,"arab_constant_scale"]
    arab_rainfall = df.loc[0,"arab_rainfall_scale"]
    # funest_spline = df.loc[0,"funest_spline_scale"]
    log_spline_rainfall_ratio = df.loc[0,"log_spline_rainfall_ratio"]
    funest_veg = 6.3 #df.loc[0,"funest_veg_scale"]

    # #fixme FUDGING
    # arab_constant = 6
    # arab_rainfall = 9.2
    # funest_spline = 8.4
    # funest_veg = 7.1



    params_simple = {
        "arab_constant_scale": arab_constant,
        "arab_rainfall_scale": arab_rainfall,
        "funest_spline_scale": arab_rainfall + log_spline_rainfall_ratio,
        "funest_veg_scale": funest_veg
    }

    funest_spline = arab_rainfall + log_spline_rainfall_ratio

    params_calib = [
        # {
        #     'Name': 'arab_constant_scale',
        #     'Dynamic': True,
        #     'MapTo': 'arab_constant_scale',
        #     'Guess': arab_constant,
        #     'Min': arab_constant-1,
        #     'Max': arab_constant+1
        # },
        {
            'Name': 'arab_rainfall_scale',
            'Dynamic': True,
            'MapTo': 'arab_rainfall_scale',
            'Guess': arab_rainfall,
            'Min': arab_rainfall-1,
            'Max': arab_rainfall+1
        },

        # {
        #     'Name': 'funest_spline_scale',
        #     'Dynamic': True,
        #     'MapTo': 'funest_spline_scale',
        #     'Guess': funest_spline,
        #     'Min': funest_spline-1,
        #     'Max': funest_spline+1
        # },
        {
            'Name': 'log_spline_rainfall_ratio',
            'Dynamic': True,
            'MapTo': 'log_spline_rainfall_ratio',
            'Guess': log_spline_rainfall_ratio,
            'Min': -3,
            'Max': 0
        },
        # {
        #     'Name': 'funest_veg_scale',
        #     'Dynamic': True,
        #     'MapTo': 'funest_veg_scale',
        #     'Guess': funest_veg,
        #     'Min': funest_veg-1,
        #     'Max': funest_veg+1
        # }
    ]

    return [params_calib, params_simple]


[params, burnin_params] = load_params_from_rank0_burnin()


def map_sample_to_model_input(cb, sample):
    # arab_constant = sample["arab_constant_scale"]
    arab_constant = 6.3
    arab_rainfall = sample["arab_rainfall_scale"]
    # funest_spline = sample["funest_spline_scale"]
    log_spline_rainfall_ratio = sample["log_spline_rainfall_ratio"]
    funest_spline = arab_rainfall + log_spline_rainfall_ratio
    # funest_veg = sample["funest_veg_scale"]
    funest_veg = 6.3

    arab_constant_rescale = 1.0 #pow(10, arab_constant) / pow(10, burnin_params['arab_constant_scale'])
    arab_rainfall_rescale = pow(10, arab_rainfall) / pow(10, burnin_params['arab_rainfall_scale'])
    funest_spline_rescale = pow(10, funest_spline) / pow(10, burnin_params['funest_spline_scale'])
    funest_veg_rescale = 1.0 #pow(10, funest_veg) / pow(10, burnin_params['funest_veg_scale'])


    scale_larval_habitats(cb,
                          pd.DataFrame({
                              'CONSTANT.arabiensis': [arab_constant_rescale],
                              'TEMPORARY_RAINFALL.arabiensis': [arab_rainfall_rescale],
                              'LINEAR_SPLINE.funestus': [funest_spline_rescale],
                              'WATER_VEGETATION.funestus': [funest_veg_rescale]
                          }),
                          start_day=0)

    return sample


zm = ZambiaConfigBuilder(sim_start_year=sim_start_year, sim_duration_days=sim_duration_days, dropbox_user=dropbox_user, num_cores=num_cores)
cb = zm.cb
cd = catch_specific_params(cb, catch)

# Add interventions
zm.add_all_interventions(cb, catch)
zm.add_reports_for_likelihood_analyzers(cb, catch, filter_duration_days=sim_duration_days)



# Draw from serialized file (from rank0 burnin):
# if catch == "bbondo":
#     cb.update_params({
#         "Serialized_Population_Path": "//internal.idm.ctr/IDM/Home/jsuresh/input/kariba_gridded_sims",
#         'Serialized_Population_Filenames': ['{}_2010.dtk'.format(catch)]
#     })
# else:
cb.update_params({
    "Serialized_Population_Path": "//internal.idm.ctr/IDM/Home/jsuresh/input/kariba_gridded_sims",
    'Serialized_Population_Filenames': ['{}_2010-000.dtk'.format(catch),'{}_2010-001.dtk'.format(catch)]
})

# # Drop EIR in regional node by a factor of 10 at beginning of 2014: this will overwrite previous EIR intervention
monthly_profile = [0.21, 0.28, 0.43, 0.65, 0.84, 1.21, 1.24, 1.04, 0.84, 0.57, 0.29, 0.17]
EIR_scale_factor = 0.1*6
EIR_start_day = 365 * (2014-sim_start_year)
add_InputEIR(cb,
             monthlyEIRs=[x * EIR_scale_factor for x in monthly_profile],
             nodes={'class': 'NodeSetNodeList', 'Node_List': [100000]},
             start_day=EIR_start_day)


# Calibration-specific stuff:
sites = [zambia_calib_site(catch)]
# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
            ]
# Use OptimTool as next-point-algorithm
optimtool = OptimTool(params,
                      samples_per_iteration=samples_per_iteration,
                      center_repeats=1,
                      sigma_r=sigma_r)

calib_manager = CalibManager(name=experiment_name,
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sim_runs_per_param_set=sim_runs_per_param_set,
                             sites=sites,
                             next_point=optimtool,
                             max_iterations=max_iterations,
                             plotters=plotters)

run_calib_args = {
    "calib_manager": calib_manager
}


if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    cm = run_calib_args["calib_manager"]
    # cm.run_calibration()

    if not resume:
        cm.run_calibration()
    else:
        cm.resume_calibration(iteration=1,
                              iter_step="analyze")