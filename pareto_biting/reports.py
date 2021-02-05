from dtk.utils.Campaign.CampaignClass import CampaignEvent, ReportNodeDemographicsMalaria
from malaria.reports.MalariaReport import add_event_counter_report


def add_event_recorder_with_every_update(cb):
    cb.set_param("Report_Event_Recorder", 1)
    cb.set_param("Report_Event_Recorder_Events", ["EveryUpdate"])
    cb.set_param("Report_Event_Recorder_Ignore_Events_In_List", 0)
    cb.set_param("Report_Event_Recorder_Individual_Properties", [])
    # cb.set_param("Report_Event_Recorder_Individual_Properties", ["TravelerStatus"])
    # cb.set_param("Custom_Individual_Events",
    #              ["Received_Treatment", "Diagnostic_Survey_0", "Received_Test", "Received_RCD_Drugs",
    #               "Received_Campaign_Drugs", "Mosquito Release", "RelativeBitingRate"])
    # cb.set_param("Enable_Property_Output", 1)

def add_counter(cb):
    add_event_counter_report(cb,
                             event_trigger_list=["Received_Treatment", "Bednet_Got_New_One", "Bednet_Discarded", "Bednet_Using"],
                             start=45*365)

def add_ip_filtered_reports(cb):
    pass

# def add_filtered_report(cb, start=0, end=10000, nodes=None, description=''):
#     if not nodes:
#         nodes = []
#     filtered_report = FilteredMalariaReport(start_day=start, end_day=end, nodes=nodes,
#                                             description=description)
#     cb.add_reports(filtered_report)

def add_node_demo_report(cb):
    demo_report = ReportNodeDemographicsMalaria(Age_Bins=[],
                                                IP_Key_To_Collect='RiskGroup',
                                                Sim_Types=['MALARIA_SIM'],
                                                Stratify_By_Gender=False)
    cb.custom_reports.append(demo_report)
    # cb.add_event(demo_report)