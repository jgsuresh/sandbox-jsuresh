
import os
import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from gridded_sims.calib.sim_map import basic_inset_channel_plotter, plot_all


from simtools.Analysis.AnalyzeManager import AnalyzeManager
from gridded_sims.calib.comparison_analyzers import SimulationDirectoryMapAnalyzer
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation

from gridded_sims.calib.comparison_analyzers import SpatialPrevalenceComparison, IncidenceComparison, prev_err_func, \
    inc_err_func, comparison_channel_plotter, vector_plotter, SeasonalityComparison, BitingScales
from gridded_sims.run.site import get_catchment_list, get_ref_data, project_folder, prev_ref_data_by_round
from simtools.DataAccess.DataStore import DataStore

from gridded_sims.cf.endpoint_analyzer import SaveEndpoint

from COMPS import Client
Client.login("comps.idmod.org")



####################################
orig_exp = {}
orig_exp["exp_id"] = "a1c6bf52-055e-e911-a2c0-c4346bcb1554"
orig_exp["burnin_sweep"] = False
catch_nums = [21]

cf_exp = {}
cf_exp["exp_id"] = "d2e116d5-845c-e911-a2c0-c4346bcb1554"

####################################
cf_folder = os.path.join(project_folder,"cf")
catch_list = get_catchment_list()

run_endpoint_original = False
run_endpoint_cf = False
plot_endpoint_diff = True

if __name__=="__main__":
    # Run endpoint analyzer on original run, and output as endpoint_original.csv
    for c in catch_nums:
        catch = catch_list[c]
    catch_folder = os.path.join(cf_folder, catch)

    if run_endpoint_original:
        sim_map_filename = os.path.join(catch_folder, "sim_map_original.csv")
        endpoint_filename = os.path.join(catch_folder, "endpoint_original.csv")

        analyzer_list = []
        analyzer_list += [SaveEndpoint(save_file=endpoint_filename, year_to_use=6),
                          SimulationDirectoryMapAnalyzer(save_file=sim_map_filename)]

        am = AnalyzeManager()
        exp = retrieve_experiment(orig_exp["exp_id"])
        am.add_experiment(exp)

        for a in analyzer_list:
            am.add_analyzer(a)

        am.analyze()

    if run_endpoint_cf:
        sim_map_filename = os.path.join(catch_folder, "sim_map_cf.csv")
        endpoint_filename = os.path.join(catch_folder, "endpoint_cf.csv")

        analyzer_list = []
        analyzer_list += [SaveEndpoint(save_file=endpoint_filename, year_to_use=6),
                          SimulationDirectoryMapAnalyzer(save_file=sim_map_filename)]

        am = AnalyzeManager()
        exp = retrieve_experiment(cf_exp["exp_id"])
        am.add_experiment(exp)

        for a in analyzer_list:
            am.add_analyzer(a)

        am.analyze()

    if plot_endpoint_diff:
        df_orig = pd.read_csv(os.path.join(catch_folder, "endpoint_original.csv"))
        df_cf = pd.read_csv(os.path.join(catch_folder, "endpoint_cf.csv"))

        if False:
            # CHW hs:
            foo = df_cf[np.logical_and(df_cf["chw_rcd"]==False, df_cf["chw_hs"]==True)]
            foo.rename(columns={"EIR": "EIR_cf",
                                "RDT_prev": "RDT_prev_cf",
                                "cases": "cases_cf"},
                       inplace=True)
            df_CHW_hs = df_orig.merge(foo[["sample","EIR_cf", "RDT_prev_cf","cases_cf"]], how="left", on="sample")
            # df_CHW_rcd =
            # df_CHW =

            plt.figure(figsize=(20,5))

            lbl_list = ["EIR", "RDT_prev", "cases"]

            for i in range(3):
                m = lbl_list[i]
                plt.subplot(1,3,i+1)

                diff = df_CHW_hs[m] - df_CHW_hs["{}_cf".format(m)]
                plt.scatter(df_CHW_hs["arab"], df_CHW_hs["funest"], c=diff)
                cb = plt.colorbar()

                if m == "EIR":
                    plt.clim(-20., 0.)
                elif m == "RDT_prev":
                    plt.clim(-.05, 0.)
                elif m == "cases":
                    plt.clim(-1000,0.)

                cb.set_label("{} Difference".format(m))
                # plt.xlim(arab_range)
                # plt.ylim(funest_range)
                plt.xlabel("Arabiensis Spline")
                plt.ylabel("Funestus Spline")
                # plt.title(lbl_list[i])

            plt.suptitle("Effect of adding RCD")
            plt.tight_layout()
            plt.show()

        # CHW total:
        foo = df_cf[np.logical_and(df_cf["chw_rcd"] == False, df_cf["chw_hs"] == False)]
        foo.rename(columns={"EIR": "EIR_cf",
                            "RDT_prev": "RDT_prev_cf",
                            "cases": "cases_cf"},
                   inplace=True)
        df_CHW_hs = df_orig.merge(foo[["sample", "EIR_cf", "RDT_prev_cf", "cases_cf"]], how="left", on="sample")
        # df_CHW_rcd =
        # df_CHW =

        plt.figure(figsize=(20, 5))

        lbl_list = ["EIR", "RDT_prev", "cases"]

        for i in range(3):
            m = lbl_list[i]
            plt.subplot(1, 3, i + 1)

            diff = df_CHW_hs[m] - df_CHW_hs["{}_cf".format(m)]
            plt.scatter(df_CHW_hs["arab"], df_CHW_hs["funest"], c=diff)

            best_samples = [88, 74, 59, 29]
            b = df_CHW_hs[np.in1d(df_CHW_hs["sample"], best_samples)]
            b_diff = diff = b[m] - b["{}_cf".format(m)]
            plt.scatter(b["arab"],b["funest"],c=b_diff,marker="s",edgecolors="red", linewidth=3,s=300)

            cb = plt.colorbar()

            if m == "EIR":
                plt.clim(-20., 0.)
            elif m == "RDT_prev":
                plt.clim(-.05, 0.)
            elif m == "cases":
                plt.clim(-1000, 0.)

            cb.set_label("{} Difference".format(m))
            # plt.xlim(arab_range)
            # plt.ylim(funest_range)
            plt.xlabel("Arabiensis Spline")
            plt.ylabel("Funestus Spline")
            # plt.title(lbl_list[i])

        plt.suptitle("Effect of adding CHW")
        plt.tight_layout()
        # plt.show()
        plt.savefig(os.path.join(catch_folder, "CHW_effect.png"))

