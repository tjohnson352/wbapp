from flask import Blueprint, render_template, request, session
import pandas as pd

# Define the blueprint
dataframe_view_bp = Blueprint('dataframe_view', __name__, url_prefix='/')

@dataframe_view_bp.route('/df_view', methods=['GET', 'POST'])
def df_view():
    """
    View any DataFrame stored in the session for debugging purposes.
    """
    df_name = None
    df_html = None

    if request.method == 'POST':
        # Get the DataFrame name from the form input
        df_name = request.form.get('df_name')

        # Check if the DataFrame exists in the session
        if df_name in session:
            try:
                # Load the DataFrame and convert it to an HTML table
                df = pd.read_json(session[df_name])
                df_html = df.to_html(index=False)
            except Exception as e:
                df_html = f"<p>Error loading DataFrame: {str(e)}</p>"
        else:
            df_html = f"<p>DataFrame '{df_name}' not found in the session.</p>"

    # Render the HTML form and table
    return render_template('df_view.html', df_name=df_name, df_html=df_html)

