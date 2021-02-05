import pandas as pd
from dtk.interventions.biting_risk import change_biting_risk
from dtk.interventions.itn_age_season import add_ITN_age_season, WaningEffectExponential
from malaria.interventions.health_seeking import add_health_seeking


def add_simple_hs(cb, u5_hs_rate, o5_hs_rate=-1, start_day=1):

    if o5_hs_rate == -1:
        o5_hs_rate = u5_hs_rate * 0.5

    add_health_seeking(cb,
                       start_day=start_day,
                       targets=[{'trigger': 'NewClinicalCase',
                                 'coverage': u5_hs_rate,
                                 'agemin': 0,
                                 'agemax': 5,
                                 'seek': 1,
                                 'rate': 0.3},
                                {'trigger': 'NewClinicalCase',
                                 'coverage': o5_hs_rate,
                                 'agemin': 5,
                                 'agemax': 100,
                                 'seek': 1,
                                 'rate': 0.3},
                                {'trigger': 'NewSevereCase',
                                 'coverage': 0.9,
                                 'agemin': 0,
                                 'agemax': 5,
                                 'seek': 1,
                                 'rate': 0.5},
                                {'trigger': 'NewSevereCase',
                                 'coverage': 0.8,
                                 'agemin': 5,
                                 'agemax': 100,
                                 'seek': 1,
                                 'rate': 0.5}],
                       drug=['Artemether', 'Lumefantrine'])
                       # dosing='FullTreatmentNewDetectionTech')

    return {"u5_hs_rate": u5_hs_rate,
            "o5_hs_rate": o5_hs_rate}


def add_simple_itn(cb, coverage, start_day=1):
    blocking_config = WaningEffectExponential(
        Decay_Time_Constant=450,
        Initial_Effect=0.9
    )

    killing_config = WaningEffectExponential(
        Decay_Time_Constant=1460,
        Initial_Effect=0.6
    )

    discard_times = {
        "Expiration_Period_Distribution": "DUAL_EXPONENTIAL_DISTRIBUTION",
        "Expiration_Period_Mean_1": 260,
        "Expiration_Period_Mean_2": 2106,
        "Expiration_Period_Proportion_1": 0.6
    }

    age_cov = 0.65
    min_season_cov = 0.5

    # discard_times: A dictionary of parameters needed to define expiration distribution.
    # No need to definite the distribution with all its parameters
    # Default is bednet being discarded with EXPONENTIAL_DISTRIBUTION with Expiration_Period_Exponential of 10 years
    # Examples:
    # for Gaussian: {"Expiration_Period_Distribution": "GAUSSIAN_DISTRIBUTION",
    #                "Expiration_Period_Gaussian_Mean": 20, "Expiration_Period_Gaussian_Std_Dev":10}
    # for Exponential {"Expiration_Period_Distribution": "EXPONENTIAL_DISTRIBUTION",
    #                  "Expiration_Period_Exponential":150}

    add_ITN_age_season(cb,
                       start=start_day,
                       age_dependence={'youth_cov': age_cov,
                                       'youth_min_age': 5,
                                       'youth_max_age': 20},
                       demographic_coverage=coverage,
                       birth_triggered=False,
                       seasonal_dependence={'min_cov': min_season_cov,
                                            'max_day': 60},
                       discard_times=discard_times,
                       blocking_config=blocking_config,
                       killing_config=killing_config)

    add_ITN_age_season(cb,
                       start=start_day,
                       age_dependence={'youth_cov': age_cov,
                                       'youth_min_age': 5,
                                       'youth_max_age': 20},
                       demographic_coverage=coverage,
                       birth_triggered=True,
                       seasonal_dependence={'min_cov': min_season_cov,
                                            'max_day': 60},
                       discard_times=discard_times,
                       blocking_config=blocking_config,
                       killing_config=killing_config)



