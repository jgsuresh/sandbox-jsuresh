
"""
Perform staged calibration of larval habitat parameters for a given catchment in Mozambique

Stage 1: HF-level fit for max larval capacity parameters of arabiensis and funestus.
  Serializes files to save time on burn-ins
Stage 2: Barrio-level fit for vector habitat param multiplication factors, which draws serialization files and HF-level fit params from Stage 1
"""



import sys

# sys.path.append('C:/Code/malaria-toolbox/input_file_generation/')
# sys.path.append('C:/Code/malaria-toolbox/sim_output_processing/')
base = '../../'
sys.path.append(base + '/src/analysis/')
sys.path.append(base + 'src/sims/')


import matplotlib
matplotlib.use('Agg')
import pandas as pd
import copy
import os.path
import numpy as np

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from mozambique_experiments import MozambiqueExperiment
from experiment_setup import GriddedInputFilesCreator
from simtools.SetupParser import SetupParser
from dtk.interventions.habitat_scale import scale_larval_habitats

from GriddedCalibSite import GriddedCalibSite
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from dtk.vector.species import set_larval_habitat, set_species_param
from malaria.reports.MalariaReport import add_filtered_spatial_report, add_filtered_report, add_event_counter_report
from dtk.interventions.migrate_to import add_migration_event

# Key parameters:
hs_version = 1
importation_version = 0
num_cores = 8
priority = "Lowest"
catch_num = 6
scratch_or_resume = "resume"
max_iterations = 7

"""
pop_version: 0 for base population, 1 for 120% population. 
hs_version: 0 for Caitlin, 1 for Amelia
nmf_version: HERE
importation_version: HERE

calib_stage == 0: Build input files
calib_stage == 1: Burn-ins, with HFCA-level calibration (2 parameters)
calib_stage == 1: Serialized, with HFCA-level calibration (2 parameters)
calib_stage == 2: Serialized, with bairro-level calibration (N_bairro parameters)
"""

mozamb_catch_list = ["Chichuco","Chicutso","Magude-Sede-Facazissa","Mahel","Mapulanguene","Moine","Motaze","Panjane-Caputine"]
catch = mozamb_catch_list[catch_num]
print(catch)



samples_per_iteration = 100
sim_runs_per_param_set = 2


# ==============================================================
coreset = "emod_abcd"
# coreset = "emod_32cores"
parser_location = "HPC"

exp_name = 'Calib_{}_burnin'.format(catch)
burnin_LL_all_path = exp_name + "/_plots/LL_all.csv"


end_year = 2020
serialize_year = 2009 # Gives 1 year of buffer
nonburnin_sim_length_years = 11
burnin_sim_length_years = 65 # updated, to make the 3 year spline loop-able and match in 2015-2017
nonburnin_sim_start_year = end_year - nonburnin_sim_length_years
burnin_sim_start_year = end_year - burnin_sim_length_years

burnin_write_time = 365 * (serialize_year - burnin_sim_start_year)
serialize_write_time = 365 * (serialize_year - nonburnin_sim_start_year)


grid_pop_csv_file = base + 'data/mozambique/grid_population.csv'
healthseek_fn = base + 'data/mozambique/grid_all_healthseek_events_friction.csv'
itn_fn = base + 'data/mozambique/grid_all_itn_events.csv'
irs_fn = base + 'data/mozambique/grid_all_irs_events.csv'
msat_fn = None
mda_fn = base + 'data/mozambique/grid_all_mda_events.csv'
stepd_fn = base + 'data/mozambique/grid_all_react_events.csv'

bairro_df = MozambiqueExperiment.find_bairros_for_this_catchment(catch)

# Build config-builder:
mozamb_exp = MozambiqueExperiment(base,
                                  catch,
                                  catch,
                                  healthseek_fn=healthseek_fn,
                                  itn_fn=itn_fn,
                                  irs_fn=irs_fn,
                                  msat_fn=msat_fn,
                                  mda_fn=mda_fn,
                                  stepd_fn=stepd_fn,
                                  start_year=burnin_sim_start_year,
                                  sim_length_years=burnin_sim_length_years,
                                  immunity_mode="naive",
                                  num_cores=num_cores,
                                  parser_location=parser_location,
                                  EIR_scale_factor=0.25)


