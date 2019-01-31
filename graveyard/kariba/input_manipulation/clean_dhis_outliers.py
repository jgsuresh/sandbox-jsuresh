import pandas as pd
import numpy as np

dhis_df = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/data/Zambia/DHIS/Culled_2010-01-01_2018-08-30.csv")
orgunit_df = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/inputs/other/dhis_orgunits.csv")
# Merge with the orgunit CSV to get HF vs CHW information:
df = dhis_df.merge(orgunit_df[["orgunit","type"]],how='left',on='orgunit')

# Change W1 --> W01 for sorting purposes
def fix_week_string(x):
    # x = row["period"]
    if x[4] == "W" and len(x) == 6:
        return x[:5] + str(int(x[5:])).zfill(2)
    else:
        return x

df["period"] = df["period"].apply(fix_week_string)
# Sort by date
df.sort_values(by=["period"],inplace=True)
df.reset_index(inplace=True,drop=True)

hf_df = df[df["type"]=="HF"]

def get_week(x, ref_year=2010):
    year = int(x[:4])
    week = int(x[5:])
    return (year-ref_year)*52 + week

# hf_df["week_num"] = hf_df["period"].apply(get_week)
week_num = hf_df["period"].apply(get_week)
hf_df = hf_df.reindex(index=week_num)
hf_df = hf_df[["dataelement","orgunit","value","period"]]

def test_func(window_values,window_size=5):
    m = np.mean(window_values)
    std = np.std(window_values)
    c = window_values[2]

    if np.abs(c-m) > 3*std:
        return np.mean(window_values[1:4])
    else:
        return c


# hf_df["rolling_mean"] = hf_df.groupby(["orgunit","dataelement"]).rolling(5,center=True,min_periods=1,on="week_num").value.mean().reset_index()
# temp = hf_df.groupby(["orgunit","dataelement"]).rolling_apply(test_func, 5,center=True,min_periods=5,on="week_num")
# temp = hf_df.groupby(["orgunit","dataelement"]).rolling(5,center=True,min_periods=5,on="week_num")["value"].apply(lambda x: print(x))
temp = hf_df.groupby(["orgunit","dataelement"]).rolling(5,center=True,min_periods=5)["value"].mean()

# Group by orgunit
# def remove_outliers(x):
# Get mean of x
# Get stdev of x
# for central element of x, if it's more than 3 stdev away from mean, then replace it with the average of the two nearest.
