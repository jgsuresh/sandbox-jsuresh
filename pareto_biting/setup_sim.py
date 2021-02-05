from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

from dtk.vector.species import set_species, set_species_param

from jsuresh_helpers.running_dtk import set_executable, add_params_csv_to_dtk_config_builder
from jsuresh_helpers.uncategorized import load_csv_into_dictionary
from jsuresh_helpers.windows_filesystem import get_dropbox_location


dropbox_folder = get_dropbox_location()
input_folder = dropbox_folder + "projects/jsuresh_heterogeneous_biting_comparison/"
bin_folder = input_folder + "bin"
params_csv_filename = input_folder + "params.csv"


def set_ento(cb):
    set_species(cb, ["arabiensis", "funestus"])

    set_species_param(cb, 'arabiensis', 'Indoor_Feeding_Fraction', 0.5)
    set_species_param(cb, 'arabiensis', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'arabiensis', 'Anthropophily', 0.65)
    set_species_param(cb, 'arabiensis', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")

    set_species_param(cb, 'funestus', "Indoor_Feeding_Fraction", 0.9)
    set_species_param(cb, 'funestus', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'funestus', 'Anthropophily', 0.65)
    set_species_param(cb, 'funestus', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")



def build_project_cb():
    cb = DTKConfigBuilder.from_defaults("MALARIA_SIM")

    set_executable(cb, bin_folder)
    cb.set_input_files_root(input_folder)

    add_params_csv_to_dtk_config_builder(cb, params_csv_filename)
    set_ento(cb)

    return cb