# Create necessary input files
EIR_node_label = 100000

if False:
    IPs = [
        {'Property': 'TravelerStatus',
         'Values': ['IsTraveler',
                    'NotTraveler'],
         'Initial_Distribution': [0.07, 0.93],
         'Transitions': []}
    ]


    file_creator = GriddedInputFilesCreator(base,
                                            catch,
                                            mozamb_exp.desired_cells,
                                            mozamb_exp.cb,
                                            grid_pop_csv_file,
                                            region=mozamb_exp.region,
                                            start_year=burnin_sim_start_year,
                                            sim_length_years=burnin_sim_length_years,
                                            immunity_mode="naive",
                                            larval_param_func=mozamb_exp.larval_params_func_for_calibration,
                                            EIR_node_label=EIR_node_label,
                                            EIR_node_lat=-25.045777,
                                            EIR_node_lon=32.786861,
                                            IP_list=IPs,
                                            generate_climate_files=False,
                                            exclude_nodes_from_regional_migration=[EIR_node_label]
                                            )





# Calibration-specific stuff:
sites = [GriddedCalibSite(catch)]
# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
            ]

def best_run_so_far():
    # Return anything one would want to know about the best runs so far:
    best_from_stage = None
    best_run_dir = None

    a_sc_burnin = None
    f_sc_burnin = None

    a_sc_best = None
    f_sc_best = None


    # Identify best run across burnins, and current:
    try:
        LL_burnin = pd.read_csv(burnin_LL_all_path)
        best_LL = LL_burnin['total'].iloc[-1]
        best_run_dir = LL_burnin['outputs'].iloc[-1]
        best_run_dir = best_run_dir.split(',')[0]
        best_from_stage = 1

        a_sc_burnin = LL_burnin['arabiensis_scale'].iloc[-1]
        f_sc_burnin = LL_burnin['funestus_scale'].iloc[-1]

        a_sc_best = a_sc_burnin
        f_sc_best = f_sc_burnin
    except:
        pass

    dd = {}
    dd['best_from_stage'] = best_from_stage
    dd['best_run_dir'] = best_run_dir
    dd['a_sc_burnin'] = a_sc_burnin
    dd['f_sc_burnin'] = f_sc_burnin
    dd['a_sc_best'] = a_sc_best
    dd['f_sc_best'] = f_sc_best

    return dd


dd = best_run_so_far()

# HFCA-level params
params = [
    {
        'Name': 'arabiensis_scale',
        'Dynamic': True,
        'MapTo': 'arabiensis_scale',
        'Guess': 9.5,
        'Min': 8.5,
        'Max': 11
    },
    {
        'Name': 'funestus_scale',
        'Dynamic': True,
        'MapTo': 'funestus_scale',
        'Guess': 10.5,
        'Min': 8.5,
        'Max': 11
    }
]


def serialization_setup(cb):
    # Serialization:

    burnin=True
    sim_start_year = burnin_sim_start_year
    sim_length_years = burnin_sim_length_years

    sim_filter_start_time = 365*(burnin_sim_length_years - (end_year-serialize_year))
    sim_filter_duration = 365 * (end_year - serialize_year)

    serialization_write_time = burnin_write_time
    projection_write_time = serialization_write_time + 365 * 9 + 90  # April 1, 2018.


    # Now that cb has interventions added, give it the needed serialization information:
    cb.update_params({"Serialization_Time_Steps": [serialization_write_time, projection_write_time]})

    sim_time_dict = {}
    sim_time_dict["sim_start_year"] = sim_start_year
    sim_time_dict["sim_length_years"] = sim_length_years
    sim_time_dict["sim_filter_start_time"] = sim_filter_start_time
    sim_time_dict["sim_filter_duration"] = sim_filter_duration
    sim_time_dict["burnin"] = burnin

    return sim_time_dict


