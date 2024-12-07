from flask import Blueprint, render_template, request, session, redirect, flash, current_app
import os
import pandas as pd
import fitz  # PyMuPDF for reading PDFs
from werkzeug.utils import secure_filename
from blueprints.data_processing import structure_data
from helpers.clean_raw_data import clean_data
import inspect

home_blueprint = Blueprint('home', __name__)

def collect_frametime_input(request):
    """Collect frametime input from the form."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    frametime_data = []

    for day in days:
        is_off = request.form.get(f"{day}_off", None)  # Checkbox value
        if is_off:  # If OFF checkbox is checked, record NA
            frametime_data.append({'day': day, 'start_time': None, 'end_time': None})
        else:
            start_time = request.form.get(f"{day}_start")
            end_time = request.form.get(f"{day}_end")

            # Validate time range
            if not start_time or not end_time:
                raise ValueError(f"Start and End times for {day} are required if not OFF.")
            if start_time < "08:00" or end_time > "18:00":
                raise ValueError(f"Times for {day} must be between 08:00 and 18:00.")
            if start_time >= end_time:
                raise ValueError(f"Start time must be earlier than End time for {day}.")

            frametime_data.append({'day': day, 'start_time': start_time, 'end_time': end_time})

    return frametime_data

@home_blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Handle home page requests for uploading schedules and defining work parameters."""
    message = None

    if request.method == 'POST':
        try:
            # Collect and validate frametime input from the form
            frametime_data = collect_frametime_input(request)

            # Create a DataFrame for frametime input
            df1b = pd.DataFrame(frametime_data)
            session['df1b'] = df1b.to_json()


            # Get the work percentage from the form
            work_percent = request.form.get('work_percent', None)
            session['work_percent'] = work_percent

            if not work_percent:
                flash('Please enter your work percentage.', 'error')
                return render_template('home.html', message=message)

            # Validate work percentage
            work_percent = int(work_percent)
            if work_percent < 0 or work_percent > 100:
                flash('Work percentage must be between 0 and 100.', 'error')
                return render_template('home.html', message=message)

            # Handle file upload
            if 'schedule_pdf' not in request.files or request.files['schedule_pdf'].filename == '':
                flash('Please upload a PDF file.', 'error')
                return render_template('home.html', message=message)

            uploaded_file = request.files['schedule_pdf']
            if not uploaded_file.filename.lower().endswith('.pdf'):
                flash('Invalid file type. Please upload a PDF file.', 'error')
                return render_template('home.html', message=message)

            # Save uploaded file
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(upload_folder, filename)
            uploaded_file.save(filepath)

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
            # Store df1a in session
            df1a = clean_data(df1a)
            print("CCCC",df1a)
            session['df1a'] = df1a.to_json() #good

            print(f" {inspect.currentframe().f_lineno}")
            # Process df1a to generate df2a, df2b, and df2c
            df2a, df2b, df2c = structure_data(df1a)

            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()
            session['df2c'] = df2c.to_json()
            session['uploaded_pdf'] = filename

            print("!!!!!!!!!!!!")
            print(df1a,df1b,df2a,df2b,df2c)


            flash('Schedule and frametime uploaded successfully!', 'success')
            return redirect('/days')

        except ValueError as ve:
            flash(str(ve), 'error')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')
            current_app.logger.error(f'Error occurred: {e}')

    # For GET request, display the upload form
    return render_template('home.html', message=message)
