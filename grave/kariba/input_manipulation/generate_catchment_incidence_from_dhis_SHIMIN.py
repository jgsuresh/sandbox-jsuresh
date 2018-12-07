import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from itertools import compress

import matplotlib.dates as mdates
date_to_mdate = mdates.strpdate2num("%Y-%m-%d")

from zambia_helpers import *
from helpers.relative_time import *

base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/"

chw_lookup = pd.read_csv(os.path.join(base,"inputs/other/","Master_CHW_HF_MACEPA_CHW_ZM.csv"))
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



def diagnostic_plots_catch(catch, save_base="../../figs/incidence/"):
    # Use Shimin's list of "real catchment" to assign CHW/HF to catchment

    if catch == "chipepo":
        catch_name = "Chipepo Gwembe"
    elif catch == "gvdc":
        catch_name = "GVDC"
    else:
        catch_name = catch.title()

    catch_chw_lookup = chw_lookup[chw_lookup['hf.catch.real']==catch_name]
    chw_list = sorted(list(set(catch_chw_lookup[catch_chw_lookup['type']=='Community Health Worker']['name'])))
    hf_list = sorted(list(set(catch_chw_lookup[catch_chw_lookup['type']!='Community Health Worker']['name'])))
    print("CHWs: ", chw_list)
    print("HFs: ", hf_list)

    chw_dhis = dhis[dhis["orgunit"].isin(chw_list)]
    hf_dhis = dhis[dhis["orgunit"].isin(hf_list)]
    chw_dhis.reset_index(inplace=True)
    hf_dhis.reset_index(inplace=True)

    print(chw_dhis)
    print(hf_dhis)


    #CHW: RDT stocks, Passive Number Positive, Index Cases followed up, Active Number Tested
    # HF: Clinical malaria cases, RDT stocks, RDT positive cases, RDT tested cases
    chw_dhis['mdate'] = chw_dhis["period"].apply(lambda x: convert_CHW_period_to_mdate(x))
    hf_dhis['mdate'] = hf_dhis["period"].apply(lambda x: convert_HF_period_to_mdate(x))

    chw_dhis.sort_values(by=['mdate'],inplace=True)
    hf_dhis.sort_values(by=['mdate'],inplace=True)

    summed_chw_dhis = chw_dhis.groupby(['mdate','dataelement']).agg({'value': 'sum'})
    summed_chw_dhis.reset_index(inplace=True)

    # Make diagnostic plots:
    # different incidence metrics vs time

    plt.figure(figsize=(10,5))
    cut = summed_chw_dhis['dataelement']=='Passive Number Positive'
    plt.plot_date(summed_chw_dhis['mdate'][cut], summed_chw_dhis['value'][cut],ls='-', label='CHWs: Passive Number Positive', zorder=2)
    cut = hf_dhis['dataelement']=='RDT positive cases'
    plt.plot_date(hf_dhis['mdate'][cut], hf_dhis['value'][cut],ls='-', label='HF: RDT positive cases',zorder=1)
    plt.legend()
    plt.ylabel("Count")
    # plt.show()
    plt.title(catch)
    plt.savefig(os.path.join(save_base,"{}_CHW_vs_HF.png".format(catch)))
    # CHW incidence vs HF incidence


    plt.close('all')
    plt.figure(figsize=(10, 5))
    cut = hf_dhis['dataelement']=='RDT positive cases'
    plt.plot_date(hf_dhis['mdate'][cut], hf_dhis['value'][cut],ls='-', label='HF: RDT positive cases')
    cut = hf_dhis['dataelement']=='Clinical malaria cases'
    plt.plot_date(hf_dhis['mdate'][cut], hf_dhis['value'][cut],ls='-', label='HF: Clinical malaria cases')
    cut = hf_dhis['dataelement']=='RDT tested cases'
    plt.plot_date(hf_dhis['mdate'][cut], hf_dhis['value'][cut],ls='-', label='HF: RDT tested cases')
    cut = np.logical_and(hf_dhis['dataelement'] == 'RDT Stocks: RDT Balance on hand',hf_dhis['value']==0)
    if np.sum(cut) > 0:
        plt.plot_date(hf_dhis['mdate'][cut], hf_dhis['value'][cut], ls='--', color='black', label='HF: RDT Stocks is ZERO')
    plt.legend()
    plt.title(catch)
    plt.ylabel("Count")
    plt.savefig(os.path.join(save_base,"{}_HF.png".format(catch)))



    plt.close('all')
    plt.figure(figsize=(10, 5))
    cut = summed_chw_dhis['dataelement']=='Passive Number Positive'
    plt.plot_date(summed_chw_dhis['mdate'][cut], summed_chw_dhis['value'][cut],ls='-', label='CHW: Passive Number Positive')
    cut = summed_chw_dhis['dataelement']=='Index Cases followed up'
    plt.plot_date(summed_chw_dhis['mdate'][cut], summed_chw_dhis['value'][cut],ls='-', label='CHW: Index Cases Followed up')
    cut = summed_chw_dhis['dataelement']=='Active Number Tested'
    plt.plot_date(summed_chw_dhis['mdate'][cut], summed_chw_dhis['value'][cut],ls='-', label='CHW: Active Number Tested')
    cut = np.logical_and(summed_chw_dhis['dataelement'] == 'RDT Stocks: RDT Balance on hand',summed_chw_dhis['value']==0)
    if np.sum(cut) > 0:
        plt.plot_date(summed_chw_dhis['mdate'][cut], summed_chw_dhis['value'][cut], ls='--', color='black', label='CHW: RDT Stocks is ZERO')
    plt.legend()
    plt.title(catch)
    plt.ylabel("Count")
    # plt.show()
    plt.savefig(os.path.join(save_base,"{}_CHW.png".format(catch)))



