"""
File: merge_clean_grant_data.py
Author: Oren Tirschwell
Date: 6/27/2024
Description: Import all department grant data, merge into one dataframe, run basic cleaning operations, and output column subset
"""

# Global Variables
LIMIT_TO_NEW_ENTRIES_ONLY = True
REMOVE_STATE_GOVTS = True

# Library Imports
import pandas as pd
import os
import glob
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore', category=pd.errors.DtypeWarning)

from constants import PATH_TO_RAW_DATA


# Data Import & Filtering

# Iterate through all file string name matches to concat into one pandas dataframe
file_paths = glob.glob(os.path.join(PATH_TO_RAW_DATA, 'indiv_dpt_grants/**/*.csv'), recursive=True)
all_data = [pd.read_csv(g) for g in file_paths]
df = pd.concat(all_data)
del all_data

# Apply basic filtering operations to our data based on global constant variables
if LIMIT_TO_NEW_ENTRIES_ONLY:
    df = df[df['action_type_description'] == 'NEW']

if REMOVE_STATE_GOVTS:
    df = df[df['business_types_description'] != 'STATE GOVERNMENT']

# De-dupe grants
# Note: ordering is important here. We must be sure to filter for NEW entries only *before* we de-dupe by date.
dup_cols = [
    'usaspending_permalink',
]
df.sort_values(by='action_date', ascending=True, inplace=True)
df.drop_duplicates(subset=dup_cols, keep='last', inplace=True)


# Basic Data Views
print(f'Our data set has {len(df)} rows.')
print(df.head(2))

# Verify we have data for all departments, all years (confirming data download was successful)
print(df[['awarding_agency_name', 'action_date_fiscal_year']].value_counts().unstack())

# Basic Data Cleaning & Processing
df['total_outlayed_amount_for_overall_award'] = df['total_outlayed_amount_for_overall_award'].fillna(0)

df['estimated_remaining_funds'] = df['total_obligated_amount'] - df['total_outlayed_amount_for_overall_award']

df['spent_percent'] = ((df['total_outlayed_amount_for_overall_award'] / df['total_obligated_amount'])*100).round(0)

df['remaining_funds_percent'] = ((df['estimated_remaining_funds'] / df['total_obligated_amount'])*100).round(0)

df['period_of_performance_current_end_date'] = pd.to_datetime(df['period_of_performance_current_end_date'])
df['period_of_performance_start_date'] = pd.to_datetime(df['period_of_performance_start_date'])
df['action_date'] = pd.to_datetime(df['action_date'])

df['grant_is_open'] = df['period_of_performance_current_end_date'] >= datetime(2024,9,1)

df['city_state'] = df['primary_place_of_performance_city_name'] + ', ' + df['primary_place_of_performance_state_name']
# df['city_state'] = df['city_state'].apply(lambda x: str(x).title())

print(f'There are {len(df[df.total_obligated_amount <= 0])} grants where the total obligated amount is <= 0.')
df = df[df.total_obligated_amount > 0]

df['prime_award_base_transaction_description'] = df['prime_award_base_transaction_description'].apply(lambda x: str(x).capitalize())
df['recipient_name'] = df['recipient_name'].apply(lambda x: x.title())


# Output dataframe to temp storage file
out_cols = [
    'assistance_award_unique_key',
    'total_obligated_amount',
    'total_outlayed_amount_for_overall_award',
    'action_date',
    'action_date_fiscal_year',
    'period_of_performance_start_date',
    'period_of_performance_current_end_date',
    'awarding_agency_name',
    'program_activities_funding_this_award',
    'cfda_title',
    'prime_award_base_transaction_description',
    'recipient_name',
    'recipient_state_name',
    'recipient_city_name',
    'city_state',
    'usaspending_permalink',
    'estimated_remaining_funds',
    'grant_is_open'
]

dir_path = Path('processed_data')
dir_path.mkdir(exist_ok=True)

df[out_cols].to_parquet('processed_data/merged_cleaned_grants.parquet')
