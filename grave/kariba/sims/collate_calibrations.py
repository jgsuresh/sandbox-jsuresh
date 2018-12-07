import os
import pandas as pd

from zambia_helpers import *
from shutil import copyfile

dropbox_user = 'jsuresh'


burnin_dir_dict = {"bbondo": "bbondo_burnin",
                   "sinafala": "sinafala_burnin_higher_v2",
                   "sinamalima": "sinamalima_burnin_higher_v2",
                   "chiyabi": "chiyabi_burnin_higher_v2"}

# Save rank0 parameters into CSV


# Loop over all catchments
def create_rank0_burnins_csv(catch_list=None):
    if not catch_list:
        catch_list = get_catchment_list(dropbox_user=dropbox_user)
    for catch in catch_list:
        # burnin_dir = "{}_burnin".format(catch)
        burnin_dir = burnin_dir_dict[catch]
        # Look for catchment_burnin folder
        if os.path.exists(burnin_dir):
            # If can't find it, skip
            # If can, then open _plots/LL_all.csv to find best run
            df_LL = pd.read_csv(os.path.join(burnin_dir, "_plots/","LL_all.csv"))
            df_LL.sort_values(by='total', ascending=False, inplace=True)
            df_LL.reset_index(inplace=True, drop=True)

            df_LL.rename(columns={"{}_incidence_likelihood".format(catch): "incidence_likelihood",
                                  "{}_prevalence_likelihood".format(catch): "prevalence_likelihood"},
                         inplace=True)
            df_LL.index.name = 'rank'
            df_LL.reset_index(inplace=True)
            df_LL["catch"] = catch

            if "full_LL" in locals():
                full_LL = pd.concat([full_LL, df_LL], ignore_index=True)
            else:
                full_LL = df_LL.copy(deep=True)
            #
            # rank0 =  df_LL.loc[0]
            #
            # rank0["catch"] = catch
            #
            # if "rank0_df" in locals():
            #     rank0_df = pd.concat([rank0_df, rank0], ignore_index=True)
            # else:
            #     rank0_df = rank0.copy(deep=True)

    # Save all of these best runs into a file
    # print(rank0_df)
    rank0_df = full_LL[full_LL["rank"]==0]
    print(rank0_df)
    rank0_df.to_csv("rank0_burnins.csv", index=False)


# Copy serialization file for this run
def copy_burnin_serialize_files(copy_dir = "Z:/jsuresh/input/kariba_gridded_sims/"):
    # Open rank0_burnins CSV:
    rank0_df = pd.read_csv("rank0_burnins.csv")

    # Loop over rows:
    for ri, row in rank0_df.iterrows():
        # row = dict(row)
        # For each row, open the corresponding output folder
        output_dir = row['outputs']
        catch = row['catch']

        output_dir = output_dir.split('\\\\internal.idm.ctr\\IDM\\Home\\')[1]
        output_dir = os.path.join("Z:/",output_dir)
        output_dir = output_dir.replace("\\","/")

        if catch == "bbondo":
            copyfile(os.path.join(output_dir,"output/state-20440.dtk"),os.path.join(copy_dir, "{}_2010.dtk".format(catch)))
        else:
            copyfile(os.path.join(output_dir,"output/state-20440-000.dtk"),os.path.join(copy_dir, "{}_2010-000.dtk".format(catch)))
            copyfile(os.path.join(output_dir,"output/state-20440-001.dtk"),os.path.join(copy_dir, "{}_2010-001.dtk".format(catch)))
    # Copy the serialized file from there to copy_dir as "catch_2010.x"



if __name__ == "__main__":
    create_rank0_burnins_csv(["bbondo","chiyabi","sinafala"])
    copy_burnin_serialize_files()