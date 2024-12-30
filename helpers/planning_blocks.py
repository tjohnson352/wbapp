import pandas as pd
from datetime import datetime, timedelta

def planning_block(df):
    """
    Identifies gaps of 30 minutes or more between consecutive rows on the same day in a schedule DataFrame.
    Adds a "Planning Block" activity for each identified gap.

    Parameters:
        df (pd.DataFrame): Input DataFrame with columns ['day', 'timespan', 'activities', 'type', 'minutes', 'gap_issues'].

    Returns:
        pd.DataFrame: Updated DataFrame with "Planning Block" rows added.
    """
    def parse_timespan(timespan):
        """Parse the timespan into start and end times."""
        start_str, end_str = timespan.split(" - ")
        start = datetime.strptime(start_str.strip(), "%H:%M")
        end = datetime.strptime(end_str.strip(), "%H:%M")
        return start, end

    # Add start_time and end_time columns for easier comparison
    df["start_time"], df["end_time"] = zip(*df["timespan"].apply(parse_timespan))

    new_rows = []  # To store new rows for Planning Blocks

    # Iterate through rows to identify gaps
    for i in range(len(df) - 1):
        current_day = df.loc[i, "day"]
        next_day = df.loc[i + 1, "day"]

        if current_day == next_day:  # Only compare rows on the same day
            current_end = df.loc[i, "end_time"]
            next_start = df.loc[i + 1, "start_time"]

            # Calculate the gap in minutes
            gap_minutes = (next_start - current_end).total_seconds() / 60

            if gap_minutes >= 30:
                # Create a new row for the Planning Block
                planning_row = {
                    "day": current_day,
                    "timespan": f"{current_end.strftime('%H:%M')} - {next_start.strftime('%H:%M')}",
                    "activities": "* Planning block",
                    "type": " * Planning",
                    "minutes": int(gap_minutes),
                    "gap_issues": "good"
                }
                # Insert the new row after the current row
                new_rows.append((i + 0.5, planning_row))

    # Insert new rows into the DataFrame
    for idx, row in new_rows:
        df = pd.concat(
            [df.iloc[:int(idx)], pd.DataFrame([row], index=[idx]), df.iloc[int(idx):]]
        )

    # Sort and reset index
    df = df.sort_index().reset_index(drop=True)

    # Drop the temporary columns
    df.drop(columns=["start_time", "end_time"], inplace=True)

    return df
