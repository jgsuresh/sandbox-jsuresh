import os
import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

from gridded_sims.calib.sim_map import basic_inset_channel_plotter, plot_all


from simtools.Analysis.AnalyzeManager import AnalyzeManager
from gridded_sims.calib.comparison_analyzers import SimulationDirectoryMapAnalyzer
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation

from gridded_sims.calib.comparison_analyzers import SpatialPrevalenceComparison, IncidenceComparison, prev_err_func, \
    inc_err_func, comparison_channel_plotter, vector_plotter, SeasonalityComparison, BitingScales
from gridded_sims.run.site import get_catchment_list, get_ref_data, project_folder, prev_ref_data_by_round
from simtools.DataAccess.DataStore import DataStore

from COMPS import Client
Client.login("comps.idmod.org")



####################################
c = 52
year_start = 2009
ref_date = "{}-01-01".format(year_start)




# Luumbo
if c == 21:
    rds_to_include = [10, 1, 4]

    dist_max = {10: 4,
                1: 5,
                4: 5}
elif c == 1:
    # Bbondo
    # rds_to_include = [0,1]
    rds_to_include = list(range(10))
    dist_max = {}
    for j in range(10):
        dist_max[j] = 3
    # dist_max[0] = 0.5
    # dist_max[1] = 1
elif c == 9: #Chiyabi
    rds_to_include = [1,7, 10]
    dist_max = {1: 4,
                7: 4,
                10: 4}

elif c == 52: # sinamalima
    dist_max = {1: 15,
                3: 20,
                4: 12,
                5: 15}
    rds_to_include = list(dist_max.keys())

####################################
calib_folder = os.path.join(project_folder,"calibs")
catch_list = get_catchment_list()

catch = catch_list[c]
print("Catchment {}".format(catch))

catch_folder = os.path.join(calib_folder, catch)

sim_map_filename = os.path.join(catch_folder, "sim_map.csv")
prev_dist_filename = os.path.join(catch_folder, "prev_distance.csv")
inc_comp_filename = os.path.join(catch_folder, "inc_comparison.csv")

sim_map_df = pd.read_csv(sim_map_filename)
prev_dist_df = pd.read_csv(prev_dist_filename)
inc_comp_df = pd.read_csv(inc_comp_filename)
prev_dist_df = prev_dist_df.merge(sim_map_df[["__sample_index__", "arab", "funest", "id"]],
                                  how="left", left_on="sample", right_on="__sample_index__")

prev_ref_data = prev_ref_data_by_round(catch, start_date=ref_date)
prev_ref_data.rename(columns={"prev": "data",
                              "N": "weight"}, inplace=True)
prev_ref_data = prev_ref_data[["sim_date", "data", "weight"]]


if __name__=="__main__":

    # Loop over rounds in "rds to include", find all sims which have prev_distance < distance_max for this round.

    available_sims = {}
    available_sims["id"] = list(set(sim_map_df["id"]))
    available_sims["sample"] = list(set(sim_map_df["__sample_index__"]))
    rounds_so_far = []

    for r in rds_to_include:
        in_round = prev_dist_df["round"] == r
        in_cut = prev_dist_df["sim_dist"] < dist_max[r]

        sims_this_rd = {}
        sims_this_rd["id"] = list(prev_dist_df[np.logical_and(in_round, in_cut)]["id"])
        sims_this_rd["sample"] = list(prev_dist_df[np.logical_and(in_round, in_cut)]["sample"])
        print("For round {} alone, there are {} sims that are within distance {}.".format(r, len(sims_this_rd["id"]), dist_max[r]))

        sims_so_far = {}
        sims_so_far["id"] = list(set(sims_this_rd["id"]) & set(available_sims["id"]))
        sims_so_far["sample"] = list(set(sims_this_rd["sample"]) & set(available_sims["sample"]))
        rounds_so_far.append(r)
        print("For all rounds included so far: {} -- there are {} sims that fit all criteria.".format(rounds_so_far, len(sims_so_far["id"])))

        available_sims = sims_so_far.copy()

    print("Samples : {}".format(available_sims["sample"]))

    if len(available_sims) > 0:
        am = AnalyzeManager()
        for sim_id in available_sims["id"]:
            am.add_simulation(retrieve_simulation(sim_id))

        am.add_analyzer(comparison_channel_plotter("Blood Smear Parasite Prevalence",
                                                   filenames=['output/ReportMalariaFilteredCatchment.json'],
                                                   reference_data=prev_ref_data,
                                                   ref_date=ref_date,
                                                   legend=False,
                                                   working_dir=catch_folder,
                                                   save_type="other",
                                                   save_name="excl_prev_test"))

        am.analyze()

        plt.figure()

        # Set plot range to 2017:
        for s in available_sims["sample"]:
            df = inc_comp_df[inc_comp_df["sample"]==s]
            plt.plot(np.array(df["cases_sim"]))
        plt.plot(np.array(df["cases_ref"]),color='black',lw=2,marker='o', label="ref")

        x_ticks_locs = []
        x_ticks_labels = []
        for i in range(len(df)):
            y = str(int(df["year"].iloc[i]+2009))
            m = str(int(df["month"].iloc[i]))

            if m == "1":
                x_ticks_locs.append(i)
                x_ticks_labels.append(y)
        plt.xticks(ticks=x_ticks_locs, labels=x_ticks_labels)
        plt.ylabel("Cases")

        plt.legend()

        plt.savefig(os.path.join(catch_folder, "excl_incid_test.png"))
        plt.close()

#
#
# # prev_dist_df = pd.read_csv(prev_dist_filename)
# #
# #     # Also save intermediate file which is the same as above but grouped by round WITH EXCLUSIONS
# #     exclude_rounds = [2,3]
# #     excl = np.in1d(prev_dist_df["round"], exclude_rounds)
# #     remove_excl = np.logical_not(excl)
# #
# #     prev_dist_df_EXCL = prev_dist_df[remove_excl]
# #     prev_dist_by_sample_EXCL = prev_dist_df_EXCL.groupby('sample').agg({"dist_times_N_ref": "sum",
# #                                                               "N_ref": "sum"})
# #     prev_dist_by_sample_EXCL["sim_dist"] = prev_dist_by_sample_EXCL["dist_times_N_ref"]/prev_dist_by_sample_EXCL["N_ref"]
# #     prev_dist_by_sample_EXCL.reset_index(inplace=True)
# #     prev_dist_by_sample_EXCL = prev_dist_by_sample_EXCL[["sample", "sim_dist"]]
# #     prev_dist_by_sample_EXCL.to_csv(prev_dist_sample_EXCL_filename, index=False)
#
#