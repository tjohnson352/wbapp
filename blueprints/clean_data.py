import pandas as pd
import re
from collections import Counter

def clean_data(df1):
    # Step 1: Concatenate rows ending with a dash ('-') with the next row to handle split content
    i = 0
    while i < len(df1) - 1:
        if len(df1.loc[i, 'Content']) > 1 and df1.loc[i, 'Content'].endswith('-'):
            # Concatenate the current row's content with the next row's content
            df1.loc[i, 'Content'] += " " + df1.loc[i + 1, 'Content']
            # Mark the next row for deletion
            i += 1  # Move to the next row
        else:
            i += 1      
    
    # Step 2: Concatenate rows containing a single dash followed by rows with a time pattern
    i = 0
    while i < len(df1) - 1:
        # Find a row with a single dash
        if len(df1.iloc[i]['Content']) == 1 and df1.iloc[i]['Content'] == '-':
            # Look for the next row with a time pattern
            time_pattern = r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$'
            for j in range(i + 1, len(df1)):
                if re.match(time_pattern, df1.iloc[j]['Content']):
                    # Join rows from the one above the dash to the row with the time row
                    combined_content = ''.join(df1.iloc[i - 1:j]['Content'].values) + ' ' + df1.iloc[j]['Content']
                    df1.at[i - 1, 'Content'] = combined_content
                    # Drop rows from the dash to the time row
                    df1 = df1.drop(df1.index[i:j + 1]).reset_index(drop=True)
                    i -= 1  # Adjust index to reflect the dropped rows
                    break
        i += 1

    # Step 3: Concatenate rows with a time pattern (e.g., '##:## - ##:##') with the preceding row
    i = 1
    time_pattern = r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$'
    while i < len(df1):
        if re.match(time_pattern, df1.iloc[i]['Content']):
            # Join the current row with the preceding row
            df1.at[i - 1, 'Content'] += ' ' + df1.iloc[i]['Content']
            # Drop the current row
            df1 = df1.drop(df1.index[i]).reset_index(drop=True)
        else:
            i += 1

    ### Teacher and School Names Extraction
    ### Extract Teacher and School Names

    # Step 9: Remove rows that match the exact time pattern (e.g., #:## or ##:##)
    time_pattern = r'^\d{1,2}:\d{2}$'
    df1 = df1[~df1['Content'].str.match(time_pattern)]

    # Step 10: Identify the teacher's full name as the most repeated string in the 'Content' column
    most_common_string = ""
    most_common_string = Counter(df1['Content']).most_common(1)
    full_name = most_common_string[0][0]

    # Step 11: Split the teacher's full name into first and last name
    name_parts = full_name.split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if name_parts else ""

    # Step 12: Split rows containing fewer than 4 semicolons into multiple rows to address formatting issues
    i = 0
    while i < len(df1):
        row_content = df1.iloc[i]['Content']
        
        # Check if there are fewer than 4 semicolons in the row
        if row_content.count(';') < 4 and row_content.count(';') > 0:
            parts = row_content.split(';')
            
            # Keep the first part in the current row
            df1.iloc[i, df1.columns.get_loc('Content')] = parts[0].strip()
            
            # Insert the remaining parts as new rows below the current row
            for j, part in enumerate(parts[1:], start=1):
                new_row = pd.DataFrame({'Content': [part.strip()]})
                df1 = pd.concat([df1.iloc[:i + j], new_row, df1.iloc[i + j:]]).reset_index(drop=True)
        
        i += 1

    # Step 14: Extract the school name from rows containing 'IES'
    school_row = df1[df1['Content'].str.contains("IES", na=False)]
    if not school_row.empty:
        school_name = school_row.iloc[0]['Content'].strip()  # Get the first match and strip any leading/trailing whitespace
    else:
        school_name = ""

    return df1, full_name, first_name, last_name, school_name
