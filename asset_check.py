from simtools.Utilities.COMPSUtilities import get_asset_collection_id_for_simulation_id

from COMPS.Client import Client

Client.login("https://comps.idmod.org")
foo = get_asset_collection_id_for_simulation_id("b89993b6-c163-ea11-a2c5-c4346bcb1550")

print(foo)