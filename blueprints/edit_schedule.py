from flask import Blueprint, render_template, session, request, jsonify, current_app
import pandas as pd
from helpers.add_teaching_gaps import post_gaps, pre_gaps, between_gaps, gap_violations, frametime_violations, planning_block
from helpers.time_checker import time_checker
from helpers.report_generator import generate_pdf, generate_plain_text_report, generate_plain_text_schedule
from helpers.ft_days import ft_days, prime_dfs
from io import StringIO



edit_schedule_blueprint = Blueprint('edit_schedule', __name__)

@edit_schedule_blueprint.route('/days', methods=['GET', 'POST'])
def display_schedule():
    try:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        current_day_index = session.get('day_index', 0)

        if request.method == 'POST':
            data = request.get_json()
            current_app.logger.info(f"Received payload: {data}")  # Debugging

            if not data:
                return jsonify({'error': 'No data received.'}), 400

            frametime = data.get('frametime', {})
            selected_activities = data.get('selected_activities', [])
            is_off = data.get('is_off', False)

            # Handle "Off" work day case
            if is_off:
                start_ft = "00:00"
                end_ft = "00:00"

            else:
                start_ft = frametime.get('start_time')  # e.g., "08:00"
                end_ft = frametime.get('end_time')  # e.g., "16:00"

                if not start_ft or not end_ft:
                    return jsonify({'error': 'Frametime start and end times are required unless the day is marked as off.'}), 400

  
            # Update df1b with frametime for the current day
            current_day = days[current_day_index]
            df1b_json = session.get('df1b', '{}')
            df1b = pd.read_json(StringIO(df1b_json)) if df1b_json != '{}' else pd.DataFrame(columns=['day', 'start_time', 'end_time'])

            # Ensure the 'day' column exists before filtering
            if 'day' in df1b.columns:
                df1b = df1b[df1b['day'] != current_day]  # Remove any existing entry for the day

            # Convert start_ft and end_ft to ensure they are in "HH:MM" format
            if start_ft:
                start_ft = ':'.join(f"{int(part):02d}" for part in start_ft.split(':'))  # Ensures leading zeros
            if end_ft:
                end_ft = ':'.join(f"{int(part):02d}" for part in end_ft.split(':'))  # Ensures leading zeros

            # Add the new frametime entry
            new_frametime_entry = pd.DataFrame([{
                'day': current_day,
                'start_time': pd.to_datetime(start_ft, format='%H:%M').strftime('%H:%M') if start_ft else None,
                'end_time': pd.to_datetime(end_ft, format='%H:%M').strftime('%H:%M') if end_ft else None
            }])

            if not new_frametime_entry.dropna(how='all').empty:
                df1b = pd.concat([df1b, new_frametime_entry], ignore_index=True)
            session['df1b'] = df1b.astype({'start_time': 'string', 'end_time': 'string'}).to_json()

            # Update df2b with selected activities if it's not an off day
            df2b = pd.read_json(StringIO(session.get('df2b', '{}')))

            if not is_off:
                for index in selected_activities:
                    df2b.at[index, 'day'] = current_day

            # Sort df2b by 'day' and 'timespan'
            day_order = {'Unassigned': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
            df2b['day_order'] = df2b['day'].map(day_order).fillna(0).astype(int)
            df2b = df2b.sort_values(by=['day_order', 'timespan'], ascending=[True, True]).reset_index(drop=True)
            df2b.drop(columns=['day_order'], inplace=True)
            session['df2b'] = df2b.to_json()

            # Move to the next day
            if current_day_index < len(days) - 1:
                session['day_index'] = current_day_index + 1
                return jsonify({'message': f'Activities assigned to {current_day}.', 'complete': False}), 200
            else:
                session.pop('day_index', None)  # Clear day_index after Friday

                df2b['day'] = df2b['day'].apply(lambda x: x if x in days else 'DELETED')  # Replace invalid days with 'DELETED'
                session['df2b'] = df2b.to_json()  # Save back to session
                updated_schedule()
                return jsonify({'message': 'All activities assigned.', 'complete': True}), 200
            

        # GET request: Display the schedule for the current day
        current_day = days[current_day_index]
        df2b = pd.read_json(StringIO(session.get('df2b', '{}')))
        

        return render_template('edit_schedule.html', table=df2b, current_day=current_day)

    except Exception as e:
        current_app.logger.error(f"Error in /days route: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred.'}), 500

def updated_schedule():
    try:
        # Retrieve df2b from the session
        df2b_json = session.get('df2b')
        if not df2b_json:
            current_app.logger.error("df2b not found in session.")
            return jsonify({'error': 'df2b not found in session.'}), 400

        # Convert JSON to DataFrame
        df2b = pd.read_json(StringIO(df2b_json))

        # Extract rows where 'day' is not "DELETED" and save to df2c
        df2c = df2b[df2b['day'] != "DELETED"].copy()
        session['df2c'] = df2c.to_json()  # Save df2c back to the session

        # Call ft_days to extract and save unique days
        ft_days()

        # Dynamically create DataFrames for each day and save to session
        prime_dfs()

        # Add frametime data from df1b to each day's DataFrame
        if 'df1b' in session:
            df1b = pd.read_json(StringIO(session['df1b']))

            # Loop through dynamically created DataFrames
            for day, variable_name in {
                'Monday': 'df3a',
                'Tuesday': 'df3b',
                'Wednesday': 'df3c',
                'Thursday': 'df3d',
                'Friday': 'df3e'
            }.items():
                if variable_name in session:
                    df = pd.read_json(StringIO(session[variable_name]))
                    frametime_row = df1b[df1b['day'] == day]
                    if not frametime_row.empty:
                        # Extract start and end times
                        start_time = pd.to_datetime(frametime_row['start_time'].values[0]).strftime('%H:%M') if not pd.isnull(frametime_row['start_time'].values[0]) else 'N/A'
                        end_time = pd.to_datetime(frametime_row['end_time'].values[0]).strftime('%H:%M') if not pd.isnull(frametime_row['end_time'].values[0]) else 'N/A'

                        # Add Start Work as the first activity
                        start_row = {
                            'day': day,
                            'activities': 'Start Work',
                            'type': 'Frametime',
                            'timespan': f"{start_time} - {start_time}",
                            'minutes': 0
                        }
                        df.loc[-1] = start_row  # Add row at the beginning
                        df.index = df.index + 1  # Shift index
                        df.sort_index(inplace=True)

                        # Add End Work as the last activity
                        end_row = {
                            'day': day,
                            'activities': 'End Work',
                            'type': 'Frametime',
                            'timespan': f"{end_time} - {end_time}",
                            'minutes': 0
                        }
                        df.loc[len(df)] = end_row  # Add row at the end

                    # Save updated DataFrame back to the session
                    session[variable_name] = df.to_json()

        # Additional processing for all dynamically created DataFrames
        for variable_name in ['df3a', 'df3b', 'df3c', 'df3d', 'df3e']:
            if variable_name in session:
                df = pd.read_json(StringIO(session[variable_name]))

                # Add pre lesson 5-min teaching gaps
                df = pre_gaps(df)

                # Add post lesson 5-min teaching gaps
                df = post_gaps(df)

                # Merge adjacent pre- and post lesson 5-min teaching gaps into between gaps
                df = between_gaps(df)

                # Catch gap violations
                gap_violations(df)

                # Add planning blocks
                df = planning_block(df)

                # Save the updated DataFrame back to the session
                session[variable_name] = df.to_json()

        # Catch frametime violations and other time issues
        frametime_violations()
        time_checker()
        generate_plain_text_report()
        generate_pdf()

        # Save all dynamically created DataFrames into a consolidated 'dataframes' session key
        dataframes = {}
        for variable_name in ['df3a', 'df3b', 'df3c', 'df3d', 'df3e']:
            if variable_name in session:
                df = pd.read_json(StringIO(session[variable_name]))
                dataframes[variable_name] = df.to_json()

        # Save consolidated dataframes to session
        session['dataframes'] = dataframes
        session.modified = True  # Ensure session is marked as modified
        generate_plain_text_schedule()


        return jsonify({'message': 'Schedule updated successfully!'}), 200

    except Exception as e:
        current_app.logger.error(f"Error in updated_schedule: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
