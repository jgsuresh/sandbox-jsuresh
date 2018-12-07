import pandas as pd
import numpy as np
import json

from zambia_helpers import *


def catchment_milen_params():
    # Open milen grid cell to cluster lookup:
    base = 'C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/'
    cluster_df = pd.read_csv(os.path.join(base, "inputs/milen/cluster_to_grid_lookup.csv"))
    lookup_df = pd.read_csv(os.path.join(base, "inputs/grid_csv/grid_lookup.csv"))

    lookup_df = lookup_df.merge(cluster_df[["grid_cell","cluster_id","rainfall_scale","spline_scale"]],how='left',left_on='grid_cell', right_on='grid_cell')
    lookup_df.dropna(inplace=True)

    # Loop over catchments
    catch_list = get_catchment_list()
    rainfall_list = []
    spline_list = []

    for catch in catch_list:
        # # For each catchment, get grid cells.
        # catch_cells = catchment_grid_cells(catch)

        catch_lookup = lookup_df["catchment"] == catch
        if np.sum(catch_lookup) == 0:
            rainfall_list.append(np.nan)
            spline_list.append(np.nan)

        else:
            # Get pop-weighted larval habitat params
            catch_df = lookup_df[catch_lookup]
            rainfall_val = np.sum(catch_df["pop"]*catch_df["rainfall_scale"])/np.sum(catch_df["pop"])
            rainfall_list.append(8 + np.log10(rainfall_val))

            spline_val = np.sum(catch_df["pop"] * catch_df["spline_scale"]) / np.sum(catch_df["pop"])
            spline_list.append(8 + np.log10(spline_val))

    output_df = pd.DataFrame({
        "catchment": catch_list,
        "rainfall_pow10": rainfall_list,
        "spline_pow10": spline_list
    })
    output_df["constant_pow10"] = np.log10(2e6)
    output_df["waterveg_pow10"] = np.log10(2e6)

    output_df.to_csv(os.path.join(base,"inputs/milen/catchment_milen_params.csv"))


def convert_milen_best_fit_to_csv():
    # Load Milen's best-fit larval params JSON file and get larval param fit for this cluster_id
    base = 'C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/'
    fn = os.path.join(base, "inputs/milen/milen_best_fits.json")
    f = open(fn,"r")
    larval_fits_dict = json.load(f)
    f.close()

    # Open milen grid cell to cluster lookup:
    cluster_df = pd.read_csv(os.path.join(base, "inputs/milen/cluster_to_grid_lookup.csv"))

    cluster_id_list = list(set(cluster_df["cluster_id"]))

    rainfall_scale_list = []
    spline_scale_list = []

    for cluster_id in cluster_id_list:
        try:
            cluster_dict = larval_fits_dict[cluster_id]['fit']['params']
            rainfall_scale_list.append(cluster_dict["arabiensis_sc"])
            spline_scale_list.append(cluster_dict["funestus_sc"])
        except:
            rainfall_scale_list.append(np.nan)
            spline_scale_list.append(np.nan)

    output_df = pd.DataFrame({
        "cluster_id": cluster_id_list,
        "rainfall_scale": rainfall_scale_list,
        "spline_scale": spline_scale_list
    })

    # Now merge this to the milen cluster CSV:
    cluster_df = cluster_df.merge(output_df, how="left",on="cluster_id")
    cluster_df.to_csv(os.path.join(base, "inputs/milen/cluster_to_grid_lookup_NEW.csv"))

def milen_larval_param_fit_for_cluster(cluster_id):
    # Load Milen's best-fit larval params JSON file and get larval param fit for this cluster_id
    base = 'C:/Users/jsuresh/OneDrive - IDMOD/Projects/zambia-gridded-sims/'
    fn = base + "data/larval_params/milen_best_fits.json"
    f = open(fn,"r")
    larval_fits_dict = json.load(f)
    f.close()

    return_dict = larval_fits_dict[cluster_id]['fit']['params']
    del return_dict['drug_cov']
    del return_dict['itn_level']

    return return_dict


if __name__ == "__main__":
    # convert_milen_best_fit_to_csv()
    catchment_milen_params()