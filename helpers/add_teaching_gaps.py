import pandas as pd
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

def gap_violations(df):
    """
    Check for overlaps in 'LESSON GAP' timespans with adjacent activities.
    If an overlap is detected, mark the 'day' column as 'Gap issue'.

    Parameters:
    df (pd.DataFrame): The DataFrame to check.

    Returns:
    pd.DataFrame: The modified DataFrame with 'day' updated for gap issues.
    """
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
                    df.at[i, 'day'] = 'Gap issue'
            except Exception as e:
                # Log or print error if timespan parsing fails
                print(f"Error processing row {i}: {e}")

    return df
