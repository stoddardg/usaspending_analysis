"""
File: process_analyze_gun_data.py
Author: Oren Tirschwell
Date: 6/28/2024
Description: Produce basic cleaning and proximity statistics on gun violence data
"""

# Library and data imports
import pandas as pd
import os
import numpy as np
from scipy.spatial.distance import cdist
from constants import PATH_TO_RAW_DATA

gun_df = pd.read_csv(os.path.join(PATH_TO_RAW_DATA, 'gun_violence.csv'))


# Basic cleaning/processing

# Subset columns
gun_df = gun_df[[
    'city_state',
    'fatal_shootings',
    'avg_popn',
    'rate_per_100k'
]]

# Remove any NA information from our gun dataframe
gun_df.dropna(axis=0, inplace=True)

# We need to exclude some cities which don't have USA Spending matches from our gun data set.
gun_df_cities_to_exclude = [
    # 'Louisville/Jefferson County, Kentucky',
    # 'Nashville-Davidson, Tennessee',
    'Urban Honolulu CDP, Hawaii',
    'Metropolitan Government Of Nashville-Davidson (Balance), Tennessee',
    'Lexington-Fayette, Kentucky',
    'Louisville/Jefferson County Metro Government (Balance), Kentucky'
]

gun_df = gun_df[~gun_df.city_state.isin(gun_df_cities_to_exclude)].reset_index(drop=True)

# Force title case
gun_df['city_state'] = gun_df['city_state'].apply(lambda x: str(x).upper())


# Now, find closest 5 cities by three metrics
# Function to find the 5 closest cities based on a specific column using 1-norm (Manhattan distance)
def find_closest_cities_1norm(df, column):
    distances = cdist(df[[column]], df[[column]], metric='cityblock')
    np.fill_diagonal(distances, np.inf)  # To exclude the city itself from being considered
    closest_indices = np.argsort(distances, axis=1)[:, :5]
    closest_cities = df['city_state'].values[closest_indices]
    return [list(cities) for cities in closest_cities]


# Calculate closest 5 cities for each column
gun_df['closest_5_fatal_shootings'] = find_closest_cities_1norm(gun_df, 'fatal_shootings')
gun_df['closest_5_avg_popn'] = find_closest_cities_1norm(gun_df, 'avg_popn')
gun_df['closest_5_rate_per_100k'] = find_closest_cities_1norm(gun_df, 'rate_per_100k')


# Output to pickle, to preserve the list format of columns
gun_df.to_pickle('processed_data/cleaned_gun_data.pkl')
