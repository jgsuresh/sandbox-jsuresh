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


class prevalence_plot_analyzer(BaseAnalyzer):
    filenames = ['output/SpatialReportMalariaFiltered_Population.bin', 'output/SpatialReportMalariaFiltered_True_Prevalence.bin']

    def __init__(self, sample, save_file=None):
        super(prevalence_plot_analyzer, self).__init__()
        self.metadata = {}
        self.prev = {}
        self.pop = {}
        self.data = {}
        # self.catch = {}

        # self.base = 'C:/Users/jsuresh/OneDrive - IDMOD/Projects/malaria-mz-magude/gridded_sims/'
        self.base = '../../'
        self.save_file = save_file
        # self.start_date = "2009-01-01"#"1955-01-01" #

    def filter(self, sim_metadata):
        if sim_metadata["__sample_index__"] == 0 and sim_metadata["Run_Number"] <= 10:
            return True
        else:
            return False
        # return True

    def apply(self, parser):
        exp_name = parser.experiment.exp_name
        # self.catch[parser.sim_id] = exp_name.split('_')[0] # Assumes the experiment name is "CATCHNAME_full"
        # self.catch[parser.sim_id] = "Panjane"
        self.catch = exp_name.split('_')[1]
        # self.catch = "Motaze"

        pop_df = construct_spatial_output_df(parser.raw_data[self.filenames[0]],'N')
        prev_df = construct_spatial_output_df(parser.raw_data[self.filenames[1]],'prev')

        data_df = pop_df.merge(prev_df,how='inner')

        # Collect aggregated data:
        # self.prev[parser.sim_id] = prev_df
        # self.pop[parser.sim_id] = pop_df
        self.data[parser.sim_id] = data_df
        self.n_tstep = max(data_df['time'])



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
        if self.cait_output_mode:
            sns.set_style("whitegrid")
        else:
            sns.set_style("darkgrid")


        date_format = "%Y-%m-%d"

        date_to_mdate = mdates.strpdate2num(date_format)

        daynum = np.arange(self.n_tstep)
        daydates_list = []
        daydates_mdates = np.array([])
        for dayn in daynum:
            hold = convert_to_date(dayn, self.start_date, date_format=date_format)
            daydates_list.append(hold)
            daydates_mdates = np.append(daydates_mdates,date_to_mdate(hold))

        def binomial_error_bars(N_pos,N):
            # Return 95% confidence for binomial
            # median = N_pos/N
            err = np.array(proportion_confint(N_pos, N, method='beta'))
            if np.sum(np.isnan(err)):
                err[np.isnan(err)] = 0

            # print("Binomial error bars for prevalence plot: ")
            # print(err)

            # errorbar wants not absolute values, but offsets.  convert to that:
            err_as_offset = err #copy?
            err_as_offset[0] = np.abs(err[0] - (N_pos/N))
            err_as_offset[1] = np.abs(err[1] - (N_pos/N))
            return err_as_offset



        def plot_for_cells(ax, cells, title=None, annotate=True):
            lookup_df = MozambiqueExperiment.find_bairros_for_this_catchment(self.catch)
            prev_ref_df = pd.read_csv(self.base + "data/mozambique/grid_prevalence_with_dates.csv")

            # PLOT SIMULATION DATA AS CURVES
            if not self.gatesreview:  # Plot as individual curves:

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
                                  fmt='-', label=label, lw=1.2, color='black',
                                  zorder=10)
            else: # Plot as spread
                all_data = np.zeros([len(daydates_mdates), 10])

                i = 0
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

                    all_data[:, i] = aggregate_df['prev']
                    i += 1

                med_curve = np.apply_along_axis(np.median, 1, all_data)
                # ll_curve = np.apply_along_axis(conf90_ll,1,all_data)
                # ul_curve = np.apply_along_axis(conf90_ul,1,all_data)
                ll_curve = np.apply_along_axis(np.min, 1, all_data)
                ul_curve = np.apply_along_axis(np.max, 1, all_data)

                ax.plot_date(daydates_mdates, med_curve, c='black', ls='-',marker=',',lw=1, label='Simulations') #, label=scenario,zorder=zorder)
                ax.fill_between(daydates_mdates, ll_curve, ul_curve, color='black', alpha=0.7) #,zorder=zorder)


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

            # error bars
            # foo['prev_err'] = err / foo['N']

            ax.scatter(foo['round_mdate'], foo['prev'],
                        c='purple', edgecolors='black', marker='s', alpha=0.95,
                        label = 'Reference', #label='{}: Pop-seen-weighted RDT+'.format(self.catch.capitalize()),
                       # s=foo['N']** 0.67,  # s=70
                        zorder=20)

            err = binomial_error_bars(foo['N_pos'],foo['N'])

            ax.errorbar(foo['round_mdate'], foo['prev'],yerr=err,linestyle='None',
                        c='purple', marker='s', alpha=0.95,label=None,
                        zorder=20)

            # if annotate and not self.cait_output_mode:
            #     for jj in range(len(foo)):
            #         plt.annotate(str(foo['N'][jj]),
            #                      (foo['round_mdate'][jj], foo['prev'][jj]),
            #                      # (foo['round_mdate'][jj]+100, foo['prev'][jj]+0.1),
            #                      size='x-large',zorder=50, color='magenta',weight='bold',alpha=0.9)


            # PLOT INTERVENTION TIMES AS RUGPLOT
            add_cell_intervention_timing_rugs_to_plot(ax,
                                                      cells,
                                                      irs_relative_path="data/mozambique/grid_all_irs_events.csv",
                                                      itn_relative_path="data/mozambique/grid_all_itn_events.csv",
                                                      mda_relative_path="data/mozambique/grid_all_mda_events.csv",
                                                      ymax=1.0,
                                                      lw=2.0,
                                                      alpha=1.0)

            if title:
                ax.set_title(title)


        # Plot 1: Catchment-level plot:
        fig = plt.figure(figsize=(12,5))
        ax = plt.subplot(111)
        catch_cells = MozambiqueExperiment.find_cells_for_this_catchment(self.catch)
        plot_for_cells(ax,catch_cells,title=self.catch)
        if not self.cait_output_mode:
            plt.legend()
        if self.cait_output_mode:
            ax.xaxis.grid(False)

        plt.xlim([date_to_mdate("2014-01-01"), date_to_mdate("2018-03-15")])
        ax.set_xticks([date_to_mdate("2014-01-01"),date_to_mdate("2015-01-01"),date_to_mdate("2016-01-01"),date_to_mdate("2017-01-01"),date_to_mdate("2018-01-01")])
        plt.ylim([-0.01,0.25])
        # plt.xlabel("Date")
        plt.ylabel("RDT Prevalence")
        plt.legend(frameon=True)
        plt.tight_layout()
        if self.save_file:
            # if self.cait_output_mode:
            #     MozambiqueExperiment.save_figs_for_caitlin(fig,self.save_file)
            # else:
            plt.savefig(self.save_file + ".pdf")
            plt.savefig(self.save_file + ".png")
        else:
            plt.show()




        if self.plot_bairros and self.catch != "Magude-Sede-Facazissa":
            plt.close('all')
            plt.figure(figsize=(12,21))
            bairro_df = MozambiqueExperiment.find_bairros_for_this_catchment(self.catch)
            bairro_nums = bairro_df['bairro'].unique()
            bairro_names = bairro_df['bairro_name'].unique()

            n_subplot = 1
            bairro_index = 0
            # print("Number of bairros: ",len(bairro_nums))
            for bairro_num in bairro_nums:
                ax = plt.subplot(8,3,n_subplot)

                try:
                    plot_for_cells(ax,
                                   np.array(bairro_df['grid_cell'][bairro_df['bairro']==bairro_num]),
                                   title='Bairro {}: {}'.format(int(bairro_num),bairro_names[bairro_index]),
                                   annotate=False)
                except:
                    pass

                ax.set_xlim([date_to_mdate("2014-01-01"), date_to_mdate("2020-01-01")])
                ax.set_ylim([-0.01, 0.25])
                if self.cait_output_mode:
                    ax.xaxis.grid(False)
                n_subplot += 1
                bairro_index += 1

            # plt.legend()

            plt.tight_layout()
            if self.save_file:
                plt.savefig(self.save_file + "_BAIRROS.pdf")
                plt.savefig(self.save_file + "_BAIRROS.png")
            else:
                plt.show()



