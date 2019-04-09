class GriddedInputFilesCreator:
    def __init__(self,
                 base,
                 exp_name,
                 desired_cells,
                 cb,
                 grid_pop_csv_file,
                 region="Zambia",
                 start_year=2001,
                 sim_length_years=19,
                 immunity_mode="naive",
                 larval_param_func=None,
                 generate_climate_files=True,
                 **kwargs):

        self.base = base
        self.exp_name = exp_name
        self.exp_base = base + 'data/COMPS_experiments/{}/'.format(exp_name)
        self.demo_fp_full = os.path.join(self.exp_base, "Demographics/demo.json")

        self.desired_cells = desired_cells
        self.cb = cb
        self.grid_pop_csv_file = grid_pop_csv_file
        self.immunity_mode = immunity_mode
        self.region = region
        self.start_year = start_year
        self.sim_length_years = sim_length_years
        self.larval_param_func = larval_param_func
        self.kwargs = kwargs

        self.gravity_migr_params = np.array([7.50395776e-06, 9.65648371e-01, 9.65648371e-01, -1.10305489e+00])

        self.file_setup(generate_climate_files=generate_climate_files)



    def file_setup(self,generate_immunity_file=True,generate_demographics_file=True,generate_climate_files=True,generate_migration_files=True):

        if generate_demographics_file:
            print("Generating demographics file...")
            self.gen_demo_file()

        # if self.immunity_mode != "naive" and generate_immunity_file:
        #     print("Generating immunity files...")
        #     if self.immunity_mode == "uniform":
        #         self.get_immunity_file_from_single_node()
        #     elif self.immunity_mode == "milen":
        #         self.gen_immunity_file_from_milen_clusters()

        if generate_migration_files:
            print("Generating migration files...")
            self.gen_migration_files()

        if generate_climate_files:
            print("Generating climate files...")
            SetupParser.init()
            [cg_start_year,cg_duration] = safe_start_year_duration_for_climate_generator(self.start_year,self.sim_length_years)

            print("Start year given to climate generator = {}".format(cg_start_year))
            print("Duration given to climate generator = {}".format(cg_duration))

            cg = ClimateGenerator(self.demo_fp_full,
                                  self.exp_base + 'Logs/climate_wo.json',
                                  self.exp_base + 'Climate/',
                                  start_year = str(cg_start_year),
                                  num_years = str(cg_duration),
                                  climate_project = "IDM-{}".format(self.region),
                                  resolution=str(0))

            cg.generate_climate_files()


    def gen_demo_file(self):
        if 'EIR_node_label' in self.kwargs:
            dg = CatchmentDemographicsGenerator.from_file_subset(self.cb,
                                                                 self.grid_pop_csv_file,
                                                                 self.desired_cells,
                                                                 EIR_node_label=self.kwargs['EIR_node_label'],
                                                                 EIR_node_lat=self.kwargs['EIR_node_lat'],
                                                                 EIR_node_lon=self.kwargs['EIR_node_lon'])
        else:
            dg = CatchmentDemographicsGenerator.from_file_subset(self.cb,
                                                                 self.grid_pop_csv_file,
                                                                 self.desired_cells)
        demo_dict = dg.generate_demographics()

        # add extra node?

        # Add catchment name to demographics file metadata:
        # demo_dict["Metadata"]["Catchment"] = self.catch

        # Add larval habitat parameters to demographics file:
        # if self.larval_params_mode != "calibrate":
        demo_dict = self.add_larval_habitats_to_demo(demo_dict)
        # if self.larval_params:
        #     temp_h = self.larval_params['temp_h']
        #     linear_h = self.larval_params['linear_h']
        #     # demo_fp = self.exp_base + "Demographics/demo_temp{}_linear{}.json".format(int(temp_h),int(linear_h))
        #     demo_fp = self.exp_base + "Demographics/demo.json"
        # else:


        if 'IP_list' in self.kwargs:
            demo_dict = self.add_individual_properties_to_demo(demo_dict, self.kwargs['IP_list'])

        demo_fp = self.exp_base + "Demographics/demo.json"

        demo_f = open(demo_fp, 'w+')
        json.dump(demo_dict, demo_f, indent=4)
        demo_f.close()

    def add_larval_habitat_multiplier_to_node(self,node_item, larval_param_dict_this_node):
        calib_single_node_pop = 1000.
        pop_multiplier = float(node_item['NodeAttributes']['InitialPopulation']) / (calib_single_node_pop)

        # Copy the larval param dict handed to this node
        node_item['NodeAttributes']['LarvalHabitatMultiplier'] = larval_param_dict_this_node.copy()

        # Then scale each entry in the dictionary by the population multiplier
        for key in node_item['NodeAttributes']['LarvalHabitatMultiplier'].keys():
            node_item['NodeAttributes']['LarvalHabitatMultiplier'][key] *= pop_multiplier


    def larval_params_func_for_calibration(self, grid_cells):
        return {"CONSTANT": np.ones_like(grid_cells),
                "TEMPORARY_RAINFALL": np.ones_like(grid_cells),
                "LINEAR_SPLINE": np.ones_like(grid_cells),
                "WATER_VEGETATION": np.ones_like(grid_cells)}



    def add_larval_habitats_to_demo(self, demo_dict):
        # Add larval habitat multipliers to demographics file
        # Uses self.larval_params_func

        # This function takes as input grid_cells, and returns a dictionary:
        # {"CONSTANT": [1,2,1,5,...],
        #  "WATER_VEGETATION": etc., }
        # where the list is the multiplier for each node.

        if not self.larval_param_func:
            # Default function, if none is supplied, is the one used for calibration
            self.larval_param_func = self.larval_params_func_for_calibration

        larval_param_multiplier_dict = self.larval_param_func(self.desired_cells)

        larval_param_name_list = list(larval_param_multiplier_dict)
        n_params = len(larval_param_name_list)

        ni = 0
        for node_item in demo_dict['Nodes']:
            larval_param_dict_this_node = {}

            for jj in range(n_params):
                lp_name = larval_param_name_list[jj]
                larval_param_dict_this_node[lp_name] = larval_param_multiplier_dict[lp_name][jj]

            self.add_larval_habitat_multiplier_to_node(node_item, larval_param_dict_this_node)

            ni += 1

        return demo_dict


    def add_individual_properties_to_demo(self, demo_dict, IPs):
        # Add individual properties to defaults section in demographics file:
        # for example:
        #     IPs = [
        #         {'Property': 'TravelerStatus',
        #          'Values': ['IsTraveler',
        #                     'NotTraveler'],
        #          'Initial_Distribution': [0.07, 0.93],
        #          'Transitions': []}
        #     ]
        demo_dict['Defaults']['IndividualProperties'] = IPs
        return demo_dict


    def gen_migration_files(self):
        migr_json_fp = self.exp_base + "Migration/grav_migr_rates.json"


        if 'exclude_nodes_from_regional_migration' in self.kwargs:
            exclude_nodes = self.kwargs['exclude_nodes_from_regional_migration']
            migr_dict = gen_gravity_links_json(self.demo_fp_full, self.gravity_migr_params, outf=migr_json_fp, exclude_nodes=exclude_nodes)
        else:
            migr_dict = gen_gravity_links_json(self.demo_fp_full, self.gravity_migr_params, outf=migr_json_fp)

        rates_txt_fp = self.exp_base + "Migration/grav_migr_rates.txt"

        save_link_rates_to_txt(rates_txt_fp, migr_dict)

        # Generate migration binary:
        migration_filename = self.cb.get_param('Local_Migration_Filename')
        print("migration_filename: ",migration_filename)
        MigrationGenerator.link_rates_txt_2_bin(rates_txt_fp,
                                                self.exp_base+migration_filename)

        # Generate migration header:
        MigrationGenerator.save_migration_header(self.demo_fp_full,
                                                 self.exp_base +'Migration/local_migration.bin')



        # If EIR node has been added, generate regional migration file respresenting all nodes to/from this node
        # From Jaline
        if 'EIR_node_label' in self.kwargs:
            # datapath = self.base + 'data/mozambique'
            # ref_fname = 'grid_lookup.csv'

            id_reference = 'Gridded world grump30arcsec'
            output_fname = self.exp_base +'Migration/'

            # df = pd.read_csv(os.path.join(datapath, ref_fname))
            source_nodeid = self.kwargs['EIR_node_label']
            days_between_trips = 30

            # for catchment, cdf in df.groupby('catchment'):
            #     nodeids = [int(x) for x in cdf['grid_cell'].values]
            #     generate_all_to_one_migration('%s_%s' % (output_fname, catchment), id_reference, nodeids, source_nodeid,
            #                                   days_between_trips, 'Regional')
            nodeids = list(self.desired_cells)
            generate_all_to_one_migration(output_fname,
                                          id_reference,
                                          nodeids,
                                          source_nodeid,
                                          days_between_trips,
                                          'Regional')



