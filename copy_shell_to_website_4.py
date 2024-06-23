import os
import shutil
import re
import nbformat

# List of cities and states
cities = [
    "ATLANTA, GEORGIA",
    "WASHINGTON, DISTRICT OF COLUMBIA",
    "SAINT LOUIS, MISSOURI",
    "MEMPHIS, TENNESSEE",
    "KANSAS CITY, MISSOURI",
    "BIRMINGHAM, ALABAMA",
    "DETROIT, MICHIGAN",
    "NEW ORLEANS, LOUISIANA",
    "BALTIMORE, MARYLAND",
    "PHILADELPHIA, PENNSYLVANIA",
    "MILWAUKEE, WISCONSIN",
    "CHICAGO, ILLINOIS",
    "PHOENIX, ARIZONA",
    "GREENSBORO, NORTH CAROLINA",
    "BATON ROUGE, LOUISIANA"
]

# Current directory and file paths
home_dir = os.getcwd()
source_file = os.path.join(home_dir, "funding_report_shell_4.ipynb")
source_file_2 = os.path.join(home_dir, "city_analysis_report_shell.ipynb")
website_dir = os.path.join(home_dir, "docs")

# Ensure the website directory exists
os.makedirs(website_dir, exist_ok=True)

# City name replacements
city_replacements = {
    "washington": "washington_dc",
    "philadelphia": "philly",
    "saint_louis": "st_louis"
}


def copy_file_by_pattern(source_file, suffix):
    for city_state in cities:
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

        # os.system(f'jupyter trust {dest_file}')


copy_file_by_pattern(source_file, '2')
copy_file_by_pattern(source_file_2, 'analysis')
