import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns

f_in = 'cbever-summaryTableForJoshAllHFCA.csv'
f_out = 'chiyabi-onenode.csv'
single_node = True

f_orig = pd.read_csv(f_in)
fe = f_orig.copy(deep=True)

# Clean this file

# Delete unnecessary columns:
del fe['district']
del fe['itn']
del fe['irs']

# Restrict ourselves to round 1 for now [?]
fe = fe[fe['round'] == 1]
# For each pixel, find max population that has ever been in that grid cell.  NOT IMPLEMENTED YET
# for lat in set(fe['latitude']):
#     for lon in set(fe['longitude']):
#

# Get desired health facilities:
# For now, Chiyabi and Luumbo:
fe = fe[np.logical_or(fe['healthfac']=='Chiyabi', fe['healthfac']=='Luumbo')]

fe = fe.reset_index()
del fe['index']

# Add node_label column
fe['node_label'] = range(fe.shape[0])

# Rename other columns to fit Milen's script
fe.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)


# Finally, reorder to match Milen's ordering:
fe = fe[['node_label','lat','lon','pop','prev']]

# FOR SINGLE NODE ONLY: Only take first entry of node
if single_node:
    fe = fe[fe['node_label'] == 0]

# Save final file to new CSV:
fe.to_csv(f_out,mode='w+')