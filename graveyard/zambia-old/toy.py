import os
import functools as fun
import json

from dtk.tools.climate.ClimateGenerator import ClimateGenerator
from dtk.tools.migration.MigrationGenerator import MigrationGenerator
from dtk.tools.spatialworkflow.DemographicsGenerator import DemographicsGenerator
from dtk.tools.spatialworkflow.SpatialManager import SpatialManager
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species_param
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser


def setup_chiyabi_single_node_cbever(cb,demo_file=None,immun_file=None,migrate=False):

    # Spatial simulation + migration settings
    cb.update_params({
        'Birth_Rate_Dependence': 'FIXED_BIRTH_RATE',  # Match demographics file for constant population size (with exponential age distribution)
        'Enable_Nondisease_Mortality': 1,
        'New_Diagnostic_Sensitivity': 0.025,  # 40/uL
        "Enable_Immunity_Initialization_Distribution": 1,
        "Immunity_Initialization_Distribution_Type": "DISTRIBUTION_COMPLEX", # [Not sure what this does]

        'Air_Temperature_Filename': "Climate/test/Zambia_30arcsec_air_temperature_daily.bin",
        'Land_Temperature_Filename': "Climate/test/Zambia_30arcsec_air_temperature_daily.bin",
        'Rainfall_Filename': "Climate/test/Zambia_30arcsec_rainfall_daily.bin",
        'Relative_Humidity_Filename': "Climate/test/Zambia_30arcsec_relative_humidity_daily.bin",
        'Vector_Species_Names': ['arabiensis', 'funestus']
    })

    set_species_param(cb, 'arabiensis', 'Larval_Habitat_Types', {
        "CONSTANT": 2000000.0,
        "TEMPORARY_RAINFALL": 100000000.0
    })

    set_species_param(cb, 'funestus', 'Larval_Habitat_Types', {
        "LINEAR_SPLINE": {
            "Capacity_Distribution_Per_Year": {
                "Times": [
                    0.0,
                    30.417,
                    60.833,
                    91.25,
                    121.667,
                    152.083,
                    182.5,
                    212.917,
                    243.333,
                    273.75,
                    304.167,
                    334.583
                ],
                "Values": [
                    0.0,
                    0.0,
                    0.0,
                    0.2,
                    0.8,
                    1.0,
                    1.0,
                    1.0,
                    0.5,
                    0.2,
                    0.0,
                    0.0
                ]
            },
            "Max_Larval_Capacity": 100000000.0
        },
        "WATER_VEGETATION": 2000000.0
    })


    if immun_file:
        cb.update_params({'Demographics_Filenames': [demo_file, immun_file]})
    else:
        cb.update_params({'Demographics_Filenames': [demo_file]})

    if migrate:
        print "migration on!"
        cb.update_params({
                            # 'Vector_Sampling_Type': 'SAMPLE_IND_VECTORS', # individual vector model (required for vector migration)
                            # 'Mosquito_Weight': 10,
                            # 'Enable_Vector_Migration': 1, # mosquito migration
                            # 'Enable_Vector_Migration_Local': 1, # migration rate hard-coded in NodeVector::processEmigratingVectors() such that 50% total leave a 1km x 1km square per day (evenly distributed among the eight adjacent grid cells).

                            'Migration_Model': 'FIXED_RATE_MIGRATION',
                            'Local_Migration_Filename': os.path.join('Migration/', exp_name + '_migration.bin'), # note that underscore prior 'migration.bin' is required for legacy reasons that need to be refactored...
                            'Enable_Local_Migration':1,
                            'Migration_Pattern': 'SINGLE_ROUND_TRIPS', # human migration
                            'Local_Migration_Roundtrip_Duration': 2, # mean of exponential days-at-destination distribution
                            'Local_Migration_Roundtrip_Probability': 0.95, # fraction that return
        })

    else:
        print "migration off!!!"
        cb.update_params({'Migration_Model': 'NO_MIGRATION'})  #'NO_MIGRATION' is actually default for MALARIA_SIM, but might as well make sure it's off




