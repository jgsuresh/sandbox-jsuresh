import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from simtools.Analysis.BaseAnalyzers.SimulationDirectoryMapAnalyzer import SimulationDirectoryMapAnalyzer
from simtools.Utilities.Experiments import retrieve_experiment

sns.set_context("talk")
sns.set_style("white")



# First download relevant data from this experiment.
# Relevant data is: Number of new infections acquired in catchment, in 2016, and in 2017.
# sim map
# CSV columns: sim map stuff, 2016_infections, 2017_infections

# Save this data to a CSV file
# Draw from CSV file to plot figure


# def analyzer:
# open ReportEventCounter


class ExtractCounterData(BaseAnalyzer):
    def __init__(self):
        filenames = ['output/ReportMalariaFilteredCatchment.json']
        super().__init__(filenames=filenames)
        self.extract_time = [7*365, 8*365] # starts at 2009
        self.extract_label = ["2016", "2017"]
        self.agg_duration = 365

    # FOR TESTING PURPOSES ONLY
    # def filter(self, simulation):
    #     return simulation.tags['Run_Number'] == 1


    def select_simulation_data(self, data, simulation):
        cases_16 = np.sum(np.array(data[self.filenames[0]]["Channels"]["New Infections"]["Data"][7*365:8*365]))
        cases_17 = np.sum(np.array(data[self.filenames[0]]["Channels"]["New Infections"]["Data"][8*365:9*365]))

        return_df = pd.DataFrame({"year": ["2016", "2017"],
                                  "infec": [cases_16, cases_17]})
        return_df["sim_id"] = simulation.id
        return return_df


    def combine(self, all_data):
        data_list = list(all_data.values())
        # clean = [x for x in data_list if x != None]
        clean = list(filter(None.__ne__, data_list))
        df = pd.concat(clean, ignore_index=True)
        return df

    def finalize(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.to_csv("iver_figure_data.csv", index=False)
        return sim_data_full



def make_figure():
    df = pd.read_csv("iver_figure_data.csv")
    sim_map = pd.read_csv("sim_map.csv")

    full = df.merge(sim_map, how="left", left_on="sim_id", right_on="id")

    vc_only = full[full["int_package"]=="vc only"]
    vc_baseline = {"2016": np.median(vc_only["2016"]),
                   "2017": np.median(vc_only["2017"])}

    # mda_only should be a dataframe with columns: mda coverage, year, cases
    subset = full[full["int_package"] == "mda without ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "year"]).agg("median")

    # mda_w_ivm should be a dataframe with columns: mda coverage, ivm_duration, year, cases
    subset = full[full["int_package"] == "mda with ivm"]
    mda_wo_ivm = subset.groupby(["mda_coverage", "ivm_duration", "year"]).agg("median")













if __name__=="__main__":
    # Run analyzers
    # analyzer_list = [ExtractCounterData(),
    #                  SimulationDirectoryMapAnalyzer()]
    analyzer_list = [SimulationDirectoryMapAnalyzer(save_file="sim_map.csv")]
    exp_list = ["e32fcd15-7e26-e911-a2bf-c4346bcb1554"]

    am = AnalyzeManager()

    for exp_name in exp_list:
        am.add_experiment(retrieve_experiment(exp_name))
    for a in analyzer_list:
        am.add_analyzer(a)

    am.analyze()





























