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
experiment_name = "{}_example".format(catch)
print(catch)

# After burnin_param_sweep has swept over and burned in over entire param space, start a new run from each of these state files
calib_folder = os.path.join(project_folder,"calibs")
burnin_sim_map = pd.read_csv(os.path.join(calib_folder,catch,"burnin_sim_map.csv"))

cb = build_project_cb()
catchment_cb_params(cb, catch)

cb.set_param("x_Temporary_Larval_Habitat", 0)
cb.set_param("Simulation_Duration", 8*365)

if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name)