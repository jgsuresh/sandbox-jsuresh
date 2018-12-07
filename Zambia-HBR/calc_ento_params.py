import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context("talk")

hlc_hbr = pd.read_csv("zambia_hbr.csv")
ppl_dist = pd.read_csv("nighttime_distribution_people.csv")

dry = ppl_dist["Season"] == "Dry"
wet = ppl_dist["Season"] == "Wet"
# Figure 1: Plot wet/dry season indoor/outdoor fractions for people:
if False:
	hours = np.arange(18,31)
	plt.figure()
	plt.plot(hours, ppl_dist[wet]["Frac_Indoors"], label="Wet")
	plt.plot(hours, ppl_dist[dry]["Frac_Indoors"], label="Dry")
	plt.legend()
	plt.xlabel("Hour")
	plt.ylabel("Fraction of people indoors")
	plt.ylim([0.3,1.0])
	plt.tight_layout()
	plt.show()


# Figure 2: Zambia HLC HBR for two years/times:
gamb = hlc_hbr["species"]=="gambiae"
funest = hlc_hbr["species"]=="funestus"	
y15 = hlc_hbr["year"] == 2015
y17 = hlc_hbr["year"] == 2017

if False:
	hours = np.arange(18,30)

	plt.figure(figsize=(10,5))
	ax = plt.subplot(221)
	ax.set_title("Gambiae in 2015")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"], label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["outdoor_bite_rate"], label="Outdoor", c="C9")
	ax.set_ylim(0.,2.0)
	ax.set_ylabel("HLC HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	plt.legend()

	ax = plt.subplot(222)
	ax.set_title("Gambiae in 2017")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"], label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["outdoor_bite_rate"], label="Outdoor", c="C9")
	ax.set_ylim(0.,2.0)
	ax.set_ylabel("HLC HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	plt.legend()

	ax = plt.subplot(223)
	ax.set_title("Funestus in 2015")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"], label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["outdoor_bite_rate"], label="Outdoor", c="C9")
	ax.set_ylim(0.,2.0)
	ax.set_ylabel("HLC HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))

	ax = plt.subplot(224)
	ax.set_title("Funestus in 2017")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"], label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["outdoor_bite_rate"], label="Outdoor", c="C9")
	ax.set_ylim(0.,2.0)
	ax.set_ylabel("HLC HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))

	plt.tight_layout()
	plt.show()


def reduce_size_by_midpoint(x):
	y = np.zeros(len(x)-1)

	for i in np.arange(np.size(y)):
		y[i] = (x[i] + x[i+1])/2.

	return y

# Figure 3: Inferred indoor vs outdoor biting rates:
# wet_dist_in = np.array(ppl_dist[wet]["Frac_Indoors"])[:-1]
# wet_dist_out = np.array(ppl_dist[wet]["Frac_Outdoors"])[:-1]
# dry_dist_in = np.array(ppl_dist[dry]["Frac_Indoors"])[:-1]
# dry_dist_out = np.array(ppl_dist[dry]["Frac_Outdoors"])[:-1]
wet_dist_in = reduce_size_by_midpoint(np.array(ppl_dist[wet]["Frac_Indoors"]))
wet_dist_out = reduce_size_by_midpoint(np.array(ppl_dist[wet]["Frac_Outdoors"]))
dry_dist_in = reduce_size_by_midpoint(np.array(ppl_dist[dry]["Frac_Indoors"]))
dry_dist_out = reduce_size_by_midpoint(np.array(ppl_dist[dry]["Frac_Outdoors"]))

if True:
	hours = np.arange(18,30)

	plt.figure(figsize=(10,5))
	ax = plt.subplot(221)
	ax.set_title("Gambiae in 2015")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*wet_dist_in, label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["outdoor_bite_rate"]*wet_dist_out, label="Outdoor", c="C9")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*dry_dist_in, c="C3", linestyle='dashed', label='_nolegend_')
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y15)]["outdoor_bite_rate"]*dry_dist_out, c="C9", linestyle='dashed', label='_nolegend_')
	ax.set_ylim(0.,0.8)
	ax.set_ylabel("Inferred Actual HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	ax.set_yticks([0,0.2,0.4,0.6,0.8])
	plt.legend()

	ax = plt.subplot(222)
	ax.set_title("Gambiae in 2017")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*wet_dist_in, label="Wet", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["outdoor_bite_rate"]*wet_dist_out, label="_nolegend_", c="C9")
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*dry_dist_in, c="C3", linestyle='dashed', label='Dry')
	ax.plot(hours, hlc_hbr[np.logical_and(gamb,y17)]["outdoor_bite_rate"]*dry_dist_out, c="C9", linestyle='dashed', label='_nolegend_')
	ax.set_ylim(0.,0.8)
	ax.set_ylabel("Inferred Actual HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	ax.set_yticks([0,0.2,0.4,0.6,0.8])
	plt.legend()

	ax = plt.subplot(223)
	ax.set_title("Funestus in 2015")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*wet_dist_in, label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["outdoor_bite_rate"]*wet_dist_out, label="Outdoor", c="C9")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*dry_dist_in, c="C3", linestyle='dashed', label='Dry')
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y15)]["outdoor_bite_rate"]*dry_dist_out, c="C9", linestyle='dashed', label='_nolegend_')
	ax.set_ylim(0.,0.8)
	ax.set_ylabel("Inferred Actual HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	ax.set_yticks([0,0.2,0.4,0.6,0.8])

	ax = plt.subplot(224)
	ax.set_title("Funestus in 2017")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*wet_dist_in, label="Indoor", c="C3")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["outdoor_bite_rate"]*wet_dist_out, label="Outdoor", c="C9")
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*dry_dist_in, c="C3", linestyle='dashed', label='Dry')
	ax.plot(hours, hlc_hbr[np.logical_and(funest,y17)]["outdoor_bite_rate"]*dry_dist_out, c="C9", linestyle='dashed', label='_nolegend_')
	ax.set_ylim(0.,0.8)
	ax.set_ylabel("Inferred Actual HBR")
	ax.set_xlabel("Hour")
	ax.set_xticks(list(hours))
	ax.set_yticks([0,0.2,0.4,0.6,0.8])

	plt.tight_layout()
	plt.show()


