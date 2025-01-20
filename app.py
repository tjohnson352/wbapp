from flask import Flask, render_template, redirect, flash, session
from flask_session import Session
import sqlite3
import os
import pandas as pd
from io import StringIO
from blueprints.home import home_blueprint
from blueprints.edit_schedule import edit_schedule_blueprint
from blueprints.dataframe_view import dataframe_view_bp
from blueprints.meta1 import meta1_blueprint
from blueprints.report_generation import report_blueprint
from helpers.database_functions import save_review
from helpers.load_schools import load_schools
from blueprints.privacy_policy import privacy_policy_blueprint
import bcrypt


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
app.register_blueprint(report_blueprint)
app.register_blueprint(privacy_policy_blueprint)



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


from flask import render_template, request, session, make_response
import pdfkit

@app.route("/download_pdf")
def download_pdf():
    # Retrieve full name from the session
    full_name = session.get('full_name', 'User')  # Default to "User" if not in session

    # Clean up the full name for the filename (e.g., replace spaces with underscores)
    sanitized_name = full_name.replace(" ", "_")

    # Generate the dynamic filename
    file_name = f"{sanitized_name}_schedule_report.pdf"

    # Use the same context as `schedule_summary()` to generate the PDF
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

    # Render the `schedule_summary.html` template with the context
    rendered = render_template(
        'schedule_summary.html',
        ft_days=ft_days,
        off_days=off_days,
        df_names=df_names,
        dataframes=dataframes,
        plain_text_report=session.get('plain_text_report', "No report available."),
        plain_text_schedule=session.get('plain_text_schedule', "No schedule available.")
    )

    # Generate the PDF
    pdf = pdfkit.from_string(rendered, False)

    # Send the PDF to the user for download with the dynamic filename
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process registration form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        school_id = request.form['school_id']
        password = request.form['password']
        consent = request.form.get('consent') == 'on'  # Checkbox value is "on" if checked

        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Database operations
            conn = sqlite3.connect("user_data.db")
            cursor = conn.cursor()

            # Insert user into the `users` table
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, consent)
                VALUES (?, ?, ?, ?, ?)
            """, (first_name, last_name, email, hashed_password.decode('utf-8'), consent))
            user_id = cursor.lastrowid  # Retrieve the newly created user's ID

            # Insert school_name into the `meta1` table
            cursor.execute("""
                INSERT INTO meta1 (id, school_name)
                VALUES (?, ?)
            """, (user_id, school_name))
            
            conn.commit()
            conn.close()

            flash("Registration successful! Please verify your email to activate your account.", "success")
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash("Email or username already exists. Please use another.", "error")
            return redirect('/register')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "error")
            return redirect('/register')

    # Load schools and pass them to the template
    schools = load_schools()
    return render_template('register.html', schools=schools)

if __name__ == '__main__':
    app.run(debug=True)
