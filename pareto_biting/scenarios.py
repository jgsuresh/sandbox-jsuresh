
"""
Scenarios to look at:

Biting variations:
1. Current standard
2. 80-20 parameters (from my wiki post)
3.

Scenario variations:
1. No interventions
2. Single bednet distribution


Things to plot:
Distribution of biting risk across adults
Prevalence
Incidence

"""
from dtk.vector.species import set_species_param
from simtools.ModBuilder import ModFn


def biting_risk_scenario(cb, scenario_number):
    if scenario_number == 0:
        cb.set_param("Enable_Demographics_Risk", 0)
        cb.set_param("Demographics_Filenames", ["demo_exponential_risk.json"])
    elif scenario_number == 1:
        cb.set_param("Enable_Demographics_Risk", 1)
        cb.set_param("Demographics_Filenames", ["demo_lognormal_risk_sigma_1.68.json"])
    elif scenario_number == 2:
        cb.set_param("Enable_Demographics_Risk", 1)
        cb.set_param("Demographics_Filenames", ["demo_exponential_risk.json"])
    elif scenario_number == 3:
        cb.set_param("Enable_Demographics_Risk", 1)
        cb.set_param("Demographics_Filenames", ["demo_gaussian_risk.json"])
    elif scenario_number == 4:
        cb.set_param("Enable_Demographics_Risk", 1)
        cb.set_param("Demographics_Filenames", ["demo_lognormal_risk_sigma_1.2.json"])
    elif scenario_number == 5:
        cb.set_param("Enable_Demographics_Risk", 1)
        cb.set_param("Demographics_Filenames", ["demo_lognormal_risk_sigma_1.6.json"])


def flat_spline_ento(cb, f_sc=1,a_sc=1):
    vcs_list = []
    if f_sc != -1:
        vcs_list.append('funestus')
    if a_sc != -1:
        vcs_list.append('arabiensis')

    cb.update_params({'Vector_Species_Names': vcs_list})

    spline_times_list = [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167, 334.583]

    set_species_param(cb,
                      'funestus',
                      "Larval_Habitat_Types",
                      {"LINEAR_SPLINE": {
                          "Capacity_Distribution_Number_Of_Years": 1,
                          "Capacity_Distribution_Over_Time": {
                              "Times": spline_times_list,
                              "Values": 12*[0.5]
                          },
                          "Max_Larval_Capacity": 10**f_sc
                      }})

    set_species_param(cb,
                      'arabiensis',
                      "Larval_Habitat_Types",
                      {"LINEAR_SPLINE": {
                          "Capacity_Distribution_Number_Of_Years": 1,
                          "Capacity_Distribution_Over_Time": {
                              "Times": spline_times_list,
                              "Values": 12*[0.5]
                          },
                          "Max_Larval_Capacity": 10**a_sc
                      }})

    return_dict = {"funest": f_sc, "arab": a_sc}
    return return_dict

def flat_ento_simplified(cb, f_sc):
    a_sc = f_sc + 0.5
    flat_spline_ento(cb, f_sc=f_sc, a_sc=a_sc)

    return {"funest": f_sc}


def modfn_sweep_over_transmission_intensity(values_to_sweep_over):
    modlist = [ModFn(flat_ento_simplified, f_sc) for f_sc in values_to_sweep_over]
    return modlist