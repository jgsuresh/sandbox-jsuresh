import os
import numpy as np
import pandas as pd

from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Analysis.BaseAnalyzers import BaseAnalyzer

from simtools.DataAccess.DataStore import DataStore
from simtools.Utilities.Experiments import retrieve_simulation, retrieve_experiment

from gridded_sims.calib.comparison_analyzers import SimulationDirectoryMapAnalyzer
from gridded_sims.run.build_cb import kariba_ento


def generate_burnins_sim_map(exp_name="smallscale_RCD_burnins", sim_map_filename="burnins_sim_map.csv"):
    # Create simulation directory map of burnins

    analyzer_list = [SimulationDirectoryMapAnalyzer(save_file=sim_map_filename)]
    am = AnalyzeManager(force_analyze=True)
    # exp = DataStore.get_most_recent_experiment(id_or_name=exp_name) #only seems to work if db.sqlite is OK
    exp = retrieve_experiment(exp_name)
    am.add_experiment(exp)

    for a in analyzer_list:
        am.add_analyzer(a)

    am.analyze()

def draw_from_burnin_using_sim_id(cb, burnin_sim_id):
    sim = retrieve_simulation(burnin_sim_id)
    serialize_path = sim.get_path()

    cb.update_params({
        'Serialized_Population_Path': os.path.join(serialize_path, 'output'),
        'Serialized_Population_Filenames': ['state-18250.dtk']
    })

def draw_from_burnin_using_vector_habs(cb, f_sc, a_sc):
    burnin_sim_id = find_burnin_sim_id_for_funest_hab(f_sc)
    draw_from_burnin_using_sim_id(cb, burnin_sim_id)

    tag_dict = kariba_ento(cb, f_sc, a_sc)
    return tag_dict

def draw_from_burnin_using_vector_habitats_BENOIT(cb, habitats, serialization_parameters):
    """
    Function called in a sweep.
    - Set the funestus and arabiensis habitat
    - Set the serialization parameters
    """
    funestus_habitat, arabiensis_habitat = habitats
    kariba_ento(cb, funestus_habitat, arabiensis_habitat)
    cb.update_params(serialization_parameters)
    return {"funest": funestus_habitat,
            "arab": arabiensis_habitat}



def find_burnin_sim_id_for_funest_hab(funest_hab, burnin_sim_map_filepath="output/burnins_sim_map_20200317.csv"):
    burnin_sim_map = pd.read_csv(burnin_sim_map_filepath)
    if "Run_Number" in burnin_sim_map:
        burnin_sim_map = burnin_sim_map[burnin_sim_map["Run_Number"]==0]

    funest_array = np.array(burnin_sim_map["funest"])
    sim_id_list = list(burnin_sim_map["id"])

    arg_select = int(np.argmin(np.abs(funest_array-funest_hab)))
    return sim_id_list[arg_select]


def pre_process_burnin(input_file, larval_habitats):
    """
    Pre-process the burnin.
    input file: path to the CSV file containing the sim id, funestus, arabiensis habitats, and path
    larval_habitats: habitats we want to match simulations to
    return: dictionary containing (funestus_habitat, arabiensis_habitat) -> {serialization parameters}
    """
    burnin_sim_map = pd.read_csv(input_file)

    if "Run_Number" in burnin_sim_map:
        burnin_sim_map = burnin_sim_map[burnin_sim_map["Run_Number"]==0]

    sim_updates = {}

    for funestus_habitat, arabiensis_habitat in larval_habitats:
        # Get the simulation path with the closest funestus habitat
        simulation_path = burnin_sim_map.loc[(burnin_sim_map["funest"]-funestus_habitat).abs().argmin()]["path"]
        sim_updates[(funestus_habitat, arabiensis_habitat)] = {
            'Serialized_Population_Path': os.path.join(simulation_path, 'output'),
            'Serialized_Population_Filenames': ['state-18250.dtk']
        }

    return sim_updates




#fixme  def draw_from_burnin(arab_hab)


if __name__=="__main__":
    from COMPS import Client
    Client.login(hoststring="https://comps.idmod.org")

    generate_burnins_sim_map(sim_map_filename="burnins_sim_map_singlenode_20200317.csv",
                             exp_name="374cd6bf-5c6a-ea11-a2c5-c4346bcb1550")
