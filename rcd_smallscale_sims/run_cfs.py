
import os
import pandas as pd
import numpy as np
from dtk.tools.climate.ClimateGenerator import ClimateGenerator

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports import add_vector_migration_report
from malaria.reports.MalariaReport import add_summary_report, add_filtered_spatial_report, add_event_counter_report
from simtools.ModBuilder import ModFn, ModBuilder
from simtools.SetupParser import SetupParser

from gridded_sims.run.build_cb import kariba_ento
from rcd_smallscale_sims.interventions import add_simple_hs, chw_rcd_manager, rcd_followthrough

SetupParser.default_block = "HPC"
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_simulation
from simtools.Utilities.COMPSUtilities import create_suite

from rcd_smallscale_sims.build_cb import build_project_cb



def add_reports(cb):
    add_event_counter_report(cb, event_trigger_list=["Received_Treatment", "Received_Test", "Received_Campaign_Drugs", "Received_RCD_Drugs"], start=start,
                             duration=duration)

    cb.update_params({
        "Report_Event_Recorder": 1,
        "Report_Event_Recorder_Ignore_Events_In_List": 0,
        "Listed_Events": ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test", "Received_RCD_Drugs", "Received_Campaign_Drugs"],
        "Report_Event_Recorder_Events": ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test", "Received_RCD_Drugs", "Received_Campaign_Drugs"]
    })





start = 0
duration = 54*365
num_seeds = 1
vector_migration_values = np.array([10])  #10.**np.arange(-8, 2, 2)
interventions_on = False
testing = False


# suite_id = create_suite(suite_name="kariba_proact_v2")
suite_id = None




if testing:
    priority = "Highest"
    coreset = "emod_32cores"
else:
    priority = "Normal"
    coreset = "emod_abcd"

cb = build_project_cb(simulation_duration_days=duration)

f_sc_array = np.arange(6.5,9.6,0.1)
# f_sc_array = np.arange(5,9.6,0.2)
a_sc_array = f_sc_array + 0.8
larval_habitats_zipped = zip(f_sc_array, a_sc_array)
# kariba_ento(cb, a_sc=8, f_sc=8)
# cb.set_param("x_Vector_Migration", 1e-4) #fixme testing

if interventions_on:
    add_simple_hs(cb, u5_hs_rate=0.6)
    chw_rcd_manager(cb)
    rcd_followthrough(cb, coverage=1, delivery_method="MDA")

add_reports(cb)
#fixme TESTING-only reports:
if testing:
    add_summary_report(cb)
    add_filtered_spatial_report(cb, channels=["Population", "Blood_Smear_Parasite_Prevalence"], start=start,
                            end=(start + duration))
    add_vector_migration_report(cb)
    cb.set_param("Enable_Vector_Species_Report", 1)

#fixme SERIALIZING
cb.set_param("Serialization_Time_Steps", [50 * 365])




modlists = []

# new_modlist = [ModFn(rcd_followthrough, coverage, delivery_method)
#                for coverage in [1]
#                for delivery_method in ["MTAT", "MDA"]]
# modlists.append(new_modlist)

if num_seeds > 1:
    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    modlists.append(new_modlist)

# Vector migration sweep:
new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Vector_Migration_Local', x) for x in vector_migration_values]
modlists.append(new_modlist)

# Habitats sweep:
new_modlist = [ModFn(kariba_ento, habitat[0],habitat[1]) for habitat in larval_habitats_zipped]
modlists.append(new_modlist)

builder = ModBuilder.from_combos(*modlists)

if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)



    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name="smallscale_RCD_burnins",
                                exp_builder=builder,
                                suite_id=suite_id)

