# Analyzer which checks migration:
# parses immigration/emigration event recorder.
# Computes number of local migration events that people typically take. (histogram)
# Computes number of regional migration events that people take. (histogram)

# all_trips = read output file
# regional trips: immigration or emigration with node 100000
# local trips: all other trips

# groupby person who's doing the travelling, and count.

#first attempt was with an analyzer, then realized it's much easier just downloading the ReportEventRecorder and doing it with pandas directly

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


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

def convert_all_trip_hist_to_round_trip(trip_hist):
    # Odd bins are people who have travelled there but not yet returned (end of year)
    # Just remove these for simplicity

    # simplified_trip_hist = trip_hist.copy()
    # for i in np.arange(len(bins)):
    #     if i%2 == 0:
    #         pass
    #     else:
    #         simplified_trip_hist[i] = 0
    #
    rnd_trip_hist = np.zeros(np.int(len(trip_hist)/2))
    for i in np.arange(len(rnd_trip_hist)):
        rnd_trip_hist[i] = trip_hist[2*i]
        rnd_trip_hist[i] += trip_hist[2*i + 1]
        #For odd trip counts, people haven't completed their round trip.  Subtract the odd trip and add them to round_trip_histogram


    return [rnd_trip_hist, np.arange(len(rnd_trip_hist))]



if __name__=="__main__":
    # Assume all trips are round trips.  Then total # of ROUND trips = # of trips/2
    regional_trips = df['Node_ID'] == 100000
    n_regional_trips = np.sum(regional_trips)
    n_regional_rnd_trips = n_regional_trips/2.

    local_trips = np.logical_not(regional_trips)
    n_local_trips = np.sum(local_trips)
    n_local_rnd_trips = n_local_trips/2.

    print("Total # of REGIONAL round trips: ", n_regional_rnd_trips)
    print("Total # of LOCAL round trips: ", n_local_rnd_trips)


    df_regional = df[regional_trips]
    df_local = df[local_trips]

    local_by_person = df_local.groupby('Individual_ID')['Time'].nunique()
    regional_by_person = df_regional.groupby('Individual_ID')['Time'].nunique()

    local_trips_hist, bins = np.histogram(local_by_person, bins=np.arange(30))
    regional_trips_hist, bins = np.histogram(regional_by_person, bins=np.arange(30))

    if False:
        regional_by_person = df_regional_imm.groupby('Individual_ID')['Time'].nunique()
        local_by_person = df_local_imm.groupby('Individual_ID')['Time'].nunique()

    local_rnd_trips_hist, bins = convert_all_trip_hist_to_round_trip(local_trips_hist)
    regional_rnd_trips_hist, bins = convert_all_trip_hist_to_round_trip(regional_trips_hist)

    # Add in people who never move
    if tot_pop > np.sum(regional_rnd_trips_hist):
        regional_rnd_trips_hist[0] = tot_pop - np.sum(regional_rnd_trips_hist)
    if tot_pop > np.sum(local_rnd_trips_hist):
        local_rnd_trips_hist[0] = tot_pop - np.sum(local_rnd_trips_hist)

    plt.figure()
    plt.suptitle("{}: x_Local = 5, x_Regional = 0.03".format(catch))
    plt.subplots_adjust(top=0.5)
    ax = plt.subplot(211)
    # plt.hist(local_by_person, bins=np.arange(15),align='left', rwidth=0.2, color='C0')
    ax.bar(bins,local_rnd_trips_hist,color='C0')
    ax.axvline(np.sum(bins*local_rnd_trips_hist)/tot_pop, c='black',linestyle='dashed')
    ax.set_title("Local ROUND trips per year")
    ax.set_ylabel("Number of Individuals")
    ax.set_xlabel("Number of round trips")


    ax = plt.subplot(212)
    # # plt.hist(regional_by_person, bins=np.arange(15),align='left', rwidth=0.2, color='C1')
    ax.bar(bins,regional_rnd_trips_hist,color='C1')
    ax.axvline(np.sum(bins*regional_rnd_trips_hist)/tot_pop, c='black',linestyle='dashed')
    ax.set_title("Regional ROUND trips per year")
    ax.set_ylabel("Number of Individuals")
    ax.set_xlabel("Number of round trips")

    plt.tight_layout()

    plt.show()