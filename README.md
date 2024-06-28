# USA Spending Analysis

## Repo Structure

#### Data Prep Steps

To produce the website, you must run all of the following files, in order. No modifications to file settings or paths should be needed, and all dependent directories will be created by these scripts.

1. Run [merge_clean_grant_data.py](merge_clean_grant_data.py); produces `processed_data/merged_cleaned_grants.parquet`
2. Run [match_grant_programs.py](match_grant_programs.py); produces `processed_data/mapped_grants.parquet`. Filters out any non-program match grants.
3. Run [process_analyze_gun_data.py](process_analyze_gun_data.py); produces `processed_data/cleaned_gun_data.pkl`
4. Run [city_grant_summaries.py](city_grant_summaries.py); produces `processed_data/city_grant_summaries.csv` and `processed_data/city_dept_summaries.csv`.
5. Run [copy_pages_to_site.py](copy_pages_to_site.py)
6. Finally, `cd` into `docs` and run `quarto render --execute` to render the website live.


#### Additional Files

- [constants.py](constants.py) contains constant variables used across multiple scripts.
- [program_mapping.json](program_mapping.json) contains our high-level Violence Prevention Related programs, and the associated `program_activities_funding_this_award` and `cfda_title` values.
- [cities_funding_data_generator.py](cities_funding_data_generator.py) is used to generate the cities funding pages
- [cities_analysis_generator.py](cities_analysis_generator.py) is used to generate the cities analysis pages
- [cities_funding_data_shell.ipynb](cities_funding_data_shell.ipynb) represents the shell of the city funding pages
- [cities_analysis_shell.ipynb](cities_analysis_shell.ipynb) represents the shell of the analysis pages


## Environment Setup

This repository was run using Python 3.7 and the Python packages in a conda environment shown in [requirements.txt](requirements.txt).