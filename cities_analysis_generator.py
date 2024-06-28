"""
File: cities_analysis_generator.py
Author: Oren Tirschwell
Date: 6/28/2024
Description: Provide the code to generate city analysis data pages
"""

# Library Imports

import pandas as pd
import numpy as np

from IPython.display import display, Markdown, HTML

from itables import init_notebook_mode, JavascriptFunction, show
import itables.options as opt

from constants import CLEAN_COL_NAMES, CURRENCY_RENDER, CITIES

import plotly.express as px
import plotly.graph_objects as go


init_notebook_mode(all_interactive=True)


# Global variable
depts = ['All', 'DOE', 'DOJ', 'HUD', 'Labor']


# Wrapper function to produce the dashboard
def gen_cities_funding_page(focal_city, focal_state):
    print_introduction(focal_city)
    focal_point = f'{focal_city}, {focal_state}'
    prep_and_output_comparison_graphs(focal_point)
    prep_and_output_dept_overview_table(focal_point, focal_city)
    prep_and_output_dept_detailed_grant_tables(focal_point)



def print_introduction(focal_city):
    display(Markdown("\n# Introduction"))
    md_txt = f'Welcome to the city comparison view of USASpending.gov data, that may be relevant to violence prevention for **{focal_city.title()}**. Please note that grants displayed on this page are limited to grant programs that were deemed to be related to violence prevention funding. For more information, see the [Methodology page](/methodology.html).'
    display(Markdown(md_txt))


def prep_and_output_comparison_graphs(focal_point):
    comparison_table = pd.read_csv('../processed_data/city_dept_summaries.csv')
    display(Markdown('\n# Violence Prevention Funding vs Annual Fatal Shootings, Comparison\n\nThis display may serve as a comparison to see funding amounts for the current city (in blue) vs other cities (in green).\n\n:::{.panel-tabset group="Funding Dept"}'))
    for dept in depts:
        display(Markdown(f'\n### {dept}'))
        curr_df = comparison_table[
            (comparison_table.awarding_agency_abbrev == dept)
        ]
        gen_funding_shooting_scatter_plot(curr_df, focal_point)
    
    display(Markdown('\n:::'))


def gen_funding_shooting_scatter_plot(df, focal_point):
    plot_df = df[df.city_state.isin(CITIES)].copy().rename({
        'fatal_shootings': 'Annual Fatal Shootings', 
        'avg_popn': 'Avg Population',
        'total_obligated_funds': 'Funding'
    }, axis=1)

    plot_df['Formatted Population'] = plot_df['Avg Population'].apply(lambda x: f"{x:,}")
    plot_df['Formatted Funding'] = plot_df['Funding'].apply(lambda x: f"${x:,.0f}")
    plot_df['Formatted Funding Per Shooting'] = plot_df['cvi_funding_per_hom'].apply(lambda x: f"${x:,.0f}")
    
    plot_df['color'] = plot_df['city_state'].apply(lambda x: 'blue' if x == focal_point else '#4BBF73')
    
    # Create the main scatter plot
    fig = px.scatter(plot_df, 
                    y='Funding', 
                    x='Annual Fatal Shootings', 
                    size='Avg Population',
                    color_discrete_sequence=['#4BBF73'],
                    hover_name='city_state',
                    hover_data={
                        'Formatted Funding': True, 
                        'Annual Fatal Shootings': True, 
                        'Formatted Population': True, 
                        'Formatted Funding Per Shooting': True,
                        'color': False,  # Ensure 'color' is not included in hover data
                    })
    
    fig.update_traces(hovertemplate='<b>%{hovertext}</b><br>' +
                                    'Violence Prevention Funding: %{customdata[0]}<br>' +
                                    'Annual Fatal Shootings: %{x}<br>' +
                                    'Violence Prevention Funding Per Shooting: %{customdata[2]}<br>' +
                                    'Population: %{customdata[1]}')

    # Add a hidden scatter plot to hold the color values
    fig.add_trace(go.Scatter(
        x=plot_df['Annual Fatal Shootings'],
        y=plot_df['Funding'],
        mode='markers',
        marker=dict(color=plot_df['color'], size=np.sqrt(plot_df['Avg Population']) / 55),
        hoverinfo='skip',  # Skip hover info for this trace
        showlegend=False
    ))

    fig.update_layout(xaxis_title='Annual Fatal Shootings',
                      yaxis_title='Violence Prevention Funding',
                      width=750,
                      showlegend=False)
    
    fig.show()


