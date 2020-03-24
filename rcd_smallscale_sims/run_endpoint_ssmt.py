from simtools.Managers.WorkItemManager import WorkItemManager
from simtools.SetupParser import SetupParser
from simtools.AssetManager.FileList import FileList


# Run parameters:
exp_id = "ef2059d5-f46b-ea11-a2c5-c4346bcb1550"
years_from_end_to_include = 4

# filename = "InsetChart.json"
# years_from_end_to_include = 1
# filename = "ReportMalariaFilteredFinal_Year.json"


# ===================================================================================

wi_name = "rcd_endpoints"
# command = "python get_endpoints.py {} {} {}".format(exp_id, years_from_end_to_include, filename)
command = "python get_endpoints.py {} {}".format(exp_id, years_from_end_to_include)
user_files = FileList(root='ssmt_endpoint', files_in_root=['get_endpoints.py'])

if __name__ == "__main__":
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    wim = WorkItemManager(item_name=wi_name,
                          command=command,
                          user_files=user_files)
    wim.execute(True)

