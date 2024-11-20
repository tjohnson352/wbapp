from flask import Blueprint, Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
import pandas as pd
from services.pdf_service import extract_pdf  # Import updated function
from services.data_service import clean_data  # Import the data cleaning function
from services.frametime_service import handle_frametime_action, get_frametime, update_frametime, save_frametime, submit_frametime
import uuid
import logging
import re


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session handling
upload_blueprint = Blueprint('upload', __name__)

# Set session lifetime to 1 hour
SESSION_LIFETIME = timedelta(hours=1)

# Set up logging
logging.basicConfig(level=logging.INFO)


### ROUTES FOR DISPLAYING THE DATAFRAMES
@upload_blueprint.route('/df1', methods=['GET'])
def display_raw_data():
    if 'df1' in session:
        df1 = pd.read_json(session['df1'])
        return render_template('tables/df_template.html', df=df1, title='Raw Data')
    else:
        return "Data not available."

@upload_blueprint.route('/df2')
def display_df2():
    if 'df2' in session:
        df2 = pd.read_json(session['df2'])
        return render_template('tables/df_template.html', df=df2, title='Cleaned Data')
    return redirect(url_for('upload.upload_schedule'))


@upload_blueprint.route('/df3', methods=['GET'])
def display_df3():
    if 'df3' in session:
        df3 = pd.read_json(session['df3'])
        return render_template('tables/df_template.html', df=df3, title='Structured Data')
    else:
        return "Data not available."


@upload_blueprint.route('/df4', methods=['GET'])
def display_df4():
    if 'df4' in session:
        df4 = pd.read_json(session['df4'])
        return render_template('tables/df_template.html', df=df4, title='Frametime Data')
    else:
        return "Data not available."


@upload_blueprint.route('/df5', methods=['GET'])
def display_df5():
    if 'df5' in session:
        df5 = pd.read_json(session['df5'])
        return render_template('tables/df_template.html', df=df5, title='Metadata (School & Teacher))')
    else:
        return "Data not available."


### END OF DATAFRAMES ROUTES


@upload_blueprint.route('/', methods=['GET', 'POST'])  # schedule upload
def upload_schedule():
    if request.method == 'POST':
        # Start a new session for each uploaded file
        session.clear()
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True  # Make the session permanent
        session.modified = True

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
            df1 = extract_pdf(file_path)
            df1 = pd.DataFrame(df1, columns=["Content"])
            df2, df5, df3 = clean_data(df1)

            # Save processed data to session
            session['df5'] = df5.to_json()
            session['df2'] = df2.to_json()
            session['df3'] = df3.to_json()
            session['df1'] = df1.to_json()  # Raw data for debugging or re-processing

            # Redirect to Frametime setup
            return redirect(url_for('upload.display_frametime'))

        return render_template('upload_schedule.html', message='Invalid file type. Only PDF allowed')

    return render_template('upload_schedule.html')  # Render the upload page


@upload_blueprint.route('/frametime', methods=['GET', 'POST'])
def display_frametime():
    if request.method == 'POST':
        # Update the frametime using form data with new time patterns
        form_data = request.form.to_dict()

        # Reformat time patterns like "1520" to "15:20"
        for key, value in form_data.items():
            if re.match(r'^\d{4}$', value):  # Matches a 4-digit pattern
                formatted_time = f"{value[:2]}:{value[2:]}"
                form_data[key] = formatted_time

        # Update the frametime using the formatted data
        update_frametime(form_data)

        # Redirect to load the updates page immediately after saving frametime
        return redirect(url_for('upload.display_frametime'))

    # If it's a GET request, get the current frametime and render it
    df4 = get_frametime()
    save_frametime(df4)  # Ensure default frametime is saved in the session
    return render_template('frametime.html', df4=df4)


@app.route("/frametime", methods=["GET", "POST"])
def set_frametime():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "back":
            return redirect(url_for("upload_schedule"))  # Redirect to the base URL

        # Update the frametime with form data
        update_frametime(request.form)


if __name__ == "__main__":
    app.run(debug=True)
