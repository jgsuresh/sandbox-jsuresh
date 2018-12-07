import os
import pandas as pd
import numpy as np
import calendar

from calibtool.CalibSite import CalibSite
from helpers.relative_time import *



class zambia_calib_site(CalibSite):

    metadata = {}

    def __init__(self, catch_name, dropbox_user="jsuresh"):
        super(zambia_calib_site, self).__init__(catch_name)
        self.catch_name = self.name
        # self.base = "C:/Users/{}/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/".format(dropbox_user)

    def update_metadata(self):
        self.start_date = '2010-01-01'

        base = "C:/Users/{}/Dropbox (IDM)/Malaria Team Folder/projects/zambia_gridded_sims/kariba_gridded_sims/".format("jsuresh")

        prev_reference_csv = base + "inputs/grid_csv/grid_prevalence.csv"
        lookup_csv = base + "inputs/grid_csv/grid_lookup.csv"

        prev_reference_data = pd.read_csv(prev_reference_csv)
        lookup_data = pd.read_csv(lookup_csv)

        return_data = prev_reference_data.merge(lookup_data,how='left',on='grid_cell')

        return_data['sim_date'] = return_data['date'].apply(lambda x: convert_to_day_365(x,self.start_date))
        return_data['sim_date'] = return_data['sim_date']-1

        in_catch = return_data['catchment'] == self.name
        self.reference = {}
        ref_prevalence = return_data[in_catch]
        ref_prevalence.reset_index(inplace=True,drop=True)
        self.reference["prev_data"] = ref_prevalence



        # Load clinical case count data:
        reference_csv = base + "inputs/grid_csv/catch_incidence.csv"
        reference_data = pd.read_csv(reference_csv)
        reference_data.dropna(inplace=True)

        # Add year and month to dataframe based on fulldate column
        # reference_data["year"] = reference_data['fulldate'].apply(lambda x: int(str(x).split('-')[0]))
        # reference_data["month"] = reference_data['fulldate'].apply(lambda x: int(str(x).split('-')[1]))
        reference_data["year"] = reference_data['period'].apply(lambda x: int(str(x)[:4]))
        reference_data["month"] = reference_data['period'].apply(lambda x: int(str(x)[4:]))

        # Normalize by year for direct comparison with data:
        reference_data["year"] = reference_data["year"]-int(self.start_date.split('-')[0])
        in_catch = reference_data['catch'] == self.name
        ref_incidence = reference_data[in_catch]

        # Put in format that incidence likelihood analyzer needs
        ref_incidence.rename(columns={"Total cases": "cases"}, inplace=True)
        ref_incidence = ref_incidence[["year","month","cases"]]
        ref_incidence.reset_index(inplace=True,drop=True)
        self.reference["monthly_cases"] = ref_incidence




    def get_setup_functions(self):
        self.update_metadata()
        return []

    def get_reference_data(self, reference_type):
        if reference_type == 'gridded_prevalence':
            return self.reference["prev_data"]

        elif reference_type == 'monthly_cases':
            return self.reference["monthly_cases"]

    def get_region_list(self):
        return []

    def get_analyzers(self):
        from prevalence_likelihood_analyzer import prevalence_likelihood
        from incidence_likelihood_analyzer import incidence_likelihood
        return [prevalence_likelihood(self), incidence_likelihood(self)]



# class zambia_burnin_site(zambia_calib_site):
#     def get_analyzers(self):
#         return [prevalence_burnin_likelihood(self), incidence_burnin_likelihood(self)]