import pandas as pd
from flask import session, current_app
from io import StringIO

def pre_gaps(df):
    """
    Adds a "Pre Gap" row before each row where the 'type' column equals 'TEACHING'.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.

    Returns:
    pd.DataFrame: The modified DataFrame with gaps added.
    """
    rows_with_gaps = []

    for _, row in df.iterrows():
        # Check if the 'type' column is 'TEACHING'
        if row['type'] == 'TEACHING':
            # Calculate the Pre Gap timespan
            if pd.notnull(row['timespan']) and '-' in row['timespan']:
                start_time, end_time = row['timespan'].split('-')
                start_time = pd.to_datetime(start_time.strip(), format='%H:%M')
                pre_gap_end = start_time - pd.Timedelta(minutes=5)
                timespan = f"{pre_gap_end.strftime('%H:%M')} - {start_time.strftime('%H:%M')}"
            else:
                timespan = "N/A"

            # Create a Pre Gap row
            pre_gap_row = {
                'day': row['day'],
                'activities': 'Pre Gap',
                'type': 'LESSON GAP',
                'timespan': timespan,
                'minutes': 5
            }

            rows_with_gaps.append(pre_gap_row)  # Append the Pre Gap row first

        # Append the current row
        rows_with_gaps.append(row.to_dict())  # Convert row to dict for appending

    # Convert the list of dictionaries to a DataFrame
    return pd.DataFrame(rows_with_gaps, columns=df.columns)

def post_gaps(df):
    """
    Adds a "Post Gap" row after each row where the 'type' column equals 'TEACHING'.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.

    Returns:
    pd.DataFrame: The modified DataFrame with gaps added.
    """
    rows_with_gaps = []

    for _, row in df.iterrows():
        # Append the current row
        rows_with_gaps.append(row.to_dict())  # Convert row to dict for appending

        # Check if the 'type' column is 'TEACHING'
        if row['type'] == 'TEACHING':
            # Calculate the Post Gap timespan
            if pd.notnull(row['timespan']) and '-' in row['timespan']:
                start_time, end_time = row['timespan'].split('-')
                end_time = pd.to_datetime(end_time.strip(), format='%H:%M')
                post_gap_start = end_time + pd.Timedelta(minutes=5)
                timespan = f"{end_time.strftime('%H:%M')} - {post_gap_start.strftime('%H:%M')}"
            else:
                timespan = "N/A"

            # Create a Post Gap row
            post_gap_row = {
                'day': row['day'],
                'activities': 'Post Gap',
                'type': 'LESSON GAP',
                'timespan': timespan,
                'minutes': 5
            }

            rows_with_gaps.append(post_gap_row)  # Append as dictionary

    # Convert the list of dictionaries to a DataFrame
    return pd.DataFrame(rows_with_gaps, columns=df.columns)

def between_gaps(df):
    """
    Merges consecutive 'Post Gap' and 'Pre Gap' rows with the same timespan into a single 'Between Gap' row.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    pd.DataFrame: The modified DataFrame with merged 'Between Gap' rows.
    """
    # Convert rows to a list of dictionaries for easier iteration
    updated_rows = []
    skip_next = False  # Flag to skip the next row when merging

    for i in range(len(df) - 1):  # Iterate through the DataFrame except the last row
        if skip_next:
            skip_next = False
            continue

        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]

        # Check if current is "Post Gap" and next is "Pre Gap" with the same timespan
        if (
            current_row['activities'] == 'Post Gap' and
            next_row['activities'] == 'Pre Gap' and
            current_row['timespan'] == next_row['timespan']
        ):
            # Replace "Pre Gap" with "Between Gap"
            merged_row = next_row.copy()
            merged_row['activities'] = 'Between Gap'

            # Append the merged row and skip the next row
            updated_rows.append(merged_row.to_dict())
            skip_next = True
        else:
            # Append the current row if no merging is needed
            updated_rows.append(current_row.to_dict())

    # Add the last row if it wasn't skipped
    if not skip_next:
        updated_rows.append(df.iloc[-1].to_dict())

    # Convert the updated rows back to a DataFrame
    return pd.DataFrame(updated_rows, columns=df.columns)

