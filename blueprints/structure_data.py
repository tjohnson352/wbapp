import pandas as pd
import re
from blueprints.clean_data import clean_data
from flask import Blueprint, request, session, jsonify, render_template
from helpers.time_adjuster import time1, time4, time5, time6, time7
from helpers.id_coding import generate_unique_id,decode_unique_id

def structure_data(df1):
    # Step 4 : Call clean_data function (see /blueprints/clean_data.py for the code)
    df1, full_name, first_name, last_name, school_name = clean_data(df1)

    ### Create DataFrame df1a from Extracted Data in df1 the code from here should move to step 20 should be moved to /blueprint/structure_data.py
    df1a_data = []  # New df1a DataFrame

    # Step 18: Extract rows that include teacher activities and create a new DataFrame (df1a)
    i = 0
    while i < len(df1):
        current_row = df1.iloc[i]['Content']
        
        # Check if the current row ends with #:##
        if pd.Series(current_row).str.match(r'.*\d:\d{2}$').any():
            # Initialize the extracted activity information
            activity = current_row
            location = ""
            year_group = ""

            # Check the row below for location data if available
            if i + 1 < len(df1):
                next_row = df1.iloc[i + 1]['Content']
                if not pd.Series(next_row).str.match(r'.*\d:\d{2}$').any():
                    location = next_row
            # Check the row below the location row for year group data if available
            if i + 2 < len(df1):
                next_next_row = df1.iloc[i + 2]['Content']
                # Ensure the length is less than 5 and follows the digit + letter pattern (e.g., 9g, 7c)
                if re.match(r'^\d+[a-zA-Z]+', next_next_row.strip()):
                    year_group = next_next_row.strip()

            # Append the extracted information to df1a_data
            df1a_data.append({'activities_&_time': activity, 'year_group': year_group, 'location': location})
        i += 1

    ## Restructuring the data from here
    # Create the DataFrame df1a from the extracted data
    df1a = pd.DataFrame(df1a_data, columns=['activities_&_time', 'year_group', 'location'])

    # Store df1a in session
    session['df1a'] = df1a.to_json()

    # Step 19: Adjust 'year_group' and 'location' columns if needed to correct erroneous values
    for index, row in df1a.iterrows():
        if 'year_group' in df1a.columns and 'location' in df1a.columns:
            # If 'year_group' is empty but 'location' has a value, set 'year_group' to 'location'
            if row['year_group'] == "" and row['location'] != "":
                df1a.at[index, 'location'] = row['year_group']
            # If 'location' is empty but 'year_group' has a value, set 'location' to 'year_group'
            elif row['location'] == "" and row['year_group'] != "":
                df1a.at[index, 'year_group'] = row['location']

    # Step 20: Extract the activities and timespan into separate columns
    df1a['timespan'] = df1a['activities_&_time'].apply(lambda x: time5(x)[0] if time5(x) else "")
    df1a['activities'] = df1a.apply(lambda row: row['activities_&_time'].replace(row['timespan'], "").strip(), axis=1)
    df1a['timespan'] = df1a['timespan'].apply(time1) 
    df1a['start_time'] = df1a['timespan'].apply(time6) 
    df1a['end_time'] = df1a['timespan'].apply(time7) 
    df1a['minutes'] = df1a['timespan'].apply(time4) 

    # Define the mapping of substrings to types
    substring_type_mapping = [
        ('meet', 'GENERAL/DUTY'),
        ('tutorial', 'GENERAL/DUTY'),
        ('break', 'BREAK'),
        ('Mentor', 'GENERAL/DUTY'),
        ('cover', 'TEACHING'),
        ('sub', 'TEACHING'),
        ('hall', 'GENERAL/DUTY'),
        ('lunch','GENERAL/DUTY')
    ]

    # Function to determine the type based on the substring
    def assign_type(activity):
        for substring, activity_type in substring_type_mapping:
            if substring.lower() in activity.lower():
                return activity_type
        return 'TEACHING'

    # Apply the function to create the new 'type' column
    df1a['type'] = df1a['activities'].apply(assign_type)

    unique_id = generate_unique_id(full_name)
    decode_id = decode_unique_id(unique_id)

    df1b = pd.DataFrame({
        'id': [unique_id],
        'decode': [decode_id],
        'school_name': [school_name],
        'full_name': [full_name],
        'first_name': [first_name],
        'last_name': [last_name]
    })
    return df1a, df1b
