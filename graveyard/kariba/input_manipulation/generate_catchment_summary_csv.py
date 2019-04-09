import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context('talk')
sns.set_style('darkgrid')

lookup_df = pd.read_csv("C://Users/jsuresh/Projects/malaria-zm-kariba/gridded_sims/inputs/grid_csv/grid_lookup.csv")
lookup_df.dropna(inplace=True)

catch_list = sorted(list(lookup_df['catchment'].unique()))

#exploratory plots:
# x-axis population, y-axis number of nodes.  scatterplot catchments
catch_df = lookup_df[['catchment','grid_cell','pop']].groupby('catchment').agg({'grid_cell': 'nunique', 'pop': 'sum'})
catch_df.reset_index(inplace=True)

plt.figure()

ax = sns.lmplot(x="pop",y="grid_cell",data=catch_df, fit_reg=False)





# def label_point(x, y, val, ax):
#     a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
#     for i, point in a.iterrows():
#         ax.text(point['x']+.02, point['y'], str(point['val']))
def label_point(a, ax):
    for i, point in a.iterrows():
        ax.text(point['pop']+.02, point['grid_cell'], str(point['catchment']),fontsize=8)

label_point(catch_df, plt.gca())

plt.xlabel("Population")
plt.ylabel("Area (number of grid cells)")
plt.title("Kariba catchments")

plt.show()