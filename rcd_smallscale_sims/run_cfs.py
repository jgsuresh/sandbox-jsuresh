
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



def add_standard_reports(cb, inset_chart_mode="full_inset", start=0, include_counter=True):

    if include_counter:
        events_to_count = [
            "Received_Treatment",
            "Received_Test",
            "Received_Campaign_Drugs",
            "Received_RCD_Drugs"]
        # "New_Infection",
        # "New_Clinical_Case",

        add_event_counter_report(cb,
                                 event_trigger_list=events_to_count,
                                 start=start)

    cb.update_params({
        "Listed_Events": ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test", "Received_RCD_Drugs",
                          "Received_Campaign_Drugs"]
    })

    add_summary_report(cb)

    if inset_chart_mode == "none":
        cb.update_params({"Enable_Default_Reporting": 0})
    elif inset_chart_mode == "full_inset":
        cb.update_params({"Enable_Default_Reporting": 1})
    elif inset_chart_mode == "filtered_for_final_year":
        # Replace InsetChart with a filtered report
        cb.update_params({"Enable_Default_Reporting": 0})
        add_filtered_report(cb, start=365*3, description="Final_Year")


def add_testing_reports(cb, spatial_reports_on=True, vector_migration_report_on=True):
    if spatial_reports_on:
        add_filtered_spatial_report(cb, channels=["Population", "Blood_Smear_Parasite_Prevalence"], start=start,
                                    end=(start + duration))
    if vector_migration_report_on:
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

# Interventions
def toggle_rcd(cb, rcd_on):
    if rcd_on:
        chw_rcd_manager(cb, days_between_followups=days_between_rcd_followups)
        rcd_followthrough(cb,
                          followup_sweep_coverage=rcd_sweep_node_coverage,
                          delivery_method=rcd_delivery_method)
    return {"rcd_on": rcd_on}



if __name__ == "__main__":
    testing = False
    num_seeds = 100
    sweep_over_healthseeking = False
    sweep_over_rcd_onoff = False
    sweep_over_vector_migration = False
    # sweep_over_larval_habitats = False
    rcd_delivery_method = "MTAT"
    exp_name = "smallscale_MTAT_q1"
    use_asset = False
    running_burnin = False
    chw_performance = "low"

    if chw_performance == "high":
        days_between_rcd_followups = 7
        rcd_sweep_node_coverage = 1
    elif chw_performance == "low":
        days_between_rcd_followups = 9
        rcd_sweep_node_coverage = 0.2


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

    cb = build_project_cb(simulation_duration_days=duration)


    if use_asset:
        print("Using asset")
        asset_collection_id = "39be2a33-4d5a-ea11-a2c5-c4346bcb1550"
        cb.set_collection_id(asset_collection_id)

    # f_sc_array = np.array([7.6, 7.7, 7.8, 7.9, 8.0])
    if testing:
        f_sc_array = np.array([7.4])
    else:
        # f_sc_array = np.arange(6.65, 8, 0.01)
        # f_sc_array = f_sc_array[::2] # subsample, for faster running
        f_sc_array = np.linspace(6.64, 8, 69, endpoint=True)

    a_sc_array = f_sc_array + 0.8



    larval_habitats_zipped = zip(f_sc_array, a_sc_array)







    # Reporting
    inset_mode = "filtered_for_final_year"
    if running_burnin:
        include_counter = False
    else:
        include_counter = True


    add_standard_reports(cb, start=start, inset_chart_mode=inset_mode, include_counter=include_counter)
    if testing:
        add_testing_reports(cb)


    #SERIALIZING
    if running_burnin:
        cb.set_param("Serialization_Time_Steps", [50 * 365])

    recurring_outbreak(cb, outbreak_fraction=0.005)


    modlists = []


    # print("Sweeping over MTAT vs MDA")
    # chw_rcd_manager(cb, followups_per_month=chw_followups_per_month, budget_followups_by_week=budget_followups_by_week)
    # new_modlist = [ModFn(rcd_followthrough, coverage, delivery_method)
    #                for coverage in [1]
    #                for delivery_method in ["MTAT", "MDA"]]
    # modlists.append(new_modlist)

    if sweep_over_rcd_onoff:
        print("Toggling RCD on or off")
        new_modlist = [ModFn(toggle_rcd, rcd_on) for rcd_on in [False, True]]
        modlists.append(new_modlist)
    else:
        print("Implementing RCD WITHOUT sweep")
        chw_rcd_manager(cb, days_between_followups=days_between_rcd_followups)
        rcd_followthrough(cb,
                          followup_sweep_coverage=rcd_sweep_node_coverage,
                          delivery_method=rcd_delivery_method)

    if sweep_over_healthseeking:
        print("Sweeping over health-seeking rates")
        new_modlist = [ModFn(add_simple_hs, coverage) for coverage in [0.6, 0.8, 1.0]]
        modlists.append(new_modlist)
    else:
        print("Implementing HS WITHOUT sweep")
        add_simple_hs(cb, u5_hs_rate=0.6)


    if num_seeds > 1:
        new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
        modlists.append(new_modlist)

    # Vector migration sweep:
    if sweep_over_vector_migration:
        vector_migration_values = np.array([0,1e-5,1e-4,1e-3,1e-2,1e-1])
        new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Vector_Migration_Local', x) for x in vector_migration_values]
        modlists.append(new_modlist)
    else:
        vector_migration_values = np.array([10])
        new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Vector_Migration_Local', x) for x in vector_migration_values]
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
                       pre_process_burnin("output/burnins_sim_map_20200317.csv", larval_habitats_zipped).items()]
        modlists.append(new_modlist)
    # else:



    builder = ModBuilder.from_combos(*modlists)


    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)


    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=exp_name,
                                exp_builder=builder)
                                # max_creator_processes=8)

