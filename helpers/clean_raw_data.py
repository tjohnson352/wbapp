import pandas as pd
import re
from collections import Counter

def clean_data(df1a):
    # Step 0: Remove rows made up of just two digits
    df1a = df1a[~df1a['Content'].str.match(r'^\d{2}$')].reset_index(drop=True)
    # Ensure only the 'Content' column is used and reset the index
    df1a = df1a[['Content']]
    df1a.reset_index(drop=True, inplace=True)
    
    # Step 0.5: Concatenate rows where the first substring is "Time" with the preceding row
    i = 1  # Start from the second row
    while i < len(df1a):
        if df1a.iloc[i]['Content'].startswith("Time"):
            # Join the current row with the preceding row
            df1a.at[i - 1, 'Content'] += ' ' + df1a.iloc[i]['Content']
            # Drop the current row
            df1a = df1a.drop(df1a.index[i]).reset_index(drop=True)
        else:
            i += 1

    # Step 1a: Concatenate rows ending with a dash ('-') with the next row to handle split content
    i = 0
    while i < len(df1a) - 1:
        if len(df1a.loc[i, 'Content']) > 1 and df1a.loc[i, 'Content'].endswith('-'):
            # Concatenate the current row's content with the next row's content
            df1a.loc[i, 'Content'] += " " + df1a.loc[i + 1, 'Content']
            # Mark the next row for deletion
            i += 1  # Move to the next row
        else:
            i += 1     

    # Step 1b: Concatenate rows starting with a dash ('-') with the preceding row to handle split content
    i = 1  # Start from the second row to avoid index out of range error
    while i < len(df1a):
        if len(df1a.loc[i, 'Content']) > 1 and df1a.loc[i, 'Content'].startswith('-'):
            # Concatenate the current row's content with the previous row's content using " - " as a joiner
            df1a.loc[i - 1, 'Content'] += " - " + df1a.loc[i, 'Content'].lstrip('-').strip()
            # Mark the current row for deletion
            df1a = df1a.drop(index=i).reset_index(drop=True)
          
        else:
            i += 1  # Move to the next row
        
    # Step: Concatenate rows that are exactly "Junior" or "Break" with the next row
    i = 0  # Start from the first row
    while i < len(df1a) - 1:  # Ensure we don't go out of range
        # Check if the current row is exactly "Junior" or "Break"
        if df1a.loc[i, 'Content'].strip() in ["Lunch", "Junior"]:
            # Concatenate the current row's content with the next row's content
            df1a.loc[i, 'Content'] += " " + df1a.loc[i + 1, 'Content']
            # Drop the next row and reset the index
            df1a = df1a.drop(index=i + 1).reset_index(drop=True)
        else:
            i += 1  # Move to the next row
        
    # Step 2: Concatenate rows containing a single dash followed by rows with a time pattern
    i = 0
    while i < len(df1a) - 1:
        # Find a row with a single dash
        if len(df1a.iloc[i]['Content']) == 1 and df1a.iloc[i]['Content'] == '-':
            # Look for the next row with a time pattern
            time_pattern = r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$'
            for j in range(i + 1, len(df1a)):
                if re.match(time_pattern, df1a.iloc[j]['Content']):
                    # Join rows from the one above the dash to the row with the time row
                    combined_content = ''.join(df1a.iloc[i - 1:j]['Content'].values) + ' ' + df1a.iloc[j]['Content']
                    df1a.at[i - 1, 'Content'] = combined_content
                    # Drop rows from the dash to the time row
                    df1a = df1a.drop(df1a.index[i:j + 1]).reset_index(drop=True)
                    i -= 1  # Adjust index to reflect the dropped rows
                    break
        i += 1

    # Step 3: Concatenate rows with a time pattern (e.g., '##:## - ##:##') with the preceding row
    i = 1
    time_pattern = r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$'
    while i < len(df1a):
        if re.match(time_pattern, df1a.iloc[i]['Content']):
            # Join the current row with the preceding row
            df1a.at[i - 1, 'Content'] += ' ' + df1a.iloc[i]['Content']
            # Drop the current row
            df1a = df1a.drop(df1a.index[i]).reset_index(drop=True)
        else:
            i += 1

    return df1a
