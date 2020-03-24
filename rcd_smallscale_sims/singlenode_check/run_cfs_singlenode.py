
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
from rcd_smallscale_sims.organize_sims import draw_from_burnin_using_vector_habs, \
    draw_from_burnin_using_vector_habitats_BENOIT, pre_process_burnin

SetupParser.default_block = "HPC"
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_simulation, retrieve_experiment
from simtools.Utilities.COMPSUtilities import create_suite



from rcd_smallscale_sims.build_cb import build_project_cb
from rcd_smallscale_sims.run_cfs import add_standard_reports, add_testing_reports



testing = False
num_seeds = 100
rcd_delivery_method = "MTAT"
exp_name = "smallscale_MTAT_singlenode"
running_burnin = False


# Fiducial values:
chw_followups_per_month = 4
budget_followups_by_week = True



start = 0
if running_burnin:
    duration = 54 * 365  # 54 years for burnin
else:
    duration = 4*365


if testing:
    priority = "Highest"
    coreset = "emod_32cores"
    # coreset = "emod_abcd"
else:
    priority = "BelowNormal"
    coreset = "emod_abcd"

cb = build_project_cb(simulation_duration_days=duration,
                      vector_migration_on=False,
                      demo_name="demo_750person_singlenode.json")

if testing:
    f_sc_array = np.array([7.4])
else:
    f_sc_array = np.linspace(6.64, 8, 69, endpoint=True)

a_sc_array = f_sc_array + 0.8



larval_habitats_zipped = zip(f_sc_array, a_sc_array)


# Reporting
if running_burnin:
    include_counter = False
    inset_mode = "none"
else:
    include_counter = True
    inset_mode = "filtered_for_final_year"


add_standard_reports(cb, start=start, inset_chart_mode=inset_mode, include_counter=include_counter)
if testing:
    add_testing_reports(cb, spatial_reports_on=False, vector_migration_report_on=False)


#SERIALIZING
if running_burnin:
    cb.set_param("Serialization_Time_Steps", [50 * 365])

recurring_outbreak(cb, outbreak_fraction=0.005)

modlists = []


if running_burnin:
    print("NO INTERVENTIONS ON")
else:
    print("INTERVENTIONS ON")
    chw_rcd_manager(cb, followups_per_month=chw_followups_per_month, budget_followups_by_week=budget_followups_by_week)
    rcd_followthrough(cb, followup_sweep_coverage=25/750, delivery_method=rcd_delivery_method)
    add_simple_hs(cb, u5_hs_rate=0.6)



if num_seeds > 1:
    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    modlists.append(new_modlist)


# Habitats sweep:

# if sweep_over_larval_habitats:
if running_burnin:
    new_modlist = [ModFn(kariba_ento, habitat[0], habitat[1]) for habitat in larval_habitats_zipped]
    modlists.append(new_modlist)
else:
    # new_modlist = [ModFn(draw_from_burnin_using_vector_habs, habitat[0], habitat[1]) for habitat in larval_habitats_zipped]
    new_modlist = [ModFn(draw_from_burnin_using_vector_habitats_BENOIT, habitats, serialization)
                   for habitats, serialization in
                   pre_process_burnin("../output/burnins_sim_map_singlenode_20200317.csv", larval_habitats_zipped).items()]
    modlists.append(new_modlist)
# else:



builder = ModBuilder.from_combos(*modlists)

if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)


    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=exp_name,
                                exp_builder=builder)
                                # max_creator_processes=8)

