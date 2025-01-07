from flask import Blueprint, render_template, request, session, redirect, flash, current_app
import os
import pandas as pd
import fitz  # PyMuPDF for reading PDFs
from werkzeug.utils import secure_filename
from blueprints.data_processing import structure_data
from helpers.clean_raw_data import clean_data
from helpers.database_functions import setup_database, view_database
import inspect

home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/', methods=['GET', 'POST'])
def home():
    
    setup_database()
    view_database()

    """Handle home page requests for uploading schedules."""
    if request.method == 'POST':
        try:
            uploaded_file = request.files.get('schedule_pdf')
            if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
                flash('Invalid file type. Please upload a PDF file.', 'error')
                return render_template('home.html')

            # Limit file size
            uploaded_file.seek(0, os.SEEK_END)
            file_size_mb = uploaded_file.tell() / (1024 * 1024)
            uploaded_file.seek(0)
            if file_size_mb > 5:
                flash('The uploaded file is too large. Please upload a file smaller than 5 MB.', 'error')
                return render_template('home.html')

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
                    return render_template('home.html')

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
                return render_template('home.html')

            session['df1a'] = df1a.to_json()

            df2a, df2b = structure_data()
            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()

            flash('File uploaded and processed successfully!', 'success')
            return redirect('/meta1')  # Redirect to the next step

        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')
            current_app.logger.error(f"Error in home route: {e}")

    # For GET request, display the upload form
    return render_template('home.html')
