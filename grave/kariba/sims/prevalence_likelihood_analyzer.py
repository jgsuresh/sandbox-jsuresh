import numpy as np
import pandas as pd
import logging
import os

from calibtool.LL_calculators import gamma_poisson, beta_binomial
from calibtool.analyzers.BaseCalibrationAnalyzer import BaseCalibrationAnalyzer
from sim_output_processing.spatial_output_dataframe import construct_spatial_output_df

from zambia_helpers import LL_compression


logger = logging.getLogger(__name__)

class prevalence_likelihood(BaseCalibrationAnalyzer):

    # filenames = ['output/InsetChart.json']

    # data_group_names = ['sample', 'sim_id'] #, 'channel']

    def __init__(self, site):
        super().__init__(site)

        self.filenames = ['output/SpatialReportMalariaFiltered_Population.bin',
                          'output/SpatialReportMalariaFiltered_True_Prevalence.bin']

        # self.reference should be a dataframe with columns: node/round/date/prev/N
        self.reference = site.get_reference_data("gridded_prevalence")

        # base = "../../"
        dropbox_base = "C:/Users/{}/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/".format("jsuresh")

        self.round_compiled_reference = pd.read_csv(os.path.join(dropbox_base,"inputs","grid_csv","round_prevalence.csv"))
        self.round_compiled_reference = self.round_compiled_reference[self.round_compiled_reference["catchment"]==site.name]
        self.round_compiled_reference = self.round_compiled_reference[["round","N","N_pos","prev"]]


    def filter(self, sim_metadata):
        return True

    def apply(self, parser):
        pop_df = construct_spatial_output_df(parser.raw_data[self.filenames[0]],'N')
        prev_df = construct_spatial_output_df(parser.raw_data[self.filenames[1]],'prev')


        # Merge these together and pass it on to the combine function:
        full_df = pop_df.merge(prev_df,how='inner')

        # Reset times to zero:
        full_df['time'] = full_df['time'] - np.min(full_df['time'])
        full_df['time'] = full_df['time'] + 1 # shift times by 1 day so that MSAT/MDA don't get messed up

        # Instead of passing entire simulation output, first merge with reference data dates to extract relevant data:
        full_df = self.reference[['grid_cell','sim_date','round']].merge(full_df,
                                                                         how='inner', #'left',
                                                                         left_on=['grid_cell','sim_date'],
                                                                         right_on=['node','time'])

        full_df['N_pos'] = full_df['N']*full_df['prev']
        return_df = full_df.groupby('round').agg({'N':'sum','N_pos':'sum'})
        # return_df['prev'] = return_df['N_pos']/return_df['N']

        return_df.sample = parser.sim_data.get('__sample_index__')
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
        sim_data_full = stacked.groupby(['sample', 'round']).mean()

        sim_data_full.reset_index(inplace=True)
        self.data = sim_data_full[['sample','round','N','N_pos']]

        logger.debug(self.data)



    def compare(self, sample):
        """
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        """

        # Group by round.

        temp = sample.copy(deep=True)
        temp.rename(columns={"N": "N_sim",
                             "N_pos": "N_pos_sim"},
                    inplace=True)

        comparison = temp.merge(self.round_compiled_reference[["round","N","N_pos"]], how='inner')

        comparison.rename(columns={"N": "N_ref",
                                   "N_pos": "N_pos_ref"},
                          inplace=True)

        LL =  beta_binomial(comparison['N_ref'],
                             comparison['N_sim'],
                             comparison['N_pos_ref'],
                             comparison['N_pos_sim']
                             ) #(raw_nobs, sim_nobs, raw_data, sim_data)

        return LL_compression(LL)


    def finalize(self):
        """
        Calculate the output result for each sample.
        """
        self.result = self.data.groupby('sample').apply(self.compare)
        print("Prevalence likelihood analyzer result: ",self.result)
        logger.debug(self.result)


    def cache(self):
        cache = self.data.copy()

        sample_dicts = []
        for idx, df in cache.groupby('sample', sort=True):
            d = {"round": list(df["round"]),
                "N": list(df["N"]),
                "N_pos": list(df["N_pos"])}
            sample_dicts.append(d)

        ref_d = {
            "round": list(self.round_compiled_reference["round"]),
            "N": list(self.round_compiled_reference["N"]),
            "N_pos": list(self.round_compiled_reference["N_pos"])
        }

        logger.debug(sample_dicts)
        return {'samples': sample_dicts,
                'ref': ref_d}




    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        import matplotlib.dates as mdates
        from helpers.relative_time import convert_to_date_365

        fmt_str = kwargs.pop('fmt', None)
        args = (fmt_str,) if fmt_str else ()
        if kwargs.pop('reference', False):
            ref = True
        else:
            ref = False

        ax = fig.gca()
        df = pd.DataFrame(data)

        ax.plot(df["round"],df["N_pos"]/df["N"], *args, **kwargs)
        ax.set_xlabel("Round")
        ax.set_ylabel("RDT Prevalence")


    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])

class prevalence_burnin_likelihood(prevalence_likelihood):
    pass