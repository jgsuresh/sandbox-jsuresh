# In order to improve run time, scale down Magude-Sede-Facazissa population by a factor of 5:

import pandas as pd
import numpy as np

catch = "Panjane-Caputine"
scale_fac = 1.2

# grid_pop is lower by factor of 5 for these cells
# Ref incidence for this catchment is lower by factor of 5.
# RCD coverage is higher by factor of 5 for these cells

base = '../../'
data_base = base + "data/mozambique/"

# Find catch grid cells
lookup_df = pd.read_csv(data_base + "grid_lookup_with_neighborhood.csv")
catch_cells = np.array(sorted(list(set(lookup_df["grid_cell"][lookup_df["catchment"]==catch]))))

# Find these in grid_pop, and change pop by scalefactor.  Save to new file
if True:
    pop_df = pd.read_csv(data_base + "grid_population.csv")
    in_catch = np.in1d(pop_df["node_label"],catch_cells)
    pop_df["pop"][in_catch] = np.array(scale_fac*pop_df["pop"][in_catch],dtype=np.int)

    # Make sure every cell has at least 1 person:
    zero_pop = pop_df["pop"] == 0
    if np.sum(zero_pop) > 0:
        pop_df["pop"][zero_pop] = 1

    pop_df.to_csv(data_base + "grid_population.csv")


# Find these in grid_all_react_events.csv, and change coverage by scalefactor.  Save to new file
if True:
    rcd_df = pd.read_csv(data_base + "grid_all_react_events.csv")
    in_catch = np.in1d(rcd_df["grid_cell"],catch_cells)

    rcd_df["coverage"][in_catch] = rcd_df["coverage"][in_catch]/scale_fac

    # Make sure coverage maxes out at 1.0:
    over_covered = rcd_df["coverage"] > 1.
    if np.sum(over_covered) > 0:
        rcd_df["coverage"][over_covered] = 1.

    rcd_df.to_csv(data_base + "grid_all_react_events.csv")


# # Lower reference incidence values for this catchment by factor of 5.  Save to new file:
# if True:
#     inc_df = pd.read_csv(data_base + "catchment_incidence_TRUE.csv")
#     in_catch = inc_df["catchment"] == "Magude-Sede-Facazissa"
#     inc_df["cases"][in_catch] = np.array(0.2*inc_df["cases"][in_catch],dtype=np.int)
#
#     inc_df.to_csv(data_base + "catchment_incidence.csv")