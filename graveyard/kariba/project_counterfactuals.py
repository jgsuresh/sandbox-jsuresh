from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_simulation

SetupParser.default_block = "HPC"
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

from gridded_sims.run.build_cb import *
from gridded_sims.run.site import *
from gridded_sims.run.interventions import add_all_interventions, add_regional_EIR_node, add_intervention_combos, \
    preload_intervention_csvs
from gridded_sims.run.reports import add_all_reports

from gridded_sims.run.site import project_folder


# Run parameters:
catch_num = 1

num_cores = 2
priority = "AboveNormal"
coreset = "emod_abcd"
# priority = "Highest"
# coreset = "emod_32cores"
# ====================================================================================================================


catch_list = get_catchment_list()
catch = catch_list[catch_num]
experiment_name = "{}_CHW_cf_test".format(catch)
print(catch)

# After burnin_param_sweep has swept over and burned in over entire param space, start a new run from each of these state files
calib_folder = os.path.join(project_folder,"calibs")
burnin_sim_map = pd.read_csv(os.path.join(calib_folder,catch,"burnin_sim_map.csv"))

cb = build_project_cb()
catchment_cb_params(cb, catch)


cb.set_param("Simulation_Duration",8 * 365)
add_all_reports(cb, catch, start=0 * 365)

def sweep(cb, param_name, v):
    cb.set_param(param_name, v)
    return {param_name: v}


def draw_from_burnin(cb, burnin_sim_id, t, n_cores=2):
    sim = retrieve_simulation(burnin_sim_id)
    serialized_file_path = sim.get_path()

    if n_cores == 1:
        raise NotImplementedError()

    cb.update_params({
        'Serialized_Population_Path': os.path.join(serialized_file_path, 'output'),
        'Serialized_Population_Filenames': ['state-{}-{}.dtk'.format(str(t).zfill(5), str(c).zfill(3)) for c in range(n_cores)]
    })

intervention_df_dict = preload_intervention_csvs(catch, "2010-01-01")

def counterfactuals(cb, itn, irs, mda, msat, chw_hs, chw_rcd):
    add_intervention_combos(cb, intervention_df_dict, catch, itn, irs, mda, chw_rcd, CHW_hs=chw_hs, travellers=False)
    return {"itn": itn,
            "irs": irs,
            "mda": mda,
            "msat": msat,
            "chw_hs": chw_hs,
            "chw_rcd": chw_rcd}

n_pts_sweep = 15
arab_sweep_lim = [8.7,10.1]
funest_sweep_lim = [8,9.5]
arab_spline_list = np.linspace(arab_sweep_lim[0], arab_sweep_lim[1], n_pts_sweep)
funest_spline_list = np.linspace(funest_sweep_lim[0], funest_sweep_lim[1], n_pts_sweep)
def pickup_from_sample(cb, i, t=20075):
    j = i % len(arab_spline_list)
    k = int(i/len(arab_spline_list))

    arab = arab_spline_list[j]
    funest = funest_spline_list[k]

    # Look up this sample in the burnin_sim_map:
    foo = burnin_sim_map[burnin_sim_map["__sample_index__"]==i]
    burnin_sim_id = foo["id"].iloc[0]

    draw_from_burnin(cb, burnin_sim_id, t)

    return {
        "__sample_index__": i,
        "__site__": catch,
        "arab": arab,
        "funest": funest
    }



def generate_input_variations():
    # itn, irs, mda, msat, chw_hs, chw_rcd

    tuples_list = []
    tuples_list.append([True, True, True, True, True, True])
    tuples_list.append([True, True, True, True, True, False])
    tuples_list.append([True, True, True, True, False, False])
    tuples_list.append([False, True, True, True, True, False])
    tuples_list.append([True, False, True, True, True, False])
    tuples_list.append([True, True, False, False, True, False])

    return tuples_list


if __name__ == "__main__":
    SetupParser.init()
    SetupParser.set("HPC", "priority", priority)
    SetupParser.set("HPC", "node_group", coreset)

    modlists = []
    new_modlist = [ModFn(pickup_from_sample, i) for i in range(len(arab_spline_list)*len(funest_spline_list))]
    modlists.append(new_modlist)
    #
    # new_modlist = [ModFn(counterfactuals, itn, irs, mda, msat, chw_hs, chw_rcd)
    #                for itn in [True]
    #                for irs in [True]
    #                for mda in [True]
    #                for msat in [True]
    #                for chw_hs in [False, True]
    #                for chw_rcd in [False, True]]

    tuples_list = generate_input_variations()
    new_modlist = [ModFn(counterfactuals, x[0], x[1], x[2], x[3], x[4], x[5]) for x in tuples_list]
    modlists.append(new_modlist)

    builder = ModBuilder.from_combos(*modlists)

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb,
                                exp_name=experiment_name,
                                exp_builder=builder)