class CatchmentDemographicsGenerator(DemographicsGenerator):

    def generate_defaults(self):
        """
        Generate the defaults section of the demographics file
        """

        # Currently support only static population; after demographics related refactor this whole method will likely disappear anyway
        if self.demographics_type == 'static':
            self.cb.set_param("Birth_Rate_Dependence", "FIXED_BIRTH_RATE")
        else:
            raise ValueError("Demographics type " + str(self.demographics_type) + " is not implemented!")

        exponential_age_param = 0.0001068 # Corresponds to Kayin state age dist
        population_removal_rate = 45



        mod_mortality = {
            "NumDistributionAxes": 2,
            "AxisNames": ["gender", "age"],
            "AxisUnits": ["male=0,female=1", "years"],
            "AxisScaleFactors": [1, 365],
            "NumPopulationGroups": [2, 1],
            "PopulationGroups": [
                [0, 1],
                [0]
            ],
            "ResultUnits": "annual deaths per 1000 individuals",
            "ResultScaleFactor": 2.74e-06,
            "ResultValues": [
                [population_removal_rate],
                [population_removal_rate]
            ]
        }

        individual_attributes = {
            "MortalityDistribution": mod_mortality,
            "AgeDistributionFlag": distribution_types["EXPONENTIAL_DISTRIBUTION"],
            "AgeDistribution1": exponential_age_param,
            "RiskDistribution1": 1,
            "PrevalenceDistributionFlag": 1,
            "AgeDistribution2": 0,
            "PrevalenceDistribution1": 0.13,
            "PrevalenceDistribution2": 0.15,
            "RiskDistributionFlag": 0,
            "RiskDistribution2": 0,
            "MigrationHeterogeneityDistribution1": 1,
            "ImmunityDistributionFlag": 0,
            "MigrationHeterogeneityDistributionFlag": 0,
            "ImmunityDistribution1": 1,
            "MigrationHeterogeneityDistribution2": 0,
            "ImmunityDistribution2": 0
        }

        node_attributes = {
            "Urban": 0,
            "AbovePoverty": 0.5,
            "Region": 1,
            "Seaport": 0,
            "Airport": 0,
            "Altitude": 0
        }

        if self.default_pop:
            node_attributes.update({"InitialPopulation": self.default_pop})

        defaults = {
            'IndividualAttributes': individual_attributes,
            'NodeAttributes': node_attributes,
        }

        return defaults


    @classmethod
    def from_file_subset(cls, cb, population_input_file, desired_cells,demographics_type='static', res_in_arcsec=30,
                         update_demographics=None, default_pop=1000, **kwargs):

        nodes_list = list()
        with open(population_input_file, 'r') as pop_csv:
            reader = csv.DictReader(pop_csv)
            for row in reader:
                # Latitude
                if not 'lat' in row: raise ValueError('Column lat is required in input population file.')
                lat = float(row['lat'])

                # Longitude
                if not 'lon' in row: raise ValueError('Column lon is required in input population file.')
                lon = float(row['lon'])

                # Node label
                res_in_deg = cls.arcsec_to_deg(res_in_arcsec)
                node_label = row['node_label'] # if 'node_label' in row else nodeid_from_lat_lon(lat, lon, res_in_deg)

                # Population
                pop = int(float(row['pop'])) if 'pop' in row else default_pop

                if int(node_label) in desired_cells:
                    # Append the newly created node to the list
                    nodes_list.append(Node(lat, lon, pop, node_label))

        # Add extra EIR node if information is given
        if 'EIR_node_label' in list(kwargs.keys()):
            nodes_list.append(Node(kwargs['EIR_node_lat'],
                                   kwargs['EIR_node_lon'],
                                   0, #kwargs['EIR_node_pop'],
                                   kwargs['EIR_node_label']))

        return cls(cb, nodes_list, demographics_type, res_in_arcsec, update_demographics, default_pop)


    def generate_nodes(self):
        nodes = []
        for i, node in enumerate(self.nodes):
            node_attributes = node.to_dict()
            node_id = int(node_attributes['FacilityName'])

            if self.demographics_type == 'static':
                # value correspond to a population removal rate of 45: 45/365
                birth_rate = (float(node.pop) / (1000 + 0.0)) * 0.12329
                node_attributes.update({'BirthRate': birth_rate})
            else:
                # perhaps similarly to the DTK we should have error logging modes and good generic types exception raising/handling
                # to avoid code redundancy
                print(self.demographics_type)
                raise ValueError("Demographics type " + str(self.demographics_type) + " is not implemented!")

            nodes.append({'NodeID': node_id, 'NodeAttributes': node_attributes})

        return nodes





IPs = [
    {'Property': 'TravelerStatus',
     'Values': ['IsTraveler',
                'NotTraveler'],
     'Initial_Distribution': [0.07, 0.93],
     'Transitions': []}
]