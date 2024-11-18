import pandas as pd
from collections import Counter
import re  # To help with regex matching for time format
from datetime import datetime
import numpy as np
 
def clean_data(df1):
    
    # STEP 1: Form df5 with the extracted teacher and school name
    metadata = extract_name_metadata(df1)

    df5 = pd.DataFrame({
        'school': [metadata['school_name']],
        'first_name': [metadata['teacher_first_name']],
        'last_name': [metadata['teacher_last_name']]
    })

    # Step 2: Form df2 as the place to process the data from df1
    df2 = df1.rename(columns={'Content': 'data'}).copy()

    # Step 3: Process df2 to add time, lone_dash, end_dash, start_end, joined_activities, and activities columns
    df2 = process_df2(df2)

    # Step 4: Add year_group column to df2
    df2 = add_year_group_column(df2)

    # Step 5: Create df3 which contains structured data from the 'activities' column of df2 (excluding empty rows)
    df3 = df2[['activities']].copy()
    df3 = df3[df3['activities'] != ""]  # Exclude empty rows in 'activities'


    # Split the 'activities' column into activity name and time span
    activity_names = []
    year_group_codes = []  # Initialize as a list
    start_times = []
    end_times = []
    minutes = []

    # Iterate through each row in df3 to split activity, start time, end time, and calculate minutes
    for idx, row in df3.iterrows():
        activity = row['activities']
        # Use regex to find the time span pattern
        match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', activity)
        if match:
            # Extract start time, end time, activity name, and year_group
            start_time = match.group(1)
            end_time = match.group(2)
            activity_name = activity[:match.start()].strip()
            year_group = df2.loc[idx, 'year_group'] if 'year_group' in df2.columns else ""  # Extract the year_group

            # Calculate the time span in minutes
            if start_time and end_time:
                start_hours, start_minutes = map(int, start_time.split(":"))
                end_hours, end_minutes = map(int, end_time.split(":"))
                start_total_minutes = start_hours * 60 + start_minutes
                end_total_minutes = end_hours * 60 + end_minutes
                duration_minutes = max(0, end_total_minutes - start_total_minutes)  # Avoid negative durations
            else:
                duration_minutes = None
        else:
            # If no time span is found, keep the whole activity as name and leave times empty
            activity_name = activity
            start_time = ""
            end_time = ""
            duration_minutes = None
            year_group = ""  # Default value for year_group if no match

        activity_names.append(activity_name)
        year_group_codes.append(year_group)  # Append to the corrected list
        start_times.append(start_time)
        end_times.append(end_time)
        minutes.append(duration_minutes)

    # Add the split data back into df3
    df3['activities'] = activity_names
    df3['year_group'] = year_group_codes
    df3['start'] = start_times
    df3['end'] = end_times
    df3['minutes'] = minutes

    # Replace empty strings in 'start' with NaT for proper sorting
    df3['start'] = df3['start'].replace("", np.nan)

    # Convert 'start' column to datetime for proper sorting
    df3['start'] = pd.to_datetime(df3['start'], format='%H:%M', errors='coerce')

    # Sort by activities first and then by start time
    df3 = df3.sort_values(by=['activities', 'start'], ascending=[True, True]).reset_index(drop=True)

    # Convert 'start' back to string for display purposes
    df3['start'] = df3['start'].dt.strftime('%H:%M').fillna("")

    # Reset index to keep the dataframe clean
    df3.reset_index(drop=True, inplace=True)

    # Add the "type" column in position 1 in
    df3.insert(
        1,  # Position to insert the new column
        'type',  # Name of the new column
        df3.apply(
            lambda row: (
                "BREAK" if row['activities'].strip().lower() == "break"
                else "TEACHING" if isinstance(row['year_group'], str) and row['year_group'].strip()
                and not any(keyword in row['activities'].strip().lower() for keyword in ["mentor", "lunch"])
                else "OTHER"
            ),
            axis=1
        )
    )
    df3['activities'] = df3['activities'].apply(
    lambda x: re.sub(r'(?i)\blunch\b', 'Lunch Duty', x) if isinstance(x, str) else x
)
    df3.loc[df3['type'] == "BREAK", 'year_group'] = ""
    df3.loc[df3['activities'].str.contains(r'cover|subbing', case=False, na=False), 'type'] = "SUBBING"

    return df2, df5, df3