def convert_CHW_period_to_date(period_string):
    # example: "201508"
    year = period_string[:4]
    # if period_string[4] == "W":
    #     print
    month = period_string[4:]
    # month = np.int(period_string[4:])
    #
    # # Assume that, for example, "April
    # month += 1
    # if month == 13:
    #     month = 1
    #
    # return "{}-{}-01".format(year, month)

    return "{}-{}-15".format(year, month)

def convert_HF_period_to_date(period_string):
    # example: "2015W14"
    year = period_string[:4]
    week = period_string[5:]

    dayn = 3 + 7*(np.int(week)-1)

    return convert_to_date_365(dayn, "{}-01-01".format(year))


def convert_CHW_period_to_mdate(period_string):
    date_str = convert_CHW_period_to_date(period_string)
    if date_str == "2012-W28-15":
        print(period_string)
        exit()
    return date_to_mdate(date_str)

def convert_HF_period_to_mdate(period_string):
    date_str = convert_HF_period_to_date(period_string)
    return date_to_mdate(date_str)


def diagnostic_plots_all(start_catch=None,skip_catch=[]):
    if start_catch:
        start_flag=False
    else:
        start_flag=True

    for catch in get_catchment_list():
        if start_catch and catch == start_catch:
            start_flag = True

        if catch not in skip_catch and start_flag:
            print(catch)

            diagnostic_plots_catch(catch, save_base=os.path.join(base,"figs/incidence/"))


def find_matches_in_dhis(org):

    org_list = list(set(dhis["orgunit"]))

    mask_list = list(map(lambda x: org in x, org_list))
    match_list = list(compress(org_list,mask_list))
    # print(match_list)
    for match in match_list:
        print(match)
    return match_list


def compare_shimin_to_dhis():
    for catch in get_catchment_list():
        print(catch)

        # Shimin:
        if catch == "chipepo":
            # catch_name = "Chipepo Gwembe"
            catch_name = "Chipepo"
        elif catch == "gvdc":
            catch_name = "GVDC"
        elif catch == "simwatchela":
            catch_name = "Simwatachela"
        else:
            catch_name = catch.title()

        # print(chw_lookup[np.logical_or(chw_lookup["hf.catch.close"]==catch_name, chw_lookup["hf.catch.real"]==catch_name)])



        # DHIS:
        find_matches_in_dhis(catch)
        find_matches_in_dhis(catch_name)

# if __name__=="__main__":

# diagnostic_plots_catch("sulwegonde")
# diagnostic_plots_all(skip_catch=["cheeba","chipepo","masuku","masuku mines","munyumbwe","nanduba","sinamalima","sulwegonde"])
# diagnostic_plots_all(skip_catch=["chipepo","masuku mines","nanduba","sinamalima","sulwegonde"])
# diagnostic_plots_all(skip_catch=["chipepo","chipepo siavonga","gvdc","ibbwemunyama","jamba"], start_catch="jamba")
# diagnostic_plots_all(start_catch="manchanvwa", skip_catch=["manchanvwa"])


compare_shimin_to_dhis()