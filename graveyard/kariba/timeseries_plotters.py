def ref_data_for_plotters(catch, inc_file="catchment_incidence", prev_file="catchment_prevalence"):
    dropbox = get_dropbox_location()
    project_folder = os.path.join(dropbox, "projects/mz_magude/")

    inc_ref_data = pd.read_csv(os.path.join(project_folder, "dtk_simulation_input/mozambique/{}.csv".format(inc_file))) #This one has been scaled down to pop of 10k
    inc_ref_data = inc_ref_data[inc_ref_data["catchment"]==catch].reset_index()
    inc_ref_data.rename(columns={"cases": "data", "fulldate": "date"}, inplace=True)
    inc_ref_data = inc_ref_data[["date", "data"]]

    prev_ref_data = pd.read_csv(os.path.join(project_folder, "gridded_simulation_input/{}.csv".format(prev_file)))
    prev_ref_data = prev_ref_data[prev_ref_data["catchment"]==catch].reset_index()
    prev_ref_data.rename(columns={"prev": "data", "N": "weight"}, inplace=True)
    prev_ref_data = prev_ref_data[["date", "data", "weight"]]

    return {"True Prevalence": prev_ref_data,
            "Monthly Incidence": inc_ref_data}
