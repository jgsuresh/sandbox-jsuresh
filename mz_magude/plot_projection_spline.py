# Plot projection splines

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('white')

import pandas as pd
import numpy as np
from mozambique_experiments import MozambiqueExperiment


mozamb_catch_list = ["Chichuco","Chicutso","Magude-Sede-Facazissa","Mahel","Mapulanguene","Moine","Motaze","Panjane-Caputine"]
spline_list = ["funestus"] + mozamb_catch_list


def projection(spline):
    proj_dict = {}
    worst = np.zeros(12)
    med = np.zeros(12)
    best = np.zeros(12)

    for i in np.arange(12):
        months = [spline[i], spline[i + 12], spline[i + 24]]
        best[i] = np.min(months)
        med[i] = np.median(months)
        worst[i] = np.max(months)

    proj_dict["best"] = best
    proj_dict["med"] = med
    proj_dict["worst"] = worst

    return proj_dict



plt.figure()

i_fig = 1
for catch in mozamb_catch_list:
    arab_times, arab_spline = MozambiqueExperiment.catch_3_yr_spline(catch, "gambiae")
    ax = plt.subplot(3,3,i_fig)

    proj_dict = projection(arab_spline)
    ax.plot(arab_spline,lw=3,c='black')
    ax.plot(np.tile(proj_dict["worst"],3),c='red',ls='dashed')
    ax.plot(np.tile(proj_dict["med"],3), c='orange',ls='dashed')
    ax.plot(np.tile(proj_dict["best"],3), c='green',ls='dashed')
    ax.set_title("{} gambiae".format(catch))

    ax.set_xlabel("Month")

    i_fig += 1

ax = plt.subplot(3,3,9)
funest_times, funest_spline = MozambiqueExperiment.catch_3_yr_spline(catch, "funestus")
proj_dict = projection(funest_spline)
ax.plot(funest_spline, lw=2, c='black',label='3 year')
ax.plot(np.tile(proj_dict["worst"],3), c='red',label='worst')
ax.plot(np.tile(proj_dict["med"],3), c='orange',label='med')
ax.plot(np.tile(proj_dict["best"],3), c='green',label='best')
ax.set_xlabel("Month")
ax.set_title("funestus")
ax.legend()


plt.tight_layout()
plt.show()