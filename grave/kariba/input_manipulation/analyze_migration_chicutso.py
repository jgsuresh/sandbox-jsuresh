
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context("talk")
sns.set_style("darkgrid")


regional_work_node_label = 100000
# df = pd.read_csv("ReportEventRecorder.csv")
# df = pd.read_csv("ReportEventRecorder_xlocal4.csv")
# df = pd.read_csv("ReportEventRecorder_MSF_xlocal4.csv")

# tot_pop = 4950 #Moine


# catch = "Chichuco"
# tot_pop = 11190
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x08.csv".format(catch))

catch = "Chicutso"
tot_pop = 2286
df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x2.csv".format(catch))
df_hmr = pd.read_csv("C:/Users/jsuresh/Desktop/ReportHumanMigrationTracking_{}_x2.csv".format(catch))

# catch = "MSF"
# tot_pop = 10070
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x04.csv".format(catch))

# catch = "Mahel"
# tot_pop = 1786
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x5.csv".format(catch))

# catch = "Mapulanguene"
# tot_pop = 2020
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x5.csv".format(catch))

# catch = "Moine"
# tot_pop = 4946
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x15.csv".format(catch))

# catch = "Motaze"
# tot_pop = 8868
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x06.csv".format(catch))

# catch = "PC"
# tot_pop = 3368
# df = pd.read_csv("C:/Users/jsuresh/Desktop/ReportEventRecorder_{}_x5.csv".format(catch))



#=================================================================================

def fix_human_migration_csv_columns(df):
    rename_dict = {}
    for colname in df.columns:
        if colname[0] == " ":
            rename_dict[colname] = colname[1:]

    df.rename(columns=rename_dict,inplace=True)


def trip_histogram(individual_trip_count, max_trip_in_hist=20):
    trip_hist = np.arange(max_trip_in_hist+1)
    for i in np.arange(max_trip_in_hist+1):
        trip_hist[i] = np.sum(individual_trip_count==i)

    # Add in non-travellers:
    trip_hist[0] = tot_pop - np.size(individual_trip_count)
    return [trip_hist, np.arange(max_trip_in_hist+1)]

def plot_catch_trip_hist():
    fix_human_migration_csv_columns(df_hmr)

    df_local = df_hmr[df_hmr["MigrationType"]=="local"]
    df_regional = df_hmr[df_hmr["MigrationType"]!="local"]

    df_local_fromhome = df_local[np.equal(df_local["Home_NodeID"],df_local["From_NodeID"])]
    df_local_fromhome.reset_index(inplace=True,drop=True)
    local_trip_count = np.array(df_local_fromhome.groupby("IndividualID").count()["Time"])

    n_local_travellers = np.size(local_trip_count)

    trip_hist,bins = trip_histogram(local_trip_count)

    ax = plt.figure()
    plt.plot(bins,trip_hist,ls='-',marker='o')
    plt.axvline(np.sum(bins * trip_hist) / tot_pop, c='C0', linestyle='dashed')
    plt.ylabel("Number of Individuals")
    plt.xlabel("Number of round trips")
    # plt.show()

    return ax


if __name__=="__main__":
    plot_catch_trip_hist()
