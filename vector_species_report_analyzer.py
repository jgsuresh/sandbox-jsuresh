import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
# from simtools.Analysis.BaseAnalyzers import BaseAnalyzer
from dtk.helpers import *

class VectorSpeciesReportAnalyzer(BaseAnalyzer):

    def __init__(self, save_file=None, channel='Adult Vectors Per Node'):
        super().__init__()
        self.channel = channel
        self.filenames = ['output/VectorSpeciesReport.json']
        self.save_file = save_file

    @classmethod
    def ts_to_dt(self, timesteps):

        refd = datetime.date(2009, 1, 1).toordinal()
        return [datetime.date.fromordinal(x + refd - timesteps[0]) for x in timesteps]

    def apply(self, parser):

        # Load data from simulation
        d = parser.raw_data[self.filenames[0]]
        species = d['Header']['Subchannel_Metadata']['MeaningPerAxis'][0][0]
        df = pd.DataFrame()
        for si, s in enumerate(species) :
            data = pd.DataFrame({ self.channel : d['Channels'][self.channel]['Data'][si]})
            data['species'] = s
            data['Time'] = data.index
            data['date'] = self.ts_to_dt(data['Time'])
            df = pd.concat([df, data])
        df['Month_temp'] = df['date'].apply(lambda x : x.month)
        df['Year'] = df['date'].apply(lambda x : x.year - 2015)
        df['Month'] = df['Month_temp'] + 12*df['Year']
        df['sim_id'] = parser.sim_id
        return df

    def combine(self, parsers):

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        self.data = pd.concat(selected)

    def finalize(self):
        import seaborn as sns
        sns.set_style("darkgrid")

        fig = plt.figure(figsize=(10,6))
        ax = fig.gca()
        for a, adf in self.data.groupby('sim_id') :
            for s, sdf in adf.groupby('species') :
               ax.plot(sdf['date'], sdf[self.channel], label=s)
        ax.legend()
        plt.ylabel(self.channel)
        if self.save_file:
            plt.savefig(self.save_file + ".png")
            plt.savefig(self.save_file + ".pdf")
        else:
            plt.show()


if __name__ == '__main__' :

    am = AnalyzeManager()
    am.add_analyzer(VectorSpeciesReportAnalyzer())
    am.add_simulation('4047a20f-b33d-e811-a2bf-c4346bcb7274')
    am.analyze()
