# Helper script:
#         - If it’s a correct *_serialize_climatefix run, then sim_map tells us where to look for the serialized files, which is great.
#         - But if it’s a *_project_climatefix run, then there is no serialized file output.

import pandas as pd
import numpy as np
import os

from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore

from gridded_sims.calib.comparison_analyzers import SimulationDirectoryMapAnalyzer
from gridded_sims.run.site import get_catchment_list

prev_dist_thresh = 2
inc_norm_dist_thresh = 2


catch_list = get_catchment_list()
best_runs_dict = {}
ref_date = "2010-01-01"


if __name__=="__main__":

    # Write special serialized_files_sim_map for runs that need it
    for c in range(56):
        catch = catch_list[c]
        c_folder = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/calibs/{}".format(catch)
        sim_map_filename = os.path.join(c_folder, "serialized_files_sim_map.csv")

        # See if you can find an experiment named CATCH_project_climatefix

        try:
            name_try = "{}_project_climatefix".format(catch)
            proj_exp = DataStore.get_most_recent_experiment(id_or_name=name_try)

            # If you can find the experiment, find the corresponding parent simulation and output its sim map
            if proj_exp:
                name_try = "{}_serialize".format(catch)
                orig_exp = DataStore.get_most_recent_experiment(id_or_name=name_try)

                am = AnalyzeManager()
                am.add_experiment(orig_exp)
                am.add_analyzer(SimulationDirectoryMapAnalyzer(save_file=sim_map_filename))
                am.analyze()
                print("Wrote serialized_files_sim_map for {}".format(catch))

        except:
            pass


