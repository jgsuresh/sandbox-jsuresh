
"""
Perform staged calibration of larval habitat parameters for a given catchment in Mozambique

Stage 1: HF-level fit for max larval capacity parameters of arabiensis and funestus.
  Serializes files to save time on burn-ins
Stage 2: Barrio-level fit for vector habitat param multiplication factors, which draws serialization files and HF-level fit params from Stage 1
"""



import sys
import copy

# sys.path.append('C:/Code/malaria-toolbox/input_file_generation/')
# sys.path.append('C:/Code/malaria-toolbox/sim_output_processing/')
from dtk.utils.reports import add_human_migration_report
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder

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

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    # Key parameters:
    hs_version = 1
    importation_version = 0
    num_cores = 1
    priority = "BelowNormal"
    catch_num = 1


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




    # ==============================================================
    coreset = "emod_32cores"
    parser_location = "HPC"

    exp_name = '{}_migrcheck'.format(catch)

    bairro_df = MozambiqueExperiment.find_bairros_for_this_catchment(catch)

    # Build config-builder:
    mozamb_exp = MozambiqueExperiment(base,
                                      catch,
                                      catch,
                                      start_year=1955,
                                      immunity_mode="naive",
                                      num_cores=num_cores,
                                      parser_location=parser_location,
                                      EIR_scale_factor=0.25)


    cb = copy.deepcopy(mozamb_exp.cb)

    # For migration checking run
    add_human_migration_report(cb)
    # Fix human population for simplicity
    cb.update_params({
        "Enable_Natural_Mortality": 0,
        "Enable_Nondisease_Mortality": 0,
        "Enable_Birth": 0
    })
    # TURNING OFF REGIONAL MIGRATION FOR CLARITY:
    cb.params['Enable_Regional_Migration'] = 0

    cb.params['Simulation_Duration'] = 365

    # New changes (July 2018):
    # 10x lower local migration
    cb.update_params({
        "x_Local_Migration": 5,
        "Local_Migration_Roundtrip_Probability": 1.0,
        'x_Regional_Migration': 0.03,
        "Regional_Migration_Roundtrip_Probability": 1.0,
    })



    all_nodes = list(mozamb_exp.desired_cells)

    cb.params['logLevel_JsonConfigurable'] = "WARNING"

    #travelers:
    cb.params['Disable_IP_Whitelist'] = 1
    add_migration_event(cb,
                        nodeto=100000,
                        # coverage=0.5,
                        coverage=0,
                        repetitions=500,
                        # tsteps_btwn=30,
                        tsteps_btwn=3000,
                        duration_of_stay=3,
                        duration_before_leaving_distr_type='UNIFORM_DURATION',
                        duration_before_leaving=0,
                        duration_before_leaving_2=30,
                        nodesfrom={'class': 'NodeSetNodeList',
                                   'Node_List': all_nodes},
                        ind_property_restrictions=[{'TravelerStatus': 'IsTraveler'}])

    add_filtered_report(cb,
                        nodes=all_nodes,
                        description='Catchment')

    add_filtered_report(cb,
                        nodes=[100000],
                        description='Work')


    # Add counter report for clinical incidence
    # add_event_counter_report(cb,
    #                          event_trigger_list=['Received_Treatment', 'Received_IRS', 'Received_Campaign_Drugs', 'Received_RCD_Drugs', 'Bednet_Got_New_One', 'Received_Test'])



    # Add counter for new infections in work node vs all other nodes:
    add_event_counter_report(cb,
                             event_trigger_list=['NewInfectionEvent'],
                             description='WorkInfections',
                             # start=sim_filter_start_time,
                             # duration=sim_filter_duration,
                             nodes={'Node_List': all_nodes, "class": "NodeSetNodeList"})

    add_event_counter_report(cb,
                             event_trigger_list=['NewInfectionEvent'],
                             description='NonworkInfections',
                             # start=sim_filter_start_time,
                             # duration=sim_filter_duration,
                             nodes={'Node_List': [100000], "class": "NodeSetNodeList"})


    # Add migration events reporter
    # cb.update_params({
    #     "Report_Event_Recorder": 1,
    #     "Report_Event_Recorder_Ignore_Events_In_List": 0,
    #     "Listed_Events": ["Bednet_Got_New_One","Bednet_Using","Bednet_Discarded"],
    #     "Report_Event_Recorder_Events": ["Immigrating", "Emigrating"]
    # })
    cb.params['Report_Event_Recorder'] = 1
    cb.params["Report_Event_Recorder_Ignore_Events_In_List"] = 0
    cb.params["Listed_Events"] = ["Bednet_Got_New_One","Bednet_Using","Bednet_Discarded"]
    cb.params["Report_Event_Recorder_Events"] = ["Immigrating", "Emigrating"]

    # run_sim_args is what the `dtk run` command will look for
    run_sim_args = {
        'exp_name': exp_name,
        'config_builder': cb
    }


    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    # exp_manager = ExperimentManagerFactory.init()
    # exp_manager.run_simulations(**run_sim_args)
    # # Wait for the simulations to be done
    # exp_manager.wait_for_finished(verbose=True)
    # assert (exp_manager.succeeded())

    modlists = []
    builder = ModBuilder.from_combos(*modlists)
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb, exp_name=exp_name, exp_builder=builder)

    # zambia_exp.submit_experiment(num_seeds=1)
