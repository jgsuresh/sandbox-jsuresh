# Open LL_all.csv
# Contour- plot:

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

catch = "chiyabi"
# df = pd.read_csv("chiyabi_burnin_from_milen_optimtool/_plots/LL_all.csv")
df = pd.read_csv("chiyabi_burnin_from_milen_optimtool_v5/_plots/LL_all.csv")
# catch = "sinafala"
# df = pd.read_csv("sinafala_burnin/_plots/LL_all.csv")



if True:
    x = df["arab_rainfall_scale"]
    # y = df["arab_rainfall_scale"] + np.log10(df["spline_rainfall_ratio"])
    y = df["arab_rainfall_scale"] + df["log_spline_rainfall_ratio"]
    # y = df["funest_spline_scale"]

    plt.figure()
    plt.suptitle(catch)
    ax = plt.subplot(211)
    # plt.contour(x,y,df["{}_prevalence_likelihood".format(catch)])
    plt.scatter(x,y,c=df["{}_prevalence_likelihood".format(catch)],zorder=10)
    cb = plt.colorbar()
    cb.set_label("Prevalence Likelihood")
    ax.set_xlabel("TEMPORARY_RAINFALL")
    ax.set_ylabel("LINEAR_SPLINE")
    # ax.set_title("Prevalence Likelihood")

    ax = plt.subplot(212)
    # plt.contour(x,y,df["{}_incidence_likelihood".format(catch)])
    plt.scatter(x,y,c=df["{}_incidence_likelihood".format(catch)],zorder=10)
    cb = plt.colorbar()
    cb.set_label("Incidence Likelihood")
    ax.set_xlabel("TEMPORARY_RAINFALL")
    ax.set_ylabel("LINEAR_SPLINE")

    plt.tight_layout()
    plt.show()


if False:
    # Funestus
    # x = df["arab_rainfall_scale"] + np.log10(df["spline_rainfall_ratio"])
    x = df["funest_spline_scale"]
    y = df["funest_veg_scale"]

    plt.figure()
    plt.suptitle(catch)
    ax = plt.subplot(211)
    # plt.contour(x,y,df["{}_prevalence_likelihood".format(catch)])
    plt.scatter(x,y,c=df["{}_prevalence_likelihood".format(catch)],zorder=10)
    cb = plt.colorbar()
    cb.set_label("Prevalence Likelihood")
    ax.set_xlabel("LINEAR_SPLINE")
    ax.set_ylabel("WATER_VEGETATION")

    ax = plt.subplot(212)
    # plt.contour(x,y,df["{}_incidence_likelihood".format(catch)])
    plt.scatter(x,y,c=df["{}_incidence_likelihood".format(catch)],zorder=10)
    cb = plt.colorbar()
    cb.set_label("Incidence Likelihood")
    ax.set_xlabel("LINEAR_SPLINE")
    ax.set_ylabel("WATER_VEGETATION")

    plt.tight_layout()
    plt.show()


if True:
    # Arabiensis
    x=df["arab_rainfall_scale"]
    y = df["arab_constant_scale"]

    plt.figure()
    plt.suptitle(catch)
    ax = plt.subplot(211)
    # plt.contour(x,y,df["{}_prevalence_likelihood".format(catch)])
    plt.scatter(x, y, c=df["{}_prevalence_likelihood".format(catch)], zorder=10)
    cb = plt.colorbar()
    ax.set_xlabel("TEMPORARY_RAINFALL")
    ax.set_ylabel("CONSTANT")
    # ax.set_title("Prevalence Likelihood")

    ax = plt.subplot(212)
    # plt.contour(x,y,df["{}_incidence_likelihood".format(catch)])
    plt.scatter(x, y, c=df["{}_incidence_likelihood".format(catch)], zorder=10)
    cb = plt.colorbar()
    cb.set_label("Incidence Likelihood")
    ax.set_xlabel("TEMPORARY_RAINFALL")
    ax.set_ylabel("CONSTANT")

    plt.tight_layout()
    plt.show()

