from dtk.interventions.ivermectin import add_ivermectin
from malaria.reports.MalariaReport import add_filtered_report, add_filtered_spatial_report, add_event_counter_report
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation

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

from gridded_sims.ivermectin_paper.project_from_burnin import iver_sweep

def add_filtered_reports(cb, catch, start=0, duration=10000000):
    add_filtered_spatial_report(cb, channels=["Population", "True_Prevalence"], start=start, end=(start + duration))

    # Filtered report just for work node, and just for catchment:
    regional_EIR_node_label = 100000
    catch_node_ids = find_cells_for_this_catchment(catch)

    add_filtered_report(cb, nodes=[regional_EIR_node_label], description='Work', start=start,
                        end=(start + duration))
    add_filtered_report(cb, nodes=catch_node_ids, description='Catchment', start=start,
                        end=(start + duration))

def load_burnin_x_temp(cb, x_temp):
    # burnin_id_dict = {2:"8f334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   3:"90334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   4:"91334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   5:"92334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   6:"93334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   7:"94334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   8:"95334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   9:"96334a00-dd2c-e911-a2c5-c4346bcb7273",
    #                   10:"97334a00-dd2c-e911-a2c5-c4346bcb7273"}
    burnin_id_dict = {2:"f80b7373-da2d-e911-a2c5-c4346bcb7273",
                      3:"f90b7373-da2d-e911-a2c5-c4346bcb7273",
                      4:"fa0b7373-da2d-e911-a2c5-c4346bcb7273",
                      5:"fb0b7373-da2d-e911-a2c5-c4346bcb7273",
                      6:"fc0b7373-da2d-e911-a2c5-c4346bcb7273",
                      7:"fd0b7373-da2d-e911-a2c5-c4346bcb7273",
                      8:"fe0b7373-da2d-e911-a2c5-c4346bcb7273",
                      9:"000c7373-da2d-e911-a2c5-c4346bcb7273",
                      10:"010c7373-da2d-e911-a2c5-c4346bcb7273"}

    sim = retrieve_simulation(burnin_id_dict[x_temp])
    serialized_file_path = sim.get_path()

    cb.update_params({
        'Serialized_Population_Path': os.path.join(serialized_file_path, 'output'),
        # 'Serialized_Population_Filenames': ['state-19710.dtk']
        'Serialized_Population_Filenames': ['state-19710-000.dtk', 'state-19710-001.dtk']
    })

    return {"x_temp": x_temp}




if __name__ == "__main__":
    # Run parameters:
    catch = "Magude-Sede-Facazissa"
    num_cores = 1
    num_seeds = 10
    priority = "Normal"
    coreset = "emod_abcd"
    # priority = "Highest"
    # coreset = "emod_32cores"
    # ====================================================================================================================

    experiment_name = "MSF_intervention_extremes_test"
    arab_times, arab_spline = catch_1_yr_spline(catch, "gambiae")
    funest_times, funest_spline = catch_1_yr_spline(catch, "funestus")

    cb = build_project_cb()
    catchment_cb_params(cb, catch)
    # cb.set_param("x_Regional_Migration", 0.0081)

    # Burnin serialized at 2009.  So current run, which goes to beginning of 2019, has run duration of 10 years:
    # sim_start_date = "2009-01-01"
    sim_start_date = "2014-01-01"
    cb.set_param("Simulation_Duration", 4 * 365)
    # draw_from_burnin(cb, burnin_sim_id)

    # NO IMPORTATIONS
    cb.set_param("x_Regional_Migration", 0)

    ivm_interventions_folder = os.path.join(project_folder, "dtk_simulation_input/mozambique/ivermectin_paper/")
    hs_timeshifted = os.path.join(ivm_interventions_folder, "grid_all_healthseek_events.csv")
    itn_simplified = os.path.join(ivm_interventions_folder, "grid_all_itn_events.csv")
    irs_simplified = os.path.join(ivm_interventions_folder, "grid_all_irs_events.csv")
    mda_simplified = os.path.join(ivm_interventions_folder, "grid_all_mda_events.csv")
    intervention_df_dict = preload_intervention_csvs(catch, sim_start_date,
                                                     hs_file=hs_timeshifted,
                                                     itn_file=itn_simplified,
                                                     irs_file=irs_simplified,
                                                     mda_file=mda_simplified)
    # add_intervention_combos(cb, intervention_df_dict, catch, True, False, False, False, travellers=False)
    add_all_reports(cb, catch, start=0 * 365)

    # arab_burnin = 9.388
    # funest_burnin = 10.2778
    arab_burnin = 10
    funest_burnin = 9.4
    set_ento(cb, arab_burnin, funest_burnin, arab_times, arab_spline, funest_times, funest_spline)



    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []

    new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
    modlists.append(new_modlist)

    new_modlist = [ModFn(load_burnin_x_temp, x_temp) for x_temp in [2,3,4,6,7,8,9,10]]
    modlists.append(new_modlist)

    new_modlist = [ModFn(iver_sweep, intervention_df_dict, "ITN only", "none", -1, -1),
                   ModFn(iver_sweep, intervention_df_dict, "ITN and IRS", "none", -1, -1),
                   ModFn(iver_sweep, intervention_df_dict, "ITN and IRS", "MDA without IVM", 0.2, -1),
                   ModFn(iver_sweep, intervention_df_dict, "ITN and IRS", "MDA with IVM", 0.8, 90)]
    modlists.append(new_modlist)


    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)