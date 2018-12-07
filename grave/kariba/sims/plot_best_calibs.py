# Parse CalibManager.json to get best runs and make custom plots of them:
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


def parse_calib_manager(fit_type="full"): #calib_folder_path, plot_best_N=5):
    fn = os.path.join(calib_folder_path, "CalibManager.json")
    with open(fn,'r') as f:
        cm = json.load(f)

    cm_df = pd.DataFrame(cm['results'])

    if fit_type == "full":
        cm_df.sort_values('total', ascending=False, inplace=True)
    elif fit_type == "prevalence":
        cm_df.sort_values('{}_prevalence_likelihood'.format(catch), ascending=False, inplace=True)
    elif fit_type == "incidence":
        cm_df.sort_values('{}_incidence_likelihood'.format(catch), ascending=False, inplace=True)
    best_iter_list = list(cm_df['iteration'][:plot_best_N])
    best_sample_list = list(cm_df['sample'][:plot_best_N])

    best_expid_list = []
    for j in range(plot_best_N):
        iter = best_iter_list[j]

        iter_fn = os.path.join(calib_folder_path, "iter{}".format(iter),"IterationState.json")
        with open(iter_fn,'r') as f:
            iter_dict = json.load(f)
            best_expid_list.append(iter_dict['experiment_id'])

    return [best_expid_list, best_iter_list, best_sample_list]





# best_expid_list, best_iter_list, best_sample_list = parse_calib_manager()

def plot_best(fit_type="full"):
    best_expid_list, best_iter_list, best_sample_list = parse_calib_manager(fit_type=fit_type)

    for r in range(plot_best_N):
        print("Rank ",r)
        expid = best_expid_list[r]
        i = best_iter_list[r]
        s = best_sample_list[r]

        print("Plotting RDT prevalence time series...")
        save_dir = os.path.join(calib_folder_path, '_plots/', 'prevalence_custom/')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir,'{}_rank{}_sample{}'.format(fit_type, r, s))
        plot_RDT(expid, [s], save_file=save_file)

        print("Plotting vector HBRs...")
        save_dir = os.path.join(calib_folder_path, '_plots/', 'vector_report/')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir,'{}_rank{}_sample{}'.format(fit_type, r, s))
        plot_vectors(expid, s, save_file=save_file)

def plot_selected(sample_list, calib=True, expid=None, RDT=True, vector=True):

    if calib:
        best_expid_list, best_iter_list, best_sample_list = parse_calib_manager()
        expid = best_expid_list[0]


    for r in range(len(sample_list)):
        s = sample_list[r]

        if plot_RDT:
            print("Plotting RDT prevalence time series...")
            save_dir = os.path.join(calib_folder_path, '_plots/', 'prevalence_custom/')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_file = os.path.join(save_dir,'sample{}'.format(s))
            plot_RDT(expid, [s], save_file=save_file)

        if vector:
            print("Plotting vector HBRs...")
            save_dir = os.path.join(calib_folder_path, '_plots/', 'vector_report/')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_file = os.path.join(save_dir,'sample{}'.format(s))
            plot_vectors(expid, s, save_file=save_file)




def plot_all(calib=True, expid=None):
    if calib:
        # Currently designed only for burnin "calibs" with only 1 iteration
        best_expid_list, best_iter_list, best_sample_list = parse_calib_manager()
        expid = best_expid_list[0]


    print("Plotting RDT prevalence time series...")
    save_dir = os.path.join(calib_folder_path, '_plots/', 'prevalence_custom/')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_file = os.path.join(save_dir,'all')
    plot_RDT(expid, [-1], save_file=save_file)




def plot_RDT(exp_id, sample, save_file=None, **kwargs):
    am = AnalyzeManager()
    am.add_experiment(retrieve_experiment(exp_id))
    am.add_analyzer(prevalence_plot_analyzer(catch, sample, save_file=save_file, **kwargs))
    am.analyze()


def plot_vectors(exp_id, sample, save_file=None):
    am = AnalyzeManager()
    am.add_experiment(retrieve_experiment(exp_id))
    am.add_analyzer(VectorSpeciesReportAnalyzer(sample, save_file=save_file, channel='Daily HBR'))
    am.analyze()



