from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_simulation

SetupParser.default_block = "HPC"
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

from gridded_sims.run.build_cb import *
from gridded_sims.run.site import *
from gridded_sims.run.interventions import add_all_interventions, add_regional_EIR_node
from gridded_sims.run.reports import add_all_reports

from gridded_sims.run.site import project_folder


# Run parameters:
catch_num = 21

num_cores = 2
# priority = "AboveNormal"
# coreset = "emod_abcd"
priority = "Highest"
coreset = "emod_32cores"
# ====================================================================================================================


catch_list = get_catchment_list()
catch = catch_list[catch_num]
experiment_name = "{}_biting_test".format(catch)
print(catch)

# After burnin_param_sweep has swept over and burned in over entire param space, start a new run from each of these state files
calib_folder = os.path.join(project_folder,"calibs")
burnin_sim_map = pd.read_csv(os.path.join(calib_folder,catch,"burnin_sim_map.csv"))

cb = build_project_cb()
catchment_cb_params(cb, catch)


cb.set_param("Simulation_Duration",8 * 365)
# add_all_interventions(cb, catch, sim_start_date="2010-01-01", travellers=False)
# add_all_reports(cb, catch, start=0 * 365)

# def temp_rainfall_sweep(cb, a_sc, arab_spline):
#     kariba_ento(cb, f_sc=9, a_sc=a_sc, arab_spline=arab_spline)
#     return {"arab": a_sc, "arab_spline": arab_spline}

def a_vs_f(cb, type):
    if type == "arab_spline":
        kariba_ento(cb, f_sc=-1, a_sc=9, arab_spline=True)
    elif type == "arab_tr":
        kariba_ento(cb, f_sc=-1, a_sc=10, arab_spline=False)
    elif type == "funest_spline":
        kariba_ento(cb, f_sc=9, a_sc=-1, funest_spline=True)
    elif type == "funest_wveg":
        kariba_ento(cb, f_sc=10, a_sc=-1, funest_spline=False)
    return {"type": type}


# arab_spline_list = np.linspace(8, 10, 5)
def sweep(cb, name, v):
    cb.set_param(name, v)
    return {name: v}

if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []
    # new_modlist = [ModFn(a_vs_f, t) for t in ["arab_spline", "arab_tr", "funest_spline","funest_wveg"]]
    new_modlist = [ModFn(a_vs_f, t) for t in ["funest_wveg"]]
    modlists.append(new_modlist)
    new_modlist = [ModFn(sweep, n, v)
                   for n in ["Semipermanent_Habitat_Decay_Rate"]
                   for v in [0.0001, 0.001, 0.01, 0.1, 1]]
    modlists.append(new_modlist)

    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)