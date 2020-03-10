import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context("talk")
sns.set_style("white")


def make_figure():
    df = pd.read_csv("iver_figure_data.csv")
    sim_map = pd.read_csv("sim_map.csv")

    full = df.merge(sim_map, how="left", left_on="sim_id", right_on="id")

    vc_only = full[full["int_package"]=="vc only"]
    vc_baseline = {"2016": np.median(vc_only["2016"]),
                   "2017": np.median(vc_only["2017"])}

    # mda_only should be a dataframe with columns: mda coverage, year, cases
    subset = full[full["int_package"] == "mda without ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "year"]).agg("median")

    # mda_w_ivm should be a dataframe with columns: mda coverage, ivm_duration, year, cases
    subset = full[full["int_package"] == "mda with ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "ivm_duration", "year"]).agg("median")


    plt.figure()

    plt.show()



def make_figure_elimination():
    df = pd.read_csv("iver_figure_data.csv")
    sim_map = pd.read_csv("sim_map.csv")

    full = df.merge(sim_map, how="left", left_on="sim_id", right_on="id")

    vc_only = full[full["int_package"]=="vc only"]
    vc_baseline = {"2016": np.median(vc_only["2016"]),
                   "2017": np.median(vc_only["2017"])}

    # mda_only should be a dataframe with columns: mda coverage, year, cases
    subset = full[full["int_package"] == "mda without ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "year"]).agg("median")

    # mda_w_ivm should be a dataframe with columns: mda coverage, ivm_duration, year, cases
    subset = full[full["int_package"] == "mda with ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "ivm_duration", "year"]).agg("median")


