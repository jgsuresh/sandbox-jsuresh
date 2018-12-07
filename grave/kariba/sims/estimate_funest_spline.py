import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

with open("temporary_rainfall_InsetChart.json") as f:
    foo = json.load(f)

infec = np.array(foo['Channels']['New Infections']['Data'])
hbr = np.array(foo['Channels']['Daily Bites per Human']['Data'])
cc = np.array(foo['Channels']['New Clinical Cases']['Data'])

infec = infec[365:]
hbr = hbr[365:]
cc = cc[365:]



hbr_mean = (hbr[:365] + hbr[365*2:365*3] + hbr[365*3:365*4])/3
hbr_mean_norm = hbr_mean/np.max(hbr_mean)

days = np.arange(365)
hbr_mean_monthly = np.zeros(12)
for m in np.arange(12):
    days_cut = np.logical_and(days >= m*30.417, days < (m+1)*30.417)
    hbr_mean_monthly[m] = np.mean(hbr_mean[days_cut])

month_days = np.array([
    0.0,
    30.417,
    60.833,
    91.25,
    121.667,
    152.083,
    182.5,
    212.917,
    243.333,
    273.75,
    304.167,
    334.583
])

with open("arab_spline_v7_InsetChart.json") as f:
    foo = json.load(f)
hbr_spline = np.array(foo['Channels']['Daily Bites per Human']['Data'])

plt.figure()
# plt.plot(hbr)
plt.plot(hbr[:365], label="Climate year 1")

# plt.plot(hbr[365:365*2])
plt.plot(hbr[365*2:365*3], label="Climate year 2")
plt.plot(hbr[365*3:365*4], label="Climate year 3")
plt.plot(hbr_spline[365:365*2], label="SPLINE")
plt.plot(hbr_mean,linestyle='dashed', color='black', lw=2, label="Daily mean")
plt.step(month_days, hbr_mean_monthly, linestyle='-', marker='o', color='black', lw=2, where='post', label="Monthly spline")
plt.xlabel("Days")
plt.ylabel("Human Biting Rate")
plt.title("Arabiensis TEMPORARY_RAINFALL biting")
plt.legend()
plt.show()

print(month_days)
print(hbr_mean_monthly/np.max(hbr_mean_monthly))

arab_spline = [ #shifted by 1 month
    1.,
    0.92682906,
    0.49808722,
    0.13498624,
    0.02845621,
    0.01, #0.00695699,
    0.01, #0.00373352,
    0.01, #0.00302715,
    0.01, #0.00737515,
    0.04031032,
    0.11421247,
    0.58640474,]

funest_spline = [
    0.01,
    0.01,
    0.01,
    0.01,
    0.2,
    0.5,
    0.5,
    0.5,
    1.0, #oct
    1.0, #sept
    0.35,
    0.01]

old_funest_spline = [
    0.01,
    0.01,
    0.01,
    0.2,
    0.8,
    1.0,
    1.0,
    1.0,
    0.5,
    0.2,
    0.01,
    0.01]


# plt.figure()
# plt.plot(np.arange(1,13),arab_spline, label="arab")
# plt.plot(np.arange(1,13),funest_spline, label="funest",color="C2")
# plt.plot(np.arange(1,13),old_funest_spline, label="funest",color="C2",linestyle='dashed')
# plt.legend()
# plt.show()