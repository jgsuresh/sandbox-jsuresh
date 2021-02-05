
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



class SaveEndpointFromInset(SaveEndpoint):
    def __init__(self, years_to_output=[1], save_file=None, output_filename='InsetChart.json'):
        super().__init__(save_file=save_file, output_filename=output_filename)

        self.years_to_output = years_to_output


    def select_simulation_data(self, data, simulation):
        t = np.array([])
        RDT_prev = np.array([])
        daily_bite_rate = np.array([])
        vpfm = np.array([])
        ani = np.array([])

        # Get timesteps
        d = data[self.filenames[0]]["Channels"]["Blood Smear Parasite Prevalence"]["Data"]
        all_timesteps = np.arange(1,len(d)+1)

        # Get data for every year in the list self.years_to_include
        for y in self.years_to_output:
            s = (y-1)*365
            e = y*365
            RDT_prev_arr = np.array(data[self.filenames[0]]["Channels"]["Blood Smear Parasite Prevalence"]["Data"][s:e])
            daily_bite_rate_arr = np.array(data[self.filenames[0]]["Channels"]["Daily Bites per Human"]["Data"][s:e])
            vfpm_arr = np.array(data[self.filenames[0]]["Channels"]["Variant Fraction-PfEMP1 Major"]["Data"][s:e])
            ani_arr = np.array(data[self.filenames[0]]["Channels"]["Avg Num Infections"]["Data"][s:e])
            # true_prev_arr = np

            timestep_arr = all_timesteps[s:e]

            RDT_prev = np.append(RDT_prev, RDT_prev_arr)
            daily_bite_rate = np.append(daily_bite_rate, daily_bite_rate_arr)
            vpfm = np.append(vpfm, vfpm_arr)
            ani = np.append(ani, ani_arr)
            t = np.append(t, timestep_arr)

        sim_data = {
            "timestep": t,
            "RDT_prev": RDT_prev,
            "daily_bite_rate": daily_bite_rate,
            "variant_fraction_pfemp1_major": vpfm,
            "avg_num_infections": ani
        }

        sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            sim_data[tag] = simulation.tags[tag]

        return pd.DataFrame(sim_data)




def run_endpoint_analyzers_and_save_output(exp_id, years_to_output):
    print("TEST")
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    am = AnalyzeManager(force_analyze=False)
    analyze_inset = SaveEndpointFromInset(years_to_output, save_file=None)
    am.add_analyzer(analyze_inset)
    # analyzer_list = [analyze_inset]
    # for analyzer in analyzer_list:
    #     am.add_analyzer(analyzer)

    exp = retrieve_experiment(exp_id)
    print(exp)
    am.add_experiment(exp)
    am.analyze()

    df_result = am.analyzers[0].results

    cols_to_save=["timestep", "RDT_prev", "daily_bite_rate", "Run_Number","funest","variant_fraction_pfemp1_major","avg_num_infections"]
    df_result.to_csv("endpoints_{}.csv".format(exp_id), index=False, columns=cols_to_save)
    return df_result




if __name__ == "__main__":
    # print(sys.argv[1])
    list1 = [int(c) for c in sys.argv[1].strip('[]').split(',')]
    years_to_output = list1
    exp_id = sys.argv[2]

    print(years_to_output)
    print(exp_id)

    run_endpoint_analyzers_and_save_output(exp_id, years_to_output)

