import pandas as pd
from helpers.relative_time import *

dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/inputs/grid_csv/"

prev_df = pd.read_csv(dropbox_base + "grid_prevalence.csv")
lookup_df = pd.read_csv(dropbox_base + "grid_lookup.csv")

prev_df["N_pos"] = prev_df["N"]*prev_df["prev"]
ref_date = "2010-01-01"
prev_df["daynum"] = prev_df["date"].apply(lambda x: convert_to_day_365(x,ref_date))
prev_df["daynum_times_N"] = prev_df["daynum"] * prev_df["N"]

full = prev_df.merge(lookup_df,how='left')
full.dropna(inplace=True)

rd_df = full.groupby(["round","catchment"]).agg({"N":"sum","N_pos":"sum","daynum_times_N": "sum"})
rd_df.reset_index(inplace=True)

rd_df['prev'] = rd_df['N_pos']/rd_df['N']
rd_df['daynum_weighted_avg'] = rd_df["daynum_times_N"]/rd_df["N"]
rd_df['date_weighted_avg'] = rd_df["daynum_weighted_avg"].apply(lambda x: convert_to_date_365(x, ref_date))

save_df = rd_df[['round','date_weighted_avg','catchment','N','N_pos','prev']]

save_df.to_csv(dropbox_base + "round_prevalence_NEW.csv",index=False)