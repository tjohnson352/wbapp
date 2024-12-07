from flask import Blueprint, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd
from services.pdf_service import extract_pdf
from services.data_service import clean_data
import uuid

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/', methods=['GET', 'POST'])
def upload_schedule():
    if request.method == 'POST':
        # Start a new session for each uploaded file
        session.clear()
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True

        if 'file' not in request.files:
            return render_template('upload_schedule.html', message='No file part in request')

        file = request.files['file']
        if file.filename == '':
            return render_template('upload_schedule.html', message='No selected file')

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join('/tmp', filename)
            file.save(file_path)

            # Process the uploaded PDF
            df1a = extract_pdf(file_path)
            df1a = pd.DataFrame(df1a, columns=["Content"])
            df2a, df2b, df3 = clean_data(df1a)

            # Save processed data to session
            session['dataframes'] = {
                'df1a': df1a.to_json(),
                'df2a': df2a.to_json(),
                'df2b': df2b.to_json(),
                'df3': df3.to_json(),
            }

            # Redirect to frametime setup
            return redirect(url_for('frametime.display_frametime'))

        return render_template('upload_schedule.html', message='Invalid file type. Only PDF allowed')

    return render_template('upload_schedule.html')
