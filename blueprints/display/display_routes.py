from flask import Blueprint, session, render_template
import pandas as pd

display_blueprint = Blueprint('display', __name__)

def get_dataframe_from_session(key):
    """Helper function to retrieve a DataFrame from the session."""
    if 'dataframes' in session and key in session['dataframes']:
        return pd.read_json(session['dataframes'][key])
    return None

@display_blueprint.route('/data/<key>', methods=['GET'])
def display_data(key):
    """Generic route to display a DataFrame."""
    df = get_dataframe_from_session(key)
    if df is not None:
        return render_template('tables/df_template.html', df=df, title=key.upper())
    return f"Data not available for {key.upper()}."

@display_blueprint.route('/schedule/<day>', methods=['GET'])
def display_day_schedule(day):
    """Route to display day-specific schedules."""
    key = f"df4{day[0].lower()}"
    df = get_dataframe_from_session(key)
    if df is not None:
        return render_template('tables/df_template.html', df=df, title=f"{day.capitalize()} Activities")
    return f"Data not available for {day.capitalize()}."
