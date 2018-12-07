import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

import matplotlib.dates as mdates
date_to_mdate = mdates.strpdate2num("%Y-%m-%d")

from zambia_helpers import *
from helpers.relative_time import *

catch = "bbondo"

chw_lookup = pd.read_csv("CHW_grid_lookup.csv")
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

dhis = pd.read_csv("C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/data/Zambia/DHIS/Export_2010-01-01_2018-08-28_TEST2.csv", usecols=dhis_cols)
dhis = dhis[dhis["dataelement"].isin(dhis_dataelements)]
# Convert value to numeric, and return NaN if not possible:
dhis["value"] = pd.to_numeric(dhis["value"],errors='coerce')

                   # dtype={"dataelement": str,
                   #        "period": str,
                   #        "orgunit": str,
                   #        "value": np.int32},
                   # na_filter=True)
dhis.dropna(inplace=True)


def RHC_name_changes(chw_list):
    for chw in chw_list:
        if "Rural Health Centre" in chw:
            split_strings = chw.split('Rural Health Centre')
            alt_name = split_strings[0] + "RHC" + split_strings[1]
            chw_list.append(alt_name)

def diagnostic_plots_catch(catch, save_base="../../figs/incidence/"):
    catch_cells = catchment_grid_cells(catch)

    #fixme Dealing properly with edge case where closest CHW overlaps with other districts as well

    catch_chw_lookup = chw_lookup[np.in1d(chw_lookup['loc.id'], catch_cells)]
    chw_list = sorted(list(set(catch_chw_lookup['closest.chw.name'])))
    print(chw_list)

    HF_names = ["so {} Rural Health Centre".format(catch.capitalize()),"so {} RHC".format(catch.capitalize())]

    RHC_name_changes(chw_list)
    orgunit_list = chw_list + HF_names

    # catch_chw_lookup.to_csv("bbondo_test.csv")
    chw_dhis = dhis[dhis["orgunit"].isin(chw_list)]
    hf_dhis = dhis[dhis["orgunit"].isin(HF_names)]
    catch_dhis = dhis[dhis["orgunit"].isin(orgunit_list)]


    chw_dhis.reset_index(inplace=True)
    hf_dhis.reset_index(inplace=True)


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

            diagnostic_plots_catch(catch)


if __name__=="__main__":
    diagnostic_plots_catch("sulwegonde")
    # diagnostic_plots_all(skip_catch=["cheeba","chipepo","masuku","masuku mines","munyumbwe","nanduba","sinamalima","sulwegonde"])
    # diagnostic_plots_all(skip_catch=["chipepo","masuku mines","nanduba","sinamalima","sulwegonde"])