if True:
    exp_name = 'GridTest_v2'

    location = 'HPC'
    SetupParser.default_block = location

    num_cores = 1
    num_years = 2
    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', #'VECTOR_SIM'
                                        Num_Cores=num_cores,
                                        Simulation_Duration=int(365*num_years))

    cb.set_experiment_executable('inputs/Eradication.exe')
    cb.set_input_files_root('inputs')

    cb.update_params({
                    'Enable_Spatial_Output': 1, # spatial reporting
                    'Spatial_Output_Channels': ['Infectious_Vectors', 'Adult_Vectors', 'New_Infections','Population', 'Prevalence', 'New_Diagnostic_Prevalence', 'Daily_EIR', 'New_Clinical_Cases', 'Human_Infectious_Reservoir', 'Daily_Bites_Per_Human', 'Land_Temperature','Relative_Humidity', 'Rainfall', 'Air_Temperature']
                    })

    cb.set_param("Enable_Demographics_Builtin", 0)
    cb.set_param("Valid_Intervention_States", [])
    # setup_chiyabi_single_node_cbever(cb,demo_file='Demographics/chiyabi-luumbo-rd1.json',immun_file='Immunity/immune_test_p1_33_p2_117.json',migrate=True)




# INITIALIZE SETUP PARSER
# This block will be used unless overridden on the command-line
if False:
    SetupParser.init()

# GENERATE DEMOGRAPHICS FILE FROM CSV OF GRID POPULATIONS
if False:
    grid_pop_csv_file = './gridding/test2.csv'
    dg = DemographicsGenerator.from_file(cb,grid_pop_csv_file)
    demo_dict = dg.generate_demographics()
    demo_fp = "./inputs/Demographics/demo_test.json"
    demo_f = open(demo_fp,'w+')
    json.dump(demo_dict,demo_f,indent=4)
    demo_f.close()


# GENERATE CLIMATE FILES
if False:
    cg = ClimateGenerator(demo_fp, './logs/climate_wo.json', './inputs/Climate/test')


# GENERATE MIGRATION FILES:
if True:
    demo_fp = 'C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/inputs/Demographics/chiyabi-luumbo-rd1_demographics.json'
    adj_fp = 'C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/gridding/chiyabi-luumbo-rd1_adjacency.json'

    mg = MigrationGenerator(demo_fp, adj_fp)

    mg.generate_link_rates()
    mg.save_link_rates_to_txt('C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/gridding/migr_rates.txt')

    # Generate migration binary:
    migration_filename = cb.get_param('Local_Migration_Filename')
    MigrationGenerator.link_rates_txt_2_bin('C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/gridding/migr_rates.txt',
                                            'C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/inputs/Migration/', exp_name + '_migration.bin')
                                            # os.path.join('./inputs/', migration_filename))
    # om("Migration binary saved to: " + os.path.join(self.sim_data_input, migration_filename))

    # Generate migration header:
    MigrationGenerator.save_migration_header(demo_fp,outfilename='C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/inputs/Migration/{}_migration.bin.json'.format(exp_name))


# demographics generator instance
# dg = DemographicsGenerator.from_file(cb,grid_pop_csv_file)

# geography = "Sinamalima"
#
# exp_name = prefix + "_base"
#
# # Working directory is current dir for now
# working_dir = os.path.abspath('.')
# input_path = os.path.join(working_dir, "input")
# output_dir = os.path.join(working_dir, "output")
# population_input_file = 'pop_gridded_alts.csv'  # see format in dtk.tools.spatialworkflow.DemographicsGenerator
# nodes_params_input_file = "grid_habs.json"
# migration_matrix_input_file = "gridded_households_adj_list.json"
#
# # Create the spatial_manager
# spatial_manager = SpatialManager(
#     location,
#     cb,
#     # setup,
#     geography,
#     exp_name,
#     working_dir,
#     input_path,
#     sim_data_input_root='.',
#     # assuming the input files will reside on COMPS user's directory (e.g. \\idmppfil01\idm\home\user_name) which is mapped to T as a network drive; change if necessary
#     population_input_file=population_input_file,
#     migration_matrix_input_file=migration_matrix_input_file,
#     output_dir=output_dir,
#     log=True,
#     num_cores=num_cores,
#
#     # update_demographics=fun.partial(apply_pop_scale_larval_habitats, os.path.join(input_path, nodes_params_input_file)),
#     # generate_climate = True,
#     # generate_migration = True,
#     # generate_load_balancing = True,
#     # generate_immune_overlays= True
# )








run_sim_args =  {
    'config_builder': cb,
    'exp_name': exp_name,
    # 'exp_builder':builder
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)