def prep_and_output_dept_overview_table(focal_point, focal_city):
    comparison_table = pd.read_csv('../processed_data/city_dept_summaries.csv')
    comparison_table = comparison_table[comparison_table.city_state == focal_point][[
        'awarding_agency_abbrev',
        'total_obligated_funds',
        'avg_funds_closest_5_avg_popn',
        'avg_funds_closest_5_fatal_shootings',
        'avg_funds_closest_5_rate_per_100k'
    ]].sort_values('awarding_agency_abbrev')

    created_cell_js = JavascriptFunction("""
        function (td, cellData, rowData, row, col) {
            var fundingPerHomicide = rowData[1];
            var fatalShootings = rowData[2];
            if (col === 1) {
                if (fundingPerHomicide < fatalShootings) {
                    $(td).css('background-color', '#ffabab');
                } else {
                    $(td).css('background-color', 'lightgreen');
                }
            }
        }
    """)

    opt.style = 'bootstrap'  # Apply a clean style
    opt.showIndex = False
    opt.lengthMenu = [25, 50, 100]
    opt.scrollCollapse = True
    opt.classes = "display compact cell-border"
    opt.eval_functions = True

    display(HTML("<style>.dt-container { font-size: small; }</style>"))

    opt.columnDefs = [
        {"className": "dt-head-center", "targets": "_all"},
        {"className": "dt-body-center", "targets": [1, 2, 3, 4]},
        {"className": "dt-body-right", "targets": [0]},
        {
            "targets": [1, 2, 3, 4],  # Apply to specific columns
            "render": CURRENCY_RENDER,
            "createdCell": created_cell_js,
        }
    ]

    display(Markdown('\n# City Comparisons\n\nHere, we display each individual department and then grant source, and its total funding value. Then, we look at the total funding value for the closest 5 cities (absolute distance) via three metrics: average population, number of fatal shootings, and number of shootings per 100k residents.'))
    gun_df = pd.read_pickle('../processed_data/cleaned_gun_data.pkl')
    closest_metrics = gun_df[gun_df.city_state == focal_point]
    closest_cities = closest_metrics.closest_5_fatal_shootings.iloc[0]
    display(Markdown(f'\n\nFor example, the closest 5 cities by population to {focal_city.title()} (which had a population of {format(round(closest_metrics.avg_popn.iloc[0]), ",")} people) were:\n\n'))

    for city in closest_cities:
        n_shootings = gun_df[gun_df.city_state == city].fatal_shootings.iloc[0]
        n_people = gun_df[gun_df.city_state == city].avg_popn.iloc[0]
        display(Markdown(f'\n- {city.title()} ({format(n_people, ",")} people)'))

    display(Markdown(f'\n\nFor the closest cities by population, we show in red the categories where {focal_city.title()} is relatively under-funded, and in green, those where it is relatively over-funded.'))
    display(Markdown('\n\n## Department Overview'))
    
    show(comparison_table.rename(CLEAN_COL_NAMES, axis=1))


def prep_and_output_dept_detailed_grant_tables(focal_point):
    comparison_table = pd.read_csv('../processed_data/city_grant_summaries.csv')
    comparison_table = comparison_table[comparison_table.city_state == focal_point][[
        'awarding_agency_abbrev',
        'program_match',
        'formatted_program_match',
        'total_obligated_funds',
        'avg_funds_closest_5_avg_popn',
        'avg_funds_closest_5_fatal_shootings',
        'avg_funds_closest_5_rate_per_100k'
    ]].sort_values('formatted_program_match')

    display(Markdown('\n\n## Grant-Level Analysis\n\n:::{.panel-tabset group="Funding Dept"}'))

    opt.style = "width:855px"
    opt.autoWidth = False
    opt.scrollY = "1500px"

    comparison_table.rename(CLEAN_COL_NAMES, axis=1, inplace=True)
    for dept in depts:
        display(Markdown(f'\n\n### {dept}'))
        if (dept == 'All'):
            show(comparison_table.drop(columns=['Department', 'Funding Program']))
        else:
            show(comparison_table[comparison_table.Department == dept].drop(columns=['Department', 'Funding Dept/Program']))
    display(Markdown(':::'))