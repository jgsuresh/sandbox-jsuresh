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
    am = AnalyzeManager()
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


def find_burnin_sim_id_for_funest_hab(funest_hab, burnin_sim_map_filepath="burnins_sim_map_finescale_all.csv"):
    burnin_sim_map = pd.read_csv(burnin_sim_map_filepath)
    if "Run_Number" in burnin_sim_map:
        burnin_sim_map = burnin_sim_map[burnin_sim_map["Run_Number"]==0]

    funest_array = np.array(burnin_sim_map["funest"])
    sim_id_list = list(burnin_sim_map["id"])

    arg_select = int(np.argmin(np.abs(funest_array-funest_hab)))
    return sim_id_list[arg_select]



#fixme  def draw_from_burnin(arab_hab)


if __name__=="__main__":
    from COMPS import Client
    Client.login(hoststring="https://comps.idmod.org")

    generate_burnins_sim_map(sim_map_filename="burnins_sim_map_finescale_v3.csv", exp_name="3726ab91-a75c-ea11-a2c5-c4346bcb1550")
