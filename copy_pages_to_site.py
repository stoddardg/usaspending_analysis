"""
File: copy_pages_to_site.py
Author: Oren Tirschwell
Date: 6/28/2024
Description: Copy our two shell pages to the website for running with quarto
"""

# Import libraries and constants
import os
import shutil
import re
import nbformat

from constants import CITIES

# Current directory and file paths
home_dir = os.getcwd()
source_file = os.path.join(home_dir, 'cities_funding_data_shell.ipynb')
source_file_2 = os.path.join(home_dir, 'cities_analysis_shell.ipynb')
website_dir = os.path.join(home_dir, 'docs')

# Ensure the website directory exists
os.makedirs(website_dir, exist_ok=True)

# City name replacements
city_replacements = {
    'washington': 'washington_dc',
    'philadelphia': 'philly',
    'saint_louis': 'st_louis'
}


def copy_file_by_pattern(source_file, suffix):
    for city_state in CITIES:
        # Split city and state
        city, state = city_state.split(", ")
        
        # Make city name lowercase
        city_lower = city.lower().replace(' ', '_')
        
        # Apply specific city name replacements
        city_lower = city_replacements.get(city_lower, city_lower)
        
        # Destination file path
        dest_file = os.path.join(website_dir, f"{city_lower}_{suffix}.ipynb")
        
        # Copy and rename the file
        shutil.copy2(source_file, dest_file)
        
        # Read the copied file content
        with open(dest_file, 'r', encoding='utf-8') as file:
            notebook = nbformat.read(file, as_version=4)

        for cell in notebook.cells:
            if cell.cell_type == 'markdown':
                # Replace title in markdown cells
                cell.source = cell.source.replace('title: "Chicago"', f'title: "{city.title()}"')
            elif cell.cell_type == 'code':
                # Replace focal_city and focal_state in code cells
                cell.source = re.sub(r"focal_city = 'CHICAGO'", f"focal_city = '{city.upper()}'", cell.source)
                cell.source = re.sub(r"focal_state = 'ILLINOIS'", f"focal_state = '{state.upper()}'", cell.source)
        
        # Write the modified notebook back to the file
        with open(dest_file, 'w', encoding='utf-8') as file:
            nbformat.write(notebook, file)

        os.system(f'jupyter trust {dest_file}')


copy_file_by_pattern(source_file, 'funding')
copy_file_by_pattern(source_file_2, 'analysis')
