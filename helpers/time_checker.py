import pandas as pd
from flask import session, current_app
from io import StringIO
import numpy as np

def time_checker():
    try:
        # Load DataFrames safely from session using StringIO
        # df1b: contains information about scheduled days and times
        # df2c: contains break and task type information for different days
        df1b = pd.read_json(StringIO(session['df1b']))
        df2c = pd.read_json(StringIO(session['df2c']))
        work_percent = session.get('work_percent', 0)  # Retrieve work percentage for calculations

        # Ensure 'day' column in both DataFrames is a string for matching
        df1b['day'] = df1b['day'].astype(str)
        df2c['day'] = df2c['day'].astype(str)

        # Initialize 'break_time' column to "None" to store matched break times
        df1b['break_time'] = "None"

        # Match rows in df1b with corresponding break times in df2c based on the 'day' column
        # If a match exists, assign the 'timespan' value to 'break_time' in df1b
        for index, row in df1b.iterrows():
            day = row['day']
            match = df2c[(df2c['day'] == day) & (df2c['type'] == 'BREAK')]

            if not match.empty:
                # Assign the first match's timespan to the current row
                df1b.loc[index, 'break_time'] = str(match['timespan'].iloc[0])

        # Split 'break_time' into separate 'break_start' and 'break_end' columns
        # Ensure proper handling when 'break_time' does not contain a valid " - "
        df1b['break_start'], df1b['break_end'] = zip(*df1b['break_time'].apply(
            lambda x: x.split(' - ') if ' - ' in str(x) else [None, None]
        ))

        # Convert time-related columns to datetime objects for accurate time calculations
        df1b['start_time'] = pd.to_datetime(df1b['start_time'], errors='coerce')
        df1b['end_time'] = pd.to_datetime(df1b['end_time'], errors='coerce')
        df1b['break_start'] = pd.to_datetime(df1b['break_start'], format='%H:%M', errors='coerce')
        df1b['break_end'] = pd.to_datetime(df1b['break_end'], format='%H:%M', errors='coerce')

        # Calculate total time span (in hours) between start_time and end_time for each row
        df1b['frametimespan'] = (df1b['end_time'] - df1b['start_time']).dt.total_seconds() / 3600
        df1b['frametimespan'] = df1b['frametimespan'].fillna(0).round(2)

        # Combine dates from start_time with break_start and break_end for time calculations
        df1b['break_start'] = df1b.apply(
            lambda row: pd.to_datetime(f"{row['start_time'].date()} {row['break_start'].time()}")
            if pd.notna(row['start_time']) and pd.notna(row['break_start']) else pd.NaT, axis=1
        )
        df1b['break_end'] = df1b.apply(
            lambda row: pd.to_datetime(f"{row['start_time'].date()} {row['break_end'].time()}")
            if pd.notna(row['start_time']) and pd.notna(row['break_end']) else pd.NaT, axis=1
        )

        # Calculate 'early_break' (time from start to break start) and 'late_break' (time from break end to finish)
        df1b['early_break'] = df1b.apply(
            lambda row: (row['break_start'] - row['start_time']).total_seconds() / 3600
            if pd.notna(row['start_time']) and row['break_time'] != "None" else None, axis=1
        )
        df1b['late_break'] = df1b.apply(
            lambda row: (row['end_time'] - row['break_end']).total_seconds() / 3600
            if pd.notna(row['start_time']) and row['break_time'] != "None" else None, axis=1
        )

        # Add a 'comments' column to classify each row based on calculated time spans and breaks
        df1b['comments'] = df1b.apply(
            lambda row: 'Good' if row['frametimespan'] > 5 and (row['early_break'] <= 5 and row['late_break'] <= 5)
            else 'Off' if row['frametimespan'] == 0
            else 'Needs adjustment' if row['frametimespan'] > 5 and (row['early_break'] > 5 or row['late_break'] > 5)
            else 'missing' if row['frametimespan'] > 5
            else 'Good',
            axis=1
        )

        # Save the updated DataFrame to the session
        session['df1b'] = df1b.to_json()

        # Calculate total frametime assigned and round to 1 decimal
        assigned_frametime = round(df1b['frametimespan'].sum(), 1)

        # Compute contract frametime and teaching time based on work percentage
        contract_frametime = round(34 * work_percent / 100, 1)
        contract_teachtime = round(18 * work_percent / 100, 1)

        # Compute total breaks in hours
        total_breaks = df1b[df1b['break_time'] != "None"].shape[0] * 0.5

        # Identify days with 'missing' or 'adjustment' comments
        break_issues = df1b.loc[df1b['comments'].isin(["missing", "adjustment"]), 'day'].tolist()
        break_issues = ', '.join(break_issues)

        # Calculate contract frametime including breaks
        contract_frametime_with_breaks = round(contract_frametime + total_breaks, 1)

        # Calculate total minutes spent on different types of work and round to 1 decimal
        df2c['minutes'] = pd.to_numeric(df2c['minutes'], errors='coerce')
        total_break_time = round((df2c[df2c['type'] == 'BREAK']['minutes'].sum()) / 60, 1)
        total_general_duty_time = round((df2c[df2c['type'] == 'GENERAL/DUTY']['minutes'].sum()) / 60, 1)
        total_teach_time = round(df2c[df2c['type'] == 'TEACHING']['minutes'].sum() / 60, 1)

        # Adjust contract teaching time for middle managers
        middle_manager = str(session.get('middle_manager', "")).lower()
        adjusted_contract_teach_time = round(contract_teachtime - 1.5, 1) if middle_manager == "yes" else contract_teachtime

        # Save calculated results to session
        session['total_break_time'] = total_break_time
        session['total_general_duty_time'] = total_general_duty_time
        session['total_teach_time'] = total_teach_time
        session['contract_teachtime'] = contract_teachtime
        session['adjusted_contract_teach_time'] = adjusted_contract_teach_time
        session['contract_frametime'] = contract_frametime
        session['contract_frametime_with_breaks'] = contract_frametime_with_breaks
        session['assigned_frametime'] = assigned_frametime
        session['break_issues'] = break_issues

    except Exception as e:
        # Log the error and raise the exception for debugging
        current_app.logger.error(f"Error in time_checker: {e}")
        raise
