from flask import Blueprint, render_template, session
import pandas as pd

edit_schedule_blueprint = Blueprint('edit_schedule', __name__)

@edit_schedule_blueprint.route('/days', methods=['GET'])
def display_schedule():
    """Display df2b to allow the user to edit days."""
    from flask import current_app

    # Log session data
    current_app.logger.info(f"Session data: {session.keys()}")

    # Check if df2b exists in the session
    df2b_json = session.get('df2b', None)
    if not df2b_json:
        current_app.logger.error("df2b not found in session.")
        return render_template('edit_schedule.html', table=None)

    # Parse df2b from JSON
    try:
        df2b = pd.read_json(df2b_json)
        current_app.logger.info(f"df2b DataFrame: {df2b}")
        return render_template('edit_schedule.html', table=df2b)
    except Exception as e:
        current_app.logger.error(f"Error parsing df2b JSON: {e}")
        return render_template('edit_schedule.html', table=None)
