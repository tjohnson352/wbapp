from flask import Blueprint, render_template, session, request, jsonify, current_app
import pandas as pd
from helpers.add_teaching_gaps import post_gaps, pre_gaps, between_gaps, gap_violations
from helpers.total_minutes import total_minutes
from helpers.time_checker import time_checker


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
                start_minutes = None
                end_minutes = None
            else:
                start_time = frametime.get('start_time')  # e.g., "08:00"
                end_time = frametime.get('end_time')  # e.g., "16:00"

                if not start_time or not end_time:
                    return jsonify({'error': 'Frametime start and end times are required unless the day is marked as off.'}), 400

                # Convert time to total minutes since midnight
                start_hours, start_mins = map(int, start_time.split(':'))
                end_hours, end_mins = map(int, end_time.split(':'))
                start_minutes = start_hours * 60 + start_mins
                end_minutes = end_hours * 60 + end_mins

            # Update df1b with frametime for the current day
            current_day = days[current_day_index]
            df1b_json = session.get('df1b', '{}')
            df1b = pd.read_json(df1b_json) if df1b_json != '{}' else pd.DataFrame(columns=['day', 'start_time', 'end_time'])

            # Ensure the 'day' column exists before filtering
            if 'day' in df1b.columns:
                df1b = df1b[df1b['day'] != current_day]  # Remove any existing entry for the day

            # Add the new frametime entry
            new_frametime_entry = pd.DataFrame([{
                'day': current_day,
                'start_time': start_minutes,
                'end_time': end_minutes
            }])
            df1b = pd.concat([df1b, new_frametime_entry], ignore_index=True)
            session['df1b'] = df1b.to_json()

            # Update df2b with selected activities if it's not an off day
            df2b = pd.read_json(session.get('df2b', '{}'))

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
        df2b = pd.read_json(session.get('df2b', '{}'))
        

        return render_template('edit_schedule.html', table=df2b, current_day=current_day)

    except Exception as e:
        current_app.logger.error(f"Error in /days route: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred.'}), 500

def updated_schedule():
    try:
        df2b_json = session.get('df2b')
        if not df2b_json:
            current_app.logger.error("df2b not found in session.")
            return jsonify({'error': 'df2b not found in session.'}), 400

        df2b = pd.read_json(df2b_json)

        # Extract all rows of df2b to df2c except those with column day == DELETE
        df2c = df2b[df2b['day'] != "DELETE"].copy() 

        # Sort df2c by columns = day, timespan
#        day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
#        df2c['day_order'] = df2c['day'].map(day_order)
#        df2c['day'] = pd.Categorical(df2c['day'], categories=day_order.keys(), ordered=True)
#        df2c.sort_values(by=['day', 'timespan'], inplace=True)
#        df2c.drop(columns=['day_order'], inplace=True, errors='ignore')
#        df2c.reset_index(drop=True, inplace=True)

#        current_app.logger.info(f"Updated df2b: {df2b}")

        # Create separate DataFrames for each day
        df3a = df2c[df2c['day'] == 'Monday'].reset_index(drop=True)
        df3b = df2c[df2c['day'] == 'Tuesday'].reset_index(drop=True)
        df3c = df2c[df2c['day'] == 'Wednesday'].reset_index(drop=True)
        df3d = df2c[df2c['day'] == 'Thursday'].reset_index(drop=True)
        df3e = df2c[df2c['day'] == 'Friday'].reset_index(drop=True)

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
        session['df2c'] = df2c.to_json()
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
