import pandas as pd
from flask import session, current_app
from io import StringIO

def pre_gaps(df):
    """
    Adds a "Pre Gap" row before each row where the 'type' column equals 'TEACHING',
    ensuring that no "Pre Gap" rows are added in the first or second position.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.

    Returns:
    pd.DataFrame: The modified DataFrame with gaps added.
    """
    rows_with_gaps = []

    for idx, row in df.iterrows():
        # Skip adding a Pre Gap if the row is in the first or second position
        if idx < 2:
            rows_with_gaps.append(row.to_dict())
            continue

        # Check if the 'type' column is 'TEACHING'
        if row['type'] == 'TEACHING':
            # Calculate the Pre Gap timespan
            if pd.notnull(row['timespan']) and '-' in row['timespan']:
                start_time, _ = row['timespan'].split('-')
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

            # Append the Pre Gap row
            rows_with_gaps.append(pre_gap_row)

        # Append the current row
        rows_with_gaps.append(row.to_dict())  # Convert row to dict for appending

    # Convert the list of dictionaries to a DataFrame
    return pd.DataFrame(rows_with_gaps, columns=df.columns)


def post_gaps(df):
    """
    Adds a "Post Gap" row after each row where the 'type' column equals 'TEACHING',
    ensuring that no "Post Gap" rows are added as the last or second-to-last row.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.

    Returns:
    pd.DataFrame: The modified DataFrame with gaps added.
    """
    rows_with_gaps = []

    for idx, row in df.iterrows():
        # Append the current row
        rows_with_gaps.append(row.to_dict())  # Convert row to dict for appending

        # Check if adding a "Post Gap" row would make it the last or second-to-last row
        if idx >= len(df) - 2:
            continue

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
    If an overlap is detected, mark the 'issues' column as 'Gap issue'.

    Parameters:
    df (pd.DataFrame): The DataFrame to check.
    df_name (str): The variable name for saving in the session dynamically.

    Returns:
    pd.DataFrame: The modified DataFrame with 'issues' column updated for gap issues.
    """
    # Initialize 'issues' column with default value 'none'
    df['issues'] = 'none'

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
                    df.at[i, 'issues'] = 'Gap issue'
            except Exception as e:
                # Log or print error if timespan parsing fails
                print(f"Error processing row {i}: {e}")

    # Save DataFrame to session dynamically based on df_name
    session[df_name] = df.to_json()
    return df

def frametime_violations():
    """
    Checks for frametime violations in all day-specific DataFrames (df3a-df3e).
    Updates the respective DataFrame with the violations in the 'issues' column.
    Generates a concise, logical report for Start Work and End Work violations.
    Saves only the days with violations to the session.
    """
    import os

    # Read keywords and exceptions from file
    keywords = {}
    file_path = os.path.join('helpers', 'activity_keywords.txt')
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:  # Skip comments and empty lines
                continue
            if '(' in line and ')' in line:  # Keyword with exception
                keyword, exception = line.split('(')
                keywords[keyword.strip().lower()] = exception.strip(')').lower()  # Store keywords in lowercase
            else:
                keywords[line.lower()] = None  # Store keyword without exception in lowercase

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

        # Helper function to determine frametime adjustment
        def frametime_adjustment(activity_row, default_minutes, keywords):
            # Adjust only if the type is TEACHING
            if activity_row['type'] != 'TEACHING':
                return default_minutes-5
            activity_lower = activity_row['activities'].lower()  # Convert activity to lowercase for comparison
            for keyword, exception in keywords.items():
                if keyword in activity_lower:
                    if exception and exception in activity_lower:
                        continue  # Skip adjustment if exception is present
                    return default_minutes + 5  # Use 10 minutes for matching keywords
            return default_minutes

        # Check for Start Work violation
        if not df.empty and df.iloc[0]['activities'] == 'Start Work' and df.iloc[0]['type'] == 'FRAMETIME':
            first_activity = df.iloc[1]  # Next activity row
            adjustment_minutes = frametime_adjustment(first_activity, 5, keywords)
            adjustment_time = pd.to_datetime(first_activity['timespan'].split(' - ')[0]) - pd.Timedelta(minutes=adjustment_minutes)
            current_start_time = pd.to_datetime(df.iloc[0]['timespan'].split(' - ')[0])  # Current start time in Start Work row

            if adjustment_time != current_start_time:
                start_violation = f"{day}: Adjust FT start to {adjustment_time.strftime('%H:%M')}"
                df.at[0, 'issues'] = f"Adjust to {adjustment_time.strftime('%H:%M')}"  # Update 'issues' column for the first row

        # Check for End Work violation
        if not df.empty and df.iloc[-1]['activities'] == 'End Work' and df.iloc[-1]['type'] == 'FRAMETIME':
            last_activity = df.iloc[-2]  # Preceding activity row
            adjustment_minutes = frametime_adjustment(last_activity, 5, keywords)
            adjustment_time = pd.to_datetime(last_activity['timespan'].split(' - ')[1]) + pd.Timedelta(minutes=adjustment_minutes)
            current_end_time = pd.to_datetime(df.iloc[-1]['timespan'].split(' - ')[1])  # Current end time in End Work row

            if adjustment_time != current_end_time:
                end_violation = f"{day}: Adjust FT end to {adjustment_time.strftime('%H:%M')}"
                df.at[len(df) - 1, 'issues'] = f"Adjust to {adjustment_time.strftime('%H:%M')}"  # Update 'issues' column for the last row

        # Add violations to the report if any
        if start_violation:
            reports.append(start_violation)
        if end_violation:
            reports.append(end_violation)

        # Save the updated DataFrame back to the session
        session[df_key] = df.to_json()

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

    # Retrieve the total gap minutes from the session or initialize it
    planning_time = session.get('planning_time', 0)

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
                'issues': 'none'
            }
            
            # Update the total gap minutes
            planning_time += round(int(gap_minutes)/60,3)

            # Insert the new row into the DataFrame
            df = pd.concat([df.iloc[:i + 1], pd.DataFrame([new_row]), df.iloc[i + 1:]]).reset_index(drop=True)
            # Increment i by 1 to skip over the new row
            i += 1
        i += 1

    # Store the updated total gap minutes back into the session
    session['planning_time'] = planning_time

    return df


