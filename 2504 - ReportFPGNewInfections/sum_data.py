import pandas as pd



"""
SporozoiteToHuman_Time
SporozoiteToHuman_NodeID
SporozoiteToHuman_VectorID
SporozoiteToHuman_BiteID
SporozoiteToHuman_HumanID
SporozoiteToHuman_NewInfectionID
SporozoiteToHuman_NewGenomeID
HomeNodeID
FemaleGametocyteToVector_Time
FemaleGametocyteToVector_NodeID
FemaleGametocyteToVector_VectorID
FemaleGametocyteToVector_BiteID
FemaleGametocyteToVector_HumanID
FemaleGametocyteToVector_InfectionID
FemaleGametocyteToVector_GenomeID
MaleGametocyteToVector_Time
MaleGametocyteToVector_NodeID
MaleGametocyteToVector_VectorID
MaleGametocyteToVector_BiteID
MaleGametocyteToVector_HumanID
MaleGametocyteToVector_InfectionID
MaleGametocyteToVector_GenomeID
"""

def analyze_fpg_new_infections(filename):
    df = pd.read_csv( filename )
    
    num_new_infections = df['SporozoiteToHuman_NewInfectionID'].nunique()
    print(f"Number of new infections: count={num_new_infections} - fraction={num_new_infections/len(df):0.3f}")

    unique_bites = df['SporozoiteToHuman_BiteID'].unique()
    print(f"Unique Bites: {len(unique_bites)}")

    count = df['SporozoiteToHuman_BiteID'].isin(df['MaleGametocyteToVector_BiteID']).sum()
    print(f"Number of bites simultaneously exchanging sporozoites and gametocytes: count={count} - fraction={count/len(df):0.3f}")

    bites_more_than_one_infection = df['SporozoiteToHuman_BiteID'].value_counts().gt(1).sum()
    print(f"Bites with more than one infection: count={bites_more_than_one_infection} - fraction={bites_more_than_one_infection/len(unique_bites):0.03}")

    print("Number of bites per mosquito vs number of mosquitoes making those number of bites:")
    bites_per_mosquito = df.groupby("SporozoiteToHuman_VectorID")["SporozoiteToHuman_BiteID"].nunique().value_counts()
    print(bites_per_mosquito)

if __name__ == "__main__":
    analyze_fpg_new_infections( "ReportFpgNewInfections.csv" )
