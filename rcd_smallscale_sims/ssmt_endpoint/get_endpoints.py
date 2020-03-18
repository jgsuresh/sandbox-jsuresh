
# Run endpoint analyzer on all runs in the suite, and collect ALL results into a single results CSV/dataframe
import sys
import numpy as np
import pandas as pd
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from simtools.Utilities.Experiments import retrieve_experiment


class SaveEndpoint(BaseAnalyzer):
    def __init__(self, save_file=None, output_filename="InsetChart.json"):
        filenames = ['output/{}'.format(output_filename)]
        super().__init__(filenames=filenames)

        self.save_file = save_file

    def combine(self, all_data):
        data_list = []
        for sim in all_data.keys():
            data_list.append(all_data[sim])

        return pd.concat(data_list).reset_index(drop=True)

    def finalize(self, all_data):
        sim_data_full = self.combine(all_data)
        if self.save_file:
            sim_data_full.to_csv(self.save_file, index=False)
        return sim_data_full








def get_pop_weighted_channel_from_summary_report(data_summary, channel, num_years):
    pop_by_age_bin = data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin']
    channel_of_interest = data_summary['DataByTimeAndAgeBins'][channel]

    pop_weighted_channel = np.array([
        np.sum(np.array(channel_of_interest[i]) * np.array(pop_by_age_bin[i])) for i in range(num_years)
    ])

    return pop_weighted_channel


def get_annual_cases_from_summary_report(data_summary, num_years):
    return get_pop_weighted_channel_from_summary_report(data_summary, 'Annual Clinical Incidence by Age Bin', num_years)

def get_severe_cases_from_summary_report(data_summary, num_years):
    return get_pop_weighted_channel_from_summary_report(data_summary, 'Severe Clinical Incidence by Age Bin', num_years)

def get_annual_EIR_from_summary_report(data_summary, num_years, num_nodes=30):
    aeir = np.array(data_summary['DataByTime']['Annual EIR'][:num_years])

    print("Correcting since Summary Report incorrectly adds EIR across nodes...")
    aeir = aeir/num_nodes

    return aeir



def get_annual_avg_RDT_prev_from_summary_report(data_summary, num_years):
    pop_by_age_bin = data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin']
    rdtprev_by_age_bin = data_summary['DataByTimeAndAgeBins']['PfPR by Age Bin']

    rdt_prev = np.array([
        np.sum(np.array(rdtprev_by_age_bin[i]) * np.array(pop_by_age_bin[i])) / np.sum(pop_by_age_bin[i]) for i in range(num_years)
    ])
    return rdt_prev


class SaveEndpointFromSummaryReport(SaveEndpoint):
    def __init__(self, save_file=None, output_filename="MalariaSummaryReport_AnnualAverage.json", years_to_include=4, num_nodes=30):
        super().__init__(save_file=save_file, output_filename=output_filename)

        self.years_to_include = years_to_include
        self.num_nodes = num_nodes


    def select_simulation_data(self, data, simulation):
        data_summary = data[self.filenames[0]]

        y = np.arange(self.years_to_include)
        cases = get_annual_cases_from_summary_report(data_summary, self.years_to_include)
        severe_cases = get_annual_cases_from_summary_report(data_summary, self.years_to_include)
        EIR = get_annual_EIR_from_summary_report(data_summary, self.years_to_include, self.num_nodes)
        RDT_prev = get_annual_avg_RDT_prev_from_summary_report(data_summary, self.years_to_include)

        sim_data = {
            "year": y,
            "cases": cases,
            "severe_cases": severe_cases,
            "EIR": EIR,
            "avg_RDT_prev": RDT_prev
        }


        sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            sim_data[tag] = simulation.tags[tag]

        return pd.DataFrame(sim_data)













class SaveEndpointFromCounter(SaveEndpoint):
    def __init__(self, save_file=None, output_filename="ReportEventCounter.json", years_to_include=4):
        super().__init__(save_file=save_file, output_filename=output_filename)

        self.years_to_include = years_to_include


    def select_simulation_data(self, data, simulation):
        data_summary = data[self.filenames[0]]

        received_treatment = np.array([])
        received_test = np.array([])
        received_RCD_drugs = np.array([])
        received_campaign_drugs = np.array([])

        start_index = -(self.years_to_include*365+1)

        # Get last years of data:
        for j in range(self.years_to_include):
            s = j * 365 + start_index
            e = (j + 1) * 365 + start_index
            received_treatment_array = np.array(data_summary["Channels"]["Received_Treatment"]["Data"][s:e])
            received_test_array = np.array(data_summary["Channels"]["Received_Test"]["Data"][s:e])
            received_RCD_drugs_array = np.array(data_summary["Channels"]["Received_RCD_Drugs"]["Data"][s:e])
            received_campaign_drugs_array = np.array(data_summary["Channels"]["Received_Campaign_Drugs"]["Data"][s:e])

            received_treatment = np.append(received_treatment, np.sum(received_treatment_array))
            received_test = np.append(received_test, np.sum(received_test_array))
            received_RCD_drugs = np.append(received_RCD_drugs, np.sum(received_RCD_drugs_array))
            received_campaign_drugs = np.append(received_campaign_drugs, np.sum(received_campaign_drugs_array))

        sim_data = {}
        sim_data["year"] = np.arange(self.years_to_include)
        sim_data["received_treatment"] = received_treatment
        sim_data["received_test"] = received_test
        sim_data["received_RCD_drugs"] = received_RCD_drugs
        sim_data["received_campaign_drugs"] = received_campaign_drugs


        sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            sim_data[tag] = simulation.tags[tag]

        return pd.DataFrame(sim_data)






