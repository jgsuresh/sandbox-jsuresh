import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_context("talk")

import random

import scipy
from scipy.spatial import cKDTree

from statsmodels.stats.proportion import proportion_confint
# https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html

def positivity_within_radius(X, kdt, rdt_pos, rmax, rmin=0):
    near_pts = np.array(kdt.query_ball_point(X, rmax))

    #     print(len(near_pts))
    if rmin > 0:
        too_near_pts = np.array(kdt.query_ball_point(X, rmin))
        # Remove points that are too-near from near_pts
        exclude_too_near_cut = np.logical_not(np.isin(near_pts, too_near_pts))
        #         print("near_pts ",near_pts)
        #         print("too_near_pts ",too_near_pts)
        #         print("exclude_too_near ",exclude_too_near_cut)
        #         print(len(too_near_pts))
        if np.sum(exclude_too_near_cut) == 0:
            near_pts = np.array([])
        else:
            near_pts = near_pts[exclude_too_near_cut]
        #             print("updated near_pts ",near_pts)

    num_near_pts = np.float(len(near_pts))

    if rmin == 0:
        if num_near_pts == 1:
            pos = np.nan
            num_near_pts = 0
        else:
            pos = (np.sum(rdt_pos[near_pts]) - 1) / (num_near_pts - 1)  # minus one to not recount index person themselves
            num_near_pts -= 1
    elif num_near_pts == 0:
        pos = np.nan
        num_near_pts = 0
    else:
        pos = (np.sum(rdt_pos[near_pts])) / (num_near_pts)

    if pos < 0:
        print("negative prev")
        pass


    return pos, num_near_pts



def calculate_avg_prev_around_index_cases(catch_rd_df, rd_kdt, rdt_pos_rd, rmin=0, rmax=5, return_disaggregated_data=False):
    # df: Dataframe for single catchment for a single round
    # rd_kdt: KDTree for ALL catchments for this round
    # rdt_pos_rd: rdt-status for ALL catchments for this round (corresponds to rd_kdt)
    pos_cut = catch_rd_df["rdt_pos"] == 1
    num_pos = np.sum(pos_cut)
    pos_individuals_xy = np.array(catch_rd_df[["x", "y"]][pos_cut])
    # rdt_pos_catch = np.array(catch_rd_df["rdt_pos"])

    # Loop over every RDT-positive, and calculate prevalence around this person within rmin and rmax.
    prev_array = np.zeros(num_pos)
    tot_n_tracker = 0
    tot_np_tracker = 0

    ntot_array = np.array([])
    npos_array = np.array([])

    for ii in np.arange(num_pos):
        X = pos_individuals_xy[ii]

        pos, num_near_pts = positivity_within_radius(X, rd_kdt, rdt_pos_rd, rmax, rmin=rmin)
        prev_array[ii] = pos

        tot_n_tracker += num_near_pts
        tot_np_tracker += num_near_pts * pos

        ntot_array = np.append(ntot_array, num_near_pts)
        npos_array = np.append(npos_array, num_near_pts * pos)


    people_around = np.logical_not(np.isnan(prev_array))
    ntot_array = ntot_array[people_around]
    npos_array = npos_array[people_around]
    prev_array_without_nans = prev_array[people_around]


    if return_disaggregated_data:
        return ntot_array, npos_array
    else:
        return np.mean(prev_array_without_nans)


def randomize_cases(df_rd):
    # Randomize cases for every catchment, but keeping the number of infections in each catchment constant
    # df_rd = df_rd.sort_values(by="catch").reset_index(drop=True)
    cdf_list = []
    shuffled_rdt_pos_array = np.array([])

    for c, cdf in df_rd.groupby("catch"):
        rdt_pos = np.array(cdf["rdt_pos"])
        # np.random.shuffle(rdt_pos)  # Randomize who is RDT+ in the catchment
        # shuffled_rdt_pos = random.sample(rdt_pos, len(rdt_pos))
        shuffled_rdt_pos = np.random.permutation(rdt_pos)
        #         cdf["rdt_pos"] = rdt_pos
        #         cdf_list.append(cdf)
        shuffled_rdt_pos_array = np.append(shuffled_rdt_pos_array, shuffled_rdt_pos)

    return_df = df_rd.copy()
    return_df["rdt_pos"] = shuffled_rdt_pos_array

    return return_df


def calc_binomial_errors(all_rounds_df, rd, catch, rmin=0, rmax=5, alpha=0.05):
    # Get binomial error bars around every observation, then properly aggregate errors when computing the mean.

    df_rd = all_rounds_df[all_rounds_df["round"] == rd].sort_values(by="catch").reset_index(drop=True)
    rd_kdtree = cKDTree(df_rd[["x", "y"]])

    catch_cut = list(df_rd["catch"] == catch)
    catch_df = df_rd[catch_cut]
    rdt_pos_rd = np.array(df_rd["rdt_pos"])
    ntot_array, npos_array = calculate_avg_prev_around_index_cases(catch_df, rd_kdtree, rdt_pos_rd,
                                                       rmax=rmax, rmin=rmin,
                                                       return_disaggregated_data=True)

    n_index = len(ntot_array)

    if n_index == 0:
        return np.nan, np.nan, np.nan
    else:
        center_array = np.zeros_like(ntot_array)
        ci_low_array = np.zeros_like(ntot_array)
        ci_high_array = np.zeros_like(ntot_array)
        for i in np.arange(len(ntot_array)):
            ntot = ntot_array[i]
            npos = npos_array[i]

            ci_low, ci_high = proportion_confint(npos, ntot, method="wilson")
            center_array[i] = npos/ntot
            ci_low_array[i] = ci_low
            ci_high_array[i] = ci_high

        ci_low_diff_array = np.abs(ci_low_array-center_array)
        ci_high_diff_array = np.abs(ci_high_array - center_array)

        mean_final = np.mean(center_array)
        ci_high_final = (1./n_index) * np.sqrt(np.sum(ci_high_diff_array**2))
        ci_low_final = (1./n_index) * np.sqrt(np.sum(ci_low_diff_array ** 2))

        return mean_final, mean_final-ci_low_final, mean_final+ci_high_final

