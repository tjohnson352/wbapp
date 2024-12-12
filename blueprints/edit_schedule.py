from flask import Blueprint, render_template, session, request, jsonify, current_app
import pandas as pd
from helpers.add_teaching_gaps import post_gaps, pre_gaps, between_gaps, gap_violations
from helpers.total_minutes import total_minutes
from helpers.time_checker import time_checker


edit_schedule_blueprint = Blueprint('edit_schedule', __name__)

@edit_schedule_blueprint.route('/days', methods=['GET', 'POST'])
def display_schedule():
    """Display and update df2b to allow the user to edit days."""

    if request.method == 'POST':
        try:
            # Parse the updated data from the request
            updated_data = request.get_json().get('updated_data', [])
            if not updated_data:
                return jsonify({'error': 'No data provided in the request.'}), 400

            # Load df2b from session
            df2b_json = session.get('df2b')
            if not df2b_json:
                return jsonify({'error': 'df2b not found in session.'}), 400

            # Convert JSON data to a DataFrame
            df2b = pd.read_json(df2b_json)
            if len(updated_data) != len(df2b):
                return jsonify({'error': 'Mismatch between updated data and current schedule rows.'}), 400

            # Update the 'day' column in the DataFrame
            for index, row in enumerate(updated_data):
                if index < len(df2b):
                    day_value = row.get('day', 'Assign or Delete')
                    if day_value:  # Ensure day value is not None
                        df2b.at[index, 'day'] = day_value

            # Save the updated DataFrame back to the session
            session['df2b'] = df2b.to_json()
            current_app.logger.info(f"Updated df2b DataFrame: {df2b}")
            return jsonify({'message': 'Schedule updated successfully!'}), 200

        except Exception as e:
            current_app.logger.error(f"Error updating schedule: {str(e)}", exc_info=True)
            return jsonify({'error': 'An error occurred while updating the schedule.'}), 500

    # GET method: Display the schedule
    try:
        # Log session data
        current_app.logger.info(f"Session data keys: {list(session.keys())}")

        # Check if df2b exists in the session
        df2b_json = session.get('df2b')
        if not df2b_json:
            current_app.logger.error("df2b not found in session.")
            return render_template('edit_schedule.html', table=None)

        # Parse df2b from JSON
        df2b = pd.read_json(df2b_json)
        current_app.logger.info(f"Loaded df2b DataFrame: {df2b}")
        return render_template('edit_schedule.html', table=df2b)

    except Exception as e:
        current_app.logger.error(f"Error loading schedule for editing: {str(e)}", exc_info=True)
        return render_template('edit_schedule.html', table=None)
    

from flask import Blueprint, request, session, jsonify, current_app
import pandas as pd


@edit_schedule_blueprint.route('/updated_schedule', methods=['POST'])
def updated_schedule():
    try:
        # Parse JSON from the request
        updated_data = request.get_json().get('updated_data', [])
        current_app.logger.info(f"Received updated data: {updated_data}")

        # Retrieve the current DataFrame from session
        df2b_json = session.get('df2b')
        if not df2b_json:
            current_app.logger.error("df2b not found in session.")
            return jsonify({'error': 'df2b not found in session.'}), 400

        df2b = pd.read_json(df2b_json)

        # Update the DataFrame with the new day values
        for index, row in enumerate(updated_data):
            if index < len(df2b):
                df2b.at[index, 'day'] = row.get('day', 'Assign or Delete')

        # Save the updated DataFrame back to the session
        session['df2b'] = df2b.to_json()
        
        # Extract all rows of df2b to df2d except those with column day == DELETE
        df2d = df2b[df2b['day'] != "DELETE"].copy() 

        # Sort df2d by columns = day, timespan
        day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
        df2d['day_order'] = df2d['day'].map(day_order)
        df2d['day'] = pd.Categorical(df2d['day'], categories=day_order.keys(), ordered=True)
        df2d.sort_values(by=['day', 'timespan'], inplace=True)
        df2d.drop(columns=['day_order'], inplace=True, errors='ignore')
        df2d.reset_index(drop=True, inplace=True)

        current_app.logger.info(f"Updated df2b: {df2b}")

        # Create separate DataFrames for each day
        df3a = df2d[df2d['day'] == 'Monday'].reset_index(drop=True)
        df3b = df2d[df2d['day'] == 'Tuesday'].reset_index(drop=True)
        df3c = df2d[df2d['day'] == 'Wednesday'].reset_index(drop=True)
        df3d = df2d[df2d['day'] == 'Thursday'].reset_index(drop=True)
        df3e = df2d[df2d['day'] == 'Friday'].reset_index(drop=True)

        # Add frametime data from df1b to each day's DataFrame
        if 'df1b' in session:
            df1b = pd.read_json(session['df1b'])

            for day, df in [('Monday', df3a), ('Tuesday', df3b), ('Wednesday', df3c), ('Thursday', df3d), ('Friday', df3e)]:
                frametime_row = df1b[df1b['day'] == day]
                if not frametime_row.empty:
                    # start_time = frametime_row['start_time'].values[0]
                    start_time = pd.to_datetime(frametime_row['start_time'].values[0]).strftime('%H:%M') if not pd.isnull(frametime_row['start_time'].values[0]) else 'N/A'
                    # end_time = frametime_row['end_time'].values[0]
                    end_time = pd.to_datetime(frametime_row['end_time'].values[0]).strftime('%H:%M') if not pd.isnull(frametime_row['end_time'].values[0]) else 'N/A'


                    # Add Start Work as the first activity
                    start_row = {
                        'day': day,
                        'activities': 'Start Work',
                        'type': 'FRAMETIME',
                        'timespan': start_time,
                        'minutes': 'N/A'
                    }
                    df.loc[-1] = start_row  # Add row at the beginning
                    df.index = df.index + 1  # Shift index
                    df.sort_index(inplace=True)

                    # Add End Work as the last activity
                    end_row = {
                        'day': day,
                        'activities': 'End Work',
                        'type': 'FRAMETIME',
                        'timespan': end_time,
                        'minutes': 'N/A'
                    }
                    df.loc[len(df)] = end_row  # Add row at the end
            
        # add pre lesson 5-min teaching gaps
        df3a = pre_gaps(df3a)
        df3b = pre_gaps(df3b)
        df3c = pre_gaps(df3c)
        df3d = pre_gaps(df3d)
        df3e = pre_gaps(df3e)

        # add post lesson 5-min teaching gaps
        df3a = post_gaps(df3a)
        df3b = post_gaps(df3b)
        df3c = post_gaps(df3c)
        df3d = post_gaps(df3d)
        df3e = post_gaps(df3e)
        
        # merge adjacent pre- and post lesson 5-min teaching gaps into between gap
        df3a = between_gaps(df3a)
        df3b = between_gaps(df3b)
        df3c = between_gaps(df3c)
        df3d = between_gaps(df3d)
        df3e = between_gaps(df3e)

        # catches gap violations
        df3a = gap_violations(df3a)
        df3b = gap_violations(df3b)
        df3c = gap_violations(df3c)
        df3d = gap_violations(df3d)
        df3e = gap_violations(df3e)

        # Save the DataFrames to the session
        session['df2d'] = df2d.to_json()
        session['df3a'] = df3a.to_json()
        session['df3b'] = df3b.to_json()
        session['df3c'] = df3c.to_json()
        session['df3d'] = df3d.to_json()
        session['df3e'] = df3e.to_json()

        total_minutes()
        time_checker()


        return jsonify({'message': 'Schedule updated successfully!'}), 200

    except Exception as e:
        current_app.logger.error(f"Error in updated_schedule: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
