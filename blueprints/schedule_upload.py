from flask import Blueprint, render_template, request, session, redirect, flash, current_app, url_for
import os
import pandas as pd
from helpers.pdf_processing import extract_text_from_pdf, process_schedule_data
from helpers.names_coding import validate_names, update_user_school_id, is_own_school
from helpers.clean_raw_data import clean_data
from helpers.auth_functions import get_db_connection
from helpers.file_storage import validate_and_save_uploaded_file
from flask import get_flashed_messages

schedule_upload_bp = Blueprint('schedule_upload_bp', __name__)

# Configurable upload folder path
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

@schedule_upload_bp.route('/', methods=['GET', 'POST'])
def home():
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for("auth_bp.login"))
    
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

        # Fetch first_name, last_name, and is_admin
        cursor.execute("""
            SELECT first_name, last_name 
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        user_details = cursor.fetchone()

        if not user_details:
            flash("User not found in the database.", 'error')
            return redirect(url_for('auth_bp.login'))

        session['first_name'], session['last_name'] = user_details

        # Fetch admin level
        cursor.execute("""
            SELECT is_admin FROM user_auth WHERE user_id = ?
        """, (user_id,))
        admin_level = cursor.fetchone()

        # Store admin level in session
        session['is_admin'] = admin_level[0] if admin_level else 0

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
            data = extract_text_from_pdf(filepath)
            
            if not isinstance(data, list) or not all(isinstance(line, str) for line in data):
                raise ValueError("Extracted PDF content is not valid.")

            df1a = pd.DataFrame(data, columns=['Content'])
            df1a = clean_data(df1a) 

            session['df1a'] = df1a.to_json()

            # Process structured data and save temporary files
            df2a, df2b = process_schedule_data()

            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()
            
            # Get admin level from session
            is_admin = session.get('is_admin', 0)

            # Always run name validation to determine if the admin is evaluating their own schedule
            full_name = session.get('full_name', '').strip().lower()
            consent_full_name = (session.get('first_name', '') + " " + session.get('last_name', '')).strip().lower()
            session['consent_full_name'] = consent_full_name

            # Check if the name validation passes (1) or fails (0)
            is_own_schedule = 1 if validate_names() else 0
            session['is_own_schedule'] = is_own_schedule  # Store result in session

            # Skip restriction only if the user is a central officer (4) or admin (5)
            if is_admin not in [3, 4, 5] and not is_own_schedule:
                
                flash("Data Privacy Violation!<br>The uploaded schedule is not yours.<br>Due to GDPR compliance, processing was stopped.", 'danger')
                return redirect(url_for('schedule_upload_bp.home'))  
            
            update_user_school_id()
            is_own_school()

            if is_admin == 3 and session.get('is_school') == 0:
                flash("Data Privacy Violation!<br>You can only process you own schedule or, as a lokal officer, schedules of teachers at your school.<br>Due to GDPR compliance, processing was stopped.", 'danger')
                return redirect(url_for('schedule_upload_bp.home'))  

            flash('File uploaded and processed successfully!', 'success')
            return redirect(url_for('meta1.meta1'))

        except Exception as e:
            print(f"Error in handle_schedule_upload: {e}")
            flash("An error occurred during schedule processing.", 'danger')
            return redirect(url_for('schedule_upload_bp.home'))

    return render_template('upload_schedule.html')
