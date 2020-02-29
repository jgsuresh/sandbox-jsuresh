import pandas as pd
import numpy as np


# 1. Enrichment as a function of transmission intensity
# 2. RCD followup rates as a function of transmission intensity


def calculate_background_prevalence():
    # Compute average prevalence for each catchment at each round, and save:
    # catch | round | n_obs | n_pos | pos_frac

    # Import relevant columns of rounds data
    fn = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/data/Zambia/MACEPA/rounds_data/cleaned_and_merged/masterDatasetAllRounds2012-2016.csv"
    df = pd.read_csv(fn, usecols=["person_id", "round", "catch", "rdt_pos"])

    c = []
    r = []
    n_obs = []
    n_pos = []
    pos_frac = []

    for index, sdf in df.groupby(["round", "catch"]):
        r.append(index[0])
        c.append([index[1]])
        n_obs.append(sdf.nun)

    # fixme Oops.  Let's actually try this as a notebook to start with.



def calculate_enrichment_radii():
    # Import relevant columns of rounds data
    fn = "C:/Users/jsuresh/Dropbox (IDM)/Malaria Team Folder/data/Zambia/MACEPA/rounds_data/cleaned_and_merged/masterDatasetAllRounds2012-2016.csv"
    df = pd.read_csv(fn, usecols=["person_id", "round", "latitude", "longitude", "catch", "rdt_pos"])

    for r, sdf in df.groupby("round"):



