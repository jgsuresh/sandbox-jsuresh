from dtk.interventions.ivermectin import add_ivermectin
from malaria.reports.MalariaReport import add_filtered_report, add_filtered_spatial_report, add_event_counter_report
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_experiment

SetupParser.default_block = "HPC"
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

from malaria.interventions.malaria_drug_campaigns import add_drug_campaign

from gridded_sims.run.build_cb import *
from gridded_sims.run.interventions import add_all_interventions, preload_intervention_csvs, add_intervention_combos, add_mda
from gridded_sims.run.reports import add_all_reports


from gridded_sims.calib.calib_helpers import set_ento

from gridded_sims.ivermectin_paper.simplified_ento import catch_1_yr_spline

def add_filtered_reports(cb, catch, start=0, duration=10000000):
    add_filtered_spatial_report(cb, channels=["Population", "True_Prevalence"], start=start, end=(start + duration))

    # Filtered report just for work node, and just for catchment:
    regional_EIR_node_label = 100000
    catch_node_ids = find_cells_for_this_catchment(catch)

    add_filtered_report(cb, nodes=[regional_EIR_node_label], description='Work', start=start,
                        end=(start + duration))
    add_filtered_report(cb, nodes=catch_node_ids, description='Catchment', start=start,
                        end=(start + duration))


if __name__ == "__main__":
    # Run parameters:
    catch = "Magude-Sede-Facazissa"
    num_cores = 2
    num_seeds = 10
    priority = "Normal"
    coreset = "emod_abcd"
    # priority = "Highest"
    # coreset = "emod_32cores"
    # ====================================================================================================================

    experiment_name = "MSF_intervention_sweep"
    arab_times, arab_spline = catch_1_yr_spline(catch, "gambiae")
    funest_times, funest_spline = catch_1_yr_spline(catch, "funestus")

    cb = build_project_cb()
    catchment_cb_params(cb, catch)
    # cb.set_param("x_Regional_Migration", 0.0081)

    # Draw from burnin:
    # serialized_file_path = "C:/Users/jsuresh/Projects/malaria-mz-magude/gridded_sims/ivermectin_paper/burnin/one_year_spline"
    serialized_file_path = "//internal.idm.ctr/IDM/home/jsuresh/input/magude_ivermectin/2019-02-08/one_year_spline"
    cb.update_params({
        'Serialized_Population_Path': serialized_file_path,
        'Serialized_Population_Filenames': ['state-19710-000.dtk', 'state-19710-001.dtk']
    })

    # Burnin serialized at 2009.  So current run, which goes to beginning of 2019, has run duration of 10 years:
    sim_start_date = "2009-01-01"
    cb.set_param("Simulation_Duration", 10 * 365)
    end_year = 2019

    ivm_interventions_folder = os.path.join(project_folder, "dtk_simulation_input/mozambique/ivermectin_paper/")
    itn_simplified = os.path.join(ivm_interventions_folder, "grid_all_itn_events.csv")
    irs_simplified = os.path.join(ivm_interventions_folder, "grid_all_irs_events.csv")
    mda_simplified = os.path.join(ivm_interventions_folder, "grid_all_mda_events.csv")
    intervention_df_dict = preload_intervention_csvs(catch, sim_start_date,
                                                     itn_file=itn_simplified,
                                                     irs_file=irs_simplified,
                                                     mda_file=mda_simplified)
    add_intervention_combos(cb, intervention_df_dict, catch, True, False, False, False, travellers=False)
    add_all_reports(cb, catch, start=0 * 365)

    arab_burnin = 9.388
    funest_burnin = 10.2778
    set_ento(cb, arab_burnin, funest_burnin, arab_times, arab_spline, funest_times, funest_spline)



    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []

    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    modlists.append(new_modlist)

    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Regional_Migration', x) for x in [0.1, 0.01,0.001,0.0001,0]]
    modlists.append(new_modlist)

    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)