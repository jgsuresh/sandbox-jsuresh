from simtools.Managers.WorkItemManager import WorkItemManager
from simtools.SetupParser import SetupParser
from simtools.AssetManager.FileList import FileList


# Run parameters:
exp_id = "4bda73fd-f165-eb11-a2dd-c4346bcb7271"

# start_years = [1,2,3,4,5]
# burnin_end = [45,46,47,48,49,50]
# hs_burnin_end = [55,56,57,58,59]
# bednet_years = [60,61,62,63,64,65]
# years_to_output = start_years + burnin_end + hs_burnin_end + bednet_years
elim_years = [64,65]
years_to_output = elim_years
# ===================================================================================
years_to_output_string = str(years_to_output).replace(' ','')

wi_name = "heterogeneous_biting_ssmt"
command = "python get_endpoints.py {} {}".format(years_to_output_string, exp_id)
user_files = FileList(root='ssmt_endpoint', files_in_root=['get_endpoints.py'])

if __name__ == "__main__":
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    wim = WorkItemManager(item_name=wi_name,
                          command=command,
                          user_files=user_files)
    wim.execute(True)