# Figure 4: indoor biting fractions vs assumed:
# For Gambiae in 2015, take all indoor bites and outdoor bites, and take in/(in+out)

if False:
	gamb_15_wet = np.sum(hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*wet_dist_in)/np.sum(hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*wet_dist_in + hlc_hbr[np.logical_and(gamb,y15)]["outdoor_bite_rate"]*wet_dist_out)
	gamb_15_dry = np.sum(hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*dry_dist_in)/np.sum(hlc_hbr[np.logical_and(gamb,y15)]["indoor_bite_rate"]*dry_dist_in + hlc_hbr[np.logical_and(gamb,y15)]["outdoor_bite_rate"]*dry_dist_out)

	gamb_17_wet = np.sum(hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*wet_dist_in)/np.sum(hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*wet_dist_in + hlc_hbr[np.logical_and(gamb,y17)]["outdoor_bite_rate"]*wet_dist_out)
	gamb_17_dry = np.sum(hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*dry_dist_in)/np.sum(hlc_hbr[np.logical_and(gamb,y17)]["indoor_bite_rate"]*dry_dist_in + hlc_hbr[np.logical_and(gamb,y17)]["outdoor_bite_rate"]*dry_dist_out)


	funest_15_wet = np.sum(hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*wet_dist_in)/np.sum(hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*wet_dist_in + hlc_hbr[np.logical_and(funest,y15)]["outdoor_bite_rate"]*wet_dist_out)
	funest_15_dry = np.sum(hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*dry_dist_in)/np.sum(hlc_hbr[np.logical_and(funest,y15)]["indoor_bite_rate"]*dry_dist_in + hlc_hbr[np.logical_and(funest,y15)]["outdoor_bite_rate"]*dry_dist_out)

	funest_17_wet = np.sum(hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*wet_dist_in)/np.sum(hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*wet_dist_in + hlc_hbr[np.logical_and(funest,y17)]["outdoor_bite_rate"]*wet_dist_out)
	funest_17_dry = np.sum(hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*dry_dist_in)/np.sum(hlc_hbr[np.logical_and(funest,y17)]["indoor_bite_rate"]*dry_dist_in + hlc_hbr[np.logical_and(funest,y17)]["outdoor_bite_rate"]*dry_dist_out)


	plt.figure()
	ax = plt.subplot(211)
	# plt.scatter([15,15,17,17], [gamb_15_wet, gamb_15_dry, gamb_17_wet, gamb_17_dry])
	ax.scatter([2015,2017], [gamb_15_wet, gamb_17_wet], label="Wet")
	ax.scatter([2015,2017], [gamb_15_dry, gamb_17_dry], label="Dry")
	ax.axhline(0.5, color="gray", linestyle="dashed", label="Current DTK Setting")
	ax.set_xticks([2015, 2017])
	ax.set_xlim([2011,2019])
	ax.set_ylabel("Indoor Feeding Fraction")
	ax.set_title("Gambiae")
	plt.legend()

	ax = plt.subplot(212)
	ax.scatter([2015,2017], [funest_15_wet, funest_17_wet], label="Wet")
	ax.scatter([2015,2017], [funest_15_dry, funest_17_dry], label="Dry")
	ax.axhline(0.9, color="gray", linestyle="dashed", label="Current DTK Setting")
	ax.set_xticks([2015, 2017])
	ax.set_xlim([2011,2019])
	ax.set_ylabel("Indoor Feeding Fraction")
	ax.set_title("Funestus")
	# plt.legend()

	plt.tight_layout()
	plt.show()