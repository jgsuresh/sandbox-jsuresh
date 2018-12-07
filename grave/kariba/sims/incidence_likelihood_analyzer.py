import logging
import pandas as pd
import numpy as np

from calibtool.analyzers.BaseCalibrationAnalyzer import BaseCalibrationAnalyzer
from calibtool.LL_calculators import gamma_poisson

from sim_output_processing.spatial_output_dataframe import construct_spatial_output_df
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.Utilities.Experiments import retrieve_experiment

from zambia_helpers import LL_compression
from zambia_calib_site import zambia_calib_site

# import deepcopy
from simtools.SetupParser import SetupParser

logger = logging.getLogger(__name__)



class incidence_likelihood(BaseCalibrationAnalyzer):

    def __init__(self, site):
        super(incidence_likelihood, self).__init__(site)
        self.filenames = ['output/ReportEventCounter.json',
                          'output/SpatialReportMalariaFiltered_Population.bin'] #,
                          # 'output/InsetChart.json']

        self.reference = site.get_reference_data('monthly_cases')

        self.month = [1] * 31 + [2] * 28 + [3] * 31 + [4] * 30 + [5] * 31 + [6] * 30 \
                + [7] * 31 + [8] * 31 + [9] * 30 + [10] * 31 + [11] * 30 + [12] * 31
        # self.month = np.array(self.month)
        self.NMF_factor = 1.0 #0.55

    def filter(self, sim_metadata):
        return True

    def apply(self, parser):
        # Load data from simulation
        pop_df = construct_spatial_output_df(parser.raw_data[self.filenames[1]], 'N')
        pop_df = pop_df.groupby('time').agg({'N':'sum'})

        cases = np.array(parser.raw_data[self.filenames[0]]["Channels"]["Received_Treatment"]["Data"])

        #fixme Have to do an ugly hack here because imposing a filter on which days for a ReportEventCounter doesn't work currently
        # Determine whether we are in a burn-in or a serialized run:
        # Serialized runs start at 2010 and end at mid-2016.  So any run longer than this is a burnin:
        burnin = (len(cases) > 6*365+182)
        if burnin:
            # Assume that simulation ends at end of 2013.  We only want the final 4 years of data:
            cases = cases[-(4*365):]
        else:
            # Assume that simulation ends July 1, 2016.  We only want final 6.5 years of data:
            cases = cases[-(6*365+182):]

        year = [0]*365+[1]*365+[2]*365+[3]*365+[4]*365+[5]*365+[6]*365+[7]*365+[8]*365+[9]*365
        n_years = 10
        month = []
        for i in range(n_years):
            month += self.month

        year = year[:len(cases)]
        month = month[:len(cases)]

        sim_data = pd.DataFrame({'year': year,
                                 'month': month,
                                 'cases': cases,
                                 'N': pop_df['N']})


        # Aggregate by month:
        sim_data = sim_data.groupby(['year', 'month']).agg({"cases": "sum",
                                                           "N": "mean"}).reset_index()

        # Merge with reference data to get specific months that we have observations to compare to:
        return_df = self.reference[['year','month']].merge(sim_data,
                                                           how='inner',
                                                           on=['year','month'])

        return_df.sample = parser.sim_data.get('__sample_index__')
        # return_df.run_number = parser.sim_data['Run_Number']
        return_df.sim_id = parser.sim_id
        return return_df



    def combine(self, parsers):
        '''
        Combine the simulation data into a single table for all analyzed simulations.
        '''
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=1,
                             keys=[(d.sample, d.sim_id) for d in selected],
                             names=['sample', 'sim_id'])
        stacked = combined.stack(['sample', 'sim_id'])
        sim_data_full = stacked.groupby(['sample', 'year', 'month']).mean()

        sim_data_full.reset_index(inplace=True)
        self.data = sim_data_full[['sample','year','month','cases','N']]
        logger.debug(self.data)



    def compare(self, sample):
        temp = sample.copy(deep=True)

        temp.rename(columns={"cases": "cases_sim"}, inplace=True)
        comparison = temp.merge(self.reference, how='inner', on=['year', 'month'])
        comparison.rename(columns={"cases": "cases_ref"}, inplace=True)


        # # Fancy footwork: for 2014, use an aggregated version.  For 2015 onwards, use monthly.
        # agg_version = "2014 and 2015"
        #
        # if agg_version == "2014_only":
        #     hold_2014 = comparison[comparison["year"]==(2014-2009)].copy()
        #
        #     if len(hold_2014) > 0:
        #         agg_2014 = pd.DataFrame({
        #             "N": [hold_2014.sum()['N']],
        #             "cases_sim": [hold_2014.sum()['cases_sim']],
        #             "cases_ref": [hold_2014.sum()['cases_ref']],
        #             "year": [(2014-2009)],
        #             "month": [0],
        #             "sample":[hold_2014['sample'][0]]
        #         })
        #         comparison = comparison[comparison["year"]>(2014-2009)]
        #         comparison = pd.concat([agg_2014,comparison])
        #
        # elif agg_version == "2014 and 2015":
        #     hold_2014 = comparison[comparison["year"] == (2014 - 2009)].copy()
        #     hold_2015 = comparison[comparison["year"] == (2015 - 2009)].copy()
        #     comparison = comparison[comparison["year"] > (2015 - 2009)]
        #
        #     if len(hold_2014) > 0:
        #         agg_2014 = pd.DataFrame({
        #             "N": [hold_2014.sum()['N']],
        #             "cases_sim": [hold_2014.sum()['cases_sim']],
        #             "cases_ref": [hold_2014.sum()['cases_ref']],
        #             "year": [(2014 - 2009)],
        #             "month": [0],
        #             # "sample": [hold_2014['sample'][0]]
        #         })
        #
        #         comparison = pd.concat([agg_2014, comparison])
        #
        #     if len(hold_2015) > 0:
        #         agg_2015 = pd.DataFrame({
        #             "N": [hold_2015.sum()['N']],
        #             "cases_sim": [hold_2015.sum()['cases_sim']],
        #             "cases_ref": [hold_2015.sum()['cases_ref']],
        #             "year": [(2015 - 2009)],
        #             "month": [0],
        #             # "sample": [hold_2015['sample'][0]]
        #         })
        #
        #         comparison = pd.concat([agg_2015, comparison])


        # Don't need negative sign: gamma_poisson actually returns a log-likelihood
        LL =  gamma_poisson(np.array(comparison['N']),
                             np.array(comparison['N']),
                             np.array(comparison['cases_ref']*self.NMF_factor),
                             np.array(comparison['cases_sim'])) #(raw_nobs, sim_nobs, raw_data, sim_data)

        return LL_compression(LL)


    def finalize(self):
        """
        Calculate the output result for each sample.
        # """
        # print(self.data)
        self.result = self.data.groupby('sample').apply(self.compare)
        print("MonthlyIncidence analyzer result: ",self.result)
        # print(self.result)
        logger.debug(self.result)


    def cache(self):
        cache = self.data.copy()

        sample_dicts = []
        for idx, df in cache.groupby('sample', sort=True):
            d = {
                "month": list(df["month"]),
                "year": list(df["year"]),
                "cases": list(df["cases"])
            }
            sample_dicts.append(d)

        ref_d = {
            "month": list(self.reference["month"]),
            "year": list(self.reference["year"]),
            "cases": list(self.reference["cases"]*self.NMF_factor)
        }

        logger.debug(sample_dicts)
        return {'samples': sample_dicts,
                'ref': ref_d}

    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        # import matplotlib
        # matplotlib.rcParams['pdf.fonttype'] = 42

        import matplotlib.dates as mdates
        # import seaborn as sns
        # sns.set_style("darkgrid")

        fmt_str = kwargs.pop('fmt', None)
        args = (fmt_str,) if fmt_str else ()
        if kwargs.pop('reference', False):
            ref = True
        else:
            ref = False

        ax = fig.gca()
        df = pd.DataFrame(data)

        date_format = "%Y-%m-%d"
        date_to_mdate = mdates.strpdate2num(date_format)
        # print("date")
        df["date"] = df.apply(lambda x: "{}-{}-01".format(int(x["year"])+2010, str(int(x["month"])).zfill(2)),axis=1)
        # print("mdate")
        df["mdate"] = df.apply(lambda x: date_to_mdate(x["date"]),axis=1)
        # print("plot")
        # ax.plot(df["year"] * 12 + df["month"], df["cases"], *args, **kwargs)
        ax.plot_date(df["mdate"],df["cases"],*args,**kwargs)

        ax.set_xlabel("Date")
        ax.set_ylabel("Cases")
        ax.set_xlim([date_to_mdate("2010-01-01"), date_to_mdate("2017-01-01")])
        # ax.tick_params(direction="inout")


    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])



if __name__=="__main__":
    SetupParser.init('HPC')

    am = AnalyzeManager()

    # Calibration experiments:
    am.add_experiment(retrieve_experiment("a0bee2bd-f8b5-e811-a2c0-c4346bcb7275"))

    am.add_analyzer(incidence_likelihood(zambia_calib_site("bbondo")))
    am.analyze()
