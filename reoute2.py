from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from services.pdf_service import extract_raw_text_from_pdf
from services.data_service import clean_data
from services.frametime_service import get_frametime, update_frametime, save_frametime
from services.schedule_service import create_df6, get_df6, save_df6

# Define the Blueprint
upload_blueprint = Blueprint('upload', __name__)

# File Upload Directory
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@upload_blueprint.route('/', methods=['GET', 'POST'])
def upload_schedule():
    if request.method == 'POST':
        # Start a new session
        session.clear()

        # Check if a file is uploaded
        file = request.files.get('file')
        if not file or file.filename == '':
            return render_template('upload_schedule.html', message="No file selected")

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract and process raw text
        raw_data = extract_raw_text_from_pdf(file_path)
        df1 = pd.DataFrame(raw_data, columns=["Content"])
        session['raw_data'] = df1.to_json()

        # Clean data and save intermediate results
        df2, df5, df3 = clean_data(df1)
        session['df2'] = df2.to_json()
        session['df5'] = df5.to_json()
        session['df3'] = df3.to_json()

        # Redirect to frametime setup
        return redirect(url_for('upload.display_frametime'))

    return render_template('upload_schedule.html')

@upload_blueprint.route('/frametime', methods=['GET', 'POST'])
def display_frametime():
    if request.method == 'POST':
        # Update frametime settings based on form data
        update_frametime(request.form)
        return redirect(url_for('upload.display_updates'))  # Proceed to updates

    # Load existing frametime or defaults
    df4 = get_frametime()
    save_frametime(df4)
    return render_template('frametime.html', df4=df4)

@upload_blueprint.route('/updates', methods=['GET', 'POST'])
def display_updates():
    if request.method == 'POST':
        # Retrieve and update df6 from the session
        df6 = get_df6()
        for idx, row in df6.iterrows():
            day = request.form.get(f"day_{idx}", "REMOVE")
            activity_type = request.form.get(f"type_{idx}", "TEACHING")
            df6.at[idx, 'day'] = day
            df6.at[idx, 'activity_type'] = activity_type

        # Save updated df6
        save_df6(df6)
        return redirect(url_for('upload.display_df6'))  # Redirect to the final view

    # Create df6 if not already in session
    if 'df6' not in session and 'df3' in session:
        df3 = pd.read_json(session['df3'])
        df6 = create_df6(df3)
    else:
        df6 = get_df6()

    return render_template('updates.html', df6=df6)

@upload_blueprint.route('/df1')
def display_raw_data():
    if 'raw_data' in session:
        df1 = pd.read_json(session['raw_data'])
        return render_template('tables/df_template.html', df=df1, title="Raw Data")
    return "No data available."

@upload_blueprint.route('/df6')
def display_df6():
    if 'df6' in session:
        df6 = pd.read_json(session['df6'])
        return render_template('tables/df_template.html', df=df6, title="Final Schedule")
    return "No data available."


