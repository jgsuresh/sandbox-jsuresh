
import os
import pandas as pd
import numpy as np
from dtk.interventions.outbreakindividual import recurring_outbreak
from dtk.tools.climate.ClimateGenerator import ClimateGenerator

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports import add_vector_migration_report
from malaria.reports.MalariaReport import add_summary_report, add_filtered_spatial_report, add_event_counter_report, \
    add_filtered_report
from simtools.ModBuilder import ModFn, ModBuilder
from simtools.SetupParser import SetupParser

from gridded_sims.run.build_cb import kariba_ento
from rcd_smallscale_sims.interventions import add_simple_hs, chw_rcd_manager, rcd_followthrough
from rcd_smallscale_sims.organize_sims import draw_from_burnin_using_vector_habs

SetupParser.default_block = "HPC"
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_simulation, retrieve_experiment
from simtools.Utilities.COMPSUtilities import create_suite



from rcd_smallscale_sims.build_cb import build_project_cb



def add_standard_reports(cb):
    add_event_counter_report(cb, event_trigger_list=["Received_Treatment", "Received_Test", "Received_Campaign_Drugs", "Received_RCD_Drugs"], start=start,
                             duration=duration)

    cb.update_params({
        "Listed_Events": ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test", "Received_RCD_Drugs",
                          "Received_Campaign_Drugs"]
    })

    # Replace InsetChart with a filtered report
    cb.update_params({"Enable_Default_Reporting": 0})
    add_filtered_report(cb, start=365*3, description="Final_Year")


def add_testing_reports(cb):
    add_summary_report(cb)
    add_filtered_spatial_report(cb, channels=["Population", "Blood_Smear_Parasite_Prevalence"], start=start,
                                end=(start + duration))
    add_vector_migration_report(cb)
    cb.set_param("Enable_Vector_Species_Report", 1)

    cb.update_params({
        "Report_Event_Recorder": 1,
        "Report_Event_Recorder_Ignore_Events_In_List": 0,
        "Report_Event_Recorder_Events": ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test",
                                         "Received_RCD_Drugs", "Received_Campaign_Drugs"]
    })

    # InsetChart
    cb.update_params({"Enable_Default_Reporting": 1})

# def add_assets(cb, asset_exp_id):
#     print("retrieving asset experiment")
#     asset_expt = retrieve_experiment(asset_exp_id)
#     template_asset = asset_expt.simulations[0].tags
#     cb.set_exe_collection(template_asset["exe_collection_id"])
#     cb.set_dll_collection(template_asset["dll_collection_id"])
#     cb.set_input_collection(template_asset["input_collection_id"])





start = 0
duration = 4*365
num_seeds = 100
vector_migration_values = np.array([10])
healthseeking_on = True
rcd_on = False
rcd_delivery_method = "MTAT"
testing = False
draw_from_burnins = True
chw_followups_per_month = 4
budget_followups_by_week = True
exp_name = "smallscale_HS_sweep_no_RCD"
# asset_exp_id = "88afbd76-8d62-ea11-a2c5-c4346bcb1550"
asset_collection_id = "49b76c38-f562-ea11-a2c5-c4346bcb1550"

if testing:
    priority = "Highest"
    coreset = "emod_32cores"
else:
    priority = "Normal"
    coreset = "emod_abcd"

cb = build_project_cb(simulation_duration_days=duration)
# add_assets(cb, asset_exp_id)
cb.set_collection_id(asset_collection_id)

# f_sc_array = np.array([7.6, 7.7, 7.8, 7.9, 8.0])
f_sc_array = np.arange(6.65,8,0.01)
f_sc_array = f_sc_array[::2] # subsample, for faster running
a_sc_array = f_sc_array + 0.8

larval_habitats_zipped = zip(f_sc_array, a_sc_array)

if healthseeking_on:
    add_simple_hs(cb, u5_hs_rate=0.6)
if rcd_on:
    chw_rcd_manager(cb, followups_per_month=chw_followups_per_month, budget_followups_by_week=budget_followups_by_week)
    rcd_followthrough(cb, coverage=1, delivery_method=rcd_delivery_method)

add_standard_reports(cb)
if testing:
    add_testing_reports(cb)


#SERIALIZING
if not draw_from_burnins:
    cb.set_param("Serialization_Time_Steps", [50 * 365])

recurring_outbreak(cb, outbreak_fraction=0.005)


modlists = []

# new_modlist = [ModFn(rcd_followthrough, coverage, delivery_method)
#                for coverage in [1]
#                for delivery_method in ["MTAT", "MDA"]]
# modlists.append(new_modlist)


# print("Sweeping over health-seeking rates")
# new_modlist = [ModFn(add_simple_hs, coverage) for coverage in [0.8, 1.0]]
# modlists.append(new_modlist)

if num_seeds > 1:
    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    modlists.append(new_modlist)

# Vector migration sweep:
new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Vector_Migration_Local', x) for x in vector_migration_values]
modlists.append(new_modlist)

# Habitats sweep:
if draw_from_burnins:
    new_modlist = [ModFn(draw_from_burnin_using_vector_habs, habitat[0], habitat[1]) for habitat in larval_habitats_zipped]
    modlists.append(new_modlist)
else:
    new_modlist = [ModFn(kariba_ento, habitat[0], habitat[1]) for habitat in larval_habitats_zipped]
    modlists.append(new_modlist)


builder = ModBuilder.from_combos(*modlists)

if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)


    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=exp_name,
                                exp_builder=builder)

