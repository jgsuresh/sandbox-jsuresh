# Loop over catchments
# From each folder, get sim_map, prev_distance_by_sample, to get the following:
# | Catchment | Exp ID | Sim ID|  Sample | arab | funest | COMPS output location | prev_dist_v1 | prev_dist_v2 | inc_dist

# Output these to a single CSV calib_map.CSV
import pandas as pd
import numpy as np
import os

from gridded_sims.run.site import get_catchment_list

prev_dist_thresh = 100000000
inc_norm_dist_thresh = 100000000


catch_list = get_catchment_list()
best_runs_dict = {}
ref_date = "2010-01-01"

make_sanity_plots=False

# for c in range(56):
# catch = catch_list[c]
# for catch in ["batoka","bbondo","dimbwe","jamba","jembo","kasikili","luyaba","maamba","masempala","nanduba","siansowa","sianyoolo"]:

exclude_samples = {}
include_samples = {}
only_include_samples = {}

# exclude_samples["dimbwe"] = [157,175,187,192,195,198,199]
# include_samples["dimbwe"] = [188,202]

only_include_samples["batoka"] = [15,31,47,63,79,95,111,127,141,142,157,172,187,198]
only_include_samples["bbondo"] = [12,13,27,99,100]
only_include_samples["buleyamalima"] = [63,79,95,110,126,142,158,159]
only_include_samples["dimbwe"] = [126,127,141,142,143,158,159,173,174,187,188,189,201,202,212]
only_include_samples["harmony"] = [111,127,173]
only_include_samples["jamba"] = [63, 79, 126, 122, 109, 93]
only_include_samples["jembo"] = [63, 79,94,95,110,126,140,153,154,155,156,157,167,168,169,170,171,184,185,192,194,197,199]
only_include_samples["kanchele"] = [79,95,110,124,125,126,141,156,169,182]
only_include_samples["kasikili"] = [14,15,30,31,45,46,47,61,62,76,77,78,79,93,108,109,122,123]
only_include_samples["luyaba"] = [14,15,31,46,47,61,62,76,77,91,93,107,108,122,123]
only_include_samples["maamba"] = [94,111,124,125,126,127,141,142,143, 154, 157, 167,168,169,170,171,172]
only_include_samples["manchanvwa"] = [217,224,226,228,229,230,231,232,233,234,241,245] # PREVALENCE ONLY
only_include_samples["mtendere"] = [10,11,26,41,42,55,56,71,85]
only_include_samples["munyumbwe"] = [77,78]
only_include_samples["nakempa"] = [92,107,121,132,133,134,135,136,144,145,146,147,148,149,150,151,160,161,162,163]
only_include_samples["namaila"] = [11,12,39,42,43,44,58,61,75,90,91,105,119,120,129,133,134,135,136,144,145,146,147,148,149]
only_include_samples["nanduba"] = [78,138,155,163,164,169,176,179]
only_include_samples["siameja"] = [42,55]
only_include_samples["siansowa"] = [11,12,13,26,27,42,43,44,58,72,73,74,86,87,88,99,100,101,112]
only_include_samples["sianyoolo"] = [31,46,47,63,77,78,79,94,95,107,108,109,110,124,125,135]
only_include_samples["sikaneka"] = [31,61,77]
only_include_samples["sinafala"] = [15,31]
only_include_samples["sinamalima"] = [78]



