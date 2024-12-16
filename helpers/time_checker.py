import pandas as pd
from flask import session, current_app
from io import StringIO

def time_checker():
    try:
        # Load DataFrames safely from session using StringIO
        df1b = pd.read_json(StringIO(session['df1b']))
        df2c = pd.read_json(StringIO(session['df2c']))
        work_percent = session.get('work_percent', 0)

        # Ensure 'day' is a string for consistent matching
        df1b['day'] = df1b['day'].astype(str)
        df2c['day'] = df2c['day'].astype(str)

        # Initialize 'break_time' column to hold string values
        df1b['break_time'] = "None"

        # Match rows and assign 'timespan' where 'type' == 'BREAK'
        for index, row in df1b.iterrows():
            day = row['day']
            match = df2c[(df2c['day'] == day) & (df2c['type'] == 'BREAK')]

            if not match.empty:
                # Assign the timespan as a string
                df1b.loc[index, 'break_time'] = str(match['timespan'].iloc[0])

        # Split 'break_time' into 'break_start' and 'break_end' columns
        df1b[['break_start', 'break_end']] = df1b['break_time'].str.split(' - ', expand=True)

        # Convert relevant columns to datetime for calculations
        df1b['start_time'] = pd.to_datetime(df1b['start_time'], errors='coerce')
        df1b['end_time'] = pd.to_datetime(df1b['end_time'], errors='coerce')
        df1b['break_start'] = pd.to_datetime(df1b['break_start'], format='%H:%M', errors='coerce')
        df1b['break_end'] = pd.to_datetime(df1b['break_end'], format='%H:%M', errors='coerce')
        df1b['frametimespan'] = (df1b['end_time'] - df1b['start_time']).dt.total_seconds() / 3600
        df1b['frametimespan'] = df1b['frametimespan'].fillna(0).round(2)

        # Combine date from start_time with break_start and break_end
        df1b['break_start'] = df1b.apply(
            lambda row: pd.to_datetime(f"{row['start_time'].date()} {row['break_start'].time()}")
            if pd.notna(row['start_time']) and pd.notna(row['break_start']) else pd.NaT, axis=1
        )

        df1b['break_end'] = df1b.apply(
            lambda row: pd.to_datetime(f"{row['start_time'].date()} {row['break_end'].time()}")
            if pd.notna(row['start_time']) and pd.notna(row['break_end']) else pd.NaT, axis=1
        )

        # Calculate 'early_break' and 'late_break'
        df1b['early_break'] = df1b.apply(
            lambda row: (row['break_start'] - row['start_time']).total_seconds() / 3600
            if pd.notna(row['start_time']) and row['break_time'] != "None" else None, axis=1
        )

        df1b['late_break'] = df1b.apply(
            lambda row: (row['end_time'] - row['break_end']).total_seconds() / 3600
            if pd.notna(row['start_time']) and row['break_time'] != "None" else None, axis=1
        )

        # Create 'comments' column based on the specified conditions
        df1b['comments'] = df1b.apply(
            lambda row: 'Good' if row['frametimespan'] > 5 and (row['early_break'] <= 5 or row['late_break'] <= 5)
            else 'Off' if row['frametimespan'] == 0
            else 'Adjustment' if row['frametimespan'] > 5 and (row['early_break'] > 5 and row['late_break'] > 5)
            else 'Missing',
            axis=1
        )

        # Save the updated df1b back to the session
        session['df1b'] = df1b.to_json()

        assigned_frametime = df1b['frametimespan'].sum()
        assigned_frametime = round(assigned_frametime,1)
        
        contract_frametime = 34 * work_percent / 100
        contract_frametime = round(contract_frametime,1)
        
        contract_teachtime = 18 * work_percent / 100
        contract_teachtime = round(contract_teachtime,1)
        
        total_breaks = df1b[df1b['break_time'] != "None"].shape[0]*.5
        break_issues = df1b.loc[df1b['comments'] == "Missing", 'day'].tolist()
        qnty_break_issues = len(break_issues)
        
        contract_frametime_with_breaks = contract_frametime + total_breaks
        contract_frametime_with_breaks = round(contract_frametime_with_breaks,1)

        # Calculate total minutes for each type
        df2c['minutes'] = pd.to_numeric(df2c['minutes'], errors='coerce')
        total_break_time = df2c[df2c['type'] == 'BREAK']['minutes'].sum()
        total_general_duty_time = df2c[df2c['type'] == 'GENERAL/DUTY']['minutes'].sum()
        assigned_teachtime = round(df2c[df2c['type'] == 'TEACHING']['minutes'].sum()/60,1)

        # Save results to session or variables
        session['total_break_time'] = total_break_time
        session['total_general_duty_time'] = total_general_duty_time
        session['assigned_teachtime'] = assigned_teachtime

        # Create a DataFrame with your data
        df_time = pd.DataFrame({
            'Metric': [
                'Contractual frametime',
                'Contractual frametime + breaks',
                'Assigned frametime',
                'Contractual teaching',
                'Assigned teaching',
                'Break issue',
                'Qnty break issues'
            ],
            'Value': [
                contract_frametime,
                contract_frametime_with_breaks,
                assigned_frametime,
                contract_teachtime,
                assigned_teachtime,
                ', '.join(break_issues),
                qnty_break_issues
            ]
        })

        # Convert the DataFrame to JSON and save in session
        session['df_time'] = df_time.to_json()

        current_app.logger.info("Time checker completed successfully.")
        return session['time_checker_results']

    except Exception as e:
        current_app.logger.error(f"Error in time_checker: {e}")
        raise