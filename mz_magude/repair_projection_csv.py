import pandas as pd
import numpy as np

base = '../../'
data_base = base + "data/mozambique/"
intervention_base = base + 'data/mozambique/intervention_scenarios/'


pop_df = pd.read_csv(data_base + "grid_population.csv")

grid_cells = np.array(sorted(list(set(pop_df["node_label"]))))
print(grid_cells)

for interven_num in [0,1,2]:
    folder = intervention_base + 'scenario_{}/'.format(interven_num)

    for fn in ['grid_all_healthseeking_events_friction.csv',
               'grid_all_irs_events.csv',
               'grid_all_mda_events.csv',
               'grid_all_react_events.csv']:
        csv_fp = folder + fn
        df = pd.read_csv(csv_fp)

        df = df[np.in1d(df['grid_cell'],grid_cells)]

        if fn == 'grid_all_react_events.csv':
            df['coverage'][df['coverage'] > 1.0] = 1.0

        df.reset_index(inplace=True)
        df.to_csv(csv_fp)
