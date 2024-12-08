from flask import Blueprint, render_template, session, request, jsonify, current_app
import pandas as pd

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


@edit_schedule_blueprint.route('/save_schedule', methods=['POST'])
def save_schedule():
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
        current_app.logger.info(f"Updated df2b: {df2b}")

        return jsonify({'message': 'Schedule updated successfully!'}), 200

    except Exception as e:
        current_app.logger.error(f"Error in save_schedule: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
