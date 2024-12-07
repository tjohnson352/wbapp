from flask import Blueprint, request, render_template, session, redirect, url_for
import os
import uuid
import pandas as pd
from werkzeug.utils import secure_filename
from services.pdf_service import extract_pdf
from services.data_service import clean_data

schedule_routes = Blueprint('schedule_routes', __name__)

@schedule_routes.route('/', methods=['GET', 'POST'])
def upload_schedule():
    """
    Route to upload a PDF schedule, process it, and store structured data in session.
    """
    if request.method == 'POST':
        session.clear()
        session['session_id'] = str(uuid.uuid4())

        file = request.files.get('file')
        if not file or not file.filename.endswith('.pdf'):
            return render_template('upload_schedule.html', message='Invalid file type. Only PDF allowed.')

        filename = secure_filename(file.filename)
        file_path = os.path.join('/tmp', filename)
        file.save(file_path)

        df1a = extract_pdf(file_path)
        df1a = pd.DataFrame(df1a, columns=["Content"])
        df2a, df2b, df3 = clean_data(df1a)

        session['df1a'] = df1a.to_json()
        session['df2a'] = df2a.to_json()
        session['df2b'] = df2b.to_json()
        session['df3'] = df3.to_json()

        return redirect(url_for('frametime_routes.setup_frametime'))

    return render_template('upload_schedule.html')

@schedule_routes.route('/edit', methods=['GET', 'POST'])
def edit_schedule():
    """
    Route to edit the structured schedule stored in session.
    """
    if 'df3' not in session:
        return redirect(url_for('frametime_routes.setup_frametime'))

    df3 = pd.read_json(session['df3'])
    if request.method == 'POST':
        for index, row in df3.iterrows():
            df3.at[index, 'day'] = request.form.get(f"day_{index}", row['day'])

        session['df3'] = df3.to_json()
        return redirect(url_for('data_routes.display_data', df_name='df3'))

    return render_template('edit_schedule.html', df3=df3)
