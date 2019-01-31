'''
Construct basic grid adjacency given population grid of pixels.
Construct migration model file.
'''

import pandas as pd
import numpy as np
from geopy.distance import vincenty
import json

max_migration_length = 10 #km
# Note: Milen defines this in units of "neighborhood hops"

# Open population CSV file:
grid_pop_csv_file = 'chiyabi-luumbo-rd1.csv'
f_grid = pd.read_csv(grid_pop_csv_file)

adj_list = {}


# SPEED SLOW: COULD PROBABLY SPEED UP BY CONVERTING TO NUMPY ARRAYS FIRST
# Loop over all pixels:
for n1 in f_grid['node_label']:
    adj_list[str(n1)] = {}
    l1 = f_grid['node_label'] == n1
    for n2 in f_grid['node_label']:
        l2 = f_grid['node_label'] == n2

        d = vincenty((f_grid['lat'][l1].values[0], f_grid['lon'][l1].values[0]), (f_grid['lat'][l2].values[0], f_grid['lon'][l2].values[0])).km
        # print "d",d

        if d <= max_migration_length:
            adj_list[str(n1)][str(n2)] = d

a_f = open(grid_pop_csv_file[:-4] + "_adjacency.json",'w')
json.dump(adj_list, a_f, indent=4)
a_f.close()

#  MILEN'S VERSION:
# # get each cell in the grid
# for i, idx_x in enumerate(f_orig['lat'][0]):
#     idx_y = filtered_household_cells_idx[1][i]
#     node_label = str(i)
#
#     adj_list[node_label] = {}
#
#     # find the potential neighbors of the cell
#     neigh_candidates = []
#     for i in range(idx_x - migration_radius, idx_x + migration_radius + 1):
#         for j in range(idx_y - migration_radius, idx_y + migration_radius + 1):
#             neigh_candidates.append([i, j])
#
#     # check if neighbor cells exist on the grid (e.g. their household density is sufficiently high)
#     for neigh_cand in neigh_candidates:
#         if str(neigh_cand[0]) + "_" + str(neigh_cand[1]) in coor_idxs_2_node_label:
#             neigh_node_label = coor_idxs_2_node_label[str(neigh_cand[0]) + "_" + str(neigh_cand[1])]
#
#             lat_src = Y_mid[idx_y][idx_x]
#             lon_src = X_mid[idx_y][idx_x]
#
#             lat_dst = Y_mid[neigh_cand[1]][neigh_cand[0]]
#             lon_dst = X_mid[neigh_cand[1]][neigh_cand[0]]
#
#             # calculate source destination distance and weight the graph
#             w = vincenty((lat_src, lon_src), (lat_dst, lon_dst)).km
#
#             adj_list[node_label][neigh_node_label] = w
#
# with open("gridded_households_adj_list.json", "w") as a_f:
#     json.dump(adj_list, a_f, indent=3)
#
# # logging.info("Grid graph adjacency matrix saved to gridded_households_adj_list.json")