import pandas as pd
import numpy as np
import math
import os

from dtk.interventions.input_EIR import add_InputEIR
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species_param
from dtk.interventions.itn_age_season import add_ITN_age_season
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.irs import add_IRS
from helpers.relative_time import convert_to_day_365
from malaria.reports.MalariaReport import add_filtered_spatial_report, add_filtered_report, add_event_counter_report
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign
from malaria import infection, immunity, symptoms

from zambia_helpers import catchment_grid_cells



class ZambiaConfigBuilder:

    def __init__(self,
                 sim_start_year,
                 sim_duration_days,
                 dropbox_user='jsuresh',
                 num_cores=4,
                 parser_location='HPC',
                 immunity_params='prashanth'):

        # user =

        self.dropbox_base = "C:/Users/{}/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/".format(dropbox_user)
        # self.catch = catch
        self.sim_start_year = sim_start_year
        self.sim_duration_days = sim_duration_days
        self.num_cores = num_cores
        self.parser_location = parser_location

        self.start_date = "{}-01-01".format(self.sim_start_year)  # Day 1 of simulation
        self.immunity_params = 'prashanth'

        self.build_cb()
        self.set_up_EIR_node(self.cb)
        # print("WARNING: EIR NODE NOT SET UP IN ZAMBIA CONFIG-BUILDER")
        self.add_zambia_ento_to_cb()


        # Updated reporting:
        self.cb.update_params({"Report_Detection_Threshold_Blood_Smear_Parasites": 0})
        self.cb.update_params({"Parasite_Smear_Sensitivity": 0.025})



    #################################################################################################
    # CONFIG-BUILDER SETUP

    def build_cb(self):
        self.basic_cb()
        self.spatial_cb_setup()

    def basic_cb(self):
        SetupParser.default_block = self.parser_location

        self.cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
        self.cb.set_experiment_executable(os.path.join(self.dropbox_base,'bin/malaria_ongoing_build_185/Eradication.exe'))
        self.cb.set_input_files_root(os.path.join(self.dropbox_base, 'inputs/catchments/'))


        # Tell config builder where to find dlls for specified Bamboo build of executable
        self.cb.set_dll_root(os.path.join(self.dropbox_base, 'bin/malaria_ongoing_build_185/'))

        self.cb.set_param("Num_Cores", self.num_cores)

        # Reduce StdOut size
        self.cb.params['logLevel_default'] = "WARNING"
        self.cb.params['Enable_Log_Throttling'] = 1
        self.cb.params["Memory_Usage_Warning_Threshold_Working_Set_MB"] = 50000
        self.cb.params["Memory_Usage_Halting_Threshold_Working_Set_MB"] = 60000
        
        # Prevent DTK from spitting out too many messages
        self.cb.params['logLevel_JsonConfigurable'] = "WARNING"
        self.cb.params['Disable_IP_Whitelist'] = 1

        # Latest parameters
        # self.cb.update_params(immunity.params)
        self.cb.update_params(infection.params)
        self.cb.update_params(symptoms.params)

        if self.immunity_params == 'prashanth':
            self.cb.update_params({
                'Antigen_Switch_Rate': pow(10, -9.116590124),
                'Base_Gametocyte_Production_Rate': 0.06150582,
                'Base_Gametocyte_Mosquito_Survival_Rate': 0.002011099,
                'Falciparum_MSP_Variants': 32,
                'Falciparum_Nonspecific_Types': 76,
                'Falciparum_PfEMP1_Variants': 1070,
                'Gametocyte_Stage_Survival_Rate': 0.588569307,
                'MSP1_Merozoite_Kill_Fraction': 0.511735322,
                'Max_Individual_Infections': 3,
                'Nonspecific_Antigenicity_Factor': 0.415111634
            })
        elif self.immunity_params == "jaline":
            self.cb.update_params({
                'Base_Gametocyte_Production_Rate': 0.044,
                "Gametocyte_Stage_Survival_Rate": 0.82,
                'Antigen_Switch_Rate': 2.96e-9,
                'Falciparum_PfEMP1_Variants': 1112,
                'Falciparum_MSP_Variants': 7,
                'MSP1_Merozoite_Kill_Fraction': 0.43,
                'Falciparum_Nonspecific_Types': 90,
                'Nonspecific_Antigenicity_Factor': 0.42,
                'Base_Gametocyte_Mosquito_Survival_Rate': 0.00088,
                "Max_Individual_Infections": 5
            })




    def spatial_cb_setup(self):
        self.cb.params['Simulation_Duration'] = self.sim_duration_days
        # self.cb.update_params({'Demographics_Filenames': ['demo.json']})

        # CLIMATE
        # self.cb.update_params({
        #     "Climate_Model": "CLIMATE_CONSTANT"
        # })
        # self.cb.update_params({
        #     'Air_Temperature_Filename': "Zambia_30arcsec_air_temperature_daily.bin",
        #     'Land_Temperature_Filename': "Zambia_30arcsec_air_temperature_daily.bin",
        #     'Rainfall_Filename': "Zambia_30arcsec_rainfall_daily.bin",
        #     'Relative_Humidity_Filename': "Zambia_30arcsec_relative_humidity_daily.bin"
        # })

        #######################################################################################################
        # MIGRATION-RELATED PARAMETERS:
        #######################################################################################################

        # LOCAL (intra-catchment)
        # self.cb.update_params({'Migration_Model': 'NO_MIGRATION'})  #'NO_MIGRATION' is actually default for MALARIA_SIM, but might as well make sure it's off
        self.cb.update_params({
            'Migration_Model': 'FIXED_RATE_MIGRATION',
            'Enable_Local_Migration':1,
            # 'Local_Migration_Filename': 'Migration/local_migration.bin', # note that underscore prior 'migration.bin' is required for legacy reasons that need to be refactored...
            'Migration_Pattern': 'SINGLE_ROUND_TRIPS', # human migration
            'Local_Migration_Roundtrip_Duration': 2, # mean of exponential days-at-destination distribution
            'Local_Migration_Roundtrip_Probability': 1.0, # fraction that return
            # 'x_Local_Migration': 1.0,
        })

        # REGIONAL (inter-catchment)
        # self.cb.update_params({
        #     'Enable_Regional_Migration': 1,
        #     # 'Regional_Migration_Filename': 'Migration/_Regional_Migration.bin',
        #     'Regional_Migration_Roundtrip_Duration': 3,
        #     'Regional_Migration_Roundtrip_Probability': 1,
        #     # 'x_Regional_Migration': 0.03,
        # })


        # Miscellaneous:
        self.cb.set_param("Enable_Demographics_Other", 1)
        self.cb.set_param("Enable_Demographics_Builtin", 0)
        self.cb.set_param("Valid_Intervention_States", [])
        # self.cb.set_param("New_Diagnostic_Sensitivity", 0.025) # 40/uL
        self.cb.set_param("Report_Detection_Threshold_True_Parasite_Density", 40.0)
        self.cb.update_params({"Report_Detection_Threshold_PfHRP2": 40.0})

        # Human population properties:
        self.cb.update_params({
            'Birth_Rate_Dependence': 'FIXED_BIRTH_RATE',  # Match demographics file for constant population size (with exponential age distribution)
            'Enable_Nondisease_Mortality': 1
        })


        # Immunity:
        self.cb.update_params({
            "Enable_Immunity_Initialization_Distribution": 0
        })

        # Intervention events
        intervene_events_list = ["Bednet_Got_New_One","Bednet_Using","Bednet_Discarded"]

        self.cb.update_params({
            "Report_Event_Recorder": 0,
            "Report_Event_Recorder_Ignore_Events_In_List": 0,
            "Listed_Events": intervene_events_list,
            "Report_Event_Recorder_Events": intervene_events_list
        })


    def add_zambia_ento_to_cb(self):
        # Vector properties:
        self.cb.update_params({'Vector_Species_Names': ['arabiensis', 'funestus']})

        # Arabiensis
        set_species_param(self.cb,
                          'arabiensis',
                          'Larval_Habitat_Types', {
                              "CONSTANT": 2000000.0,
                              "TEMPORARY_RAINFALL": 100000000.0
                          })

        set_species_param(self.cb, 'arabiensis', 'Indoor_Feeding_Fraction', 0.5)
        set_species_param(self.cb, 'arabiensis', 'Adult_Life_Expectancy', 20)
        set_species_param(self.cb, 'arabiensis', 'Anthropophily', 0.65)
        set_species_param(self.cb, 'arabiensis', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")


        # Funestus
        set_species_param(self.cb,
                          'funestus',
                          'Larval_Habitat_Types', {
                              "LINEAR_SPLINE": {
                                  "Capacity_Distribution_Number_Of_Years": 1,
                                  "Capacity_Distribution_Over_Time": {
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

        set_species_param(self.cb, 'funestus', "Indoor_Feeding_Fraction", 0.9)
        set_species_param(self.cb, 'funestus', 'Adult_Life_Expectancy', 20)
        set_species_param(self.cb, 'funestus', 'Anthropophily', 0.65)
        set_species_param(self.cb, 'funestus', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")

        self.cb.params['Enable_Vector_Species_Report'] = 1

        # if 'Vector_Sugar_Feeding_Frequency' in self.cb.params:
        #     del self.cb.params['Vector_Sugar_Feeding_Frequency']




    def set_up_EIR_node(self, cb, EIR_scale_factor=6, EIR_start_day=0):
        # From Jaline

        cb.update_params({
            'Enable_Regional_Migration': 1,
            'Regional_Migration_Roundtrip_Duration': 3,
            'Regional_Migration_Roundtrip_Probability': 1,
            'x_Regional_Migration': 0.0405,
            # 'Regional_Migration_Filename': 'Regional_Migration.bin',
        })

        # EIR profile copied from Jaline's household model
        monthly_profile = [0.21, 0.28, 0.43, 0.65, 0.84, 1.21, 1.24, 1.04, 0.84, 0.57, 0.29, 0.17]

        add_InputEIR(cb,
                     monthlyEIRs=[x * EIR_scale_factor for x in monthly_profile],
                     nodes={'class': 'NodeSetNodeList', 'Node_List': [100000]},
                     start_day=EIR_start_day)

        return {"EIR_scale_factor": EIR_scale_factor}




    #################################################################################################
    # INTERVENTIONS (ADDITIONS TO CAMPAIGN FILE)

    # Input: intervention_df = pd.read_csv("grid_itn_events.csv")
    # format: interventions by grid cell.  Has columns for "grid_cell", "fulldate", "simday"
    def try_campaign_compression(self, intervention_df, bin_fidelity=1.0):

        # Because implementing things on a grid_cell level leads to enormous campaign files, try to group things together wherever possible
        def round_nearest(x, a):
            # try:
            #     rounded = round(round(x / a) * a, -int(math.floor(math.log10(a))))
            # except:
            #     print(x,a)
            #     exit()
            rounded = round(round(x / a) * a, -int(math.floor(math.log10(a))))
            return rounded

        binned_intervention_df = intervention_df.copy(deep=True)

        # Bin all fields other than grid_cell and date:
        field_list = list(intervention_df.columns)
        field_list.remove('grid_cell')
        field_list.remove('fulldate')
        field_list.remove('simday')

        # Bin these fields with bin width = bin_fidelity
        for field in field_list:
            binned_intervention_df[field] = intervention_df[field].map(lambda x: round_nearest(x, bin_fidelity))

        # Group by the new binned fields, as well as by date
        data_fields = ['simday'] + field_list
        binned_and_grouped = binned_intervention_df.groupby(data_fields)

        return [binned_intervention_df, binned_and_grouped, data_fields]



    def try_campaign_compression_v2(self, intervention_df, field_list, bin_fidelity=0.1, simday_fidelity=10):

        def round_nearest(x, a):
            rounded = round(round(x / a) * a, -int(math.floor(math.log10(a))))
            return rounded

        binned_intervention_df = intervention_df.copy(deep=True)

        # Bin these fields with bin width = bin_fidelity
        for field in field_list:
            binned_intervention_df[field] = intervention_df[field].map(lambda x: round_nearest(x, bin_fidelity))

        binned_intervention_df['simday'] = intervention_df['simday'].map(lambda x: round_nearest(x, simday_fidelity))

        # Group by the new binned fields, as well as by date
        data_fields = ['simday'] + field_list
        binned_and_grouped = binned_intervention_df.groupby(data_fields)

        return [binned_intervention_df, binned_and_grouped, data_fields]


    def add_hs(self, cb, filename=None):
        if not filename:
            filename = self.dropbox_base + "inputs/grid_csv/grid_all_healthseek_events.csv"
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        hs_field_list = ["cov_newclin_youth", "cov_newclin_adult", "cov_severe_youth", "cov_severe_adult", "duration"]
        binned_intervene_events, binned_and_grouped, data_fields = self.try_campaign_compression_v2(intervene_events, hs_field_list)

        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))

            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                node_dict = {"class": "NodeSetAll"}
            else:
                node_dict = {"class": "NodeSetNodeList", "Node_List": node_list}

            add_health_seeking(cb,
                               start_day=float(table_dict['simday']),
                               targets=[{'trigger': 'NewClinicalCase',
                                         'coverage': float(table_dict['cov_newclin_youth']),
                                         'agemin': 0,
                                         'agemax': 5,
                                         'seek': 1,
                                         'rate': 0.3},
                                        {'trigger': 'NewClinicalCase',
                                         'coverage': float(table_dict['cov_newclin_adult']),
                                         'agemin': 5,
                                         'agemax': 100,
                                         'seek': 1,
                                         'rate': 0.3},
                                        {'trigger': 'NewSevereCase',
                                         'coverage': float(table_dict['cov_severe_youth']),
                                         'agemin': 0,
                                         'agemax': 5,
                                         'seek': 1, 'rate': 0.5},
                                        {'trigger': 'NewSevereCase',
                                         'coverage': float(table_dict['cov_severe_adult']),
                                         'agemin': 5,
                                         'agemax': 100,
                                         'seek': 1,
                                         'rate': 0.5}],
                               drug=['Artemether', 'Lumefantrine'],
                               dosing='FullTreatmentNewDetectionTech',
                               nodes=node_dict,
                               duration=float(table_dict['duration']))


    def add_itn(self, cb, filename=None):
        if not filename:
            filename = self.dropbox_base+ "inputs/grid_csv/grid_all_itn_events.csv"
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        itn_field_list = ["age_cov","cov_all","min_season_cov","fast_fraction"]
        binned_intervene_events, binned_and_grouped, data_fields  = self.try_campaign_compression_v2(intervene_events, itn_field_list)

        birthnet_df = intervene_events.copy(deep=True)
        birthnet_df['duration'] = birthnet_df.groupby('grid_cell')['simday'].shift(-1).sub(birthnet_df['simday'])
        birthnet_df['duration'].fillna(-1, inplace=True)
        birthnet_field_list = itn_field_list + ["duration"]
        BIRTH_binned_intervene_events, BIRTH_binned_and_grouped, BIRTH_data_fields = self.try_campaign_compression_v2(birthnet_df, birthnet_field_list)


        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))
            node_list = sorted(list(set(group['grid_cell']))) #fixme Needed to add this because sometimes there are duplicate nodes in the list, and this breaks things
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            start = float(table_dict['simday'])
            if start >= 0:
                # Regular bednet distribution
                add_ITN_age_season(cb,
                                   start=float(table_dict['simday']),
                                   age_dep={'youth_cov': float(table_dict['age_cov']),
                                            'youth_min_age': 5,
                                            'youth_max_age': 20},
                                   coverage_all=float(table_dict['cov_all']),
                                   as_birth=False,
                                   seasonal_dep={'min_cov': float(table_dict['min_season_cov']),
                                                 'max_day': 60},
                                   discard={'halflife1': 260,
                                            'halflife2': 2106,
                                            'fraction1': float(table_dict['fast_fraction'])},
                                   nodeIDs=nodeIDs)

        # Birthnet distribution
        for table, group in BIRTH_binned_and_grouped:
            table_dict = dict(zip((BIRTH_data_fields), table))
            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            start = float(table_dict['simday'])
            if start >= 0:
                add_ITN_age_season(cb,
                                   as_birth=True,
                                   duration=table_dict['duration'],
                                   start=float(table_dict['simday']),
                                   age_dep={'youth_cov': float(table_dict['age_cov']),
                                            'youth_min_age': 5,
                                            'youth_max_age': 20},
                                   coverage_all=float(table_dict['cov_all']),
                                   seasonal_dep={'min_cov': float(table_dict['min_season_cov']),
                                                 'max_day': 60},
                                   discard={'halflife1': 260,
                                            'halflife2': 2106,
                                            'fraction1': float(table_dict['fast_fraction'])},
                                   nodeIDs=nodeIDs)


    def add_irs(self, cb, filename=None):
        if not filename:
            filename = self.dropbox_base + "inputs/grid_csv/grid_all_irs_events.csv"
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        irs_field_list = ["cov_all", "killing", "exp_duration", "box_duration"]
        binned_intervene_events, binned_and_grouped, data_fields = self.try_campaign_compression_v2(intervene_events, irs_field_list)

        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))
            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            add_IRS(cb, start=int(table_dict['simday']),
                    coverage_by_ages=[{'coverage': float(table_dict['cov_all'])}],
                    waning={"Killing_Config": {
                        "Initial_Effect": float(table_dict['killing']),
                        "Decay_Time_Constant": float(table_dict['exp_duration']),
                        "Box_Duration": float(table_dict['box_duration']),
                        "class": "WaningEffectBoxExponential"
                    }},
                    nodeIDs=nodeIDs)


    def add_msat(self, cb, filename=None):
        if not filename:
            filename = self.dropbox_base + "inputs/grid_csv/grid_all_msat_events.csv"
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        msat_field_list = ["cov_all"]
        binned_intervene_events, binned_and_grouped, data_fields = self.try_campaign_compression_v2(intervene_events, msat_field_list)

        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))
            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            add_drug_campaign(cb,
                              campaign_type='MSAT',
                              drug_code='AL',
                              diagnostic_type='BLOOD_SMEAR_PARASITES',
                              diagnostic_threshold=0,
                              start_days=[float(table_dict['simday'])],
                              coverage=table_dict['cov_all'],
                              repetitions=1,
                              interval=60,
                              nodes=nodeIDs)


    def add_mda(self, cb, filename=None):
        if not filename:
            filename = self.dropbox_base + "inputs/grid_csv/grid_all_mda_events.csv"
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        mda_field_list = ["cov_all"]
        binned_intervene_events, binned_and_grouped, data_fields = self.try_campaign_compression_v2(intervene_events, mda_field_list)

        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))
            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            add_drug_campaign(cb,
                              campaign_type='MDA',
                              drug_code='DP',
                              start_days=[float(table_dict['simday'])],
                              coverage=table_dict['cov_all'],
                              repetitions=1,
                              interval=60,
                              nodes=nodeIDs)


    def add_rcd(self, cb, filename=None):
        if not filename:
            # filename = self.dropbox_base + "inputs/grid_csv/grid_all_react_events.csv"
            filename = self.dropbox_base + "inputs/grid_csv/grid_all_react_events_SIMPLE.csv"
            print("WARNING: using simplified RCD file-- grid_all_react_events_SIMPLE.csv")
        intervene_events = pd.read_csv(filename)

        # Restrict to catchment of interest
        intervene_events = intervene_events[np.in1d(intervene_events['grid_cell'],self.catch_cells)]
        intervene_events.reset_index(inplace=True)

        # Compute simulation days relative to start date or use default in file
        intervene_events['simday'] = [convert_to_day_365(x, self.start_date, "%Y-%m-%d")
                                       for x in intervene_events.fulldate]

        rcd_field_list = ["coverage", "trigger_coverage", "interval"]
        binned_intervene_events, binned_and_grouped, data_fields = self.try_campaign_compression_v2(intervene_events, rcd_field_list)

        for table, group in binned_and_grouped:
            table_dict = dict(zip((data_fields), table))
            node_list = sorted(group['grid_cell'])
            if node_list == sorted(self.catch_cells):
                nodeIDs = []
            else:
                nodeIDs = node_list

            for i in range(len(intervene_events)):
                add_drug_campaign(cb,
                                  campaign_type='rfMSAT',
                                  drug_code='AL',
                                  diagnostic_type='BLOOD_SMEAR_PARASITES',
                                  diagnostic_threshold=0,
                                  start_days=[float(table_dict['simday'])],
                                  coverage=float(table_dict['coverage']),
                                  trigger_coverage=float(table_dict['trigger_coverage']),
                                  interval=float(table_dict['interval']),
                                  nodes=nodeIDs)


    # def add_atsb

    def add_all_interventions(self, cb, catch):
        self.catch_cells = catchment_grid_cells(catch)

        self.add_hs(cb)
        self.add_itn(cb)
        self.add_irs(cb)
        self.add_msat(cb)
        self.add_mda(cb)
        self.add_rcd(cb)


    def add_intervention_combos(self, cb, catch, add_itn, add_irs, add_msat, add_mda, add_rcd):
        self.catch_cells = catchment_grid_cells(catch)

        if add_itn:
            self.add_itn(cb)
        if add_irs:
            self.add_irs(cb)
        if add_msat:
            self.add_msat(cb)
        if add_mda:
            self.add_mda(cb)
        if add_rcd:
            self.add_rcd(cb)

        return {"itn": add_itn,
                "irs": add_irs,
                "msat": add_msat,
                "mda": add_mda,
                "rcd": add_rcd}

    #################################################################################################
    # Reports that analyzers will use:
    # Note that these are specifically designed to work regardless of whether it is a burnin or not (by taking the last X years of data)
    def add_reports_for_likelihood_analyzers(self, cb, catch, filter_duration_days=3650):
        filter_end = self.sim_duration_days
        filter_start = self.sim_duration_days-filter_duration_days

        add_filtered_spatial_report(cb,
                                    start=filter_start,
                                    end=filter_end,
                                    channels=['Population', 'True_Prevalence', "Blood_Smear_Parasite_Prevalence"])  # 'New_Clinical_Cases','New_Infections'

        # Now add report for is for HF-level incidence likelihood analyzer.
        add_event_counter_report(cb,
                                 # event_trigger_list=['Received_Treatment', 'Received_IRS', 'Received_Campaign_Drugs', 'Received_RCD_Drugs', 'Bednet_Got_New_One', 'Received_Test'],
                                 event_trigger_list=['Received_Treatment'], #, 'Received_Test', 'TestedPositive', 'Received_Campaign_Drugs'],
                                 start=filter_start,
                                 duration=filter_duration_days)

        # Get list of cells that correspond to this catchment:
        catch_nodes = catchment_grid_cells(catch, as_list=True)

        add_filtered_report(cb,
                            start=filter_start,
                            end=filter_end,
                            nodes=catch_nodes)

        # Add a similar report for the migration node
        add_filtered_report(cb,
                            start=filter_start,
                            end=filter_end,
                            nodes=[100000],
                            description='Work')




    #################################################################################################
    # ONCE CB IS BUILT, FUNCTIONS FOR WHAT TO DO WITH IT


    def vector_migration_sweeper(self, vector_migration_on):
        if vector_migration_on:
            self.cb.update_params({
                'Vector_Migration_Modifier_Equation': 'LINEAR',
                'Vector_Sampling_Type': 'SAMPLE_IND_VECTORS', # individual vector model (required for vector migration)
                'Mosquito_Weight': 10,
                'Enable_Vector_Migration': 1, # mosquito migration
                'Enable_Vector_Migration_Local': 1, # migration rate hard-coded in NodeVector::processEmigratingVectors() such that 50% total leave a 1km x 1km square per day (evenly distributed among the eight adjacent grid cells).
                'Vector_Migration_Base_Rate': 0.15, # default is 0.5
                'x_Vector_Migration_Local': 1
            })
        else:
            self.cb.update_params({
                'Enable_Vector_Migration': 0,  # mosquito migration
                'Enable_Vector_Migration_Local': 0
            # migration rate hard-coded in NodeVector::processEmigratingVectors() such that 50% total leave a 1km x 1km square per day (evenly distributed among the eight adjacent grid cells).
            })
        return {"vec_migr": vector_migration_on}

    def submit_experiment(self,
                          cb,
                          num_seeds=1,
                          intervention_sweep=False,
                          migration_sweep=False,
                          vector_migration_sweep=False,
                          simple_intervention_sweep=False,
                          custom_name=None):

        # Implement the actual (not dummy) baseline healthseeking
        self.implement_baseline_healthseeking(cb)


        modlists = []

        if num_seeds > 1:
            new_modlist = [ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed) for seed in range(num_seeds)]
            modlists.append(new_modlist)

        if migration_sweep:
            new_modlist = [ModFn(DTKConfigBuilder.set_param, 'x_Local_Migration', x) for x in [0.5,1,5,10]]
            modlists.append(new_modlist)

        if vector_migration_sweep:
            new_modlist = [ModFn(self.vector_migration_sweeper, vector_migration_on) for vector_migration_on in [True, False]]
            modlists.append(new_modlist)

        if simple_intervention_sweep:
            new_modlist = [
                ModFn(self.implement_interventions, True, False, False, False, False),
                ModFn(self.implement_interventions, False, True, False, False, False),
                ModFn(self.implement_interventions, False, False, True, False, False),
                ModFn(self.implement_interventions, False, False, False, True, False),
                ModFn(self.implement_interventions, False, False, False, False, True),
                ModFn(self.implement_interventions, True, True, True, True, True)
            ]
            modlists.append(new_modlist)
        else:
            # new_modlist = [ModFn(self.implement_interventions, True, True, True, True, True)]
            new_modlist = [ModFn(self.implement_interventions, True, True, False, False, False)]
            modlists.append(new_modlist)

        builder = ModBuilder.from_combos(*modlists)

        run_name = self.exp_name
        if custom_name:
            run_name = custom_name


        # SetupParser.init()
        # SetupParser.set("HPC","priority","Normal")
        # exp_manager = ExperimentManagerFactory.init()
        # exp_manager.run_simulations(config_builder=self.cb, exp_name=run_name, exp_builder=builder)
        # return self.cb
        exp_manager = ExperimentManagerFactory.init()
        exp_manager.run_simulations(config_builder=cb, exp_name=run_name, exp_builder=builder)
        return cb