class prevalence_plot_analyzer(BaseAnalyzer):
    # filenames = ['output/SpatialReportMalariaFiltered_Population.bin', 'output/SpatialReportMalariaFiltered_True_Prevalence.bin']
    filenames = ['output/SpatialReportMalariaFiltered_Population.bin', 'output/SpatialReportMalariaFiltered_Blood_Smear_Parasite_Prevalence.bin']

    def __init__(self, catch, sample_list, save_file=None, **kwargs):
        super(prevalence_plot_analyzer, self).__init__()
        self.metadata = {}
        self.prev = {}
        self.pop = {}
        self.data = {}

        # self.base = '../../'
        self.dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/"
        self.catch = catch
        self.sample_list = sample_list
        self.save_file = save_file

        self.start_date = "2010-01-01"
        self.kwargs = kwargs


    def filter(self, sim_metadata):
        if -1 in self.sample_list:
            return True
        else:
            return sim_metadata["__sample_index__"] in self.sample_list

    def apply(self, parser):
        pop_df = construct_spatial_output_df(parser.raw_data[self.filenames[0]],'N')
        prev_df = construct_spatial_output_df(parser.raw_data[self.filenames[1]],'prev')

        data_df = pop_df.merge(prev_df,how='inner')

        # Reset times to zero:
        data_df['time'] = data_df['time'] - np.min(data_df['time'])

        # Collect aggregated data:
        # self.prev[parser.sim_id] = prev_df
        # self.pop[parser.sim_id] = pop_df
        self.data[parser.sim_id] = {}
        self.data[parser.sim_id]["data"] = data_df
        self.data[parser.sim_id]["sample"] = parser.sim_data["__sample_index__"]
        self.n_tstep = max(data_df['time'])

    def finalize(self):
        print("")

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
                sample = self.data[sim_id]["sample"]
                data_df = self.data[sim_id]["data"]
                data_df = data_df[np.in1d(data_df['node'], cells)]
                data_df['N_pos'] = data_df['N'] * data_df['prev']

                aggregate_df = data_df.groupby('time').agg({'N': 'sum', 'N_pos': 'sum'}).reset_index()
                aggregate_df['prev'] = aggregate_df['N_pos'] / aggregate_df['N']
                aggregate_df['mdate'] = aggregate_df['time'].apply(lambda x: date_to_mdate(convert_to_date_365(x,self.start_date)))

                if "color_dict" in self.kwargs:
                    color = self.kwargs['color_dict'][sample]
                else:
                    color = 'black'

                if "label_dict" in self.kwargs:
                    label = self.kwargs['label_dict'][sample]
                elif "label" not in locals():
                    label = "Simulations"
                else:
                    label = None

                ax.plot_date(np.array(aggregate_df['mdate']), np.array(aggregate_df['prev']),
                              fmt='-', label=label, lw=1.2, color=color,
                              zorder=10)
            # else: # If too many lines, Plot as spread
            #     all_data = np.zeros([len(daydates_mdates), 10])
            #
            #     i = 0
            #     for sim_id in list(self.data.keys()):
            #         data_df = self.data[sim_id]
            #         data_df = data_df[np.in1d(data_df['node'], cells)]
            #         data_df['N_pos'] = data_df['N'] * data_df['prev']
            #
            #         aggregate_df = data_df.groupby('time').agg({'N': 'sum', 'N_pos': 'sum'}).reset_index()
            #         aggregate_df['prev'] = aggregate_df['N_pos'] / aggregate_df['N']
            #         aggregate_df['mdate'] = aggregate_df['time'].apply(lambda x: date_to_mdate(convert_to_date_365(x,self.start_date)))
            #
            #         if "label" not in locals():
            #             label = "Simulations"
            #         else:
            #             label = None
            #
            #         all_data[:, i] = aggregate_df['prev']
            #         i += 1
            #
            #     med_curve = np.apply_along_axis(np.median, 1, all_data)
                # ll_curve = np.apply_along_axis(conf90_ll,1,all_data)
                # ul_curve = np.apply_along_axis(conf90_ul,1,all_data)
            #     ll_curve = np.apply_along_axis(np.min, 1, all_data)
            #     ul_curve = np.apply_along_axis(np.max, 1, all_data)
            #
            #     ax.plot_date(daydates_mdates, med_curve, c='black', ls='-',marker=',',lw=1, label='Simulations') #, label=scenario,zorder=zorder)
            #     ax.fill_between(daydates_mdates, ll_curve, ul_curve, color='black', alpha=0.7) #,zorder=zorder)


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
        fig = plt.figure(figsize=(12,5))
        ax = plt.subplot(111)
        catch_cells = catchment_grid_cells(self.catch)
        plot_for_cells(ax,catch_cells,title=self.catch)

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



