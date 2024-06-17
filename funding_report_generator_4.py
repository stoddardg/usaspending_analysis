import pandas as pd
import numpy as np

from IPython.display import display, HTML, Markdown

from itables import init_notebook_mode, JavascriptFunction
from itables import show
import itables.options as opt

import re
import os
import json


init_notebook_mode(all_interactive=True)
counter = 0

# A subset of columns to show in our output tables
display_cols = [
    'Recipient',
    'Grant Start',
    'Grant End',
    # 'Active',
    'Total $',
    'Remaining $',
    'Description',
    'Link'
]

agencies = {
    'Department of Labor': 'Labor',
    'Department of Justice': 'DOJ',
    'Department of Health and Human Services': 'HHS',
    'Department of Housing and Urban Development': 'HUD',
    'Department of Education': 'DOE'
}

currency_render = JavascriptFunction("""
    function(data, type, row) {
        if (type === 'display') {
            return '$' + parseFloat(data).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
        }
        return data;
    }
""")


def filter_to_city(df, city, state):
    return df[(df['primary_place_of_performance_city_name'] == city) & (df['primary_place_of_performance_state_name'] == state)].reset_index(drop=True)


def read_data(focal_city, focal_state):
    file_path = 'clean_data/clean_all_dept_all_contracts_all_cols.parquet'

    # Check if the file exists in the current directory
    if not os.path.exists(file_path):
        # If not, navigate up one directory and redefine the file path
        file_path = os.path.join(os.pardir, 'clean_data', 'clean_all_dept_all_contracts_all_cols.parquet')

    # Read the parquet file
    all_data = pd.read_parquet(file_path)

    df = filter_to_city(all_data, focal_city, focal_state)

    df.sort_values(by='period_of_performance_current_end_date', ascending=False, inplace=True)

    df.dropna(subset=['program_match'], inplace=True)
    df = df[
        (df.total_obligated_amount > 0)
    ]

    return df

    
def gen_summary_table(df):
    grant_summary_table = df.groupby(['awarding_agency_name', 'program_match']).agg(
        count = ('program_match','size'),
        count_open  = ('grant_is_open','sum'),
        total_estimated_remaining_funds = ('estimated_remaining_funds','sum'),
        total_obligated_funds = ('total_obligated_amount','sum')
    ).reset_index()

    def gen_new_program_match(row):
        return f'{agencies[row.awarding_agency_name]} - {row.program_match}'
    

    grant_summary_table.program_match = grant_summary_table.apply(gen_new_program_match, axis=1)

    # Move the "Other" row to the bottom
    other_rows = grant_summary_table[grant_summary_table['program_match'] == 'DOJ - Other']
    non_other_rows = grant_summary_table[grant_summary_table['program_match'] != 'DOJ - Other']

    # Concatenating with "Other" rows at the bottom
    grant_summary_table = pd.concat([non_other_rows, other_rows], ignore_index=True)

    return grant_summary_table.drop('awarding_agency_name', axis=1)


def snake_to_title(snake_str):
    """Convert snake_case string to Title Case."""
    return ' '.join(word.capitalize() for word in snake_str.split('_'))


def convert_columns_to_title_case(df):
    """Convert DataFrame column headers from snake case to title case."""
    df.columns = [snake_to_title(col) for col in df.columns]
    return df


def show_summary_table(df):
    opt.style = 'bootstrap'  # Apply a clean style
    opt.showIndex = False
    opt.lengthMenu = [10, 25, 50]
    opt.scrollY = "700px"
    opt.scrollCollapse = True
    opt.classes = "display compact cell-border"
    opt.eval_functions = True

    display(HTML("<style>.dt-container { font-size: small; }</style>"))

    show(convert_columns_to_title_case(gen_summary_table(df)),
         columnDefs = [
            {"className": "dt-head-center", "targets": "_all"},
            {"className": "dt-body-center", "targets": "_all"},
            {"className": "dt-body-right", "targets": [0]},
            {"render": currency_render, "targets": [3, 4]}
         ],
         lengthMenu=[20, 50, 100, -1])
    

# Format helper methods

def highlight_rows(s):
    return ['font-weight: bold' if s['Active'] == True else '' for _ in s]


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


def prep_line_item_dta(df):
    # Data formatting

    # Rename poorly named columns
    rename_cols = {
        'recipient_name':'Recipient',
        'period_of_performance_start_date':'Grant Start',
        'period_of_performance_current_end_date':'Grant End',
        'grant_is_open':'Active',
        'total_obligated_amount':'Total $',
        'estimated_remaining_funds':'Remaining $',
        'prime_award_base_transaction_description':'Description',
        'usaspending_permalink':'Link'
    }
    line_item_df = df.rename(columns=rename_cols).reset_index(drop=True)

    # Convert descriptions to be sentence case, recipients to be title case
    line_item_df['Description'] = line_item_df['Description'].apply(lambda x: x.capitalize())
    line_item_df['Recipient'] = line_item_df['Recipient'].apply(lambda x: x.title())

    # OREN TODO: Check NAs and infinity
    # Convert any numerical columns to currency format
    # for col in line_item_df.select_dtypes(include=['float', 'int']).columns:
    #     line_item_df[col] = line_item_df[col].apply(lambda x: f"${x:,.0f}")

    # Convert to hyperlinks
    line_item_df['Link'] = line_item_df.apply(
        lambda x: f'<a href="{x["Link"]}" target="_blank">Details{"*" if x["has_sub_grants"] else ""}</a>', 
        axis=1
    )


    # Make descriptions expandable
    line_item_df.Description = line_item_df.Description.apply(lambda x: make_expandable_text(x))

    # Format two date columns
    line_item_df['Grant Start'] = pd.to_datetime(line_item_df['Grant Start']).dt.strftime('%Y-%m-%d')
    line_item_df['Grant End'] = pd.to_datetime(line_item_df['Grant End']).dt.strftime('%Y-%m-%d')

    return line_item_df


def prep_table_disp_options():
    # Set itables options for remaining tables

    opt.style = "width:1100px"
    # opt.scrollX = True
    opt.autoWidth = False

    opt.columnDefs = [
        {"className": "dt-head-center", "targets": "_all"},
        {"className": "dt-body-center", "targets": [1, 2, 3, 4]},
        {"className": "dt-body-right", "targets": [0]},
        {"className": "dt-body-left", "targets": [5, 6]},
        {"render": currency_render, "targets": [3, 4]}
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


# Functions for showing the program dataframe
def highlight_rows_without_active(index, line_item_df):
    if line_item_df.loc[index, 'Active'] == True:
        return ['font-weight: bold' for _ in range(len(display_cols))]
    else:
        return ['' for _ in range(len(display_cols))]


def show_prog_df(line_item_df, prog_nm):
    df_to_disp = line_item_df.copy()
    df_to_disp = df_to_disp[df_to_disp['program_match'] == prog_nm]
    
    # styled_df = df_to_disp.style.apply(highlight_rows, axis=1)
    # df_without_active = df_to_disp[display_cols]
    # styled_df_without_active = df_without_active.style.apply(lambda x: highlight_rows_without_active(x.name), axis=1)
    
#     styled_df_without_active.set_table_styles(
#         [
#             {"selector": "table", "props": [("width", "100%")]},
#             {"selector": "th, td", "props": [("padding", "8px")]},
#         ]
#     )
    
#     show(styled_df_without_active.hide_index())

    show(df_to_disp[display_cols])