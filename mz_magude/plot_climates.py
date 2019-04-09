import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
sns.set_style("darkgrid")

base = '../../'
fig_base = base + 'results/climate_figs/'

dropbox_base = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/projects/Mozambique/"
climate_base = dropbox_base + "gridded_simulation_input/climate/"
catch_list = ["chichuco","chicutso","magude","mahel","mapulanguene","moine","motaze","panjane"]
# field_list = ["tmean","rain","humid"]
field_list = ["tmean"]

dd = {}

for catch in catch_list:
    dd[catch]={}

    for field in field_list:
        df_full = pd.read_csv(climate_base + "{}/Mozambique_30_climate_export.csv".format(catch))
        df_avg = pd.read_csv(climate_base + "{}_avg_year/avg-Mozambique_30_climate_export.csv".format(catch))

        df_full = df_full[df_full["param"] == field]
        df_avg = df_avg[df_avg["param"] == field]

        plt.figure()

        for year,df in df_full.groupby(['year']):
            foo = df.groupby('doy').mean()
            plt.plot(foo["value"],label=year)


        foo = df_avg.groupby('doy').mean()
        plt.plot(foo["value"],lw=2,color='black',label='Average')
        dd[catch][field] = np.array(foo["value"])

        plt.title(catch.capitalize())
        plt.ylabel(field)
        plt.xlabel("Day")
        plt.legend()

        if field == "tmean":
            plt.ylim([15,33])

        plt.tight_layout()
        plt.savefig(fig_base + '{}_{}.png'.format(catch,field))
        # plt.show()


print("Now plotting ento node things")
plt.close('all')
# Do same for entomology node:
df_avg = pd.read_csv(climate_base + "ento_avg_node_avg_year/avg-Mozambique_30_climate_export.csv".format(catch))
for field in field_list:
    df_avg = df_avg[df_avg["param"] == field]
    plt.figure()

    for catch in catch_list:
        plt.plot(dd[catch][field],label=catch.capitalize())

    foo = df_avg.groupby('doy').mean()
    plt.plot(foo["value"], lw=3, color='black', label='Ento Node')

    plt.title("Ento calibration climate")
    plt.ylabel(field)
    plt.xlabel("Day")
    plt.legend()

    if field == "tmean":
        plt.ylim([15, 33])


    plt.tight_layout()
    plt.savefig(fig_base + 'ento_{}.png'.format(field))
    # plt.show()

