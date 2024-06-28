"""
File: match_grant_programs.py
Author: Oren Tirschwell
Date: 6/27/2024
Description: Run matching scheme to determine what Violence Prevention related program the grant may fall under
"""

# Library and data imports
import pandas as pd
import json

df = pd.read_parquet('processed_data/merged_cleaned_grants.parquet')
with open('program_mapping.json', 'r') as file:
    mappings = json.load(file)


# Understand which mappings we don't have matches for
missing_values = pd.DataFrame(columns=['Department', 'Missing Program Mapping Name'])

# Iterate over the JSON data
for top_key, top_value in mappings.items():
    for second_key, second_value in top_value.items():
        # Check if specific sub-keys exist and are both empty arrays
        if (second_value.get('cfda_descriptions') == [] and 
            second_value.get('program_activities_funding') == []):
            # Append to the DataFrame
            missing_values = missing_values.append({'Department': top_key, 
                                                    'Missing Program Mapping Name': second_key}, ignore_index=True)

print(missing_values)


# Function to be row-wise applied to determine program matches
def find_matches(row):
    office_name = row['awarding_agency_name']
    cfda_matches = []
    program_funding_matches = []
    
    # Create a dictionary to track the order of appearance
    match_order = {}
    order_counter = 0
    
    # Get the associated key in mappings
    if office_name in mappings:
        programs = mappings[office_name]
        
        # Loop through each sub-key in programs
        for prog_key, prog in programs.items():
            # Check for matches in cfda_title
            if any(description in row['cfda_title'] for description in prog['cfda_descriptions']):
                cfda_matches.append(prog_key)
                if prog_key not in match_order:
                    match_order[prog_key] = order_counter
                    order_counter += 1
                
            # Check for matches in program_activities_funding_this_award
            if pd.notna(row['program_activities_funding_this_award']) and any(activity in row['program_activities_funding_this_award'] for activity in prog['program_activities_funding']):
                program_funding_matches.append(prog_key)
                if prog_key not in match_order:
                    match_order[prog_key] = order_counter
                    order_counter += 1

    # Sort matches based on their first appearance
    cfda_matches.sort(key=lambda x: match_order[x])
    program_funding_matches.sort(key=lambda x: match_order[x])
    
    match_on_program = pd.NA
    if len(program_funding_matches) > 0:
        match_on_program = True
    elif len(cfda_matches) > 0:
        match_on_program = False
    
    # Get unique matches in the order of their appearance
    unique_matches = list(dict.fromkeys(program_funding_matches + cfda_matches))
    
    # Add the matches and their count to new columns
    row['prog_matches'] = unique_matches
    row['n_prog_matches'] = len(unique_matches)
    row['matched_on_program'] = match_on_program
    # Prioritizes program_activities_funding_this award then cfda_title, first in list for either one
    row['program_match'] = unique_matches[0] if len(unique_matches) > 0 else pd.NA
    
    return row


df = df.apply(find_matches, axis=1)


# Produce various useful output statistics about program mapping success

print(pd.DataFrame(df[[
    'awarding_agency_name',
    'program_match'
]].value_counts(dropna=False)).sort_index(level=0))

print(df.n_prog_matches.value_counts(dropna=False))

print(df[[
    'awarding_agency_name',
    'n_prog_matches'
]].value_counts(dropna=False).unstack())

print(df.matched_on_program.value_counts())

print(df[[
    'awarding_agency_name',
    'matched_on_program'
]].value_counts().unstack())

print(df[df.n_prog_matches == 2][['awarding_agency_name', 'cfda_title', 'program_activities_funding_this_award']])


# Filter out the other grants
df.dropna(subset=['program_match'], inplace=True)


# Output to intermediate file
df.to_parquet('processed_data/mapped_grants.parquet')
