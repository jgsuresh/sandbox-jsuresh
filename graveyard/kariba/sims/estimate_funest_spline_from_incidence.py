import json

import numpy as np
import matplotlib.pyplot as plt

cases = np.array([
    346.2857143,
    281.2857143,
    388.2857143,
    402.7142857,
    498.7142857,
    364.8571429,
    224.8571429,
    215.4285714,
    225.5714286,
    378,
    196,
    40,
    233.5714286,
    359.4285714,
    591.4285714,
    497.2857143,
    286.7142857,
    297.1428571,
    240.4285714,
    211.8571429,
    502.1428571,
    208.4285714,
    173.5714286,
    123,
    255.1428571,
    317.7142857,
    984,
    431.5714286,
    390.7142857,
    286.5714286,
    229.1428571,
    260.7142857,
    266.4285714,
    596.5714286,
    133.8571429,
    22.57142857,
    136.7142857,
    170.7142857,
    388.2857143,
    508.7142857,
    889.2857143,
    636.8571429,
    562.1428571,
    371.8571429,
    203.4285714,
    173,
    121.2857143,
    22.71428571,
    30,
    26.71428571,
    106.4285714,
    152.1428571,
    203.2857143,
    190.8571429,
    68.57142857,
    86.85714286,
    207.1428571,
    232,
    44,
    1,
    40,
    14.14285714,
    90.42857143,
    142.4285714,
    165.1428571,
    144.4285714,
    106.7142857,
    75.42857143,
    48.28571429,
    37.85714286,
    2.142857143,
    13
])

# plt.figure()
# plt.plot(np.arange(1,13), cases[:12], label="2012")
# plt.plot(np.arange(1,13), cases[12:24], label="2013")
# plt.plot(np.arange(1,13), cases[24:36], label="2014")
# plt.plot(np.arange(1,13), cases[36:48], label="2015")
# plt.plot(np.arange(1,13), cases[48:60], label="2016")
# plt.plot(np.arange(1,13), cases[60:], label="2017")
# plt.legend()
# plt.title("Chiyabi cases")
# plt.show()

with open("funest_spline_v1_InsetChart.json") as f:
    foo = json.load(f)
hbr_spline = np.array(foo['Channels']['Daily Bites per Human']['Data'])


# plt.figure()
# plt.plot(np.arange(6,13), cases[5:12]/np.max(cases[5:12]), label="2012 cases")
# plt.plot(np.arange(6,13), cases[17:24]/np.max(cases[17:24]), label="2013 cases")
# plt.plot(np.arange(6,13), cases[29:36]/np.max(cases[29:36]), label="2014 cases")
# plt.plot(np.arange(365)/30, hbr_spline[365:365*2]/np.max(hbr_spline[365:365*2]), label="Funestus SPLINE HBR")
# # plt.plot(np.arange(7,13), cases[42:48], label="2015")
# # plt.plot(np.arange(7,13), cases[54:60], label="2016")
# # plt.plot(np.arange(7,13), cases[66:], label="2017")
#
#
# plt.legend()
# plt.title("Chiyabi")
# plt.show()


plt.figure()
arab = {
    "Times": [
        0.0,
        15.417,
        45.833,
        76.25,
        106.667,
        137.083,
        167.5,
        207.917,
        228.333,
        258.75,
        289.167,
        319.583,
        335,
        365.25
    ],
    "Values": [
        0.48,
        1.,
        0.92682906,
        0.49808722,
        0.13498624,
        0.02845621,
        0.01,  # 0.00695699,
        0.01,  # 0.00373352,
        0.01,  # 0.00302715,
        0.01,  # 0.00737515,
        0.03,
        0.05,
        0.22,
        0.48
    ]}

funest = {
    "Times": [
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
        334.583,
        365.25
    ],
    "Values": [
        0.01,
        0.01,
        0.01,
        0.01,
        0.2,
        0.5,
        0.5,
        0.5,
        1.0,  # oct
        1.0,  # sept
        0.35,
        0.01,
    0.01]}
plt.figure()
plt.step(arab["Times"],arab["Values"], label="arab spline",  where='post')
plt.step(funest["Times"],funest["Values"], label="funest spline",  where='post')
plt.xticks([30*i for i in range(13)])
plt.legend()
plt.show()