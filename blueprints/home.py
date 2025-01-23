from flask import Blueprint, render_template, request, session, redirect, flash, current_app, url_for
import os
import pandas as pd
import fitz  # PyMuPDF for reading PDFs
from werkzeug.utils import secure_filename
from blueprints.data_processing import structure_data
from helpers.names_coding import db_save_user_into
from helpers.clean_raw_data import clean_data
from helpers.database_functions import setup_database, view_database, setup_school_table


home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/', methods=['GET', 'POST'])
def home():
    # Initialize database
    setup_database()
    setup_school_table()
    view_database()

    # Redirect to login if email is not in session
    if 'email' not in session:
        return redirect(url_for('auth_bp.login'))

    """Handle home page requests for uploading schedules."""
    if request.method == 'POST':
        try:
            # Temporarily store the current user details from session
            email = session.get('email')
            user_name = session.get('user_name')
            user_id = session.get('user_id')

            # Clear the session
            session.clear()

            # Restore the user details in the session
            session['email'] = email
            session['user_name'] = user_name
            session['user_id'] = user_id

            # Retrieve user inputs for consent
            consent_checkbox = request.form.get('consent')  # Checkbox input
            user_name = request.form.get('user_name')  # Typed name input

            # Validate consent inputs
            if not consent_checkbox:
                flash('You must agree to the consent checkbox to proceed.', 'error')
                return render_template('index.html')

            if not user_name or user_name.strip() == '':
                flash('You must enter your full name to proceed.', 'error')
                return render_template('index.html')

            # Store consent data in the session
            session['consent_statement'] = consent_checkbox
            session['consent_full_name'] = user_name.strip()

            # Handle file upload
            uploaded_file = request.files.get('schedule_pdf')
            if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
                flash('Invalid file type. Please upload a PDF file.', 'error')
                return render_template('index.html')

            # Limit file size
            uploaded_file.seek(0, os.SEEK_END)
            file_size_mb = uploaded_file.tell() / (1024 * 1024)
            uploaded_file.seek(0)
            if file_size_mb > 5:
                flash('The uploaded file is too large. Please upload a file smaller than 5 MB.', 'error')
                return render_template('index.html')

            # Save uploaded file
            upload_folder = 'uploads'
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(upload_folder, filename)
            uploaded_file.save(filepath)

            # Store the file path in the session
            session['uploaded_pdf'] = filepath

            # Extract text from the PDF and create df1a
            data = []
            with fitz.open(filepath) as pdf:
                if pdf.page_count == 0:
                    flash('The uploaded PDF file appears to be empty.', 'error')
                    return render_template('index.html')

                for page_num in range(pdf.page_count):
                    page = pdf.load_page(page_num)
                    text = page.get_text()
                    lines = text.splitlines()
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    data.extend(cleaned_lines)

            df1a = pd.DataFrame(data, columns=['Content'])
            df1a = clean_data(df1a)

            if 'Content' not in df1a.columns:
                flash('Invalid PDF content structure.', 'error')
                return render_template('index.html')

            session['df1a'] = df1a.to_json()

            df2a, df2b = structure_data()
            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()

            # Verify name match
            full_name = session['full_name'].lower()
            consent_full_name = session['consent_full_name'].lower()

            full_name_parts = full_name.split(" ")
            session['full_name_parts'] = full_name_parts
            consent_name_parts = consent_full_name.split(" ")
            session['consent_name_parts'] = consent_name_parts


            if len(consent_name_parts) < 2:
                flash("Include First and Last names", 'error')
                print("too short")
                return render_template('index.html')

            if not all(part in full_name_parts for part in consent_name_parts):
                flash("Your typed name does not match the name on the schedule. GDPR regulations allow you to consent only to providing your own personal information.", 'error')
                print("mismatched")

                return render_template('index.html')
            
            else:
                flash('File uploaded and processed successfully!', 'success')
                db_save_user_into()
                return redirect('/meta1')  # Redirect to the next step

        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')
            current_app.logger.error(f"Error in home route: {e}")

    # For GET request, display the upload form
    return render_template('index.html')
