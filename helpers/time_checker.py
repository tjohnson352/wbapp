import pandas as pd
from flask import session, current_app
from io import StringIO
import numpy as np

def time_checker():
    try:
        # Constants
        WORK_HOURS = 34
        TEACH_HOURS = 18
        BREAK_DURATION_HOURS = 0.5

        # Retrieve DataFrames and session variables
        df1b = pd.read_json(StringIO(session['df1b']))
        df2c = pd.read_json(StringIO(session['df2c']))
        work_percent = session.get('work_percent', 0)
        middle_manager = session.get('middle_manager', "").strip().lower()

        # Ensure required columns exist
        required_columns_df1b = {'day', 'start_time', 'end_time'}
        required_columns_df2c = {'day', 'type', 'timespan', 'minutes'}
        if not required_columns_df1b.issubset(df1b.columns):
            raise ValueError(f"df1b is missing required columns: {required_columns_df1b - set(df1b.columns)}")
        if not required_columns_df2c.issubset(df2c.columns):
            raise ValueError(f"df2c is missing required columns: {required_columns_df2c - set(df2c.columns)}")

        # Match breaks to days
        df1b['break_time'] = df1b['day'].map(
            lambda day: df2c.query("day == @day and type == 'Break'")['timespan'].iloc[0]
            if not df2c.query("day == @day and type == 'Break'").empty else "None"
        )

        # Split timespan into start and end, convert to datetime
        time_columns = ['start_time', 'end_time', 'break_start', 'break_end']
        df1b[['break_start', 'break_end']] = (
            df1b['break_time']
            .str.split(' - ', expand=True)
            .rename(columns={0: 'break_start', 1: 'break_end'})
        )
        for col in time_columns:
            df1b[col] = pd.to_datetime(df1b[col], errors='coerce')

        # Calculate time spans
        df1b['frametimespan'] = (df1b['end_time'] - df1b['start_time']).dt.total_seconds() / 3600
        df1b['early_break'] = (df1b['break_start'] - df1b['start_time']).dt.total_seconds() / 3600
        df1b['late_break'] = (df1b['end_time'] - df1b['break_end']).dt.total_seconds() / 3600
        

        # Classify rows
        df1b['comments'] = np.where(
            df1b['frametimespan'] == 0, 'Off',
            np.where(
                df1b['frametimespan'] > 5,
                np.where(
                    (df1b['early_break'] <= 5) & (df1b['late_break'] <= 5),
                    'Good',
                    'Needs adjustment'
                ),
                'Good'
            )
        )

        # Calculate totals
        assigned_frametime = round(df1b['frametimespan'].sum(), 1)
        contract_frametime = round(WORK_HOURS * work_percent / 100, 1)
        contract_teachtime = round(TEACH_HOURS * work_percent / 100, 1)  # without breaks
        breaks = round(df1b['break_time'].ne("None").sum() * BREAK_DURATION_HOURS, 1)
        contract_frametime = round(contract_frametime + breaks, 1)  # breaks added

        # Adjust teaching time for middle managers
        adjusted_teachtime = round(contract_teachtime - 1.5, 1) if middle_manager == "yes" else contract_teachtime

        # Calculate overtime
        assigned_teachtime = round(df2c[df2c['type'] == 'Teaching']['minutes'].sum() / 60, 1)
        general_duty = round(df2c[df2c['type'] == 'General']['minutes'].sum() / 60, 1)

        # Check and calculate teaching time surplus/deficit
        if assigned_teachtime - adjusted_teachtime < 0:
            over_teachtime = f"{abs(round(assigned_teachtime - adjusted_teachtime, 1))} hrs under"
        else:
            over_teachtime = round(assigned_teachtime - adjusted_teachtime, 1)

        # Check and calculate frametime surplus/deficit
        if assigned_frametime - contract_frametime < 0:
            over_framtime = f"{abs(round(assigned_frametime - contract_frametime, 1))} hrs under"
        else:
            over_framtime = round(assigned_frametime - contract_frametime, 1)

        # Check and calculate total overtime surplus/deficit
        if assigned_frametime + assigned_teachtime - (contract_frametime + adjusted_teachtime) < 0:
            overtime_total = f"{abs(round(assigned_frametime + assigned_teachtime - (contract_frametime + adjusted_teachtime), 1))} hrs under"
        else:
            overtime_total = round(over_framtime + over_teachtime, 1)

        # Save all calculated results to the session
        session.update({
            'breaks': breaks,
            'general': general_duty,
            'contract_teachtime': contract_teachtime,
            'assigned_teach': assigned_teachtime,
            'adjusted_contract_teach_time': adjusted_teachtime,
            'contract_frametime': contract_frametime,
            'assigned_frametime': assigned_frametime,
            'over_teachtime': over_teachtime,
            'over_framtime': over_framtime,
            'total_overtime': overtime_total
        })


    except Exception as e:
        current_app.logger.error(f"Error in time_checker: {e}")
        raise
