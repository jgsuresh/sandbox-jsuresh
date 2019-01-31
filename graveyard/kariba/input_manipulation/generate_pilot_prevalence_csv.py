import pandas as pd
import numpy as np

from helpers.relative_time import *

dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/"

df = pd.read_csv(dropbox_base + "inputs/other/pilot_raw.csv")
hlat = np.array(df["houselat"])
hlon = np.array(df["houselong"])
# Grid all house lat/long into grid cells (add column "grid_cell" to pilot dataframe)

# Get lat/long for each grid_cell:
lookup_df = pd.read_csv(dropbox_base + "inputs/grid_csv/grid_lookup.csv")
lon = np.array(lookup_df["lon"])
lat = np.array(lookup_df["lat"])
gc = np.array(lookup_df["grid_cell"])

lon_pts = np.array(list(set(lon)))
lat_pts = np.array(list(set(lat)))

def find_smallest_diff(x):
    smallest = np.abs(np.max(x))
    for x0 in x:
        for x1 in x:
            if x0 != x1:
                dx = np.abs(x1-x0)
                smallest = np.min([dx, smallest])

    return smallest

# dlon = find_smallest_diff(lon_pts)
# dlat = find_smallest_diff(lat_pts)
dlon = 0.009450446299993587
dlat = 0.008983152799995509


house_gc = np.ones_like(hlat) * -1
# Loop over every grid cell:
for i in np.arange(len(gc)):
    print(i)
    lon_cut = np.logical_and(hlon > lon[i] - dlon/2., hlon < lon[i] + dlon/2.)
    lat_cut = np.logical_and(hlat > lat[i] - dlat/2., hlat < lat[i] + dlat/2.)
    cell_cut = np.logical_and(lon_cut,lat_cut)

    house_gc[cell_cut] = gc[i]

# Save into dataframe
df["grid_cell"] = house_gc.astype("int")


# Standardize rdtest values
df = df[df["rdtest"] <= 2]
df["rdtest"][df["rdtest"] == 2] = 0
df.reset_index(inplace=True, drop=True)

# Take only values which are in our grid cells:
df = df[df["grid_cell"] != -1]
df.reset_index(inplace=True, drop=True)

# Prepare to take median day:
df["day_num"] = df["datetaken_x"].apply(lambda x: convert_to_day_365(x,"1/1/2011",date_format = "%m/%d/%Y"))
df["day_num"][np.logical_or(df["day_num"] < 0, df["day_num"] > 500)] = np.nan


# Group by grid cell and compute prevalence, population, and median
g = df.groupby("grid_cell")
day_num = g.median(skipna=True)["day_num"]
N = g.count()["rdtest"]
prev = g.sum()["rdtest"]/g.count()["rdtest"]

day_num = day_num.reset_index()
N = N.reset_index()
prev = prev.reset_index()

collated_df = pd.DataFrame({
    "grid_cell": day_num["grid_cell"],
    "day_num": day_num["day_num"],
    "N": N["rdtest"],
    "prev": prev["rdtest"],
    "round": 0
})

collated_df.dropna(inplace=True)
collated_df.reset_index(inplace=True,drop=True)

# Convert back to date from day number
collated_df["date"] = collated_df["day_num"].apply(lambda x: convert_to_date_365(x,"2011-01-01",date_format = "%Y-%m-%d"))

# Save subset:
collated_df[["grid_cell","round","date","prev","N"]].to_csv(dropbox_base + "inputs/other/pilot_prevalence.csv",index=False)



