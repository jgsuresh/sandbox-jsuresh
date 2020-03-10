import pandas as pd
import numpy as np
import os.path

# Loop over catchments
# From each folder, get sim_map, prev_distance_by_sample, to get the following:
# | Catchment | Exp ID | Sim ID|  Sample | arab | funest | COMPS output location | prev_dist_v1 | prev_dist_v2 |

# Apply some threshold, and plot the resulting curves for sanity
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Utilities.Experiments import retrieve_simulation

from gridded_sims.calib.comparison_analyzers import comparison_channel_plotter
from gridded_sims.calib.ssmt_comparison.ssmt_helpers import pretty_plot_incidence
from gridded_sims.run.site import get_catchment_list, prev_ref_data_by_round

catch_list = get_catchment_list()

best_runs_dict = {}

ref_date = "2010-01-01"

# for c in [0]:
#     catch = catch_list[c]
#     c_folder = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/calibs/{}".format(catch)
#
#     # Plot individual time series:
#     prev_ref_data= prev_ref_data_by_round(catch, start_date=ref_date)
#     prev_ref_data.rename(columns={"prev": "data",
#                                   "N": "weight"}, inplace=True)
#     prev_ref_data = prev_ref_data[["sim_date", "data", "weight"]]
#
#     sm = pd.read_csv(os.path.join(c_folder, "sim_map.csv"))
#     prev_d = pd.read_csv(os.path.join(c_folder, "prev_distance_by_sample.csv"))
#     inc_comp_df = pd.read_csv(os.path.join(c_folder, "inc_comparison.csv"))
#
#     sm = sm.merge(prev_d, how="left", left_on="__sample_index__", right_on="sample")
#
#     for i in range(1,5):
#         sm_cut = sm[np.logical_and(sm["sim_dist_w1"] > i-1, sm["sim_dist_w1"] <= i)]
#
#         if len(sm_cut) > 0:
#
#             if __name__=="__main__":
#                 am = AnalyzeManager()
#
#                 for sim_id in sm_cut["id"]:
#                     am.add_simulation(retrieve_simulation(sim_id))
#
#                 am.add_analyzer(comparison_channel_plotter("Blood Smear Parasite Prevalence",
#                                                            filenames=['output/ReportMalariaFilteredCatchment.json'],
#                                                            reference_data=prev_ref_data,
#                                                            ref_date=ref_date,
#                                                            legend=False,
#                                                            working_dir='.',
#                                                            save_type="other",
#                                                            save_name=os.path.join(c_folder,"prev_dist_thresh_{}_{}".format(i-1,i))))
#
#                 # am.analyze()
#
#                 pretty_plot_incidence(inc_comp_df, list(sm_cut["sample"]), savefile="plot_inc_thres_{}_{}.png".format(i-1,i))


for c in [0]:
    catch = catch_list[c]
    c_folder = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/calibs/{}".format(
        catch)

    # Plot individual time series:
    prev_ref_data = prev_ref_data_by_round(catch, start_date=ref_date)
    prev_ref_data.rename(columns={"prev": "data",
                                  "N": "weight"}, inplace=True)
    prev_ref_data = prev_ref_data[["sim_date", "data", "weight"]]

    sm = pd.read_csv(os.path.join(c_folder, "sim_map.csv"))
    prev_d = pd.read_csv(os.path.join(c_folder, "prev_distance_by_sample.csv"))
    inc_comp_df = pd.read_csv(os.path.join(c_folder, "inc_comparison.csv"))
    inc_dist_df = pd.read_csv(os.path.join(c_folder, "inc_distance.csv"))

    sm = sm.merge(prev_d, how="left", left_on="__sample_index__", right_on="sample")
    sm = sm.merge(inc_dist_df, how="left", on="sample")
    sm["inc_dist_norm"] = sm["inc_dist"]-np.min(sm["inc_dist"])

    for i in range(1, 5):
        prev_cut = np.logical_and(sm["sim_dist_w1"] > i - 1, sm["sim_dist_w1"] <= i)

        for j in range(1,5):
            inc_cut = np.logical_and(sm["inc_dist_norm"] > j-1, sm["inc_dist_norm"] <= j)

            sm_cut = np.logical_and(prev_cut, inc_cut)
            sm_mini = sm[sm_cut]

            if len(sm_mini) > 0:

                if __name__ == "__main__":
                    am = AnalyzeManager()

                    for sim_id in sm_mini["id"]:
                        am.add_simulation(retrieve_simulation(sim_id))

                    am.add_analyzer(comparison_channel_plotter("Blood Smear Parasite Prevalence",
                                                               filenames=['output/ReportMalariaFilteredCatchment.json'],
                                                               reference_data=prev_ref_data,
                                                               ref_date=ref_date,
                                                               legend=False,
                                                               working_dir='.',
                                                               save_type="other",
                                                               save_name=os.path.join(c_folder,
                                                                                      "prev_dist_thresh_{}_inc_{}.png".format(i, j))))

                    am.analyze()

                    pretty_plot_incidence(inc_comp_df, list(sm_mini["__sample_index__"]),
                                          savefile=os.path.join(c_folder, "plot_inc_thres_{}_inc_{}.png".format(i,j)))
    # am = AnalyzeManager()
    # for sim_id in sim_map_df["id"]:
    #     am.add_simulation(retrieve_simulation(sim_id))
    #
    # am.add_analyzer(comparison_channel_plotter("Blood Smear Parasite Prevalence",
    #                                            filenames=['output/ReportMalariaFilteredCatchment.json'],
    #                                            reference_data=prev_ref_data,
    #                                            ref_date=ref_date,
    #                                            legend=False,
    #                                            working_dir='.',
    #                                            save_type="all"))
    #
    # am.analyze()


    # best_runs_dict[c] = sm