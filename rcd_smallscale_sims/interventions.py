import math
import os
from copy import deepcopy

import pandas as pd
import numpy as np
from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.migrate_to import add_migration_event
from dtk.utils.Campaign.CampaignClass import CommunityHealthWorkerEventCoordinator, NodeSetNodeList, \
    BroadcastEventToOtherNodes, BroadcastEventToOtherNodes_Node_Selection_Type_Enum, CampaignEvent, \
    CommunityHealthWorkerEventCoordinator_Initial_Amount_Distribution_Type_Enum
from dtk.utils.Campaign.utils.RawCampaignObject import RawCampaignObject

from helpers.windows_filesystem import get_dropbox_location
from helpers.relative_time import convert_to_day_365

from dtk.interventions.irs import add_IRS, add_node_IRS
from dtk.interventions.itn_age_season import add_ITN_age_season
from malaria.interventions.health_seeking import add_health_seeking
from malaria.interventions.malaria_diagnostic import add_diagnostic_survey
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign, fmda_cfg
from malaria.interventions.malaria_drugs import drug_configs_from_code

from gridded_sims.run.build_cb import get_project_folder
from gridded_sims.run.site import find_cells_for_this_catchment

project_folder = get_project_folder()
interventions_folder = os.path.join(project_folder, "inputs/grid_csv/")



def add_simple_hs(cb, u5_hs_rate, o5_hs_rate=-1):

    if o5_hs_rate == -1:
        o5_hs_rate = u5_hs_rate * 0.5

    add_health_seeking(cb,
                       start_day=1,
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
                       drug=['Artemether', 'Lumefantrine'],
                       dosing='FullTreatmentNewDetectionTech')



def chw_rcd_manager(cb, followups_per_month=5,rcd_coverage=1, budget_followups_by_week=False):
    # CHW manager.  Triggered by Received_Treatment events with probability trigger_coverage, and allocates interventions if they are in stock.
    # The intervention in this case is to broadcast "Diagnostic_Survey_0" to the parent node, requesting an MSAT.
    # Note that this setup **should** be able to see all of the nodes, and have a single stock.

    request_msat_config = BroadcastEventToOtherNodes(
        Event_Trigger="Diagnostic_Survey_0",
        Include_My_Node=True,
        Node_Selection_Type=BroadcastEventToOtherNodes_Node_Selection_Type_Enum.DISTANCE_ONLY,
        Max_Distance_To_Other_Nodes_Km=0)

    if budget_followups_by_week:
        days_between_shipments = 7
        amount_in_shipment = int(round(followups_per_month * 7/30))
        max_stock = amount_in_shipment
    else:
        days_between_shipments = 30
        amount_in_shipment = followups_per_month
        max_stock = followups_per_month

    chw = CommunityHealthWorkerEventCoordinator(
        Initial_Amount=1,
        Initial_Amount_Distribution_Type=CommunityHealthWorkerEventCoordinator_Initial_Amount_Distribution_Type_Enum.FIXED_DURATION,
        Amount_In_Shipment=amount_in_shipment,
        Days_Between_Shipments=days_between_shipments,
        Max_Stock=max_stock,
        Max_Distributed_Per_Day=1,
        Intervention_Config=request_msat_config,
        Trigger_Condition_List=["Received_Treatment"],
        Waiting_Period=0)

    chw_event = CampaignEvent(Start_Day=1,
                              Nodeset_Config={"class": "NodeSetAll"},
                              Event_Coordinator_Config=chw)

    cb.add_event(chw_event)


def rcd_followthrough(cb, coverage=1, delivery_method="MTAT"):
    # Listen for Diagnostic_Survey_0 and implement a diagnostic survey, then broadcast TestedPositive or TestedNegative.
    # Then, if TestedPositive, then administer drugs and broadcast Received_RCD_Drugs

    # Drug setup
    drug_code = 'AL'
    drug_configs = drug_configs_from_code(cb, drug_code=drug_code)

    # set up events to broadcast when receiving reactive campaign drug
    receiving_drugs_event = {
        "class": "BroadcastEvent",
        "Broadcast_Event": "Received_RCD_Drugs"
    }

    event_config = drug_configs + [receiving_drugs_event]


    if delivery_method == "MTAT":
        add_diagnostic_survey(cb,
                              coverage=coverage,
                              start_day=1,
                              diagnostic_type='BLOOD_SMEAR_PARASITES',
                              diagnostic_threshold=0,
                              trigger_condition_list=['Diagnostic_Survey_0'],
                              event_name='Reactive MSAT level 0',
                              positive_diagnosis_configs=event_config,
                              listening_duration=-1)

    elif delivery_method == "MDA":
        add_drug_campaign(cb,
                          coverage=coverage,
                          drug_code=drug_code,
                          start_days=[1],
                          campaign_type="MDA",
                          trigger_condition_list=["Diagnostic_Survey_0"],
                          listening_duration=-1
                          )
        # def add_drug_campaign(cb, campaign_type: str = 'MDA', drug_code: str = None, start_days: list = None,
        #                       coverage: float = 1.0,
        #                       repetitions: int = 1, tsteps_btwn_repetitions: int = 60,
        #                       diagnostic_type: str = 'BLOOD_SMEAR',
        #                       diagnostic_threshold: float = 40, fmda_radius: int = 0,
        #                       node_selection_type: str = 'DISTANCE_ONLY',
        #                       trigger_coverage: float = 1.0, snowballs: int = 0, treatment_delay: int = 0,
        #                       triggered_campaign_delay: int = 0, nodeIDs: list = None, target_group: any = 'Everyone',
        #                       drug_ineligibility_duration: int = 0,
        #                       node_property_restrictions: list = None, ind_property_restrictions: list = None,
        #                       disqualifying_properties: list = None, trigger_condition_list: list = None,
        #                       listening_duration: int = -1, adherent_drug_configs: list = None,
        #                       target_residents_only: int = 1,
        #                       check_eligibility_at_trigger: bool = False):

        return {"delivery_method": delivery_method,
                "coverage": coverage}

