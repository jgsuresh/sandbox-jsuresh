
def scale_larval_habs_for_bairro(cb, bairro_num, bairro_df, arab_mult, funest_mult, start_day=0):
    # Get grid cells for this bairro
    bairro_grid_cells = bairro_df[bairro_df['bairro']==bairro_num]['grid_cell']
    n_cells = len(bairro_grid_cells)

    # Make a dataframe for these node ids, with the appropriate multipliers
    scale_larval_habitats(cb,
                          pd.DataFrame({
                              'LINEAR_SPLINE.arabiensis': [arab_mult]*n_cells,
                              'LINEAR_SPLINE.funestus': [funest_mult]*n_cells,
                              'Start_Day': [start_day]*n_cells,
                              'NodeID': [int(x) for x in bairro_grid_cells]})
                          )
