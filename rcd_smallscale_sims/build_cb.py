import os
import pandas as pd
import numpy as np
from dtk.vector.species import set_species_param

from helpers.windows_filesystem import get_dropbox_location

#fixme Project has dependency on malaria-zm-kariba
from gridded_sims.run.core_cb_setup import basic_gridded_config_builder, set_executable
from gridded_sims.run.build_cb import kariba_ento

# Run parameters
default_sim_duration = 365*5


def get_project_folder():
    dropbox_folder = get_dropbox_location()
    project_folder = os.path.join(dropbox_folder, "projects/Zambia/rcd_clustering_and_impact/")
    return project_folder

def build_project_cb(simulation_duration_days=default_sim_duration):
    cb = basic_gridded_config_builder()

    project_folder = get_project_folder()
    set_executable(cb, os.path.join(project_folder, "bin/malaria_custom_build_146_chw/"))

    cb.update_params({
        "Num_Cores": 1,
        "Simulation_Duration": simulation_duration_days,
        "Demographics_Filenames": ["demo.json"],

        "Climate_Model": "CLIMATE_BY_DATA",
        "Air_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Land_Temperature_Filename": "Zambia_30arcsec_air_temperature_daily.bin",
        "Rainfall_Filename": "Zambia_30arcsec_rainfall_daily.bin",
        "Relative_Humidity_Filename": "Zambia_30arcsec_relative_humidity_daily.bin",

        "Migration_Model": "FIXED_RATE_MIGRATION",
        "Migration_Pattern": "SINGLE_ROUND_TRIPS",

        "Enable_Vector_Migration": 1,
        "Enable_Vector_Migration_Local": 1,
        "Vector_Migration_Filename_Local": "vector_local_migration.bin",
        "Vector_Migration_Modifier_Equation": "LINEAR",
        "x_Vector_Migration_Local": 1
    })

    cb.set_input_files_root(os.path.join(project_folder, "dtk_simulation_input/"))

    return cb