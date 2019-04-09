#!/usr/bin/python

import argparse
from dtk.tools.serialization import dtkFileTools as dft
import os
import sys
import pandas as pd
import numpy as np

def rewrite_spline(filename, output, spline_fname, author='self', toolname='linear_spline_rewriter'):

    print("Reading '{0}'".format(filename))
    dtk_file = dft.read(filename)

    dtk_file.author = author
    dtk_file.tool = toolname

    adf = pd.read_csv(spline_fname)

    for index, node in enumerate(dtk_file.nodes):
        print('Processing node {0}(suid={1})'.format(index, node.suid.id))
        for pair in node.m_larval_habitats:
            habitats = pair.value
            species = pair.key
            df = adf[(adf['species'] == species)]
            if 'node_id' in adf.columns.values :
                df = df[df['node_id'] == node.externalId]
            df = df.sort_values(by='Times')
            newhabs = [{ 'key' : int(x), 'value' : float(y)} for x,y in zip(df['Times'].values, df['Values'].values)]
            for habitat in habitats:
                if habitat['__class__'] == 'LinearSplineHabitat':
                    habitat.capacity_distribution = newhabs
        dtk_file.nodes[index] = node

    print("Writing '{0}'".format(output))
    dft.write(dtk_file, output)

    return



def rewrite_spline_by_node(input_fn, output_fn, spline_df_fname, author='jsuresh', toolname='linear_spline_rewriter'):

    print("Reading '{0}'".format(input_fn))
    dtk_file = dft.read(input_fn)

    dtk_file.author = author
    dtk_file.tool = toolname

    adf = pd.read_csv(spline_df_fname)

    for index in range(len(dtk_file.nodes)):
        node = dtk_file.nodes[index]
        print('Processing node {0}(suid={1})'.format(index, node.suid.id))
        for pair in node.m_larval_habitats:
            habitats = pair.value
            species = pair.key
            df = adf[np.logical_and(adf['species'] == species, adf['node'] == node.externalId)]
            newhabs = [{ 'key' : int(x), 'value' : float(y)} for x,y in zip(df['Times'].values, df['Values'].values)]
            for habitat in habitats:
                if habitat['__class__'] == 'LinearSplineHabitat':
                    habitat.capacity_distribution = newhabs
        dtk_file.nodes[index] = node

    print("Writing '{0}'".format(output_fn))
    dft.write(dtk_file, output_fn)

    return


#
#
# if __name__ == '__main__':
#     # test run:
#     rewrite_spline('C:/Users/jsuresh/Projects/malaria-mz-magude/gridded_sims/src/calibs/Calib_Chicutso_pop0_burnin/best_run/state-19710-000.dtk',
#                    'C:/Users/jsuresh/Projects/malaria-mz-magude/gridded_sims/src/calibs/Calib_Chicutso_pop0_burnin/best_run/state-TEST-000.dtk',
#                    'C:/Users/jsuresh/Projects/malaria-mz-magude/gridded_sims/src/calibs/test_spline.csv')
#

if __name__ == '__main__':
    username = os.environ['USERNAME'] if 'USERNAME' in os.environ else os.environ['USER']
    toolname = os.path.basename(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('spline_file')
    parser.add_argument('-a', '--author', default=username)
    parser.add_argument('-t', '--tool', default=toolname)

    args = parser.parse_args()

    rewrite_spline(args.source, args.destination, args.spline_file, args.author, args.tool)
    sys.exit(0)