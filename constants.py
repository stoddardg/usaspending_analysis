AGENCIES = {
    'Department of Labor': 'Labor',
    'Department of Justice': 'DOJ',
    'Department of Health and Human Services': 'HHS',
    'Department of Housing and Urban Development': 'HUD',
    'Department of Education': 'DOE'
}

CITIES = [
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

PATH_TO_RAW_DATA = 'raw_data'

CLEAN_COL_NAMES = {
    'city_state': 'City',
    'program_match': 'Funding Program',
    'formatted_program_match': 'Funding Dept/Program',
    'count': 'Total # Grants',
    'count_open': '# Open Grants',
    'estimated_remaining_funds': '$ Estimated Remaining Funds',
    'total_obligated_amount': '$ Obligated Funds',
    'total_obligated_funds': '$ Obligated Funds',
    'total_estimated_remaining_funds': '$ Estimated Remaining Funds',
    'period_of_performance_start_date': 'Grant Start',
    'period_of_performance_current_end_date': 'Grant End',
    'prime_award_base_transaction_description': 'Description',
    'usaspending_permalink': 'Link',
    'awarding_agency_abbrev': 'Department',
    'awarding_agency_name': 'Department',
    'avg_funds_closest_5_fatal_shootings': 'Closest 5: Fatal Shootings',
    'avg_funds_closest_5_avg_popn': 'Closest 5: Avg Popn',
    'avg_funds_closest_5_rate_per_100k': 'Closest 5: Shootings/100k',
    'recipient_name': 'Recipient'
}


from itables import JavascriptFunction
CURRENCY_RENDER = JavascriptFunction("""
    function(data, type, row) {
        if (type === 'display') {
            return '$' + parseFloat(data).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
        }
        return data;
    }
""")