full_c_list = list(only_include_samples.keys()) + ["chiyabi","masempela","sinazeze"]
# full_c_list = ["masempela"]
print(full_c_list)
# for catch in ["luumbo", "chipepo siavonga"]:
for catch in full_c_list:
    c_folder = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/calibs/{}".format(catch)

    print(catch)

    try:
        sm = pd.read_csv(os.path.join(c_folder, "sim_map.csv"))
        prev_d = pd.read_csv(os.path.join(c_folder, "prev_distance_by_sample.csv"))
        inc_dist_df = pd.read_csv(os.path.join(c_folder, "inc_distance.csv"))

        sm = sm.merge(prev_d, how="left", left_on="__sample_index__", right_on="sample")
        sm = sm.merge(inc_dist_df, how="left", on="sample")
        sm["inc_dist_norm"] = sm["inc_dist"]-np.min(sm["inc_dist"])

        # See if you can find the "serialized_files_
        try:
            ssm = pd.read_csv(os.path.join(c_folder, "serialized_files_sim_map.csv"))
            ssm.rename(columns={"path": "serialize_path"}, inplace=True)
            sm = sm.merge(ssm[["__sample_index__", "serialize_path"]], how="left", on="__sample_index__")
            sm["serialize_time"] = 20075
        except:
            sm["serialize_path"] = sm["path"]
            sm["serialize_time"] = 20440



        # Add in information about baseline transmission:
        try:
            b = pd.read_csv(os.path.join(c_folder, "biting.csv"))
            sm = sm.merge(b, how="left", on="sample")
        except:
            pass



        # if catch in ["dimbwe","kasikili","luyaba"]:
        #     prev_cut = sm["sim_dist_w1"] <= 1
        #     inc_cut = sm["inc_dist_norm"] <= 1
        # else:
        #     prev_cut = sm["sim_dist_w1"] <= prev_dist_thresh
        #     inc_cut = sm["inc_dist_norm"] <= inc_norm_dist_thresh
        # full_cut = np.logical_and(prev_cut, inc_cut)


        if catch in ["chiyabi","sinazeze"]:
            prev_cut = sm["sim_dist_w1"] <= 2
            full_cut = prev_cut
        elif catch == "masempela":
            prev_cut = sm["sim_dist_w1"] <= 1
            full_cut = prev_cut
        else:
            full_cut = np.in1d(sm["sample"], only_include_samples[catch])
        n_fit = np.sum(full_cut)
        print("Catchment {} had {} curves that fit requirements".format(catch, np.sum(n_fit)))


        if n_fit > 0:
            foo = sm[full_cut]
            foo = foo[["id", "sample","arab", "funest", "sim_dist", "sim_dist_w1", "inc_dist", "inc_dist_norm","path","serialize_path","serialize_time","annual_EIR","avg_daily_bites","avg_prev","peak_daily_bites"]]
            foo["catch"] = catch
            best_runs_dict[catch] = foo.copy(deep=True)


    except:
        pass







# Now that we have all of the runs, concatenate them into a single dataframe:
cmap = pd.concat(list(best_runs_dict.values()))

print("Total number of runs to project forward = {}".format(len(cmap)))
cmap.to_csv("calib_map_eye.csv", index=False)




    # if make_sanity_plots:
    #     inc_comp_df = pd.read_csv(os.path.join(c_folder, "inc_comparison.csv"))
    #
    #     # Plot individual time series:
    #     prev_ref_data = prev_ref_data_by_round(catch, start_date=ref_date)
    #     prev_ref_data.rename(columns={"prev": "data",
    #                                   "N": "weight"}, inplace=True)
    #     prev_ref_data = prev_ref_data[["sim_date", "data", "weight"]]
    #
    #             if __name__ == "__main__":
    #                 am = AnalyzeManager()
    #
    #                 for sim_id in sm_mini["id"]:
    #                     am.add_simulation(retrieve_simulation(sim_id))
    #
    #                 am.add_analyzer(comparison_channel_plotter("Blood Smear Parasite Prevalence",
    #                                                            filenames=['output/ReportMalariaFilteredCatchment.json'],
    #                                                            reference_data=prev_ref_data,
    #                                                            ref_date=ref_date,
    #                                                            legend=False,
    #                                                            working_dir='.',
    #                                                            save_type="other",
    #                                                            save_name=os.path.join(c_folder,
    #                                                                                   "prev_dist_thresh_{}_inc_{}.png".format(i, j))))
    #
    #                 am.analyze()
    #
    #                 pretty_plot_incidence(inc_comp_df, list(sm_mini["__sample_index__"]),
    #                                       savefile=os.path.join(c_folder, "plot_inc_thres_{}_inc_{}.png".format(i,j)))