def gap_violations(df, df_name='df'):
    """
    Check for overlaps in 'LESSON GAP' timespans with adjacent activities.
    If an overlap is detected, mark the 'gap_issues' column as 'Gap issue'.

    Parameters:
    df (pd.DataFrame): The DataFrame to check.
    df_name (str): The variable name for saving in the session dynamically.

    Returns:
    pd.DataFrame: The modified DataFrame with 'gap_issues' column updated for gap issues.
    """
    # Initialize 'gap_issues' column with default value 'good'
    df['gap_issues'] = 'good'

    # Iterate through the DataFrame rows using index
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]

        # Only check rows where type is 'LESSON GAP'
        if current_row['type'] == 'LESSON GAP':
            # Parse timespans into start and end times for both rows
            try:
                current_start, current_end = current_row['timespan'].split(' - ')
                next_start, next_end = next_row['timespan'].split(' - ')

                current_end = pd.to_datetime(current_end.strip(), format="%H:%M")
                next_start = pd.to_datetime(next_start.strip(), format="%H:%M")

                # Check for overlap: current_end > next_start
                if current_end > next_start:
                    df.at[i, 'gap_issues'] = 'Gap issue'
            except Exception as e:
                # Log or print error if timespan parsing fails
                print(f"Error processing row {i}: {e}")

    # Save DataFrame to session dynamically based on df_name
    session[df_name] = df.to_json()
    return df

def frametime_violations():
    """
    Checks for frametime violations in all day-specific DataFrames (df3a-df3e).
    Generates a concise, logical report for Start Work and End Work violations.
    Saves only the days with violations to the session.
    """
    reports = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    dfs = {
        'Monday': 'df3a',
        'Tuesday': 'df3b',
        'Wednesday': 'df3c',
        'Thursday': 'df3d',
        'Friday': 'df3e'
    }
    
    # Retrieve all DataFrames from the session
    for day, df_key in dfs.items():
        df_json = session.get(df_key)
        if not df_json:
            current_app.logger.warning(f"No data found for {day}")
            continue
        
        # Load DataFrame and initialize
        df = pd.read_json(StringIO(df_json))
        start_violation = None
        end_violation = None

        # Check for Start Work violation
        if not df.empty and df.iloc[0]['activities'] == 'Start Work' and df.iloc[0]['type'] == 'FRAMETIME':
            first_activity = df.iloc[1]  # Next activity row
            if df.iloc[0]['timespan'] > first_activity['timespan']:
                start_violation = (
                    f"{day}: Adjust FT start to {first_activity['timespan'].split(' - ')[0]} "
                )

        # Check for End Work violation
        if not df.empty and df.iloc[-1]['activities'] == 'End Work' and df.iloc[-1]['type'] == 'FRAMETIME':
            last_activity = df.iloc[-2]  # Preceding activity row
            if df.iloc[-1]['timespan'] < last_activity['timespan']:
                end_violation = (
                    f"{day}: Adjust FT end to {last_activity['timespan'].split(' - ')[1]} "
                )

        # Add violations to the report if any
        if start_violation:
            reports.append(start_violation)
        if end_violation:
            reports.append(end_violation)

    # Save the reports to the session if there are any violations
    if reports:
        frametime_issues = "; ".join(reports)
        session['frametime_issues'] = frametime_issues
        current_app.logger.info("Frametime violations have been identified and saved to session.")
    else:
        session['frametime_issues'] = "No frametime violations detected."
        current_app.logger.info("No frametime violations found.")


def planning_block(df):
    # Helper function to parse timespan into start and end times
    def parse_timespan(timespan):
        start, end = timespan.split(" - ")
        return pd.to_datetime(start, format="%H:%M"), pd.to_datetime(end, format="%H:%M")

    # Start processing rows with a while loop to dynamically add rows
    i = 0
    while i < len(df) - 1:  # Compare each row with the next
        current_end = parse_timespan(df.loc[i, 'timespan'])[1]
        next_start = parse_timespan(df.loc[i + 1, 'timespan'])[0]

        gap_minutes = (next_start - current_end).total_seconds() / 60

        # If the gap is 30 minutes or more, add a planning block row
        if gap_minutes >= 30:
            new_row = {
                'day': df.loc[i, 'day'],
                'timespan': f"{current_end.strftime('%H:%M')} - {next_start.strftime('%H:%M')}",
                'activities': 'Planning Block',
                'type': 'PLANNING',
                'minutes': int(gap_minutes),
                'gap_issues': 'good'
            }
            
            # Insert the new row into the DataFrame
            df = pd.concat([df.iloc[:i + 1], pd.DataFrame([new_row]), df.iloc[i + 1:]]).reset_index(drop=True)
            # Increment i by 1 to skip over the new row
            i += 1
        i += 1
    print(df)
    return df