def biting_risk_ip_groups(cb, risk_distribution="lognormal"):
    # add ips with interventions?
    # change biting risk for different intervention groups, and have it be birth triggered as well

    df_risk = pd.read_csv("pop_risk_distribution.csv")
    df_risk = df_risk[df_risk["distribution"]==risk_distribution]

    for i, row in df_risk.iterrows():
        ip_group_name = "R{}".format(row["bin"])
        risk_value = row["average_risk"]
        risk_config = {"Risk_Distribution": "CONSTANT_DISTRIBUTION",
                       "Risk_Constant": risk_value
                       }

        change_biting_risk(cb,
                           repetitions=-1,
                           ind_property_restrictions=[{"RiskGroup" : ip_group_name}],
                           risk_config=risk_config)
        change_biting_risk(cb,
                           repetitions=-1,
                           ind_property_restrictions=[{"RiskGroup" : ip_group_name}],
                           risk_config=risk_config,
                           trigger="birth")


# def add_itn(cb, events_df, block_initial=None, kill_initial=None):
#     itn_field_list = ["age_cov", "cov_all", "min_season_cov", "fast_fraction"]
#     binned_intervene_events, binned_and_grouped, data_fields = try_campaign_compression(events_df, itn_field_list)
#     birthnet_df = events_df.copy(deep=True)
#     birthnet_df.sort_values(by='simday', inplace=True)
#     birthnet_df['duration'] = birthnet_df.groupby('grid_cell')['simday'].shift(-1).sub(birthnet_df['simday'])
#     birthnet_df['duration'].fillna(-1, inplace=True)
#     birthnet_field_list = itn_field_list + ["duration"]
#     BIRTH_binned_intervene_events, BIRTH_binned_and_grouped, BIRTH_data_fields = try_campaign_compression(birthnet_df,
#                                                                                                           birthnet_field_list)
#
#     waning = {}
#     if block_initial:
#         waning["block_initial"] = block_initial
#     if kill_initial:
#         waning["kill_initial"] = kill_initial
#
#     for table, group in binned_and_grouped:
#         table_dict = dict(zip(data_fields, table))
#         node_list = sorted(list(set(group[
#                                         'grid_cell'])))  # fixme Needed to add this because sometimes there are duplicate nodes in the list, and this breaks things
#
#         start = table_dict['simday']
#         coverage = table_dict['cov_all']
#
#         if start >= 0:
#             add_ITN_age_season(cb,
#                                start=start,
#                                age_dep={'youth_cov': table_dict['age_cov'],
#                                         'youth_min_age': 5,
#                                         'youth_max_age': 20},
#                                coverage_all=coverage,
#                                as_birth=False,
#                                seasonal_dep={'min_cov': table_dict['min_season_cov'],
#                                              'max_day': 60},
#                                discard={'halflife1': 260,
#                                         'halflife2': 2106,
#                                         'fraction1': table_dict['fast_fraction']},
#                                nodeIDs=node_list,
#                                waning=waning)
#
#     # Birthnet distribution
#     for table, group in BIRTH_binned_and_grouped:
#         table_dict = dict(zip(BIRTH_data_fields, table))
#         node_list = sorted(group['grid_cell'])
#
#         start = table_dict['simday']
#         coverage = table_dict['cov_all']
#
#         if start > 0:
#             add_ITN_age_season(cb,
#                                as_birth=True,
#                                duration=table_dict['duration'],
#                                start=start,
#                                age_dep={'youth_cov': table_dict['age_cov'],
#                                         'youth_min_age': 5,
#                                         'youth_max_age': 20},
#                                coverage_all=coverage,
#                                seasonal_dep={'min_cov': table_dict['min_season_cov'],
#                                              'max_day': 60},
#                                discard={'halflife1': 260,
#                                         'halflife2': 2106,
#                                         'fraction1': table_dict['fast_fraction']},
#                                nodeIDs=node_list,
#                                waning=waning)
