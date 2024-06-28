"""
File: city_grant_summaries.py
Author: Oren Tirschwell
Date: 6/28/2024
Description: Combine gun and grant data to generate grant- and department-level city overviews
"""

# Library and data imports
import pandas as pd
import numpy as np
from constants import AGENCIES

grant_df = pd.read_parquet('processed_data/mapped_grants.parquet')
guns_df = pd.read_pickle('processed_data/cleaned_gun_data.pkl')


# Filter out a few specific grants
grants_to_exclude = [
    'https://www.usaspending.gov/award/ASST_NON_B-21-DF-22-0001_8620/',
    'https://www.usaspending.gov/award/ASST_NON_B-18-DP-22-0001_8620/',
    'https://www.usaspending.gov/award/ASST_NON_B-21-DZ-22-0001_8620/',
    'https://www.usaspending.gov/award/ASST_NON_B-22-DF-22-0001_8620/',
]

grant_df = grant_df[~grant_df.usaspending_permalink.isin(grants_to_exclude)]


# Generate grant summaries
grant_summary_table = grant_df.groupby(['city_state', 'program_match']).agg(
    count = ('program_match','size'),
    count_open  = ('grant_is_open','sum'),
    total_estimated_remaining_funds = ('estimated_remaining_funds','sum'),
    total_obligated_funds = ('total_obligated_amount','sum')
).reset_index()


# Force one row for each city_state and program_match combination, even if they are 0
# Create a MultiIndex with all combinations of unique city_state and program_match
all_combinations = pd.MultiIndex.from_product(
    [grant_summary_table['city_state'].unique(), grant_summary_table['program_match'].unique()],
    names=['city_state', 'program_match']
)

grant_summary_table = (
    grant_summary_table.set_index(['city_state', 'program_match'])
    .reindex(all_combinations, fill_value=0)
    .reset_index()
).sort_values(['city_state', 'program_match']).merge( # Need to merge back in to get awarding agency name
    grant_df[['program_match', 'awarding_agency_name']].drop_duplicates(),
    on='program_match',
    how='left'
)


# Format the program match column
def gen_new_program_match(row):
    return f'{AGENCIES[row.awarding_agency_name]} - {row.program_match}'


grant_summary_table['formatted_program_match'] = grant_summary_table.apply(gen_new_program_match, axis=1)


# Validation: do all gun dataset cities match a city in the USA Spending data set?
# Convert the city_state column in all_data to title case and get unique values
unique_city_states = grant_summary_table['city_state'].dropna().unique()

# Check if the city_state values in gun_df are in the unique_city_states list
is_in_unique_city_states = guns_df['city_state'].isin(unique_city_states)
cities_not_in_unique_city_states = guns_df.loc[~is_in_unique_city_states, 'city_state']
assert len(cities_not_in_unique_city_states) == 0


# Now, we can subset to just the cities in our gun df
our_cities_grant_summary_table = grant_summary_table[grant_summary_table.city_state.isin(guns_df['city_state'])]
merged_df = our_cities_grant_summary_table.merge(guns_df, on='city_state', how='left')


# Create several useful calculated metric fields in our data set
# This works out to be annual funding over annual homicides, so annual funding per one homicide.
merged_df['cvi_funding_per_hom'] = merged_df.total_obligated_funds / merged_df.fatal_shootings

# We add in extra by-5 divisions here in order to keep annual definitions standard. We correct for 5-year funding values.
merged_df['cvi_funding_per_person'] = merged_df.total_obligated_funds / merged_df.avg_popn / 5

# Change fatal shootings to be an annual value
merged_df['fatal_shootings'] = round(merged_df['fatal_shootings'] / 5)


# Calculate avg cvi funding for closest 5 cities

# General function which takes in the closeness metric and cvi grants
def calculate_avg_cvi_funding(row, closeness_metric):
    cities = row[closeness_metric]
    grant_program = row['program_match']
    funding_values = merged_df[
        (merged_df.city_state.isin(cities)) &
        (merged_df.program_match == grant_program)
    ]['total_obligated_funds']
    
    if len(funding_values) == 0:
        funding_values = np.array([0])
    
    return funding_values.mean()


# Apply the roundup metrics to all cities
metrics = [
    'closest_5_fatal_shootings',
    'closest_5_avg_popn',
    'closest_5_rate_per_100k'
]

for metric in metrics:
    # Apply the function to each row in gun_df
    merged_df[f'avg_funds_{metric}'] = merged_df.apply(calculate_avg_cvi_funding, axis=1, closeness_metric=metric)


# Convert list cols to strings
for col in merged_df.columns:
    if col[:8] == 'closest_':
        merged_df[col] = merged_df[col].apply(lambda x: '; '.join(x))


merged_df['awarding_agency_abbrev'] = merged_df.awarding_agency_name.apply(lambda agency: AGENCIES[agency])

# Output to csv
merged_df.to_csv('processed_data/city_grant_summaries.csv', index=False)


# Now, produce an aggregate version where we go only by city_state and awarding agency name, plus add an agency value of "All"
columns_to_keep = ['fatal_shootings', 'avg_popn', 'rate_per_100k']
columns_to_sum = [col for col in merged_df.columns if col not in columns_to_keep + ['city_state']]

constant_df = merged_df[['city_state'] + columns_to_keep].drop_duplicates()

summed_df_1 = merged_df.groupby('city_state')[columns_to_sum].sum(numeric_only=True).reset_index()
summed_df_1['awarding_agency_name'] = "All"

summed_df_2 = merged_df.groupby(['city_state', 'awarding_agency_name'])[columns_to_sum].sum(numeric_only=True).reset_index()
agg_merged_df = pd.concat([summed_df_1, summed_df_2], ignore_index=True).merge(
    constant_df, 
    on='city_state',
    how='left'
)

agg_merged_df['awarding_agency_abbrev'] = agg_merged_df.awarding_agency_name.apply(lambda agency: AGENCIES[agency] if agency in AGENCIES else agency)

agg_merged_df.to_csv('processed_data/city_dept_summaries.csv', index=False)
