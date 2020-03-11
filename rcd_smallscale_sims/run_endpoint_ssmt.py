from simtools.Managers.WorkItemManager import WorkItemManager
from simtools.SetupParser import SetupParser
from simtools.AssetManager.FileList import FileList


# Run parameters:
# exp_id = "aaf7ece4-825a-ea11-a2c5-c4346bcb1550" # burnins
# start_time = 50*365
#
# exp_id = "d9ff683a-2f5b-ea11-a2c5-c4346bcb1550" # hs-only from burnins
# start_time = 0

# exp_id = "19fd776e-305b-ea11-a2c5-c4346bcb1550" # fiducial from burnins
# start_time = 0

exp_id = "5a2c10c0-0163-ea11-a2c5-c4346bcb1550"
# start_time = 0

# ===================================================================================

wi_name = "rcd_endpoints"
command = "python get_endpoints.py {}".format(exp_id)
user_files = FileList(root='ssmt_endpoint',files_in_root=['get_endpoints.py'])

if __name__ == "__main__":
    SetupParser.default_block = 'HPC'
    SetupParser.init()

    wim = WorkItemManager(item_name=wi_name,
                          command=command,
                          user_files=user_files)
    wim.execute(True)