class SaveEndpointFromInset(SaveEndpoint):
    def __init__(self, save_file=None, output_filename='InsetChart.json', years_to_include=4):
        super().__init__(save_file=save_file, output_filename=output_filename)

        self.years_to_include = years_to_include


    def select_simulation_data(self, data, simulation):
        y = np.array([])
        cases = np.array([])
        infections = np.array([])
        EIR = np.array([])
        RDT_prev = np.array([])
        true_prev = np.array([])
        days_at_zero_true_prev = np.array([])
        true_prev_at_end = np.array([])

        start_index = -(self.years_to_include*365+1)

        # Get last years of data:
        for j in range(self.years_to_include):
            s = j*365 + start_index
            e = (j+1)*365 + start_index
            cases_array = np.array(data[self.filenames[0]]["Channels"]["New Clinical Cases"]["Data"][s:e])
            infec_array = np.array(data[self.filenames[0]]["Channels"]["New Infections"]["Data"][s:e])
            EIR_array = np.array(data[self.filenames[0]]["Channels"]["Daily EIR"]["Data"][s:e])
            RDT_prev_arr = np.array(data[self.filenames[0]]["Channels"]["Blood Smear Parasite Prevalence"]["Data"][s:e])
            true_prev_arr = np.array(data[self.filenames[0]]["Channels"]["True Prevalence"]["Data"][s:e])

            y = np.append(y,j)
            cases = np.append(cases, np.sum(cases_array))
            infections = np.append(infections, np.sum(infec_array))
            EIR = np.append(EIR, np.sum(EIR_array))
            RDT_prev = np.append(RDT_prev, np.average(RDT_prev_arr))
            true_prev = np.append(true_prev, np.average(true_prev_arr))
            days_at_zero_true_prev = np.append(days_at_zero_true_prev, np.sum(true_prev_arr[-1] == 0))
            true_prev_at_end = np.append(true_prev_at_end, true_prev_arr[-1])

        sim_data = {
            "year": y,
            "cases": cases,
            "infections": infections,
            "EIR": EIR,
            "avg_RDT_prev": RDT_prev,
            "avg_true_prev": true_prev,
            "days_at_zero_true_prev": days_at_zero_true_prev,
            "true_prev_at_end": true_prev_at_end,
        }

        sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            sim_data[tag] = simulation.tags[tag]

        return pd.DataFrame(sim_data)



def remove_duplicate_columns(df):
    columns_to_keep = []
    for c in df.columns:
        if "_duplicated" not in c:
            columns_to_keep.append(c)
    return df[columns_to_keep]


def run_analyzers_and_save_output(exp_id, years_to_include):
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    am = AnalyzeManager()
    analyze_counter = SaveEndpointFromCounter(save_file=None,
                                              years_to_include=years_to_include)

    analyze_summary = SaveEndpointFromSummaryReport(save_file=None,
                                                    years_to_include=years_to_include)

    analyzer_list = [analyze_counter,
                     analyze_summary]

    for analyzer in analyzer_list:
        am.add_analyzer(analyzer)
    exp = retrieve_experiment(exp_id)
    am.add_experiment(exp)
    am.analyze()

    # Put results together into a single DataFrame:
    df_list = [x.results for x in am.analyzers]
    if len(df_list) == 1:
        df_result = df_list[0]
    elif len(df_list) == 2:
        df_result = pd.merge(df_list[0], df_list[1],
                             on=["sim_id","year"], suffixes=["","_duplicated"])
    else:
        raise NotImplementedError

    df_result = remove_duplicate_columns(df_result)

    df_result.to_csv("endpoints_{}.csv".format(exp_id), index=False)
    return df_result

if __name__ == "__main__":
    exp_id = sys.argv[1]
    years_to_include = int(sys.argv[2])
    run_analyzers_and_save_output(exp_id, years_to_include)

