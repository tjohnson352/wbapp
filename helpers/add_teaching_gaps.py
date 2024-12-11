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





