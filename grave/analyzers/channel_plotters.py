import os

import numpy as np
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm
import seaborn as sns
sns.set_context("talk")
sns.set_style("white")

from plotting.convert_date_to_matplotlib_date import *

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer


# Very simple example plotting analyzer which plots a single channel from the Inset Chart:
class basic_inset_channel_plotter(BaseAnalyzer):
    def __init__(self, channel, working_dir=None):
        self.channel = channel
        filenames = ["output/InsetChart.json"]
        super(basic_inset_channel_plotter, self).__init__(working_dir=working_dir, filenames=filenames)

    def select_simulation_data(self, data, simulation):
        return {self.channel: data[self.filenames[0]]["Channels"][self.channel]['Data']}

    def finalize(self, all_data):
        plt.figure()
        for s in list(all_data.keys()):
            plt.plot(all_data[s][self.channel])

        plt.xlabel("Simulation Time")
        plt.ylabel(self.channel)
        plt.tight_layout()
        plt.show()





# More bells-and-whistles version of a channel plotter:
default_channels = ["True Prevalence"]
class inset_channel_plotter(BaseAnalyzer):
    def __init__(self, channels=default_channels, working_dir=None, filenames=None, **kwargs):
        """
        :param channels: list of Inset Channel channels
        :param working_dir: working directory
        :param filenames: simulation output filename (if unchanged, defaults to InsetChart.json)
        :param kwargs: optional extra keywords
            filter_dict: dictionary of acceptable tags: {tag1: [tag1_value0, tag1_value1], ...}
            label_by_tag: label will describe the value of the supplied tag
            label_by_expt: label will describe the experiment
                can select specific labels with if label_dict is supplied as label_dict = {expt_id1: label1, ...}
                or curve will simply be labelled by the experiment id
            color_by_tag: colors curves by their tag value, between color_vmin and color_vmax
            color_by_expt: each experiment given a unique color
            ref_date: date that corresponds to day 0 of simulation
        """

        self.channels = channels
        if not filenames:
            filenames = ["output/InsetChart.json"]

        super(inset_channel_plotter, self).__init__(working_dir=working_dir, filenames=filenames)

        self.kwargs = kwargs


    def filter(self, simulation):
        if "filter_dict" in self.kwargs:
            filter_dict = self.kwargs["filter_dict"]

            for tag in filter_dict:
                if simulation.tags[tag] not in filter_dict[tag]:
                    return False
            # If we haven't returned False yet, then simulation passes!  Return True
            return True
        else:
            return True

    def select_simulation_data(self, data, simulation):
        return {channel: data[self.filenames[0]]["Channels"][channel]['Data'] for channel in self.channels}

    def finalize(self, all_data):
        ci = 0
        color_dict = {}

        for channel in self.channels:

            if "figsize" in self.kwargs:
                plt.figure(figsize=self.kwargs["figsize"])
            else:
                plt.figure()


            for s in list(all_data.keys()):
                data = all_data[s][channel]

                # Determine how to label this curve:
                label = "_nolegend_"
                if "Run_Number" not in s.tags or s.tags["Run_Number"] == 0:
                    if "label_by_tag" in self.kwargs:
                        tag = self.kwargs["label_by_tag"]
                        tag_value = s.tags[tag]
                        label = "{} = {}".format(tag, tag_value)
                    elif "label_by_expt" in self.kwargs:
                        if "label_dict" in self.kwargs:
                            label = self.kwargs["label_dict"][s.experiment_id]
                        else:
                            label = s.experiment_id

                # Determine how to color this curve:
                if "color_by_tag" in self.kwargs:
                    vmin = self.kwargs["color_vmin"]
                    vmax = self.kwargs["color_vmax"]
                    tag_value = s.tags[self.kwargs["color_by_tag"]]
                    c = cm.ScalarMappable(norm=(tag_value-vmin)/(vmax-vmin), cmap="viridis")
                elif "color_by_expt" in self.kwargs:
                    if s.experiment_id in color_dict:
                        c = color_dict[s.experiment_id]
                    else:
                        c = "C{}".format(ci)
                        ci += 1
                        color_dict[s.experiment_id] = c

                # Plot by date if a ref date has been given
                if "ref_date" in self.kwargs:
                    ref_date = self.kwargs["ref_date"]
                    mdate_arr = convert_day_number_array_to_mdate(np.arange(np.size(data)), ref_date)

                    # Now plotting:
                    if "c" in locals():
                        plt.plot_date(mdate_arr, data, label=label, c=c, ls='-', marker=',')
                    else:
                        plt.plot_date(mdate_arr, data, label=label, ls='-', marker=',')

                else:
                    if "c" in locals():
                        plt.plot(data, label=label, c=c)
                    else:
                        plt.plot(data, label=label)

                    plt.xlabel("Simulation Time")

            if "plot_xlim" in self.kwargs:
                plt.xlim(self.kwargs["plot_xlim"])
            if "plot_ylim" in self.kwargs:
                plt.ylim(self.kwargs["plot_ylim"])

            plt.ylabel(channel)
            plt.legend()
            plt.tight_layout()

            plt.savefig(os.path.join(self.working_dir, channel))
            if "plot_show" in self.kwargs and self.kwargs["plot_show"]:
                plt.show()



diagnostic_channels = ["Daily Bites per Human", "Daily EIR", "Adult Vectors", "Blood Smear Parasite Prevalence"]
def plot_inset_diagnostics(experiment_list, channels=default_channels, working_dir = ".", filename="output/InsetChart.json", **kwargs):
    from simtools.Analysis.AnalyzeManager import AnalyzeManager

    am = AnalyzeManager()
    am.add_analyzer(inset_channel_plotter(channels,
                                          working_dir=working_dir,
                                          filename=filename,
                                          **kwargs))

    for expt in experiment_list:
        am.add_experiment(expt)
    am.analyze()



# An example:
if __name__ == "__main__":
    from simtools.Analysis.AnalyzeManager import AnalyzeManager

    am = AnalyzeManager()
    # am.add_analyzer(basic_inset_channel_plotter("True Prevalence"))

    diagnostic_channels = ["Daily Bites per Human", "Daily EIR", "Adult Vectors", "Blood Smear Parasite Prevalence"]
    am.add_analyzer(inset_channel_plotter(diagnostic_channels,
                                          color_by_expt=True,
                                          label_by_expt=True,
                                          label_dict = {"7e3073b4-d9f1-e811-a2bd-c4346bcb1555": "full campaign",
                                                        "a2e981fe-d9f1-e811-a2bd-c4346bcb1555": "no 2011 bednets"},
                                          ref_date="2001-01-01",
                                          figsize=(10,4),
                                          plot_xlim=convert_date_list_to_mdate(["2010-01-01","2019-01-01"]),
                                          plot_show=False))
    am.add_experiment("7e3073b4-d9f1-e811-a2bd-c4346bcb1555")
    am.add_experiment("a2e981fe-d9f1-e811-a2bd-c4346bcb1555")
    am.analyze()