def bootstrap_permutations(all_rounds_df, rd, catch, rmin=0, rmax=5, n_permutations=99):
    # Rearrange the RDT-positive cases, and calculate prevalence around index cases.  Store these results into an array

    # Spatial information is not varied, so generate a kdTree of everyone's positions in this round
    unshuffled_df_rd = all_rounds_df[all_rounds_df["round"] == rd].sort_values(by="catch").reset_index(drop=True)
    rd_kdtree = cKDTree(unshuffled_df_rd[["x", "y"]])
    catch_cut = list(unshuffled_df_rd["catch"] == catch)

    unshuffled_catch_df = unshuffled_df_rd[catch_cut]
    unshuffled_rdt_pos_rd = np.array(unshuffled_df_rd["rdt_pos"])
    real_value = calculate_avg_prev_around_index_cases(unshuffled_catch_df, rd_kdtree, unshuffled_rdt_pos_rd, rmax=rmax, rmin=rmin)
    print("Value from real data ", real_value)

    shuffled_values_arr = np.zeros(n_permutations)
    for i in np.arange(n_permutations):
        shuffled_df_rd = randomize_cases(unshuffled_df_rd)

        shuffled_catch_df = shuffled_df_rd[catch_cut]
        shuffled_rdt_pos_rd = np.array(shuffled_df_rd["rdt_pos"])
        shuffled_values_arr[i] = calculate_avg_prev_around_index_cases(shuffled_catch_df, rd_kdtree, shuffled_rdt_pos_rd,
                                                                       rmax=rmax, rmin=rmin)

        print(i, shuffled_values_arr[i])

    return real_value, shuffled_values_arr

def save_bootstrap_figures():
    all_rds_df = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/Zambia/rcd_enrichment_radius/all_rounds_data_cleaned.csv")
    all_rds_df = all_rds_df.sort_values(by=["round","catch"]).reset_index(drop=True)


    rmin_list = [0,5,50,100,140]
    rmax_list = [5,50,100,140,200]

    # catch = "Luumbo"
    # rd = 9


    for catch in list(set(all_rds_df["catch"])):
        print(catch)
        for rd in range(1,11):
            print(rd)
            for i in range(len(rmin_list)):
                rmin = rmin_list[i]
                rmax = rmax_list[i]
                print("R: {} to {}".format(rmin, rmax))

                sdf = all_rds_df[np.logical_and(all_rds_df["round"] == rd, all_rds_df["catch"] == catch)]
                if len(sdf) < 50:
                    print("Insufficient people ({})".format(len(sdf)))

                else:
                    real_value, shuffled_values = bootstrap_permutations(all_rds_df, rd, catch, rmin=rmin, rmax=rmax, n_permutations=100)

                    plt.close('all')
                    plt.figure()
                    plt.hist(shuffled_values, label="Randomized infections", bins=10)

                    # # Plot actual catchment prevalence for comparison:
                    sdf = all_rds_df[np.logical_and(all_rds_df["round"]==rd, all_rds_df["catch"]==catch)]
                    plt.axvline(np.sum(sdf["rdt_pos"])/len(sdf), label="Catchment prevalence", color='grey')
                    #
                    plt.axvline(real_value, color='black', label="Observed")
                    plt.xlabel("Prevalence around infections, from {} to {} meters".format(rmin, rmax))
                    plt.title("{} - round {}".format(catch, rd))
                    plt.legend()
                    # plt.show()
                    plt.tight_layout()
                    plt.savefig("figs/{}_rd{}_r{}-{}.png".format(catch, rd, rmin, rmax))









if __name__=="__main__":
    all_rds_df = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/Zambia/rcd_enrichment_radius/all_rounds_data_cleaned.csv")
    all_rds_df = all_rds_df.sort_values(by=["round","catch"]).reset_index(drop=True)

        rmin_list = [0,5,50,100,140]
        rmax_list = [5,50,100,140,200]

    catch_list = []
    round_list = []
    center = np.array([])
    ci_low = np.array([])
    ci_high = np.array([])

    for catch in list(set(all_rds_df["catch"])):
        print(catch)
        for rd in range(1,11):
            print(rd)
            for i in range(len(rmin_list)):
                rmin = rmin_list[i]
                rmax = rmax_list[i]
                print("R: {} to {}".format(rmin, rmax))

                sdf = all_rds_df[np.logical_and(all_rds_df["round"] == rd, all_rds_df["catch"] == catch)]
                if len(sdf) < 50:
                    print("Insufficient people ({})".format(len(sdf)))

                else:
                    catch_center, catch_ci_low, catch_ci_high = calc_binomial_errors(all_rds_df, rd, catch, rmin=rmin, rmax=rmax)
                    print(catch_center, catch_ci_low, catch_ci_high)
                    catch_list.append(catch)
                    round_list.append(rd)
                    center = np.append(center, catch_center)
                    ci_low = np.append(ci_low, catch_ci_low)
                    ci_high = np.append(ci_high, catch_ci_high)


    df_save = pd.DataFrame({
        "catch": catch_list,
        "round": round_list,
        "center": center,
        "ci_low": ci_low,
        "ci_high": ci_high
    })

    df_save.to_csv("save_test.csv", index=False)
