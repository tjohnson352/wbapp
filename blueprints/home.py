from flask import Blueprint, render_template, request, session, redirect, flash, current_app, url_for
import os
import pandas as pd
from blueprints.data_processing import structure_data
from helpers.names_coding import validate_names
from helpers.clean_raw_data import clean_data
from helpers.auth_functions import get_db_connection
from helpers.pdf_processing import extract_pdf_content
from helpers.file_storage import validate_and_save_uploaded_file
from flask import get_flashed_messages

home_blueprint = Blueprint('home', __name__)

# Configurable upload folder path
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

@home_blueprint.route('/', methods=['GET', 'POST'])
def home():
    # Clear irrelevant flash messages before rendering
    _ = get_flashed_messages(with_categories=True)
    conn = None
    try:
        # Get the user_id from the session
        user_id = session.get('user_id')
        if not user_id:
            flash("User not logged in.", 'error')
            return redirect(url_for('auth_bp.login'))

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch first_name and last_name
        cursor.execute("""
            SELECT first_name, last_name
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        user_details = cursor.fetchone()

        if not user_details:
            flash("User not found in the database.", 'error')
            return redirect(url_for('auth_bp.login'))

        # Add first_name and last_name to the session
        session['first_name'], session['last_name'] = user_details

    except Exception as e:
        flash("An error occurred while retrieving user details.", 'error')
        current_app.logger.error(f"Error retrieving user details: {e}")
    finally:
        if conn:
            conn.close()

    # Handle POST request
    if request.method == 'POST':
        try:
            # Validate and save uploaded file
            uploaded_file = request.files.get('schedule_pdf')
            filepath = validate_and_save_uploaded_file(uploaded_file, UPLOAD_FOLDER)
            session['uploaded_pdf'] = filepath

            # Process the uploaded PDF
            data = extract_pdf_content(filepath)
            if not isinstance(data, list) or not all(isinstance(line, str) for line in data):
                raise ValueError("Extracted PDF content is not valid.")

            df1a = pd.DataFrame(data, columns=['Content'])
            df1a = clean_data(df1a) 

            session['df1a'] = df1a.to_json()

            # Process structured data and save temporary files
            df2a, df2b = structure_data()

            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()
            

            # Validate names
            full_name = session.get('full_name', '').lower()
            if not full_name:
                flash("Session error: Full name not found.", 'error')
                return redirect(url_for('auth_bp.login'))

            consent_full_name = session['first_name'] + " " + session['last_name']
            if not validate_names(full_name, consent_full_name):
                flash("GDPR violation: your name does not match the name on this schedule", 'error')
                return render_template('index.html')

            flash('File uploaded and processed successfully!', 'success')
            return redirect(url_for('meta1.meta1'))

        except ValueError as e:
            flash(f"Validation error: {str(e)}", 'error')
        except Exception as e:
            flash('An unexpected error occurred during file processing. Please contact support.', 'error')
            current_app.logger.error(f"Error processing uploaded file: {e}")
            
    return render_template('index.html')
