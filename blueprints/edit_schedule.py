from flask import Blueprint, render_template, session, request, jsonify, current_app, url_for, flash, redirect
import pandas as pd
from helpers.add_teaching_gaps import post_gaps, pre_gaps, between_gaps, gap_violations, frametime_violations, planning_block
from helpers.time_checker import time_checker
from helpers.ft_days import ft_days, prime_dfs
from io import StringIO
from helpers.database_functions import view_database, get_user_data, save_user_data

edit_schedule_blueprint = Blueprint('edit_schedule', __name__)

@edit_schedule_blueprint.route('/days', methods=['GET', 'POST'])
def display_schedule():
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for("auth_bp.login"))
    
    try:
        # Get the user_id from the session
        user_id = session.get('user_id')
        if not user_id:
            flash("User not logged in.", 'error')
            return redirect(url_for('auth_bp.login'))  # Ensure 'auth_bp' is the correct blueprint name
    except Exception as e:
        flash("An error occurred: " + str(e), 'error')
        return redirect(url_for('auth_bp.login'))  # Redirect to login in case of an unexpected error

    try:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        current_day_index = session.get('day_index', 0)

        if request.method == 'POST':
            data = request.get_json()
            current_app.logger.info(f"Received payload: {data}")  # Debugging
            print(data)

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

        def create_schedule_string():
            """
            Reads df2c from the session, creates a schedule_string by concatenating row values 
            using '*' as a joiner for cell values in each row, and '||' as a joiner for rows.
            Saves the resulting schedule_string back into the session.
            """
            try:
                # Read df2c from session
                df2c = pd.read_json(StringIO(session['df2c']))

                # Create schedule_string
                schedule_string = '||'.join(
                    '*'.join(str(cell) for cell in row)
                    for row in df2c.values
                )

                # Save schedule_string to session
                session['schedule_string'] = schedule_string
                current_app.logger.info("schedule_string successfully created and saved to session.")
            
            except Exception as e:
                current_app.logger.error(f"Error in creating schedule_string: {e}")
                raise

        def reconstruct_df2c():
            """
            Reads the schedule_string from the session, reconstructs the DataFrame (df2c_recononstructed),
            which should match the original df2c structure, including column headers,
            and saves it back to the session.
            """
            try:
                # Retrieve schedule_string and df2c from session
                schedule_string = session.get('schedule_string', '')
                if not schedule_string:
                    raise ValueError("schedule_string is missing or empty in the session.")

                df2c = pd.read_json(StringIO(session['df2c']))
                original_columns = df2c.columns  # Retrieve column names from df2c

                # Split the schedule_string into rows and cells
                rows = [row.split('*') for row in schedule_string.split('||')]

                # Convert to DataFrame
                df2c_recononstructed = pd.DataFrame(rows, columns=original_columns)

                # Save df2c_recononstructed to session
                session['df2c_recononstructed'] = df2c_recononstructed.to_json()
                current_app.logger.info("df2c_recononstructed successfully reconstructed with original headings and saved to session.")

                return df2c_recononstructed  # Return the reconstructed DataFrame for verification if needed

            except Exception as e:
                current_app.logger.error(f"Error in reconstructing df2c_recononstructed: {e}")
                raise


        create_schedule_string()
        reconstruct_df2c()


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
        save_user_data()
        view_database()
        get_user_data()
        
        

        # Save all dynamically created DataFrames into a consolidated 'dataframes' session key
        dataframes = {}
        for variable_name in ['df3a', 'df3b', 'df3c', 'df3d', 'df3e']:
            if variable_name in session:
                df = pd.read_json(StringIO(session[variable_name]))
                dataframes[variable_name] = df.to_json()

        # Save consolidated dataframes to session
        session['dataframes'] = dataframes
        session.modified = True  # Ensure session is marked as modified

        return jsonify({'message': 'Schedule updated successfully!'}), 200


    except Exception as e:
        current_app.logger.error(f"Error in updated_schedule: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
