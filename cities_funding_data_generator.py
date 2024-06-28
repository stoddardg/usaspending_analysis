"""
File: cities_funding_data_generator.py
Author: Oren Tirschwell
Date: 6/28/2024
Description: Provide the code to generate city funding data pages
"""

# Library Imports

import pandas as pd

from IPython.display import display, HTML, Markdown

from itables import init_notebook_mode
from itables import show
import itables.options as opt

from constants import CLEAN_COL_NAMES, CURRENCY_RENDER, AGENCIES

import re
import os
import json


init_notebook_mode(all_interactive=True)


# Global variable
counter = 0


# Wrapper function to produce the dashboard
def gen_cities_funding_page(focal_city, focal_state):
    print_introduction(focal_city)
    prep_and_print_overview_table(focal_city, focal_state)
    prep_and_print_line_item_tables(focal_city, focal_state)


def print_introduction(focal_city):
    display(Markdown("\n# Introduction"))
    analysis_page_url = f"/{focal_city.lower().replace(' ', '_').replace('saint_', 'st_').replace('philadelphia', 'philly').replace('washington', 'washington_dc')}_analysis.html"
    md_txt = f'The tables below displays grant data from USASpending.gov that may be relevant to violence prevention for **{focal_city.title()}**. To view further analysis for this city, please navigate to the [associated analysis page]({analysis_page_url}).\n\nPlease note that grants displayed on this page are limited to grant programs that were deemed to be related to violence prevention funding. For more information, see the [Methodology page](/methodology.html).'
    display(Markdown(md_txt))


def prep_and_print_overview_table(focal_city, focal_state):
    overview_table = gen_overview_table(focal_city, focal_state)
    display(Markdown('\n# Overview'))

    opt.style = 'bootstrap'  # Apply a clean style
    opt.showIndex = False
    opt.lengthMenu = [10, 25, 50]
    opt.scrollY = "700px"
    opt.scrollCollapse = True
    opt.classes = "display compact cell-border"
    opt.eval_functions = True

    display(HTML("<style>.dt-container { font-size: small; }</style>"))

    show((overview_table),
         columnDefs = [
            {"className": "dt-head-center", "targets": "_all"},
            {"className": "dt-body-center", "targets": "_all"},
            {"className": "dt-body-right", "targets": [0]},
            {"render": CURRENCY_RENDER, "targets": [3, 4]}
         ],
         lengthMenu=[20, 50, 100, -1])



def gen_overview_table(focal_city, focal_state):
    overview_df = pd.read_csv('../processed_data/city_grant_summaries.csv')[[
        'city_state',
        'formatted_program_match',
        'count',
        'count_open',
        'total_estimated_remaining_funds',
        'total_obligated_funds',
    ]].sort_values('formatted_program_match')

    overview_df = overview_df[
        (overview_df.city_state == f'{focal_city}, {focal_state}') &
        (overview_df['count'] > 0)
    ]
    return overview_df.rename(CLEAN_COL_NAMES, axis=1).drop(columns=['City'])
    

def prep_and_print_line_item_tables(focal_city, focal_state):
    line_item_table = gen_line_item_table(focal_city, focal_state)

    opt.style = "width:1100px"
    opt.autoWidth = False

    opt.columnDefs = [
        {"className": "dt-head-center", "targets": "_all"},
        {"className": "dt-body-center", "targets": [1, 2, 3, 4]},
        {"className": "dt-body-right", "targets": [0]},
        {"className": "dt-body-left", "targets": [5, 6]},
        {"render": CURRENCY_RENDER, "targets": [3, 4]}
    ]

    # Include custom CSS/JS for expand/collapse text options
    custom_css = """
    <style>
    .expandable .full-text {
        display: none;
    }
    .expandable .preview {
        display: inline;
    }
    </style>
    """

    custom_js = """
    <script>
    function toggleText(element, fullTextId, previewId, moreId, lessId) {
        var fullText = document.getElementById(fullTextId);
        var preview = document.getElementById(previewId);
        var moreLink = document.getElementById(moreId);
        var lessLink = document.getElementById(lessId);

        if (fullText.style.display === "none") {
            fullText.style.display = "inline";
            preview.style.display = "none";
            moreLink.style.display = "none";
            lessLink.style.display = "inline";
        } else {
            fullText.style.display = "none";
            preview.style.display = "inline";
            moreLink.style.display = "inline";
            lessLink.style.display = "none";
        }
    }
    </script>
    """

    display(HTML(custom_css + custom_js))

    mappings = read_mappings()

    display(Markdown('\n&nbsp;\n'))
    display(Markdown('\n\n::: {.panel-tabset}'))
    for dept_nm, programs in mappings.items():
        display(Markdown(f"\n## {AGENCIES[dept_nm]}"))
        for program in programs.keys():
            display(Markdown(f"\n### {program}"))
            show(line_item_table[line_item_table['Funding Program'] == program].drop(columns=['Funding Program', 'Department']))
    display(Markdown(':::'))
            



def gen_line_item_table(focal_city, focal_state):
    line_item_df = pd.read_parquet('../processed_data/mapped_grants.parquet')[[
        'city_state',
        'awarding_agency_name',
        'program_match',
        'recipient_name',
        'period_of_performance_start_date',
        'period_of_performance_current_end_date',
        'total_obligated_amount',
        'estimated_remaining_funds',
        'prime_award_base_transaction_description',
        'usaspending_permalink',
    ]]

    line_item_df = line_item_df[
        (line_item_df.city_state == f'{focal_city}, {focal_state}')
    ]

    line_item_df.rename(CLEAN_COL_NAMES, axis=1, inplace=True)
    
    line_item_df['Grant Start'] = pd.to_datetime(line_item_df['Grant Start']).dt.strftime('%Y-%m-%d')
    line_item_df['Grant End'] = pd.to_datetime(line_item_df['Grant End']).dt.strftime('%Y-%m-%d')

    line_item_df.Description = line_item_df.Description.apply(lambda x: make_expandable_text(x))
    line_item_df['Link'] = line_item_df.apply(
        lambda x: f'<a href="{x["Link"]}" target="_blank">Details</a>', 
        # lambda x: f'<a href="{x["Link"]}" target="_blank">Details{"*" if x["has_sub_grants"] else ""}</a>', 
        axis=1
    )

    return line_item_df.drop(columns=['City'])


def make_expandable_text(text, preview_length=150):
    global counter
    counter += 1
    
    # Remove newline characters
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= preview_length:
        return text
    
    preview = text[:preview_length]
    full_text = text
    unique_id = f"expandable-{counter}"  # Unique ID for elements
    
    return f'''<div class="expandable"><span id="preview-{unique_id}" class="preview">{preview}... </span><span id="full-{unique_id}" class="full-text" style="display:none;">{full_text} </span><a href="javascript:void(0);" id="more-{unique_id}" onclick="toggleText(this, 'full-{unique_id}', 'preview-{unique_id}', 'more-{unique_id}', 'less-{unique_id}')">More</a><a href="javascript:void(0);" id="less-{unique_id}" style="display:none;" onclick="toggleText(this, 'full-{unique_id}', 'preview-{unique_id}', 'more-{unique_id}', 'less-{unique_id}')">Less</a></div>'''


def read_mappings():
    file_path = 'program_mapping.json'

    # Check if the file exists in the current directory
    if not os.path.exists(file_path):
        # If not, navigate up one directory and redefine the file path
        file_path = os.path.join(os.pardir, 'program_mapping.json')

    with open(file_path, 'r') as file:
        mappings = json.load(file)

    return mappings
