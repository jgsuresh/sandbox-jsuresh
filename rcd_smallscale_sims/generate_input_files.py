import pandas as pd
import json

# Generate demographics file
from dtk.tools.demographics.DemographicsGenerator import DemographicsGenerator
# from input_file_generation import DemographicsGenerator
from dtk.tools.demographics.DemographicsGeneratorConcern import WorldBankBirthRateConcern
from dtk.tools.migration.MigrationGenerator import MigrationGenerator


def make_pop_df(pop_denom=750, pop_node=30):
    # Generate input population dataframe

    n_nodes = int(pop_denom/pop_node)

    pop_df = pd.DataFrame({
        "node_label": range(1, n_nodes+1),
        "pop": pop_node,
        "lat": -16.6050279348,
        "lon": 28.0395981141,
        "Country": "Zambia"
    })

    return pop_df


# class project_demographics_generator(DemographicsGenerator):
#
#
# DemographicsGenerator
# dg = DemographicsGenerator(concerns=)

# wb = WorldBankBirthRateConcern()

# Migration

with open("vector_local_migr_rates.json") as fp:
    migr_link_rates = json.load(fp)

print(migr_link_rates)

mg = MigrationGenerator(migration_file_name="vector_local_migration.bin",
                        link_rates=migr_link_rates
                        )
mg.generate_migration(demographics_file_path="demo.json")


if __name__ == "__main__":

    df = make_pop_df()

    # demographics = DemographicsGenerator.from_dataframe(df, demographics_filename="demo.json", concerns=[wb])
    # DemographicsGenerator.to_grid_file("demo.json", demographics)