if __name__=="__main__":
    SetupParser.init('HPC')

    am = AnalyzeManager()


    # am.add_experiment(retrieve_experiment("d4b08d09-1835-e811-a2bf-c4346bcb7274")) #caputine iter12. best 8.
    # am.add_experiment(retrieve_experiment("f5e78cbb-1436-e811-a2bf-c4346bcb7274"))  # chichuco iter5.  best 0.  4/1 10:30pm
    # am.add_experiment(retrieve_experiment("f9df132a-c135-e811-a2bf-c4346bcb7274"))  # chicutso iter1. best 6 4/11 10:30pm
    # am.add_experiment(retrieve_experiment("15a20ddd-2a36-e811-a2bf-c4346bcb7274"))  # facazissa iter5. best 0.  4/1 10:30pm
    # am.add_experiment(retrieve_experiment("86413a54-0d36-e811-a2bf-c4346bcb7274"))  # magude iter3. best 10.  4/1 10:30pm  X
    # am.add_experiment(retrieve_experiment("15a1d9fe-2f36-e811-a2bf-c4346bcb7274"))  # mahel iter9.  best 0. 4/1
    #  am.add_experiment(retrieve_experiment("0fc16f8f-2636-e811-a2bf-c4346bcb7274")) # mapulanguene iter9. best 10.  4/1 10:30pm
    # am.add_experiment(retrieve_experiment("f5873afe-1336-e811-a2bf-c4346bcb7274"))  # moine iter6. best 0 4/1
    # am.add_experiment(retrieve_experiment("19794550-c135-e811-a2bf-c4346bcb7274"))  # motaze iter1. best 15 4/1
    # am.add_experiment(retrieve_experiment("e6f8c635-2d36-e811-a2bf-c4346bcb7274"))  # panjane iter6. best 0 4/1

    # am.add_experiment(retrieve_experiment("6fe0132a-c135-e811-a2bf-c4346bcb7274")) # faca stage1, iter1, best 9
    # am.add_experiment(retrieve_experiment("86413a54-0d36-e811-a2bf-c4346bcb7274")) # m-s stage 1. iter3, best 12
    # am.add_experiment(retrieve_experiment("eb30545d-e536-e811-a2bf-c4346bcb7274")) # m-s stage 2.  ite3, best 6

    # am.add_experiment(retrieve_experiment("d4b08d09-1835-e811-a2bf-c4346bcb7274")) #caputine iter12. best 8.
    # am.add_experiment(retrieve_experiment("0fc97f4a-4634-e811-a2bf-c4346bcb7274"))  # chichuco iter0.  best 3
    # am.add_experiment(retrieve_experiment("f67437d5-4e34-e811-a2bf-c4346bcb7274"))  # chicutso iter2. best 3
    # am.add_experiment(retrieve_experiment("d7d2a0be-a234-e811-a2bf-c4346bcb7274")) # facazissa iter3.  best 12
    # am.add_experiment(retrieve_experiment("3240a906-9e33-e811-a2bf-c4346bcb7274"))  # magude iter0. best 21.
    # am.add_experiment(retrieve_experiment("6cd7957f-cb34-e811-a2bf-c4346bcb7274"))  # mahel iter6. best 11.
    # am.add_experiment(retrieve_experiment("0dbd4e00-cc34-e811-a2bf-c4346bcb7274")) # mapulanguene iter8. best 3
    # am.add_experiment(retrieve_experiment("777c34a8-dc34-e811-a2bf-c4346bcb7274"))  # moine iter6. best 8
    # am.add_experiment(retrieve_experiment("5171d868-4634-e811-a2bf-c4346bcb7274"))  # motaze iter0. best 11
    # am.add_experiment(retrieve_experiment("7a5ab67b-dc34-e811-a2bf-c4346bcb7274"))  # panjane iter8. best 17

    # am.add_experiment(retrieve_experiment("2ecf9cd7-9c35-e811-a2bf-c4346bcb7274")) #aggregate 2014.  iter2, best 20
    # am.add_experiment(retrieve_experiment("d8cb3061-ae35-e811-a2bf-c4346bcb7274")) #aggregate 2014,2015.  iter2, best 5

    am.add_experiment(retrieve_experiment("2f76368f-bc57-e811-a2bf-c4346bcb7274"))

    am.add_analyzer(PrevAnalyzer(cait_output_mode=True,gatesreview=True))
    am.analyze()