def process_df2(df2):
    # Step 5: Iterate through "data" and populate the new columns based on conditions
    df2.rename(columns={'Content': 'data'}, inplace=True)
    df2['time'] = ""
    df2['lone_dash'] = ""
    df2['end_dash'] = ""
    df2['activities'] = ""
    df2['year_group'] = ""

    # Populate time, lone_dash, and end_dash columns
    temp_data = []
    result = []
    for idx, row in df2.iterrows():
        data_value = row['data'].strip()  # Ignore white space

        # Initialize variables to define the relative row position
        above = ""
        below = ""
        second_below = ""

        # Check if the value is in a time span format (e.g., "08:30 - 13:00", "8:00-9:00")
        if re.match(r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$', data_value):
            df2.at[idx, 'time'] = data_value  # Assign the matched value to 'time'
            above = df2.at[idx - 1, 'data'] # Get the value of the row above                
            concatenated_value = f"{above} {data_value}".strip() # Concatenate above and current row

            # Replace the row above with the concatenated value
            df2.at[idx - 1, 'data'] = concatenated_value
                
    for idx, row in df2.iterrows():
        data_value = row['data'].strip()  # Ignore white space                
                
        # Check if the value is a lone dash "-"
        if data_value == '-':
            df2.at[idx, 'lone_dash'] = 'lone_dash'

            # Get the row above and below, and second row below
            above = df2.at[idx - 1, 'data'] if idx > 0 else ""  # Get the row above if exists
            below = df2.at[idx + 1, 'data'] if idx + 1 < len(df2) else ""  # Get the row below if exists
            second_below = df2.at[idx + 2, 'data'] if idx + 2 < len(df2) else ""  # Get the second row below if exists

            # Check if the row below matches the time format and is at least 11 characters long
            if len(data_value) >= 11 and re.search(r'\d{1,2}:\d{2}$', data_value.strip()):  # Time format at the end
                jointed_text = f"{above}{below}".strip()  # Concatenate above and below with a space
            else:
                jointed_text = f"{above} {below}{second_below}".strip()  # Concatenate above, below, and second below

            # Record the joined text in "jointed-activities"
            df2.at[idx, 'activities'] = jointed_text
            df2.at[idx + 2, 'data'] = ""
        else:
            # Leave blank if no row above or below
            df2.at[idx, 'activities'] = ""

    for idx, row in df2.iterrows():
        data_value = row['data'].strip()  # Ignore white space 
        
        # Check if the value ends with a dash and is more than one character
        if len(data_value) > 1 and data_value.endswith('-') and idx + 1 < len(df2):
            # Mark the current row with 'end_dash'
            df2.at[idx, 'end_dash'] = 'end_dash'

            # Concatenate current row's 'data' with the next row's 'data'
            next_data = df2.at[idx + 1, 'data'].strip() if pd.notna(df2.at[idx + 1, 'data']) else ""
            joined_text = f"{data_value} {next_data}"

            # Record the joined text in the 'activities' column of the current row
            df2.at[idx, 'activities'] = joined_text

        # Check if the value ends with a time format and length is greater than 11
        if len(data_value) > 11 and re.search(r'\d{1,2}:\d{2}$', data_value):
            df2.at[idx, 'activities'] = data_value
    
    for idx, row in df2.iterrows():
        data_value = row['data'].strip()  # Ignore white space
        activities_value = row['activities'].strip() if 'activities' in row and pd.notna(row['activities']) else ""

        # Check if the first two characters of the activities column are digits or a digit and a colon
        if activities_value[:2].isdigit() or (len(activities_value) >= 2 and activities_value[0].isdigit() and activities_value[1] == ':'):
            if idx > 0:  # Ensure there is a previous row to reference
                df2.at[idx, 'activities'] = f"{df2.at[idx - 1, 'data']} {activities_value}"

    return df2

def add_year_group_column(df2):

    # Use iloc for position-based indexing
    for idx in range(len(df2) - 2):  # Stop iteration 2 rows before the end
        # Check if the 'activities' column has a valid string for the current row
        activities_value = df2.iloc[idx]['activities'] if 'activities' in df2.columns else None
        if not isinstance(activities_value, str) or not activities_value.strip():
            continue  # Skip rows without a valid string in 'activities'

        # Get the value from the second row below
        data_value = df2.iloc[idx + 2]['data'] if 'data' in df2.columns else None

        # Ensure the value exists, is a string, and is 5 characters or less
        if isinstance(data_value, str) and pd.notna(data_value) and len(data_value) <= 5:
            data_value = data_value.strip()  # Remove leading and trailing whitespace

            # Check if it matches the year_group_code pattern (digit 4-9 followed by a-g)
            if re.match(r'^[4-9][a-gA-G]', data_value):
                df2.iloc[idx, df2.columns.get_loc('year_group')] = data_value[:2].upper()  # Record the year_group_code
        
    # Iterate through rows, excluding the last row to avoid index out-of-range errors
    for idx in range(len(df2) - 1):
        # Check if the current row has a valid activities string
        activities_value = df2.iloc[idx]['activities'].strip() if 'activities' in df2.columns and pd.notna(df2.iloc[idx]['activities']) else ""
        if not activities_value:  # Skip rows without valid activities
            continue

        # Get the data value from the row below
        data_value = df2.iloc[idx + 1]['data'].strip() if 'data' in df2.columns and pd.notna(df2.iloc[idx + 1]['data']) else ""

        # Check if the data_value contains a semicolon and split it
        if ";" in data_value:
            parts = [part.strip() for part in data_value.split(";")]  # Split by ";" and strip whitespaces
            if len(parts) > 1:  # Ensure there is a second part
                second_part = parts[1]

                # Validate if the second part matches the year_group pattern (digit 4-9 followed by a-g)
                if re.match(r'^[4-9][a-gA-G]', second_part):
                    df2.iloc[idx, df2.columns.get_loc('year_group')] = second_part.upper()  # Record as year_group
    
    return df2


def extract_name_metadata(df1):
    """
    Extracts the teacher's full name, first name, last name, and school name
    from the provided DataFrame.
    """
    # Extract the teacher's full name
    filtered_texts = [
        text for text in df1['Content']
        if len(text.split()) >= 2 and len(text) >= 6
    ]
    teacher_full_name = Counter(filtered_texts).most_common(1)[0][0] if filtered_texts else ""

    # Split the full name into first and last names
    name_parts = teacher_full_name.split()
    teacher_first_name = name_parts[0] if name_parts else ""
    teacher_last_name = name_parts[-1] if name_parts else ""

    # Extract the school name
    matches = df1[df1['Content'].str.contains(r'\bIES ', na=False)]
    school_name = matches.iloc[0]['Content'].strip() if not matches.empty else ""

    return {
        "teacher_full_name": teacher_full_name,
        "teacher_first_name": teacher_first_name,
        "teacher_last_name": teacher_last_name,
        "school_name": school_name
    }
