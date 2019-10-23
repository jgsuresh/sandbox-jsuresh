# Use Jaline's code-base to pull from LL_all and plot best:

import sys
sys.path.append('../sims/')
sys.path.append('../analysis/')
sys.path.append('C:/Users/jsuresh/Code/')
sys.path.append('C:/Users/jsuresh/Code/dtk-tools/')
sys.path.append('C:/Users/jsuresh/Code/dtk-tools-malaria/')
sys.path.append('C:/Users/jsuresh/Code/malaria-toolbox/')

from analyze_prev_catchment import PrevAnalyzer
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser
from IncidencePlotter import IncidencePlotter
from GriddedCalibSite import GriddedCalibSite
from vector_species_report_analyzer import VectorSpeciesReportAnalyzer

import pandas as pd
import os
import json
from collections import OrderedDict

base = '../../'
calib_base = "./"

outdir = ""



def RDT_grabby(expname, rank, output_fname=None, plot_bairros=True) :
    calib_folder = calib_base + expname +"/"
    if not output_fname:
        output_fname = calib_folder + "rank{}_rdt".format(rank)

    LL_fname = calib_folder + "_plots/LL_all.csv"
    LL_df = pd.read_csv(LL_fname)
    LL_df.sort_values(by='total', ascending=False, inplace=True)
    LL_df.reset_index(inplace=True)

    sample = LL_df.loc[rank, 'sample']
    iteration = LL_df.loc[rank, 'iteration']

    start_date = "2009-01-01"

    am = AnalyzeManager()
    am.add_analyzer(PrevAnalyzer(start_date=start_date,
                                 save_file=output_fname,
                                 cait_output_mode=True,
                                 plot_bairros=plot_bairros))

    with open(calib_folder+"iter{}/IterationState.json".format(iteration)) as fin:
        iteration_state = json.loads(fin.read())
    siminfo = OrderedDict(iteration_state['simulations'])
    for item in list(siminfo.items()) :
        if item[1]['__sample_index__'] == sample :
            simid = item[0]
            # print("Sim ID: ",simid)
            am.add_simulation(simid)
    am.analyze()


def incidence_grabby(expname, hfca, rank, output_fname=None) :
    calib_folder = calib_base + expname +"/"
    if not output_fname:
        output_fname = calib_folder + "rank{}_cases".format(rank)

    LL_fname = calib_folder + "_plots/LL_all.csv"
    LL_df = pd.read_csv(LL_fname)
    LL_df.sort_values(by='total', ascending=False, inplace=True)
    LL_df.reset_index(inplace=True)

    sample = LL_df.loc[rank, 'sample']
    iteration = LL_df.loc[rank, 'iteration']

    am = AnalyzeManager()
    # am.add_analyzer(IncidencePlotter(GriddedCalibSite(hfca),save_file=output_fname))
    am.add_analyzer(IncidencePlotter(hfca, save_file=output_fname, save_csv=True))

    with open(calib_folder+"iter{}/IterationState.json".format(iteration)) as fin:
        iteration_state = json.loads(fin.read())
    siminfo = OrderedDict(iteration_state['simulations'])
    for item in list(siminfo.items()) :
        if item[1]['__sample_index__'] == sample :
            simid = item[0]
            am.add_simulation(simid)
    am.analyze()



def vector(expname, calib_stage, rank) :
    calib_folder = calib_base + expname +"/"
    output_fname = calib_folder + "rank{}_vectors".format(rank)

    LL_fname = calib_folder + "_plots/LL_all.csv"
    LL_df = pd.read_csv(LL_fname)
    LL_df.sort_values(by='total', ascending=False, inplace=True)
    LL_df.reset_index(inplace=True)

    sample = LL_df.loc[rank, 'sample']
    iteration = LL_df.loc[rank, 'iteration']

    am = AnalyzeManager()
    am.add_analyzer(VectorSpeciesReportAnalyzer(save_file=output_fname, channel='Daily HBR'))

    with open(calib_folder+"iter{}/IterationState.json".format(iteration)) as fin:
        iteration_state = json.loads(fin.read())
    siminfo = OrderedDict(iteration_state['simulations'])
    for item in list(siminfo.items()) :
        if item[1]['__sample_index__'] == sample :
            simid = item[0]
    am.add_simulation(simid)
    am.analyze()


if __name__=="__main__":


    mozamb_catch_list = ["Chichuco", "Chicutso", "Magude-Sede-Facazissa", "Mahel", "Mapulanguene", "Moine", "Motaze", "Panjane-Caputine"]

    # for catch in ["Panjane-Caputine"]:
    #     print("On {}".format(catch))
    #     for calib_stage in [1]:
    #         COMPS_calib_exp_name = 'Calib_{}_AMP120_stage{}'.format(catch, calib_stage)
    #         COMPS_calib_exp_name = 'Calib_{}_stage{}'.format(catch, calib_stage)

    # catch_list = ["Panjane-Caputine","Panjane-Caputine","Motaze","Motaze"]
    # COMPS_calib_exp_name_list = ["Calib_Panjane-Caputine_stage1",
    #                              "Calib_Panjane-Caputine_AMP120_stage1",
    #                              "Calib_Motaze_orig_stage1",
    #                              "Calib_Motaze_AMP120_stage1"]

    # catch_list = ["Motaze"]
    # COMPS_calib_exp_name_list = ["Calib_Motaze_AMP120_stage1"]

    # calib_stage = 1


    dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/Projects/Mozambique/figures/0503/best_calibs/"

    for catch in mozamb_catch_list:
    # for catch in ["Panjane-Caputine","Chichuco"]:
    # catch = "Magude-Sede-Facazissa"

        for imp in [0]:
            if catch == "Magude-Sede-Facazissa":
                base_name = "Calib_{}_pop0_hs1_imp{}_NMF80".format(catch, imp)
            elif catch == "Chichuco":
                base_name = "Calib_{}_pop0_hs0_imp{}_NMF80".format(catch, imp)
            else:
                base_name = "Calib_{}_pop0_hs0_imp{}".format(catch,imp)

            COMPS_calib_exp_name = base_name + "_HFCA"
            rank = 0

            print("{} rank {}".format(COMPS_calib_exp_name, rank))
            try:
                # RDT_grabby(COMPS_calib_exp_name, rank,output_fname=dropbox_base+COMPS_calib_exp_name+"_RDT", plot_bairros=False)
                incidence_grabby(COMPS_calib_exp_name, catch, rank,output_fname=dropbox_base+COMPS_calib_exp_name+"_cases")
            except:
                print("{} rank {} FAILED - may not exist".format(COMPS_calib_exp_name, rank))
