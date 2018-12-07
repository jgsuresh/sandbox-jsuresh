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

base = "../../"
sim_start_year = 1954 #2010 - 7*8 (7 climate data years)
# Sim ends on Jan 1, 2014:
sim_duration_days = 365*(2014-sim_start_year)
num_cores = 2


samples_per_iteration = 200
max_iterations = 1
priority = "AboveNormal"
coreset = "emod_abcd" #"emod_32cores"
sigma_r = 0.6

experiment_name = "{}_burnin_old_immunity_nowaterveg".format(catch)
resume = False

milen_larval_params = load_milen_larval_params(catch)



if catch == "chiyabi":
    params = [
        {
            'Name': 'arab_rainfall_scale',
            'Dynamic': True,
            'MapTo': 'arab_rainfall_scale',
            'Guess': 10.3,
            'Min': 9.5,
            'Max': 11
        },
        {
            'Name': 'log_spline_rainfall_ratio',
            'Dynamic': True,
            'MapTo': 'log_spline_rainfall_ratio',
            'Guess': milen_larval_params["spline"]-milen_larval_params["rainfall"],
            'Min': -3,
            'Max': 0
        }
    ]
elif catch == "sinafala":
    params = [
        {
            'Name': 'arab_rainfall_scale',
            'Dynamic': True,
            'MapTo': 'arab_rainfall_scale',
            'Guess': 11,
            'Min': 10,
            'Max': 12
        },
        {
            'Name': 'log_spline_rainfall_ratio',
            'Dynamic': True,
            'MapTo': 'log_spline_rainfall_ratio',
            'Guess': milen_larval_params["spline"]-milen_larval_params["rainfall"],
            'Min': -2,
            'Max': 0
        }
    ]

else:
    params = [
        {
            'Name': 'arab_rainfall_scale',
            'Dynamic': True,
            'MapTo': 'arab_rainfall_scale',
            'Guess': milen_larval_params["rainfall"],
            'Min': milen_larval_params["rainfall"]-1,
            'Max': milen_larval_params["rainfall"]+1
        },

        {
            'Name': 'log_spline_rainfall_ratio',
            'Dynamic': True,
            'MapTo': 'log_spline_rainfall_ratio',
            'Guess': milen_larval_params["spline"]-milen_larval_params["rainfall"],
            'Min': -2,
            'Max': 0
        }
    ]


class burnin_optimtool(OptimTool):
    def uniform_sampling_bounds(self, n_each_dim=3):
        import itertools

        range_dict = {}

        names = []
        ranges = []
        for param_dict in self.params:
            if n_each_dim > 3:
                values_to_sample =  np.linspace(param_dict["Min"],param_dict["Max"], n_each_dim)
            else:
                values_to_sample = np.array([param_dict["Min"], param_dict["Guess"], param_dict["Max"]])
            ranges.append(values_to_sample)
            names.append(param_dict["Name"])

        hold = np.array([x for x in itertools.product(*ranges)])

        sample_dict = {}
        for i in range(len(names)):
            sample_dict[names[i]] = np.copy(hold[:,i])

        df = pd.DataFrame(sample_dict)

        return df



    def get_samples_for_iteration(self, iteration):
        # Update args
        if self.need_resolve:
            self.resolve_args(iteration)

        if iteration == 0:
            samples = self.uniform_sampling_bounds()
            self.add_samples(samples, iteration)
        else:
            # Regress inputs and results from previous iteration
            # Move X_center, choose hypersphere, save in dataframe
            samples = self.choose_samples_via_gradient_ascent(iteration)

        samples.reset_index(drop=True, inplace=True)
        return self.generate_samples_from_df(samples)





def map_sample_to_model_input(cb, sample):
    set_species_param(cb,
                      'arabiensis',
                      'Larval_Habitat_Types', {
                          # "CONSTANT": 10.**sample['arab_constant_scale'],
                          "CONSTANT": 10.**6.5,
                          "TEMPORARY_RAINFALL": 10.**sample['arab_rainfall_scale']
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
                              "Max_Larval_Capacity": 10.**(sample['arab_rainfall_scale']+sample['log_spline_rainfall_ratio'])
                              # "Max_Larval_Capacity": 10.**sample['arab_rainfall_scale'] * sample['spline_rainfall_ratio']
                              # "Max_Larval_Capacity": 10.**sample['funest_spline_scale']
                          },
                          # "WATER_VEGETATION": 10.**sample['funest_veg_scale']
                          # "WATER_VEGETATION": 10.**5.5
                      })

    return sample


zm = ZambiaConfigBuilder(sim_start_year=sim_start_year, sim_duration_days=sim_duration_days, dropbox_user=dropbox_user, num_cores=num_cores)
cb = zm.cb
cd = catch_specific_params(cb, catch)

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


# cb.update_params({"Max_Individual_Infections": 10})
# # Drop EIR in regional node by a factor of 10 at beginning of 2014: this will overwrite previous EIR intervention
# monthly_profile = [0.21, 0.28, 0.43, 0.65, 0.84, 1.21, 1.24, 1.04, 0.84, 0.57, 0.29, 0.17]
# EIR_scale_factor = 0.1
# EIR_start_day = 365 * (2014-sim_start_year)
# add_InputEIR(cb,
#              monthlyEIRs=[x * EIR_scale_factor for x in monthly_profile],
#              nodes={'class': 'NodeSetNodeList', 'Node_List': [100000]},
#              start_day=EIR_start_day)


# Calibration-specific stuff:
sites = [zambia_calib_site(catch)]
# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
            ]
# Use OptimTool as next-point-algorithm
# optimtool = burnin_optimtool(params,
optimtool = OptimTool(params,
                      samples_per_iteration=samples_per_iteration,
                      center_repeats=1,
                      sigma_r=sigma_r)

calib_manager = CalibManager(name=experiment_name,
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
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
        cm.resume_calibration(iteration=0,
                              iter_step="analyze")