def add_interventions_and_reports(cb,sim_time_dict):
    sim_start_year = sim_time_dict["sim_start_year"]
    sim_length_years = sim_time_dict["sim_length_years"]
    sim_filter_start_time = sim_time_dict["sim_filter_start_time"]
    sim_filter_duration = sim_time_dict["sim_filter_duration"]

    mozamb_exp.start_year = sim_start_year
    mozamb_exp.sim_length_years = sim_length_years
    mozamb_exp.implement_baseline_healthseeking(cb)
    mozamb_exp.implement_interventions(cb,True,True,False,True,True)

    all_nodes = list(mozamb_exp.desired_cells)

    cb.update_params({
        'x_Regional_Migration': 0.03,
    })
    add_migration_event(cb,
                        nodeto=100000,
                        coverage=0.5,
                        repetitions=500,
                        tsteps_btwn=30,
                        duration_of_stay=3,
                        duration_before_leaving_distr_type='UNIFORM_DURATION',
                        duration_before_leaving=0,
                        duration_before_leaving_2=30,
                        nodesfrom={'class': 'NodeSetNodeList',
                                   'Node_List': all_nodes},
                        ind_property_restrictions=[{'TravelerStatus': 'IsTraveler'}])


    #new entomology:
    # Arabiensis
    set_species_param(cb, 'arabiensis', 'Indoor_Feeding_Fraction', 0.5)
    set_species_param(cb, 'arabiensis', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'arabiensis', 'Anthropophily', 0.65)
    # Funestus
    set_species_param(cb, 'funestus', "Indoor_Feeding_Fraction", 0.9)
    set_species_param(cb, 'funestus', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'funestus', 'Anthropophily', 0.65)

    # Add specific reports that we want (have to do it here because we need to know what times to filter for):

    # Add filter report that has same length for both burn-in and non-burn-in runs (2010-2020).
    # This version is for grid-level prevalence comparison
    add_filtered_spatial_report(cb,
                                start=sim_filter_start_time,
                                end=(sim_filter_start_time+sim_filter_duration),
                                # channels=['Population', 'New_Diagnostic_Prevalence'])
                                channels=['Population', 'True_Prevalence']) # 'New_Clinical_Cases','New_Infections'

    # Add filter that has same length for both burn-in and non-burn-in runs (2010-2020)
    # This version is for HF-level incidence comparison.  Add a similar report for the migration node

    add_filtered_report(cb,
                        start=sim_filter_start_time,
                        end=(sim_filter_start_time + sim_filter_duration),
                        nodes=all_nodes)
    add_filtered_report(cb,
                        start=sim_filter_start_time,
                        end=(sim_filter_start_time + sim_filter_duration),
                        nodes=[EIR_node_label],
                        description='Work')


    # # Add filter report for prevalence in each bairro
    foo = bairro_df.groupby('bairro')

    for (bairro_num,df) in foo:
        add_filtered_report(cb,
                            start=sim_filter_start_time,
                            end=(sim_filter_start_time + sim_filter_duration),
                            nodes=[int(x) for x in df['grid_cell'].values],
                            description=str(int(bairro_num)))

    # Add counter report for clinical incidence
    add_event_counter_report(cb,
                             event_trigger_list=['Received_Treatment', 'Received_IRS', 'Received_Campaign_Drugs', 'Received_RCD_Drugs', 'Bednet_Got_New_One', 'Received_Test'],
                             start=sim_filter_start_time,
                             duration=sim_filter_duration)



    # Add counter for new infections in work node vs all other nodes:
    # add_event_counter_report(cb,
    #                          event_trigger_list=['NewInfectionEvent'],
    #                          description='WorkInfections',
    #                          start=sim_filter_start_time,
    #                          duration=sim_filter_duration,
    #                          nodes={'Node_List': all_nodes, "class": "NodeSetNodeList"})
    #
    # add_event_counter_report(cb,
    #                          event_trigger_list=['NewInfectionEvent'],
    #                          description='NonworkInfections',
    #                          start=sim_filter_start_time,
    #                          duration=sim_filter_duration,
    #                          nodes={'Node_List': [EIR_node_label], "class": "NodeSetNodeList"})