class VectorSpeciesReportAnalyzer(BaseAnalyzer):

    def __init__(self, sample, save_file=None, channel='Adult Vectors Per Node'):
        super().__init__()
        self.channel = channel
        self.filenames = ['output/VectorSpeciesReport.json']
        self.save_file = save_file
        self.start_year = 2010
        self.sample = sample

    def ts_to_dt(self, timesteps):
        # refd = datetime.date(2009, 1, 1).toordinal()
        # return [datetime.date.fromordinal(x + refd - timesteps[0]) for x in timesteps]
        refd = datetime(self.start_year, 1, 1).toordinal()
        return [datetime.fromordinal(x + refd - timesteps[0]) for x in timesteps]

    def filter(self, sim_metadata):
        return sim_metadata["__sample_index__"] == self.sample

    def apply(self, parser):
        # Load data from simulation
        d = parser.raw_data[self.filenames[0]]
        species = d['Header']['Subchannel_Metadata']['MeaningPerAxis'][0][0]
        df = pd.DataFrame()
        for si, s in enumerate(species) :
            data = pd.DataFrame({ self.channel : d['Channels'][self.channel]['Data'][si]})
            data['species'] = s
            data['Time'] = data.index
            # data['date'] = self.ts_to_dt(data['Time'])
            df = pd.concat([df, data])

        if burnin:
            time_start = 365*(self.start_year-1954)
        else:
            time_start = 0
        df = df[df['Time'] > time_start]
        df['Time'] = df['Time'] - time_start
        df.reset_index(inplace=True, drop=True)

        df['date'] = self.ts_to_dt(np.array(df['Time']))
        df = df[df['date'] >= datetime(2010,1,1)]
        df['Month_temp'] = df['date'].apply(lambda x : x.month)
        df['Year'] = df['date'].apply(lambda x : x.year - self.start_year)
        df['Month'] = df['Month_temp'] + 12*df['Year']
        df['sim_id'] = parser.sim_id
        return df

    def combine(self, parsers):

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        self.data = pd.concat(selected)

    def finalize(self):
        pass

    def plot(self):
        import seaborn as sns
        sns.set_style("darkgrid")

        fig = plt.figure(figsize=(10,6))
        ax = fig.gca()

        labelled = False
        for a, adf in self.data.groupby('sim_id'):

            for s, sdf in adf.groupby('species'):
                if s == "arabiensis":
                    c = "C0"
                elif s == "funestus":
                    c = "C1"

                if labelled:
                    ax.plot(sdf['date'], sdf[self.channel], label='_nolegend_', c=c)
                else:
                    ax.plot(sdf['date'], sdf[self.channel], label=s, c=c)

            labelled = True


        ax.legend()
        ax.set_xlim(["2010-01-01","2014-01-01"])

        # ax.set_xticks(["2010-{}-01".format(str(int(i)).zfill(2)) for i in range(1,13)])
        ax.set_xticks(["2010-01-01",
                       "2011-01-01",
                       "2012-01-01",
                       "2013-01-01",
                       "2014-01-01"])
                       # "2017-01-01",
                       # "2018-01-01",
                       # "2019-01-01"])

        plt.ylabel(self.channel)
        if self.save_file:
            plt.savefig(self.save_file + ".png")
            plt.savefig(self.save_file + ".pdf")
        else:
            plt.show()


if __name__=="__main__":
    catch = "chiyabi"
    # calib_folder_name = "chiyabi_burnin_old_immunity"
    calib_folder_name = "chiyabi_burnin_sweep"
    burnin = True
    plot_best_N = 5

    # base = '../../'
    base = "C:/Users/jsuresh/Projects/malaria-zm-kariba/gridded_sims/"
    calib_folder_path = os.path.join(base, "src", "sims", calib_folder_name)

    SetupParser.init('HPC')
    # plot_best(fit_type="full")
    # plot_best(fit_type="prevalence")
    # plot_selected([5, 80], expid="68eeecf8-6bc8-e811-a2bd-c4346bcb1555", calib=False, RDT=False)
    # parse_calib_manager()
    plot_all(expid="3666323b-83e8-e811-a2bd-c4346bcb1555", calib=False)

    cmap = matplotlib.cm.get_cmap('viridis')
    rgba = cmap(0.5)

    # samples = [5,20,35,50,65,80,95,110,125,140,155,170,185,200,215]
    # color_dict = {}
    # label_dict = {}
    # for s in samples:
    #     color_dict[s] = cmap(s/215)
    #     label_dict[s] = str(s)
    #
    # plot_RDT("68eeecf8-6bc8-e811-a2bd-c4346bcb1555",
    #          [5,20,35,50,65,80,95,110,125,140,155,170,185,200,215],
    #          color_dict=color_dict)

    # samples = [0,15,30,45,60,75,90,105,120,135,150,165,180,195,210]
    # color_dict = {}
    # label_dict = {}
    # for s in samples:
    #     color_dict[s] = cmap(s/210)
    #     label_dict[s] = str(s)
    #
    # plot_RDT("3ad23ae7-d1c8-e811-a2bd-c4346bcb1555",
    #          samples,
    #          color_dict=color_dict)