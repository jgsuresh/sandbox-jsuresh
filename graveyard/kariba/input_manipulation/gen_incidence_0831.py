import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from itertools import compress

import matplotlib.dates as mdates
date_to_mdate = mdates.strpdate2num("%Y-%m-%d")

import seaborn as sns
sns.set_context("talk")
sns.set_style("darkgrid")


from zambia_helpers import *
from helpers.relative_time import *

base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/"
save_base = os.path.join(base,"figs/incidence/")

chw_lookup = pd.read_csv(os.path.join(base,"inputs/other/","dhis_orgunits.csv"))
dhis_cols = ["dataelement","period","orgunit","value"]
# CHW: RDT stocks, Passive Number Positive, Index Cases followed up, Active Number Tested
# HF: Clinical malaria cases, RDT stocks, RDT positive cases, RDT tested cases
dhis_dataelements = ["RDT Stocks: RDT Balance on hand",
                     "Passive Number Positive",
                     "Index Cases followed up",
                     "Active Number Tested",
                     "Clinical malaria cases",
                     "RDT positive cases",
                     "RDT tested cases"]

dhis = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/data/Zambia/DHIS/Export_2010-01-01_2018-08-30.csv", usecols=dhis_cols)
dhis = dhis[dhis["dataelement"].isin(dhis_dataelements)]
# Convert value to numeric, and return NaN if not possible:
dhis["value"] = pd.to_numeric(dhis["value"],errors='coerce')

dhis.dropna(inplace=True)


def gen_incidence_catch(catch):
    catch_chw_lookup = chw_lookup[chw_lookup['catch']==catch]
    chw_list = sorted(list(set(catch_chw_lookup[catch_chw_lookup['type']=='CHW']['orgunit'])))
    hf_list = sorted(list(set(catch_chw_lookup[catch_chw_lookup['type']=='HF']['orgunit'])))
    print("CHWs: ", chw_list)
    print("HFs: ", hf_list)

    chw_dhis = dhis[dhis["orgunit"].isin(chw_list)]
    hf_dhis = dhis[dhis["orgunit"].isin(hf_list)]
    chw_dhis.reset_index(inplace=True)
    hf_dhis.reset_index(inplace=True)

    # We want to aggregate these together into monthly counts.
    # First convert the CHW dataframe into a monthly incidence (it's already monthly reporting):
    summed_chw_dhis = chw_dhis.groupby(['period','dataelement']).agg({'value': 'sum'})
    summed_chw_dhis.reset_index(inplace=True)

    summed_chw_incidence = summed_chw_dhis[summed_chw_dhis["dataelement"] == "Passive Number Positive"]
    summed_chw_incidence = summed_chw_incidence[["period","value"]]
    monthly_incidence = summed_chw_incidence.copy(deep=True)
    monthly_incidence.rename(columns={"value":"CHW cases"}, inplace=True)

    # Now add the health facility incidence
    if len(hf_dhis) == 0:
        monthly_incidence["Total cases"] = monthly_incidence["CHW cases"]
    else:
        summed_hf_dhis = hf_dhis.groupby(['period','dataelement']).agg({'value':'sum'})
        summed_hf_dhis.reset_index(inplace=True)
        summed_hf_dhis = summed_hf_dhis[summed_hf_dhis["dataelement"].isin(["RDT positive cases","Clinical malaria cases"])]
        summed_hf_incidence = summed_hf_dhis.groupby(['period']).agg({'value': 'sum'})
        summed_hf_incidence.reset_index(inplace=True)

        summed_hf_incidence = summed_hf_incidence[["period", "value"]]
        monthly_hf_incidence = aggregate_weeks_to_months(summed_hf_incidence)
        monthly_hf_incidence.rename(columns={"value": "HF cases"}, inplace=True)

        monthly_incidence = monthly_incidence.merge(monthly_hf_incidence, how='outer', left_on="period", right_on="period")
        monthly_incidence.fillna(value=0, inplace=True)

        monthly_incidence["Total cases"] = monthly_incidence["CHW cases"] + monthly_incidence["HF cases"]

    # Remove spurious early zeros:
    monthly_incidence = monthly_incidence[np.logical_or(monthly_incidence["period"] > "2012", monthly_incidence["Total cases"] > 0)]

    # Also cut off at end of data capture:
    monthly_incidence = monthly_incidence[monthly_incidence["period"] < "201809"]
    monthly_incidence.reset_index(inplace=True,drop=True)
    monthly_incidence["mdate"] = monthly_incidence["period"].apply(lambda x: convert_CHW_period_to_mdate(x))


    monthly_incidence.sort_values(by=['period'], inplace=True)
    # monthly_incidence = aggregate_weeks_to_months(summed_chw_incidence)


    # Make diagnostic plots:
    # different incidence metrics vs time

    # plt.figure(figsize=(10,5))
    # plt.plot_date(monthly_incidence["mdate"],monthly_incidence["CHW cases"],ls='-',fmt=',',label='CHW cases')
    # if "HF cases" in monthly_incidence.columns:
    #     plt.plot_date(monthly_incidence["mdate"],monthly_incidence["HF cases"],ls='-',fmt=',',label='HF cases')
    # plt.plot_date(monthly_incidence["mdate"],monthly_incidence["Total cases"],ls='-',fmt=',',label='Total cases')
    # plt.legend()
    # plt.ylabel("Case count")
    # plt.title(catch)
    # plt.show()
    # plt.savefig(os.path.join(save_base, "{}.png".format(catch)))

    return monthly_incidence