def magude_3_yr_spline(spline_fn):
    # Read spline directly from mini-CSV files generated by Jaline/Caitlin

    def load_raw_spline(csv_df):
        spline = np.zeros(36)
        raw_spline = np.array(csv_df["Values"])
        spline[4:35] = raw_spline[1:-1]  # Throw out first and last entry
        return spline

    def fill_out_spline(spline):
        spline[0:4] = 0.5 * (spline[12:16] + spline[24:28])
        spline[35] = 0.5 * (spline[11] + spline[23])
        return spline

    df = pd.read_csv(spline_fn)
    spline = fill_out_spline(load_raw_spline(df))

    # Return associated times:
    times_1yr = np.array(
        [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167, 334.583])
    times = np.append(times_1yr, times_1yr + 365)
    times = np.append(times, times_1yr + 365 * 2)
    times = list(times)

    return [times, list(spline)]



def map_sample_to_model_input(cb, sample):

    sim_time_dict = serialization_setup(cb)
    add_interventions_and_reports(cb, sim_time_dict)

    dd = best_run_so_far()
    # =====================================================================================
    # Global habitats
    a_sc = sample['arabiensis_scale']
    f_sc = sample['funestus_scale']

    # LOAD FROM SPLINE:
    spline_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/Mozambique/entomology_calibration/"
    [times, funest_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180608/minicsv/Three_funestus_LifeAdj_rank0.csv'))

    if catch == "Magude-Sede-Facazissa":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180608/minicsv/Magude-Sede_gambiae_LifeAdj_rank0.csv'))
    elif catch == "Chichuco":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Chichuco_gambiae_frankenspline.csv'))
    elif catch == "Chicutso":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Chicutso_gambiae_frankenspline.csv'))
    elif catch == "Mapulanguene":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Mapulanguene_gambiae_frankenspline.csv'))
    elif catch == "Motaze":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Motaze_gambiae_frankenspline.csv'))
    elif catch == "Panjane-Caputine":
        [times, arab_spline] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Panjane_gambiae_frankenspline.csv'))
    elif catch == "Moine" or catch == "Mahel":
        [times, arab_spline_pc] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Panjane_gambiae_frankenspline.csv'))
        [times, arab_spline_ch] = magude_3_yr_spline(os.path.join(spline_base, 'Multi_year_calibration_by_HFCA_180808/minicsv/Chichuco_gambiae_frankenspline.csv'))
        arab_spline = list((np.array(arab_spline_pc) + np.array(arab_spline_ch))/2.)


    hab = {
        'arabiensis': {
            "LINEAR_SPLINE": {
                 "Capacity_Distribution_Number_Of_Years": 3,
                 "Capacity_Distribution_Over_Time": {
                 # "Capacity_Distribution_Per_Year": {
                    "Times": times,
                    "Values": arab_spline
                },
                "Max_Larval_Capacity": pow(10,a_sc)
            }
        },
        'funestus': {
            "LINEAR_SPLINE": {
                "Capacity_Distribution_Number_Of_Years": 3,
                "Capacity_Distribution_Over_Time": {
                # "Capacity_Distribution_Per_Year": {
                    "Times": times,
                    "Values": funest_spline
                },
                "Max_Larval_Capacity": pow(10, f_sc)
                # "Max_Larval_Capacity": pow(10,a_sc)/arab_funest_ratio
            }
        }
    }


    set_larval_habitat(cb, hab)


    # # FOR TESTING ONLY:
    # if mode == 'fast':
    #     cb.set_param('x_Temporary_Larval_Habitat',0)
    #     cb.set_param('x_Regional_Migration',0)


    return sample


sigma_r = 0.1
optimtool = OptimTool(params,
                      samples_per_iteration=samples_per_iteration,
                      center_repeats=1,
                      sigma_r=sigma_r)

calib_manager = CalibManager(name=exp_name,
                             config_builder=mozamb_exp.cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=sim_runs_per_param_set,
                             max_iterations=max_iterations,
                             plotters=plotters)

run_calib_args = {
    "calib_manager": calib_manager
}



if __name__ == "__main__":
    if parser_location == "LOCAL":
        SetupParser.init("LOCAL")

    else:
        SetupParser.init()

        SetupParser.set("HPC", "priority", priority)
        SetupParser.set("HPC", "node_group", coreset)

    cm = run_calib_args["calib_manager"]

    if scratch_or_resume == "scratch":
        cm.run_calibration()
    elif scratch_or_resume == "resume":
        cm.resume_calibration(iteration=0, iter_step='analyze')

