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
experiment_name = "{}_funest_spline_sweep".format(catch)
print(catch)

# After burnin_param_sweep has swept over and burned in over entire param space, start a new run from each of these state files
calib_folder = os.path.join(project_folder,"calibs")

cb = build_project_cb()
catchment_cb_params(cb, catch)


cb.set_param("Simulation_Duration",8 * 365)
add_all_interventions(cb, catch, sim_start_date="2010-01-01", travellers=False)
add_all_reports(cb, catch, start=0 * 365)

# def temp_rainfall_sweep(cb, a_sc, arab_spline):
#     kariba_ento(cb, f_sc=9, a_sc=a_sc, arab_spline=arab_spline)
#     return {"arab": a_sc, "arab_spline": arab_spline}

def f_spline_type(cb,v):
    cb.update_params({
        'Serialized_Population_Path': "//internal.idm.ctr/IDM/home/jsuresh/input/luumbo_funestus/",
        'Serialized_Population_Filenames': ['v{}-{}.dtk'.format(v, str(c).zfill(3)) for c in range(2)]
    })

    return {"v_spline": v}


if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []
    new_modlist = [ModFn(f_spline_type, v) for v in  [7,8]] # [0,1,2,3,4]]
    modlists.append(new_modlist)

    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)