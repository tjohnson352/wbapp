from flask import Flask, render_template, redirect, flash, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
import sqlite3
import os
import pandas as pd
from io import StringIO
from blueprints.account import account_bp
from blueprints.schedule_upload import schedule_upload_bp
from blueprints.edit_schedule import edit_schedule_blueprint
from blueprints.dataframe_view import dataframe_view_bp
from blueprints.meta1 import meta1_blueprint
from blueprints.report_generation import report_blueprint
from helpers.database_functions import save_review
from helpers.load_schools import load_schools
from blueprints.authentication import auth_bp
from blueprints.privacy_policy import privacy_policy_blueprint
import bcrypt
from helpers.database_functions import setup_database, view_database, setup_school_table
from datetime import timedelta


# Initialize the Flask app
from flask import Flask

app = Flask(__name__, static_folder='static')

# Secret key for session management
app.secret_key = os.urandom(24)

csrf = CSRFProtect(app)

# Initialize database
setup_database()
setup_school_table()

# Set session timeout to 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_USE_SIGNER'] = True

# Initialize the server-side session
Session(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/')  # This registers all auth_bp routes under /auth
app.register_blueprint(schedule_upload_bp)
app.register_blueprint(meta1_blueprint)
app.register_blueprint(edit_schedule_blueprint)
app.register_blueprint(dataframe_view_bp)
app.register_blueprint(report_blueprint)
app.register_blueprint(privacy_policy_blueprint)
app.register_blueprint(account_bp)

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


from flask import render_template, request, session, make_response, redirect, url_for
import pdfkit

from flask import render_template, request, session, make_response, redirect, url_for
import pdfkit
import pandas as pd
from io import StringIO

@app.route("/survey", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        # Capture responses
        review_q1 = request.form.get("review_q1")
        review_q2 = request.form.get("review_q2")
        review_q3 = request.form.get("review_q3", "No suggestions provided.")  # Default if empty

        # Store the responses in the session
        session['review_q1'] = review_q1
        session['review_q2'] = review_q2
        session['review_q3'] = review_q3

        # Redirect to the GET request to reload the page and display feedback
        return redirect(url_for('survey'))

    # Check if the form has been submitted
    submitted = 'review_q1' in session

    # Pass the stored responses to the template
    return render_template(
        "survey.html",
        review_q1=session.get('review_q1'),
        review_q2=session.get('review_q2'),
        review_q3=session.get('review_q3'),
        submitted=submitted
    )


@app.route("/download_pdf")
def download_pdf():
    # Retrieve full name from the session
    full_name = session.get('full_name', 'User')
    sanitized_name = full_name.replace(" ", "_")
    file_name = f"{sanitized_name}_schedule_report.pdf"

    # Retrieve DataFrames
    raw_dataframes = session.get('dataframes', {})
    dataframes = {}
    for key, value in raw_dataframes.items():
        if value:
            try:
                df = pd.read_json(StringIO(value))
                dataframes[key] = df.to_dict(orient='records')
            except Exception as e:
                print(f"Error loading DataFrame {key}: {e}")

    # Render the `schedule_summary.html` template
    rendered = render_template(
        'schedule_summary.html',
        ft_days=session.get('ft_days', []),
        off_days=session.get('off_days', []),
        df_names=session.get('df_names', []),
        dataframes=dataframes,
        plain_text_report=session.get('plain_text_report', "No report available."),
        plain_text_schedule=session.get('plain_text_schedule', "No schedule available.")
    )
    return redirect(url_for('auth_bp.dashboard'))

    # Configure pdfkit with a valid path
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

    # PDF options
    options = {
        'enable-local-file-access': '',  # Allow local resource access
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'encoding': 'UTF-8',
        'load-error-handling': 'ignore'
    }

    # Generate the PDF
    try:
        pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
    except OSError as e:
        return f"PDF generation failed: {e}"

    # Send the PDF as a downloadable file
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    return response



if __name__ == '__main__':
    app.run(debug=True)
