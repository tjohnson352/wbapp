from flask import Blueprint, render_template, session
import pandas as pd

data_routes = Blueprint('data_routes', __name__)

@data_routes.route('/<df_name>', methods=['GET'])
def display_data(df_name):
    """
    Generic route to display any DataFrame stored in the session.
    """
    if df_name in session:
        df = pd.read_json(session[df_name])
        title = f"{df_name.replace('_', ' ').title()} Data"
        return render_template('tables/df_template.html', df=df, title=title)
    return f"Data for {df_name} not available."
