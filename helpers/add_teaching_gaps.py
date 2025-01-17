import pandas as pd
from flask import session, current_app
from io import StringIO

def pre_gaps(df):
    """
    Adds a "*Pre gap" row before each row where the 'type' column equals 'Teaching',
    ensuring that no "*Pre gap" rows are added in the first or second position.

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

        # Check if the 'type' column is 'Teaching'
        if row['type'] == 'Teaching':
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
                'activities': '*Pre gap',
                'type': '*Lesson gap',
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
    Adds a "*Post gap" row after each row where the 'type' column equals 'Teaching',
    ensuring that no "*Post gap" rows are added as the last or second-to-last row.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.

    Returns:
    pd.DataFrame: The modified DataFrame with gaps added.
    """
    rows_with_gaps = []

    for idx, row in df.iterrows():
        # Append the current row
        rows_with_gaps.append(row.to_dict())  # Convert row to dict for appending

        # Check if adding a "*Post gap" row would make it the last or second-to-last row
        if idx >= len(df) - 2:
            continue

        # Check if the 'type' column is 'Teaching'
        if row['type'] == 'Teaching':
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
                'activities': '*Post gap',
                'type': '*Lesson gap',
                'timespan': timespan,
                'minutes': 5
            }

            rows_with_gaps.append(post_gap_row)  # Append as dictionary

    # Convert the list of dictionaries to a DataFrame
    return pd.DataFrame(rows_with_gaps, columns=df.columns)


def between_gaps(df):
    """
    Merges consecutive '*Post gap' and '*Pre gap' rows with the same timespan into a single '*Between gap' row.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    pd.DataFrame: The modified DataFrame with merged '*Between gap' rows.
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

        # Check if current is "*Post gap" and next is "*Pre gap" with the same timespan
        if (
            current_row['activities'] == '*Post gap' and
            next_row['activities'] == '*Pre gap' and
            current_row['timespan'] == next_row['timespan']
        ):
            # Replace "*Pre gap" with "*Between gap"
            merged_row = next_row.copy()
            merged_row['activities'] = '*Between gap'

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
    Identify and mark gap violations in '*Lesson gap' activities.
    Violations occur if there is less than a 5-minute buffer before or after a lesson.

    Parameters:
    df (pd.DataFrame): DataFrame to check.
    df_name (str): Session variable name for saving the updated DataFrame.

    Returns:
    pd.DataFrame: Updated DataFrame with 'issues' column noting gap violations.
    """
    # Initialize 'gap_issues_count' in the session if not already present
    if 'gap_issues_count' not in session:
        session['gap_issues_count'] = 0

    # Load the current gap issues count from the session
    gap_issues_count = session['gap_issues_count']

    # Initialize 'issues' column with default value 'none'
    df['issues'] = 'none'

    # Iterate through DataFrame rows to identify overlaps
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]

        # Check only rows with type '*Lesson gap'
        if current_row['type'] == '*Lesson gap':
            try:
                # Extract and parse start and end times
                current_start, current_end = current_row['timespan'].split(' - ')
                next_start, next_end = next_row['timespan'].split(' - ')

                current_end = pd.to_datetime(current_end.strip(), format="%H:%M")
                next_start = pd.to_datetime(next_start.strip(), format="%H:%M")

                # Flag gap issue if current_end overlaps with next_start
                if current_end > next_start:
                    df.at[i, 'issues'] = 'Minimum 5-minute buffer required before and after lessons.'
                    gap_issues_count += 1  # Increment the gap issue count
            except Exception as e:
                # Handle timespan parsing errors
                print(f"Error processing row {i}: {e}")

    # Update the weekly gap issues count in the session
    session['gap_issues_count'] = gap_issues_count

    # Save the modified DataFrame to the session dynamically
    session[df_name] = df.to_json()

    return df



