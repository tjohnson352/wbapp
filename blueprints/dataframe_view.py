from flask import Blueprint, render_template, request, session
import pandas as pd
from io import StringIO


# Define the blueprint
dataframe_view_bp = Blueprint('dataframe_view', __name__, url_prefix='/')

@dataframe_view_bp.route('/df_view', methods=['GET', 'POST'])
def df_view():
    """
    View any DataFrame stored in the session for debugging purposes.
    """
    df_name = None
    df_html = None

    # Separate session variables into DataFrames and other variables
    dataframes = {
        key: session.get(key)
        for key in session.keys()
        if key.startswith('df') and key != 'df_names'
    }
    variables = {
        key: session.get(key)
        for key in session.keys()
        if not key.startswith('df')
    }

    if request.method == 'POST':
        # Get the DataFrame name from the dropdown menu
        df_name = request.form.get('df_name')

        if not dataframes:
            df_html = "<p>No DataFrames are available in the session.</p>"
        elif df_name in dataframes:
            try:
                # Load the DataFrame and convert it to an HTML table
                df = pd.read_json(StringIO(dataframes[df_name]))
                df_html = df.to_html(index=False)
            except ValueError as e:
                df_html = f"<p>Error: The content of '{df_name}' is not a valid DataFrame JSON. Details: {str(e)}</p>"
            except Exception as e:
                df_html = f"<p>Error loading DataFrame: {str(e)}</p>"
        else:
            df_html = f"<p>DataFrame '{df_name}' not found in the session.</p>"

    # Render the HTML form and table
    return render_template(
        'df_view.html',
        df_name=df_name,
        df_html=df_html,
        session_vars=variables,
        dataframes=dataframes
    )



