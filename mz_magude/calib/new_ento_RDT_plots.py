from statsmodels.stats.proportion import proportion_confint

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from relative_time import *
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_experiment
import numpy as np
import pandas as pd
from mozambique_experiments import *
from sim_output_processing.spatial_output_dataframe import construct_spatial_output_df


class PrevAnalyzer(BaseAnalyzer):
    filenames = ['output/ReportMalariaFiltered.json']

    def __init__(self, start_date="1955-01-01", save_file=None):
        super(PrevAnalyzer, self).__init__()
        self.metadata = {}
        self.prev = {}
        self.pop = {}
        self.data = {}

        self.base = '../../'
        self.save_file = save_file
        self.start_date = start_date
        self.catch = 'Magude-Sede-Facazissa'

    def filter(self, sim_metadata):
        if sim_metadata["__sample_index__"] == 0:
            return True
        else:
            return False

    def apply(self, parser):
        exp_name = parser.experiment.exp_name
        # self.catch = exp_name.split('_')[0]

        inset = parser.raw_data[self.filenames[0]]

        self.data[parser.sim_id] = {}
        self.data[parser.sim_id]['True Prevalence'] = inset['Channels']['True Prevalence']['Data']
        self.data[parser.sim_id]['Run_Number'] = parser.sim_data['Run_Number']



    def finalize(self):
        print("")


    # @classmethod
    # def plot_comparison(self):
    def plot(self):
        import matplotlib
        matplotlib.rcParams['pdf.fonttype'] = 42

        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import seaborn as sns
        sns.set_context("talk")
        sns.set_style("whitegrid")

        date_format = "%Y-%m-%d"

        date_to_mdate = mdates.strpdate2num(date_format)

        daynum = np.arange(365 * 65)
        daynum = daynum.astype(np.float)
        daydates_list = []
        daydates_mdates = np.array([])
        for dayn in daynum:
            hold = convert_to_date_365(dayn, self.start_date, date_format=date_format)
            daydates_list.append(hold)
            daydates_mdates = np.append(daydates_mdates,date_to_mdate(hold))

        def binomial_error_bars(N_pos,N):
            # Return 95% confidence for binomial
            # median = N_pos/N
            err = np.array(proportion_confint(N_pos, N, method='beta'))
            if np.sum(np.isnan(err)):
                err[np.isnan(err)] = 0

            # errorbar wants not absolute values, but offsets.  convert to that:
            err_as_offset = err #copy?
            err_as_offset[0] = np.abs(err[0] - (N_pos/N))
            err_as_offset[1] = np.abs(err[1] - (N_pos/N))
            return err_as_offset



        def plot_ref(ax, cells):
            prev_ref_df = pd.read_csv(self.base + "data/mozambique/grid_prevalence_with_dates.csv")

            # PLOT REFERENCE DATA AS POINTS
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
                        c='C4', edgecolors='black', marker='s', alpha=0.95,
                        label = 'Reference', #label='{}: Pop-seen-weighted RDT+'.format(self.catch.capitalize()),
                       # s=foo['N']** 0.67,  # s=70
                        zorder=20)

            err = binomial_error_bars(foo['N_pos'],foo['N'])

            ax.errorbar(foo['round_mdate'], foo['prev'],yerr=err,linestyle='None',
                        c='C4', marker='s', alpha=0.95,label=None,
                        zorder=20)


            # PLOT INTERVENTION TIMES AS RUGPLOT
            gates_review_rugs(ax,
                              cells,
                              irs_relative_path="data/mozambique/grid_all_irs_events.csv",
                              itn_relative_path="data/mozambique/grid_all_itn_events.csv",
                              mda_relative_path="data/mozambique/grid_all_mda_events.csv",
                              ymax=1.0,
                              lw=2.0,
                              alpha=1.0)

        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(111)



        # all_data = np.zeros([len(daydates_mdates),2])


        i = 0
        for sim_id in list(self.data.keys()):
            ax.plot_date(daydates_mdates[-4015:], self.data[sim_id]['True Prevalence'], c='black', ls='-', marker=',', lw=1, label='Simulations')

            i += 1

        # med_curve = np.apply_along_axis(np.median, 1, all_data)
        # ll_curve = np.apply_along_axis(conf90_ll,1,all_data)
        # ul_curve = np.apply_along_axis(conf90_ul,1,all_data)
        # ll_curve = np.apply_along_axis(np.min,1,all_data)
        # ul_curve = np.apply_along_axis(np.max,1,all_data)

        # ax.plot_date(daydates_mdates, ll_curve, c='black', ls='-', marker=',', lw=1, label='Simulations')
        # ax.plot_date(daydates_mdates, ul_curve, c='black', ls='-', marker=',', lw=1)
        # ax.plot_date(daydates_mdates, med_curve, c='black', ls='-',marker=',',lw=1, label='Simulations')
        # ax.fill_between(daydates_mdates, ll_curve, ul_curve, color='black', alpha=0.7)

        catch_cells = MozambiqueExperiment.find_cells_for_this_catchment(self.catch)
        plot_ref(ax,catch_cells)
        # plt.legend()
        ax.xaxis.grid(False)

        plt.xlim([date_to_mdate("2014-01-01"), date_to_mdate("2019-01-01")])
        ax.set_xticks([date_to_mdate("2014-01-01"),date_to_mdate("2015-01-01"),date_to_mdate("2016-01-01"),date_to_mdate("2017-01-01"),date_to_mdate("2018-01-01")])
        plt.ylim([-0.01,0.25])
        # plt.xlabel("Date")
        plt.ylabel("RDT Prevalence")
        # plt.legend(frameon=True)
        plt.tight_layout()
        # if self.save_file:
        #     # if self.cait_output_mode:
        #     #     MozambiqueExperiment.save_figs_for_caitlin(fig,self.save_file)
        #     # else:
        if not self.save_file:
            self.save_file = save_file = "figs/{}".format(self.catch)
        # plt.savefig(self.save_file + ".pdf")
        # plt.savefig(self.save_file + ".png")
        # else:
        plt.show()
        print("Done!")





if __name__=="__main__":
    SetupParser.init('HPC')

    am = AnalyzeManager()
    # am.add_experiment(retrieve_experiment("0a373d77-1f93-e811-a2c0-c4346bcb7275")) # chichuco
    # am.add_experiment(retrieve_experiment("0d801fc0-3c92-e811-a2c0-c4346bcb7275")) # chicutso
    am.add_experiment(retrieve_experiment("c5c3c5bb-a79c-e811-a2c0-c4346bcb7275")) # magude-sede-facazissa
    # am.add_experiment(retrieve_experiment("210bcb89-e696-e811-a2c0-c4346bcb7275")) # mahel
    # am.add_experiment(retrieve_experiment("10238aac-7593-e811-a2c0-c4346bcb7275")) # mapulanguene
    # am.add_experiment(retrieve_experiment("85bef741-2d97-e811-a2c0-c4346bcb7275")) # moine
    # am.add_experiment(retrieve_experiment("140fe8a7-1194-e811-a2c0-c4346bcb7275")) # motaze
    # am.add_experiment(retrieve_experiment("b1c79146-6194-e811-a2c0-c4346bcb7275")) # panjane-caputine

    am.add_analyzer(PrevAnalyzer())
    am.analyze()