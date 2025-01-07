from flask import Flask, render_template, redirect, flash, session
from flask_session import Session
import os
import pandas as pd
from io import StringIO
from blueprints.home import home_blueprint
from blueprints.edit_schedule import edit_schedule_blueprint
from blueprints.dataframe_view import dataframe_view_bp
from blueprints.updated_schedule import updated_schedule_blueprint
from blueprints.meta1 import meta1_blueprint
from blueprints.report_generation import report_blueprint


# Initialize the Flask app
app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_USE_SIGNER'] = True

# Initialize the server-side session
Session(app)

# Register blueprints
app.register_blueprint(home_blueprint)
app.register_blueprint(meta1_blueprint)
app.register_blueprint(edit_schedule_blueprint)
app.register_blueprint(dataframe_view_bp)
app.register_blueprint(updated_schedule_blueprint)
app.register_blueprint(report_blueprint)


# Set the upload folder for temporary PDFs
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Optional: If you have a feedback route, uncomment below
# from helpers.submit_feedback import submit_feedback
# app.add_url_rule('/submit-feedback', view_func=submit_feedback, methods=['POST'])

# Optional: Clear session selectively at the end of each request
@app.teardown_request
def clear_session(exception=None):
    """
    Clear non-essential session data at the end of each request,
    while retaining critical keys for functionality.
    """
    essential_keys = ['user_id', 'role']  # Add keys you want to keep
    for key in list(session.keys()):
        if key not in essential_keys:
            session.pop(key, None)


@app.route('/schedule_summary')
def schedule_summary():
    """
    Route to display the weekly schedule summary.
    """
    # Retrieve relevant session data
    ft_days = session.get('ft_days', [])
    off_days = session.get('off_days', [])
    df_names = session.get('df_names', [])
    raw_dataframes = session.get('dataframes', {})

    # Convert JSON strings back to DataFrames and then to JSON-like structures
    dataframes = {}
    for key, value in raw_dataframes.items():
        if value:  # Check if value is not None
            try:
                df = pd.read_json(StringIO(value))
                dataframes[key] = df.to_dict(orient='records')  # Convert to list of dictionaries
            except Exception as e:
                print(f"Error loading DataFrame {key}: {e}")

    # Render the schedule summary
    return render_template(
        'schedule_summary.html',
        ft_days=ft_days,
        off_days=off_days,
        df_names=df_names,
        dataframes=dataframes,
        plain_text_report=session.get('plain_text_report', "No report available."),
        plain_text_schedule=session.get('plain_text_schedule', "No schedule available.")
    )


@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    pdf_path = generate_pdf()
    return f"PDF report generated and saved to {pdf_path}"



if __name__ == '__main__':
    app.run(debug=True)
