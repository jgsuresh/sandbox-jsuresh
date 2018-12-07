import numpy as np
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

from zambia_helpers import get_catchment_list

sns.set_context("talk")
sns.set_style("darkgrid")

from scipy.optimize import minimize_scalar

# Given gravity migration setup, and node locations/populations, calculate what the scale factor should be so that the median # of trips is in some desired range
dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/inputs/"
lookup_df = pd.read_csv(dropbox_base + "grid_csv/grid_lookup.csv")
trip_duration = 3

def convert_pairwise_to_total_rate(pair_rate_dict):
    tot_rate_dict = {}

    for home_id in list(pair_rate_dict.keys()):
        tot_rate_dict[home_id] = 0
        for dest_id in list(pair_rate_dict[home_id].keys()):
            tot_rate_dict[home_id] += pair_rate_dict[home_id][dest_id]

    return tot_rate_dict


def trip_histogram(individual_trip_count, max_trip_in_hist=20):
    trip_hist = np.arange(max_trip_in_hist+1)
    for i in np.arange(max_trip_in_hist+1):
        trip_hist[i] = np.sum(individual_trip_count==i)
    return [trip_hist, np.arange(max_trip_in_hist+1)]


def run_sim(x_local,node_df):
    # Run a "sim" with this setup of nodes with this x_local.
    pops = np.array(node_df["pop"])
    rate = np.array(node_df["rate"])

    individual_rates = np.repeat(rate,pops)
    individual_trip_count = np.zeros_like(individual_rates)

    # Initialize by drawing from exponential distribution:
    days_until_next_trip = np.array([])
    for j in np.arange(np.size(pops)):
        days_until_next_trip = np.append(days_until_next_trip, np.random.exponential(scale=1./(x_local * rate[j]), size=pops[j]))
    days_until_next_trip = days_until_next_trip.astype("int")


    for i in np.arange(365):
        travelling = days_until_next_trip == 0
        days_until_next_trip[travelling] = trip_duration + np.random.exponential(scale=1./(x_local * individual_rates[travelling]), size=np.sum(travelling))
        individual_trip_count[travelling] += 1

        not_travelling = np.logical_not(travelling)
        days_until_next_trip[not_travelling] -= 1

    # print(np.mean(individual_trip_count))
    return individual_trip_count


def mean_count_run_sim(x_local, node_df, target_mean_trips):
    # print("x: ",x_local)
    individual_trip_count = run_sim(x_local, node_df)
    return np.abs(np.mean(individual_trip_count)-target_mean_trips)


def optimize_sim(node_df, target_mean_trips):
    opt = minimize_scalar(mean_count_run_sim, bounds=(1e-5,10), method='bounded', args=(node_df,target_mean_trips), tol = 0.001)
    # print(opt)
    x_local_opt = opt["x"]
    individual_trip_count = run_sim(x_local_opt,node_df)
    return [x_local_opt, individual_trip_count]


def calc_x_local_catch(catch, target_mean_trips):
    # Load migr rateabilities JSON file:
    fn = os.path.join(dropbox_base,"catchments/{}/{}_grav_migr_local_rates.json".format(catch,catch))
    with open(fn,"r") as f:
        pair_rates_dict = json.load(f)

    tot_rates_dict = convert_pairwise_to_total_rate(pair_rates_dict)

    home_ids = np.array(list(tot_rates_dict.keys())).astype("float")
    rate = np.array(list(tot_rates_dict.values()))

    node_df = pd.DataFrame({
        "home_ids": home_ids.astype("int"),
        "rate": rate
    })

    # Get node populations
    catch_df = lookup_df[lookup_df["catchment"] == catch]
    node_df = node_df.merge(catch_df[["grid_cell","pop"]],how="left",left_on="home_ids",right_on="grid_cell")
    node_df.dropna(inplace=True) #drop work node
    node_df["pop"] = node_df["pop"].astype("int")

    # for x_local in [0.1,1,10]:
    #     print(run_sim(node_df,x_local))
    x_local_opt, individual_trip_count = optimize_sim(node_df, target_mean_trips)
    trip_hist, bins = trip_histogram(individual_trip_count)

    print("Optimal x_local_migration: ",x_local_opt)
    print("Median: ",np.median(individual_trip_count))
    print("Mean: ",np.mean(individual_trip_count))

    # ax = plot_catch_trip_hist()
    plt.close('all')
    plt.figure()
    plt.plot(bins, trip_hist,marker='o')
    plt.axvline(np.mean(individual_trip_count),ls='--')
    plt.title(catch + ": mean trips = {}".format(np.mean(individual_trip_count)))
    plt.xlabel("Local trips")
    plt.ylabel("# Individuals")
    plt.savefig(os.path.join(dropbox_base,"../figs/local_migration/{}.png".format(catch)))

    return x_local_opt
    # print(run_sim(node_df,2))

def calc_x_local_all_catchments(save_dict=True, target_mean_trips=5):
    catchment_list = get_catchment_list()

    catch_list = []
    x_opt_list = []
    for catch in catchment_list:
        print(catch)
        catch_list.append(catch)
        x_opt_list.append(calc_x_local_catch(catch, target_mean_trips))

    df = pd.DataFrame({
        "catch": catch_list,
        "x_Local_Migration": x_opt_list,
    })

    if save_dict:
        df.to_csv(os.path.join(dropbox_base,"grid_csv/x_local_migr_table.csv"), index=False)

if __name__ == "__main__":
    # calc_x_local_catch("batoka")
    # calc_x_local_catch("Chicutso")
    calc_x_local_all_catchments()