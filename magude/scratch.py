import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

import seaborn as sns
sns.set_context("paper")
sns.set_style("whitegrid")

full = pd.read_csv("elim_data_compiled_feb19.csv")

full.drop_duplicates(inplace=True)
# Figure 1: curves

# Figure 1: curves

chan = "elim_eoy2_frac"

df = full.copy(deep=True)
non_zero_cov = df[df["VC Coverage"] == 0.6]

plt.figure(figsize=(10, 10))

ivm_durs = [14, 30, 60, 90]

k = 0
for ITN in [False, True]:
    for IRS in [False, True]:
        plt.subplot(2, 2, k + 1)

        # Get zero MDA coverage point:
        if ITN or IRS:
            vc_cov = 0.6
        else:
            vc_cov = 0

        zero_mda_cov_df = df[np.logical_and(np.logical_and(df["ITN"] == ITN, df["IRS"] == IRS),
                                            df["MDA Coverage"] == 0)]
        zero_cov = np.array(zero_mda_cov_df[chan])[0]

        lines_dict = {}

        sub_df = df[np.logical_and(np.logical_and(df["ITN"] == ITN, df["IRS"] == IRS),
                                   df["VC Coverage"] == vc_cov)]
        #         print(sub_df)
        lines_dict["DP only"] = np.array(
            sub_df[np.logical_and(sub_df["DP"] == True, sub_df["IVM"] == False)].sort_values(by=['MDA Coverage'],
                                                                                             ascending=True)[chan])

        with_IVM = sub_df[sub_df["IVM"] == True]
        #         print(with_IVM)
        for ivm_dur in ivm_durs:
            for DP in [False, True]:
                if not DP:
                    key = "IVM only -- {} days".format(ivm_dur)
                else:
                    key = "DP and IVM -- {} days".format(ivm_dur)

                hold = with_IVM[np.logical_and(with_IVM["Endectocide Duration"] == ivm_dur,
                                               with_IVM["DP"] == DP)]
                #                 print(hold)
                lines_dict[key] = np.array(hold.sort_values(by=['MDA Coverage'], ascending=True)[chan])

        # Add zero-coverage point to all curves:
        for key in lines_dict.keys():
            lines_dict[key] = np.append(zero_cov, lines_dict[key])

        x = np.array([0., 0.2, 0.4, 0.6, 0.8, 1.0])
        plt.plot(x, lines_dict["DP only"], c="C0", label="DP only")

        for i in range(4):
            lbl = "DP and IVM -- {} days".format(ivm_durs[i])
            c = "C{}".format(i + 1)
            # print(lbl)
            # print(lines_dict[lbl])
            plt.plot(x, lines_dict[lbl], c=c, label=lbl)

            lbl = "IVM only -- {} days".format(ivm_durs[i])
            # print(lbl)
            # print(lines_dict[lbl])
            plt.plot(x, lines_dict[lbl], c=c, label=lbl, linestyle='dashed')

        plt.xlabel("MDA Coverage")
        plt.ylabel("Fraction of sims eliminating")
        if not ITN and not IRS:
            title = "No VC"
        elif ITN and not IRS:
            title = "VC: ITN only"
        elif IRS and not ITN:
            title = "VC: IRS only"
        else:
            title = "VC: ITN and IRS"
        plt.title(title)
        if k == 0:
            plt.legend()

        k+= 1

plt.tight_layout()
plt.show()
