from flask import Blueprint, render_template, request, session, redirect, flash, current_app
import os
import pandas as pd
import fitz  # PyMuPDF for reading PDFs
from werkzeug.utils import secure_filename
from blueprints.data_processing import structure_data
from helpers.clean_raw_data import clean_data
import inspect

home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/', methods=['GET', 'POST'])
def home():
    #from cryptography.fernet import Fernet

    # Generate a valid Fernet key
    #key = Fernet.generate_key()
    #print(f"Generated Fernet Key: {key.decode()}")

    """Handle home page requests for uploading schedules."""
    if request.method == 'POST':
        try:
            uploaded_file = request.files.get('schedule_pdf')
            if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
                flash('Invalid file type. Please upload a PDF file.', 'error')
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
                for page_num in range(pdf.page_count):
                    page = pdf.load_page(page_num)
                    text = page.get_text()
                    lines = text.splitlines()
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    data.extend(cleaned_lines)
            df1a = pd.DataFrame(data, columns=['Content'])

            df1a = clean_data(df1a)
            session['df1a'] = df1a.to_json() #must be stored before 

            df2a,df2b = structure_data()

            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()


            return redirect('/meta1')  # Redirect to the next step

        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')

    # For GET request, display the upload form
    return render_template('home.html')