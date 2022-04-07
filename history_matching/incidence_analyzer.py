from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core.platform_factory import Platform
from idmtools.entities import IAnalyzer

import numpy as np
import pandas as pd
from idmtools_platform_comps.utils.download.download import DownloadWorkItem

# from jsuresh_helpers.analyzers.run_analyzer import run_analyzer_locally, run_analyzer_as_ssmt


class TestA(IAnalyzer):
    def __init__(self):
        super().__init__()

class TestB(IAnalyzer):
    def __init__(self, NMF_factor=0.6):
        filenames = ['output/ReportEventCounter.json',
                     'output/ReportMalariaFilteredCatchment.json']
        super().__init__(filenames=filenames)

        self.NMF_factor = NMF_factor
        self.month = day_number_to_month()

    def map(self, data, simulation):
        pop = np.array(data[self.filenames[1]]["Channels"]["Statistical Population"]['Data'])
        population_rescale_factor = simulation.tags["population_rescale_factor"]
        pop = pop * population_rescale_factor

        cases = np.array(data[self.filenames[0]]["Channels"]["Received_Treatment"]["Data"])
        cases = cases * population_rescale_factor

        sim_duration_years = 2019 - self.sim_start_year
        year = np.repeat(np.arange(sim_duration_years), 365)

        month = []
        for i in range(sim_duration_years):
            month += self.month

        sim_data = pd.DataFrame({'year': year[-5 * 365:],
                                 'month': month[-5 * 365:],
                                 'cases': cases[-5 * 365:],
                                 'N': pop[-5 * 365]})

        # Aggregate by month:
        sim_data = sim_data.groupby(['year', 'month']).agg({"cases": "sum", "N": "mean"}).reset_index()
        return sim_data

    def combine(self, all_data):
        df_list = []
        for sim in all_data.keys():
            df = pd.DataFrame(all_data[sim])
            df.sample = sim.tags['__sample_index__']
            df.sim_id = sim.id
            df_list.append(df)

        combined = pd.concat(df_list, axis=1,
                             keys=[(df.sample, df.sim_id) for df in df_list],
                             names=['sample', 'sim_id'])
        stacked = combined.stack(['sample', 'sim_id'])
        sim_data_full = stacked.groupby(['sample', 'year', 'month']).mean()

        sim_data_full.reset_index(inplace=True)
        sim_data_full = sim_data_full[['sample', 'year', 'month', 'cases', 'N']]
        return sim_data_full

    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        return sim_data_full.groupby('sample').apply(self.compare)





def day_number_to_month():
    day_to_month = [1] * 31 + [2] * 28 + [3] * 31 + [4] * 30 + [5] * 31 + [6] * 30 \
                   + [7] * 31 + [8] * 31 + [9] * 30 + [10] * 31 + [11] * 30 + [12] * 31
    return day_to_month



class MonthlyIncidence(IAnalyzer):
    def __init__(self, NMF_factor=0.6, sim_start_year=2009):
        filenames = ['output/ReportEventCounter.json',
                     'output/ReportMalariaFilteredCatchment.json']
        super().__init__(filenames=filenames)

        self.NMF_factor = NMF_factor
        self.month = day_number_to_month()
        self.sim_start_year = sim_start_year

    def map(self, data, simulation):
        pop = np.array(data[self.filenames[1]]["Channels"]["Statistical Population"]['Data'])
        population_rescale_factor = np.float(simulation.tags["population_rescale_factor"])
        pop = pop * population_rescale_factor

        cases = np.array(data[self.filenames[0]]["Channels"]["Received_Treatment"]["Data"])
        cases = cases * population_rescale_factor

        sim_duration_years = 2019-self.sim_start_year
        year = np.repeat(np.arange(sim_duration_years), 365)

        month = []
        for i in range(sim_duration_years):
            month += self.month

        sim_data = pd.DataFrame({'year': year[-5*365:],
                                 'month': month[-5*365:],
                                 'cases': cases[-5*365:],
                                 'N': pop[-5*365]})

        # Aggregate by month:
        sim_data = sim_data.groupby(['year', 'month']).agg({"cases": "sum", "N": "mean"}).reset_index()
        return sim_data

    def combine(self, all_data):
        df_list = []
        for sim in all_data.keys():
            df = pd.DataFrame(all_data[sim])
            df.sample = sim.tags['__sample_index__']
            df.sim_id = sim.id
            df_list.append(df)

        combined = pd.concat(df_list, axis=1,
                             keys=[(df.sample, df.sim_id) for df in df_list],
                             names=['sample', 'sim_id'])
        stacked = combined.stack(['sample', 'sim_id'])
        sim_data_full = stacked.groupby(['sample', 'year', 'month']).mean()

        sim_data_full.reset_index(inplace=True)
        sim_data_full = sim_data_full[['sample','year','month','cases', 'N']]
        return sim_data_full

    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.to_csv("test.csv", index=False)
        return sim_data_full


def run_analyzer_as_ssmt(experiment_id,
                         analyzers,
                         analyzer_args,
                         analysis_name="SSMT analysis"):
    platform = Platform("SLURM")
    analysis = PlatformAnalysis(
        platform=platform,
        # platform=Platform("SLURM"),
        experiment_ids=[experiment_id],
        analyzers=analyzers,
        analyzers_args=analyzer_args,
        analysis_name=analysis_name,
    )
    analysis.analyze(check_status=True)
    wi = analysis.get_work_item()
    print(wi)

    # Download the actual output (code snippet from Clinton 1/3/22)
    dl_wi = DownloadWorkItem(related_work_items=[wi.id],
                             file_patterns=["*.csv"],
                             delete_after_download=False,
                             extract_after_download=True,
                             verbose=True)
    dl_wi.run(wait_on_done=True, platform=platform)


if __name__ == '__main__':
    experiment_id = "8faf544c-6205-ec11-a9ed-b88303911bc1"
    analyzers = [MonthlyIncidence]
    analyzer_args = [{}]

    # run_analyzer_locally(experiment_id, analyzers, analyzer_args)
    run_analyzer_as_ssmt(experiment_id=experiment_id, analyzers=analyzers, analyzer_args=analyzer_args)