# def gen_incidence_all_catches(start_catch=None,skip_catch=[]):
#     if start_catch:
#         start_flag=False
#     else:
#         start_flag=True
#
#     for catch in get_catchment_list():
#
#         if catch not in skip_catch and start_flag:
#             print(catch)
#
#             gen_incidence_catch(catch)

def gen_incidence_all_catches():
    catch_df_list = []

    for catch in get_catchment_list():
        catch_df = gen_incidence_catch(catch)
        catch_df["catch"] = catch
        catch_df_list.append(catch_df)

    full_incidence = pd.concat(catch_df_list, ignore_index=True)
    full_incidence.to_csv(base + "inputs/grid_csv/catch_incidence.csv", index=False)

def convert_CHW_period_to_date(period_string):
    # example: "201508"
    year = period_string[:4]
    month = period_string[4:]
    return "{}-{}-15".format(year, month)

def convert_HF_period_to_date(period_string):
    # example: "2015W14"
    year = period_string[:4]
    week = period_string[5:]

    dayn = 3 + 7*(np.int(week)-1)

    return convert_to_date_365(dayn, "{}-01-01".format(year))


def convert_CHW_period_to_mdate(period_string):
    date_str = convert_CHW_period_to_date(period_string)
    return date_to_mdate(date_str)

def convert_HF_period_to_mdate(period_string):
    date_str = convert_HF_period_to_date(period_string)
    return date_to_mdate(date_str)


# def diagnostic_plots_all(start_catch=None,skip_catch=[]):
#     if start_catch:
#         start_flag=False
#     else:
#         start_flag=True
#
#     for catch in get_catchment_list():
#         if start_catch and catch == start_catch:
#             start_flag = True
#
#         if catch not in skip_catch and start_flag:
#             print(catch)
#
#             diagnostic_plots_catch(catch, save_base=os.path.join(base,"figs/incidence/"))


def find_matches_in_dhis(org):

    org_list = list(set(dhis["orgunit"]))

    mask_list = list(map(lambda x: org in x, org_list))
    match_list = list(compress(org_list,mask_list))
    # print(match_list)
    for match in match_list:
        print(match)
    return match_list


# if __name__=="__main__":

# diagnostic_plots_catch("sulwegonde")
# diagnostic_plots_all(skip_catch=["cheeba","chipepo","masuku","masuku mines","munyumbwe","nanduba","sinamalima","sulwegonde"])
# diagnostic_plots_all(skip_catch=["chipepo","masuku mines","nanduba","sinamalima","sulwegonde"])
# diagnostic_plots_all(skip_catch=["chipepo","chipepo siavonga","gvdc","ibbwemunyama","jamba"], start_catch="jamba")
# diagnostic_plots_all(start_catch="sulwegonde")

gen_incidence_all_catches()

# compare_shimin_to_dhis()