from flask import Blueprint, render_template, session, request, jsonify, current_app
import pandas as pd
from helpers.add_teaching_gaps import post_gaps, pre_gaps, between_gaps, gap_violations
from helpers.total_minutes import total_minutes
from helpers.time_checker import time_checker
from helpers.time_adjuster import time8

@edit_schedule_blueprint.route('/days', methods=['GET', 'POST'])
def display_schedule():
    try:
        from helpers.time_adjuster import time8  # Ensure time8 is imported correctly

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        current_day_index = session.get('day_index', 0)

        if request.method == 'POST':
            data = request.get_json()
            current_app.logger.info(f"Received payload: {data}")  # Debugging

            if not data:
                return jsonify({'error': 'No data received.'}), 400

            frametime = data.get('frametime', {})
            selected_activities = data.get('selected_activities', [])

            if not frametime:
                return jsonify({'error': 'Invalid payload structure.'}), 400

            # Validate frametime
            start_time = frametime.get('start_time')
            end_time = frametime.get('end_time')
            if not start_time or not end_time:
                return jsonify({'error': 'Frametime start and end times are required.'}), 400

            # Update df1b with frametime for the current day
            current_day = days[current_day_index]
            df1b = pd.read_json(session.get('df1b', '{}'))
            df1b = df1b[df1b['day'] != current_day]  # Remove any existing entry for the day

            # Convert start_time and end_time to total minutes
            new_frametime_entry = pd.DataFrame([{
                'day': current_day,
                'start_time': int(start_time.split(':')[0]) * 60 + int(start_time.split(':')[1]),
                'end_time': int(end_time.split(':')[0]) * 60 + int(end_time.split(':')[1])
            }])
            df1b = pd.concat([df1b, new_frametime_entry], ignore_index=True)

            # Convert total minutes back to hh:mm format using time8
            df1b['start_time'] = df1b['start_time'].apply(lambda x: time8(x) if pd.notnull(x) else x)
            df1b['end_time'] = df1b['end_time'].apply(lambda x: time8(x) if pd.notnull(x) else x)

            # Save updated df1b to session
            session['df1b'] = df1b.to_json()

            # Update df2b with selected activities
            df2b = pd.read_json(session.get('df2b', '{}'))
            for index in selected_activities:
                df2b.at[index, 'day'] = current_day
            session['df2b'] = df2b.to_json()

            # Move to the next day
            if current_day_index < len(days) - 1:
                session['day_index'] = current_day_index + 1
                return jsonify({'message': f'Activities assigned to {current_day}.', 'complete': False}), 200
            else:
                session.pop('day_index', None)  # Clear day_index after Friday
                return jsonify({'message': 'All activities assigned.', 'complete': True}), 200

        # GET request: Display the schedule for the current day
        current_day = days[current_day_index]
        df2b = pd.read_json(session.get('df2b', '{}'))
        return render_template('edit_schedule.html', table=df2b, current_day=current_day)

    except Exception as e:
        current_app.logger.error(f"Error in /days route: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred.'}), 500


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