def frametime_violations():
    """
    Checks for frametime violations in all day-specific DataFrames (df3a-df3e).
    Updates the respective DataFrame with the violations in the 'issues' column.
    Adds comments for "Start Work" or "End Work" explaining frametime issues, including keyword-specific adjustments.
    Saves only the days with violations to the session and logs results.
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
    frametime_issue_count = 0  # Initialize counter for frametime issues
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
            if activity_row['type'] != 'Teaching':
                return 0  # No buffer for non-Teaching activities
            activity_lower = activity_row['activities'].lower()
            for keyword, exception in keywords.items():
                if keyword in activity_lower:
                    if exception and exception in activity_lower:
                        continue  # Skip adjustment if exception is present
                    return 10  # 10-minute buffer for keyword-specific adjustments
            return default_minutes  # Default 5-minute buffer for Teaching

        # Check for Start Work violation
        if not df.empty and df.iloc[0]['activities'] == 'Start Work' and df.iloc[0]['type'] == 'Frametime':
            first_activity = df.iloc[1]  # Next activity row
            adjustment_minutes = frametime_adjustment(first_activity, 5, keywords)
            adjustment_time = pd.to_datetime(first_activity['timespan'].split(' - ')[0]) - pd.Timedelta(minutes=adjustment_minutes)
            current_start_time = pd.to_datetime(df.iloc[0]['timespan'].split(' - ')[0])  # Current start time in Start Work row

            if adjustment_time < current_start_time:
                explanation = (
                    "(Special case with 10-min buffer)"
                    if adjustment_minutes == 10 else ""
                )
                start_violation = f"{day}: Adjust FT start to {adjustment_time.strftime('%H:%M')}"
                df.at[0, 'issues'] = (
                    f"Adjust START to {adjustment_time.strftime('%H:%M')}. {explanation}"
                )
                frametime_issue_count += 1  # Increment counter for Start Work issue

        # Check for End Work violation
        if not df.empty and df.iloc[-1]['activities'] == 'End Work' and df.iloc[-1]['type'] == 'Frametime':
            last_activity = df.iloc[-2]  # Preceding activity row
            adjustment_minutes = frametime_adjustment(last_activity, 5, keywords)
            adjustment_time = pd.to_datetime(last_activity['timespan'].split(' - ')[1]) + pd.Timedelta(minutes=adjustment_minutes)
            current_end_time = pd.to_datetime(df.iloc[-1]['timespan'].split(' - ')[1])  # Current end time in End Work row

            if adjustment_time > current_end_time:
                explanation = (
                    "(Special case with 10-min buffer)"
                    if adjustment_minutes == 10 else ""
                )
                end_violation = f"{day}: Adjust FT end to {adjustment_time.strftime('%H:%M')}"
                df.at[len(df) - 1, 'issues'] = (
                    f"Adjust END to {adjustment_time.strftime('%H:%M')}. {explanation}"
                )
                frametime_issue_count += 1  # Increment counter for End Work issue

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
        session['frametime_issue_count'] = frametime_issue_count  # Save count to the session
        current_app.logger.info("Frametime violations detected; saved to session.")
    else:
        session['frametime_issues'] = "No frametime violations detected."
        session['frametime_issue_count'] = frametime_issue_count  # Save count as 0
        current_app.logger.info("No frametime violations found.")

    # Log the total count of frametime issues
    current_app.logger.info(f"Total frametime issues detected: {frametime_issue_count}")




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
                'activities': '*Planning Block',
                'type': '*Planning',
                'minutes': int(gap_minutes),
                'issues': 'none'
            }
            
            # Update the total gap minutes
            planning_time += round(int(gap_minutes)/60,3)
            planning_time = round(planning_time,1)

            # Insert the new row into the DataFrame
            df = pd.concat([df.iloc[:i + 1], pd.DataFrame([new_row]), df.iloc[i + 1:]]).reset_index(drop=True)
            # Increment i by 1 to skip over the new row
            i += 1
        i += 1

    # Store the updated total gap minutes back into the session
    session['planning_time'] = planning_time

    return df


