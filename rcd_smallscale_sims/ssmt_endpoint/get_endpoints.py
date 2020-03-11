
# Run endpoint analyzer on all runs in the suite, and collect ALL results into a single results CSV/dataframe
import sys
import numpy as np
import pandas as pd
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from simtools.Utilities.Experiments import retrieve_experiment


class SaveEndpoint(BaseAnalyzer):
    def __init__(self, save_file=None,start_time_step=0, include_counter_report=False, output_filename="InsetChart.json"):
        # filenames = ['output/InsetChart.json']
        filenames = ['output/{}'.format(output_filename)]
        if include_counter_report:
            filenames.append('output/ReportEventCounter.json')
        super().__init__(filenames=filenames)

        self.save_file = save_file
        self.start_time_step = start_time_step
        self.include_counter_report = include_counter_report

    def select_simulation_data(self, data, simulation):
        y = np.array([])
        cases = np.array([])
        infections = np.array([])
        EIR = np.array([])
        prev = np.array([])


        j = 0
        # for j in range(4):
        s = j*365  + self.start_time_step
        e = (j+1)*365 + self.start_time_step
        cases_array = np.array(data[self.filenames[0]]["Channels"]["New Clinical Cases"]["Data"][s:e])
        infec_array = np.array(data[self.filenames[0]]["Channels"]["New Infections"]["Data"][s:e])
        EIR_array = np.array(data[self.filenames[0]]["Channels"]["Daily EIR"]["Data"][s:e])
        RDT_prev_arr = np.array(data[self.filenames[0]]["Channels"]["Blood Smear Parasite Prevalence"]["Data"][s:e])

        y = np.append(y,j)
        cases = np.append(cases, np.sum(cases_array))
        infections = np.append(infections, np.sum(infec_array))
        EIR = np.append(EIR, np.sum(EIR_array))
        prev = np.append(prev, np.average(RDT_prev_arr))

        if self.include_counter_report:
            received_treatment = np.array([])
            received_test = np.array([])
            received_RCD_drugs = np.array([])
            received_campaign_drugs = np.array([])

            j = 0
            # for j in range(4):
            s = j * 365 + self.start_time_step
            e = (j + 1) * 365 + self.start_time_step
            received_treatment_array = np.array(data[self.filenames[1]]["Channels"]["Received_Treatment"]["Data"][s:e])
            received_test_array = np.array(data[self.filenames[1]]["Channels"]["Received_Test"]["Data"][s:e])
            received_RCD_drugs_array = np.array(data[self.filenames[1]]["Channels"]["Received_RCD_Drugs"]["Data"][s:e])
            received_campaign_drugs_array = np.array(data[self.filenames[1]]["Channels"]["Received_Campaign_Drugs"]["Data"][s:e])

            received_treatment = np.append(received_treatment, np.sum(received_treatment_array))
            received_test = np.append(received_test, np.sum(received_test_array))
            received_RCD_drugs = np.append(received_RCD_drugs, np.sum(received_RCD_drugs_array))
            received_campaign_drugs = np.append(received_campaign_drugs, np.sum(received_campaign_drugs_array))

        sim_data = {
            "year": y,
            "cases": cases,
            "infections": infections,
            "EIR": EIR,
            "avg_RDT_prev": prev}

        if self.include_counter_report:
            sim_data["received_treatment"] = received_treatment
            sim_data["received_test"] = received_test
            sim_data["received_RCD_drugs"] = received_RCD_drugs
            sim_data["received_campaign_drugs"] = received_campaign_drugs

        for tag in simulation.tags:
            sim_data[tag] = simulation.tags[tag]

        return pd.DataFrame(sim_data)

    def combine(self, all_data):
        data_list = []
        for sim in all_data.keys():
            data_list.append(all_data[sim])

        return pd.concat(data_list)

    def finalize(self, all_data):
        sim_data_full = self.combine(all_data)
        # print("all_data ",all_data)
        # print("sim_data_full ", sim_data_full)
        if self.save_file:
            sim_data_full.to_csv(self.save_file, index=False)
        return sim_data_full

if __name__ == "__main__":
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    exp_id = sys.argv[1]
    # start_time_step = int(sys.argv[2])

    am = AnalyzeManager()
    am.add_analyzer(SaveEndpoint(save_file="endpoints_{}.csv".format(exp_id),
                                 # start_time_step=start_time_step,
                                 include_counter_report=True,
                                 output_filename="ReportMalariaFilteredFinal_Year.json"))
    exp = retrieve_experiment(exp_id)
    am.add_experiment(exp)
    am.analyze()
