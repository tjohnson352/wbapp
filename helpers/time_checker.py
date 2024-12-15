import pandas as pd
from flask import session, current_app


def time_checker():
    try:
        # Load DataFrames from the session
        work_percent = session.get('work_percent')
        assigned_teachtime = session.get('teaching') / 60
        df2c = pd.read_json(session['df2c'])
        df1b = pd.read_json(session['df1b'])
        df3_frames = [pd.read_json(session[f'df3{day}']) for day in ['a', 'b', 'c', 'd', 'e']]

        # Exclude the first and last rows in df3a-df3e (frametime rows)
        for i in range(len(df3_frames)):
            df3_frames[i] = df3_frames[i].iloc[1:-1]

        # Initialize variables
        break_issues = []
        total_assigned_frametime = 0  # Track total assigned frametime

        for index, row in df1b.iterrows():
            day = row['day']

            # Handle NaT or missing start/end times
            if pd.isna(row['start_time']) or pd.isna(row['end_time']):
                current_app.logger.info(f"Skipping {day} due to NaT in start or end time.")
                continue

            # Calculate assigned frametime
            start_time = pd.to_datetime(row['start_time'], format="%Y-%m-%d %H:%M:%S")
            end_time = pd.to_datetime(row['end_time'], format="%Y-%m-%d %H:%M:%S")
            daily_frametime = (end_time - start_time).total_seconds() / 3600
            total_assigned_frametime += daily_frametime

            # Skip if frametime is ≤ 5 hours
            if daily_frametime <= 5:
                continue

            # Check for breaks within the first 5 hours
            day_df = df3_frames[index]
            break_found = False

            for _, activity in day_df.iterrows():
                if activity['type'] == 'BREAK':
                    try:
                        break_start, break_end = [
                            pd.to_datetime(time.strip(), format="%H:%M")
                            for time in activity['timespan'].split('-')
                        ]
                        if (break_start - start_time).total_seconds() <= 5 * 3600:
                            break_found = True
                            break
                    except Exception as e:
                        current_app.logger.error(f"Error parsing timespan {activity['timespan']}: {e}")
                        continue

            if not break_found:
                break_issues.append(f"On {day} a compulsory 30-minutes BREAK is missing.")

        # Calculate weekly total time
        contract_frametime = 34 * work_percent / 100
        contract_teachtime = 18 * work_percent / 100

        total_breaks = len(df2c[df2c['type'] == 'BREAK']) * 0.5  # 30 minutes per break
        contract_frametime_with_breaks = contract_frametime + total_breaks

        # Calculate total minutes for each type
        df2c['minutes'] = pd.to_numeric(df2c['minutes'], errors='coerce')
        total_break_time = df2c[df2c['type'] == 'BREAK']['minutes'].sum()
        total_general_duty_time = df2c[df2c['type'] == 'GENERAL/DUTY']['minutes'].sum()
        total_teaching_time = df2c[df2c['type'] == 'TEACHING']['minutes'].sum()

        # Save results to session or variables
        session['total_break_time'] = total_break_time
        session['total_general_duty_time'] = total_general_duty_time
        session['total_teaching_time'] = total_teaching_time


        # Save results to session
        session['time_checker_results'] = {
            'contract_frametime': contract_frametime,
            'contract_frametime_with_breaks': contract_frametime_with_breaks,
            'assigned_frametime': total_assigned_frametime,
            'contract_teachtime': contract_teachtime,
            'assigned_teachtime': assigned_teachtime,
            'break_issues': break_issues,
        }

        current_app.logger.info("Time checker completed successfully.")
        return session['time_checker_results']

    except Exception as e:
        current_app.logger.error(f"Error in time_checker: {e}")
        raise



