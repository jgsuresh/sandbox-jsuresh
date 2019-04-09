import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_simulation

from COMPS.Client import Client
Client.login("comps.idmod.org")

SetupParser.default_block = "HPC"


priority = "Highest"
coreset = "emod_32cores"

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM', Simulation_Duration=365)
configure_site(cb, 'Namawala')

# Using dtk-tools example exe/dlls, which fits the DTKConfigBuilder.from_defaults call
cb.set_experiment_executable("C:/Users/jsuresh/Code/dtk-tools/examples/inputs/Eradication.exe")
cb.set_dll_root("C:/Users/jsuresh/Code/dtk-tools/examples/inputs/dlls")

# Serialization stuff:

# To write out a serialization file at a timestep
cb.set_param("Serialization_Time_Steps", [100, 200, 300])

# To draw from a serialized file:
def draw_from_burnin(cb, burnin_sim_id):
    sim = retrieve_simulation(burnin_sim_id)
    serialized_file_path = sim.get_path()

    cb.update_params({
        'Serialized_Population_Path': os.path.join(serialized_file_path, 'output'),
        'Serialized_Population_Filenames': ['state-{}.dtk'.format(str(time).zfill(5)) for time in [200]]
    })


draw_from_burnin(cb, "7ddc3c1a-a849-e911-a2c0-c4346bcb1554")

# run_sim_args is what the `dtk run` command will look for
run_sim_args = {
    'exp_name': 'ExampleSim',
    'config_builder': cb
}

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())