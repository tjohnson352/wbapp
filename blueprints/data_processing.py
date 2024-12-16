import pandas as pd
import re
from flask import session
from helpers.time_adjuster import time1, time4, time5, time6, time7
from helpers.assign_activity_type import assign_activity_type
from helpers.id_coding import generate_unique_id, decode_unique_id
from helpers.extract_names import get_names
from helpers.clean_raw_data import clean_data
import traceback
import inspect #  print(f" {inspect.currentframe().f_lineno}")

def structure_data():
    df1a = pd.read_json(session['df1a'])

    ### Create DataFrame df2a from Extracted Data in df1
    df2a_data = []  # New df2a DataFrame
    # Step 1: Extract rows that include teacher activities and create a new DataFrame (df2a)
    i = 0
    while i < len(df1a):
        current_row = df1a.iloc[i]['Content']
       
        # Check if the current row ends with #:##
        if pd.Series(current_row).str.match(r'.*\d:\d{2}$').any():
            # Initialize the extracted activity information
            activity = current_row
            location = ""
            year_group = ""
            # Check the row below for location data if available
            if i + 1 < len(df1a):
                next_row = df1a.iloc[i + 1]['Content']
                if not pd.Series(next_row).str.match(r'.*\d:\d{2}$').any():
                    location = next_row
            # Check the row below the location row for year group data if available
            if i + 2 < len(df1a):
                next_next_row = df1a.iloc[i + 2]['Content']
                # Ensure the length is less than 5 and follows the digit + letter pattern (e.g., 9g, 7c)
                if re.match(r'^\d+[a-zA-Z]+', next_next_row.strip()):
                    year_group = next_next_row.strip()

            # Append the extracted information to df2a_data
            
            if len(activity.strip()) > 5:  # Check if 'activities_&_time' has a length greater than 5
                df2a_data.append({'activities_&_time': activity, 'year_group': year_group, 'location': location})

        i += 1

    # Create the DataFrame df2a from the extracted data
    df2a = pd.DataFrame(df2a_data, columns=['activities_&_time', 'year_group', 'location'])
    
    # Step 2: Adjust 'year_group' and 'location' columns if needed to correct erroneous values
    for index, row in df2a.iterrows():
        if 'year_group' in df2a.columns and 'location' in df2a.columns:
            # If 'year_group' is empty but 'location' has a value, set 'year_group' to 'location'
            if row['year_group'] == "" and row['location'] != "":
                df2a.at[index, 'location'] = row['year_group']
            # If 'location' is empty but 'year_group' has a value, set 'location' to 'year_group'
            elif row['location'] == "" and row['year_group'] != "":
                df2a.at[index, 'year_group'] = row['location']

    # Step 20: Extract the activities and timespan into separate columns
    df2a['timespan'] = df2a['activities_&_time'].apply(lambda x: time5(x)[0] if time5(x) else "")
    df2a['activities'] = df2a.apply(lambda row: row['activities_&_time'].replace(row['timespan'], "").strip(), axis=1)
    df2a['timespan'] = df2a['timespan'].apply(time1)

    # Calculate minutes if necessary
    df2a['minutes'] = df2a['timespan'].apply(time4)

    # Apply helper function assign_activity_type that to assign TYPES to activities
    df2a['type'] = df2a['activities'].apply(assign_activity_type)

    # correct false BREAKS that are actually Junior School duties
    if 'type' in df2a.columns and 'minutes' in df2a.columns:
        for index, row in df2a.iterrows():
            if row['type'] == "BREAK" and row['minutes'] == 30:
                # Do not change the value
                continue
            elif row['type'] == "BREAK" and row['minutes'] != 30:
                # Change the value to GENERAL/DUTY
                df2a.at[index, 'type'] = "GENERAL/DUTY"


    # Modify activities for TEACHING rows
    df2a.loc[df2a['type'] == 'TEACHING', 'activities'] = (
        df2a.loc[df2a['type'] == 'TEACHING', 'year_group'].str.upper() + " " +
        df2a.loc[df2a['type'] == 'TEACHING', 'activities']
    )

    # Step 5: Get names and ids
    get_names()

    # Get work_percent from session
    work_percent = session.get('work_percent', 100)  # Default to 100 if not set

    # Step 6: create df2b as a selected cleaned extract of df2a
    df2b = df2a[['timespan','activities', 'type', 'minutes']].copy()
    df2b.insert(0, 'day', 'Unassigned') # adds a dummy for the dropdown menu

    return df2a, df2b