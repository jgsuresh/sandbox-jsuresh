# Create necessary input files
EIR_node_label = 100000

if calib_stage == 0:
    IPs = [
        {'Property': 'TravelerStatus',
         'Values': ['IsTraveler',
                    'NotTraveler'],
         'Initial_Distribution': [0.07, 0.93],
         'Transitions': []}
    ]


    file_creator = GriddedInputFilesCreator(base,
                                            exp_name,
                                            mozamb_exp.desired_cells,
                                            mozamb_exp.cb,
                                            grid_pop_csv_file,
                                            region=mozamb_exp.region,
                                            start_year=burnin_sim_start_year,
                                            sim_length_years=burnin_sim_length_years,
                                            immunity_mode="naive",
                                            larval_param_func=mozamb_exp.larval_params_func_for_calibration,
                                            EIR_node_label=EIR_node_label,
                                            EIR_node_lat=-25.045777,
                                            EIR_node_lon=32.786861,
                                            IP_list=IPs,
                                            generate_climate_files=False,
                                            exclude_nodes_from_regional_migration=[EIR_node_label]
                                            )

