from dtk.tools.migration.MigrationGenerator import MigrationGenerator

# demo_fp = './inputs/Demographics/chiyabi-luumbo-rd1.json'
# adj_fp = './gridding/chiyabi-luumbo-rd1_adjacency.json'
demo_fp = 'C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/inputs/Demographics/chiyabi-luumbo-rd1.json'
adj_fp = 'C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/gridding/chiyabi-luumbo-rd1_adjacency.json'

mg = MigrationGenerator(demo_fp,adj_fp)

mg.generate_link_rates()
mg.save_link_rates_to_txt('C:/Users/jsuresh/OneDrive - IDMOD/Code/zambia/gridding/migr_rates.txt')
