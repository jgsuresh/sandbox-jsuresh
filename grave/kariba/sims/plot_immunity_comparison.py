from plot_best_calibs import prevalence_plot_analyzer

import os
import json
import numpy as np
import matplotlib
from statsmodels.stats.proportion import proportion_confint

matplotlib.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from sim_output_processing.spatial_output_dataframe import construct_spatial_output_df
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from helpers.relative_time import *
from simtools.SetupParser import SetupParser

from zambia_helpers import *

class custom_prev_plot_analyzer(prevalence_plot_analyzer):

    def __init__(self, catch, color, max_individ_infections, save_file=None):
        super(custom_prev_plot_analyzer, self).__init__(catch, -1, save_file=None)
        self.color = color
        self.max_individ_infections = max_individ_infections

    def filter(self, sim_metadata):
        return sim_metadata["Max_Individual_Infections"] == self.max_individ_infections


    def plot(self):
        sns.set_context("talk")
        # if self.cait_output_mode:
        #     sns.set_style("whitegrid")
        # else:
        #     sns.set_style("darkgrid")
        sns.set_style("darkgrid")

        date_format = "%Y-%m-%d"
        date_to_mdate = mdates.strpdate2num(date_format)

        daynum = np.arange(self.n_tstep, dtype=np.float)
        daydates_list = []
        daydates_mdates = np.array([])
        for dayn in daynum:
            hold = convert_to_date_365(dayn, self.start_date, date_format=date_format)
            daydates_list.append(hold)
            daydates_mdates = np.append(daydates_mdates,date_to_mdate(hold))


        def plot_for_cells(ax, cells, title=None, annotate=True):
            prev_ref_df = pd.read_csv(self.dropbox_base + "inputs/grid_csv/grid_prevalence.csv")

            n_seeds = len(list(self.data.keys()))

            # If <= 3 curves, then plot individual curves
            # if n_seeds <= 3:
            for sim_id in list(self.data.keys()):
                data_df = self.data[sim_id]
                data_df = data_df[np.in1d(data_df['node'], cells)]
                data_df['N_pos'] = data_df['N'] * data_df['prev']

                aggregate_df = data_df.groupby('time').agg({'N': 'sum', 'N_pos': 'sum'}).reset_index()
                aggregate_df['prev'] = aggregate_df['N_pos'] / aggregate_df['N']
                aggregate_df['mdate'] = aggregate_df['time'].apply(lambda x: date_to_mdate(convert_to_date_365(x,self.start_date)))

                if "label" not in locals():
                    label = "Simulations"
                else:
                    label = None

                ax.plot_date(np.array(aggregate_df['mdate']), np.array(aggregate_df['prev']),
                              fmt='-', label=label, lw=1.2, color=self.color,
                              zorder=10)

            # PLOT REFERENCE DATA AS POINTS

            # if self.max_individ_infections == 3:
            prev_ref_df = prev_ref_df[np.in1d(prev_ref_df['grid_cell'],cells)]
            prev_ref_df['day_num'] = prev_ref_df['date'].apply(lambda x: convert_to_day_365(x, self.start_date))

            prev_ref_df = prev_ref_df[prev_ref_df['N'] > 0]

            prev_ref_df['N_pos'] = prev_ref_df['N'] * prev_ref_df['prev']
            prev_ref_df['N_times_day'] = prev_ref_df['N'] * prev_ref_df['day_num']
            foo = prev_ref_df.groupby('round').agg({'N':'sum',
                                                    'N_pos': 'sum',
                                                    'N_times_day': 'sum'}).reset_index()
            foo['prev'] = foo['N_pos'] / (foo['N'])
            foo['round_day'] = (foo['N_times_day'] / (foo['N'])).astype(int)
            foo['round_date'] = foo['round_day'].apply(lambda x: convert_to_date_365(x, self.start_date))
            foo['round_mdate'] = foo['round_date'].apply(lambda x: date_to_mdate(x))


            ax.scatter(foo['round_mdate'], foo['prev'],
                        c='purple', edgecolors='black', marker='s', alpha=0.95,
                        label = 'Reference', #label='{}: Pop-seen-weighted RDT+'.format(self.catch.capitalize()),
                       # s=foo['N']** 0.67,  # s=70
                        zorder=20)

            err = binomial_error_bars(foo['N_pos'],foo['N'])

            ax.errorbar(foo['round_mdate'], foo['prev'],yerr=err,linestyle='None',
                        c='purple', marker='s', alpha=0.95,label=None,
                        zorder=20)


            # PLOT INTERVENTION TIMES AS RUGPLOT
            add_intervention_rugs_to_plot(ax, cells)

            if title:
                ax.set_title(title)


        # Plot 1: Catchment-level plot:
        # if self.max_individ_infections == 3:
        fig = plt.figure(figsize=(12,5))
        ax = plt.subplot(111)
        # else:
        #     ax = plt.gca()
        catch_cells = catchment_grid_cells(self.catch)
        plot_for_cells(ax,catch_cells,title=self.catch)

        # if not self.cait_output_mode:
        #     plt.legend()
        # if self.cait_output_mode:
        #     ax.xaxis.grid(False)

        plt.xlim([date_to_mdate("2011-01-01"), date_to_mdate("2019-01-01")])

        ax.set_xticks([date_to_mdate("2012-01-01"),
                       date_to_mdate("2013-01-01"),
                       date_to_mdate("2014-01-01"),
                       date_to_mdate("2015-01-01"),
                       date_to_mdate("2016-01-01"),
                       date_to_mdate("2017-01-01"),
                       date_to_mdate("2018-01-01"),
                       date_to_mdate("2019-01-01")])

        # plt.ylim([-0.01,0.25])
        plt.ylabel("RDT Prevalence")
        plt.legend(frameon=True)
        plt.tight_layout()
        if self.save_file:
            plt.savefig(self.save_file + ".pdf")
            plt.savefig(self.save_file + ".png")
        else:
            plt.show()



if __name__ == "__main__":
    am = AnalyzeManager()
    # am.add_experiment(retrieve_experiment("cdb12c2d-61c3-e811-a2bd-c4346bcb1555"))
    am.add_experiment(retrieve_experiment("9df3a55a-63c3-e811-a2bd-c4346bcb1555"))
    # am.add_analyzer(custom_prev_plot_analyzer("chiyabi","C0", 3))
    # am.add_analyzer(custom_prev_plot_analyzer("chiyabi","C1", 4))
    am.add_analyzer(custom_prev_plot_analyzer("chiyabi","C2", 5))
    # am.add_analyzer(custom_prev_plot_analyzer("chiyabi","C3", 6))
    am.analyze()
