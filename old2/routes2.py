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
structured_data = Blueprint('structured_data', __name__)

# Set session lifetime to 1 hour
SESSION_LIFETIME = timedelta(hours=1)

# Set up logging
logging.basicConfig(level=logging.INFO)


### ROUTES FOR DISPLAYING THE DATAFRAMES
@structured_data.route('/df1a', methods=['GET'])
def display_raw_data():
    if 'df1a' in session:
        df1a = pd.read_json(session['df1a'])
        return render_template('tables/df_template.html', df=df1a, title='Raw Data')
    else:
        return "Data not available."

@structured_data.route('/df2a')
def display_df2a():
    if 'df2a' in session:
        df2a = pd.read_json(session['df2a'])
        return render_template('tables/df_template.html', df=df2a, title='Cleaned Data')
    return redirect(url_for('upload.upload_schedule'))


@structured_data.route('/df3', methods=['GET'])
def display_df3():
    if 'df3' in session:
        df3 = pd.read_json(session['df3'])
        return render_template('tables/df_template.html', df=df3, title='Structured Data')
    else:
        return "Data not available."


@structured_data.route('/df1b', methods=['GET'])
def display_df1b():
    if 'df1b' in session:
        df1b = pd.read_json(session['df1b'])
        return render_template('tables/df_template.html', df=df1b, title='Frametime Data')
    else:
        return "Data not available."

@structured_data.route('/df2b', methods=['GET'])
def display_df2b():
    if 'df2b' in session:
        df2b = pd.read_json(session['df2b'])
        return render_template('tables/df_template.html', df=df2b, title='Metadata (School & Teacher))')
    else:
        return "Data not available."


### END OF DATAFRAMES ROUTES


@structured_data.route('/', methods=['GET', 'POST'])  # schedule upload
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
            df1a = extract_pdf(file_path)
            df1a = pd.DataFrame(df1a, columns=["Content"])
            df2a, df2b, df3 = clean_data(df1a)

            # Save processed data to session
            session['df2a'] = df2a.to_json()
            session['df2b'] = df2b.to_json()
            session['df3'] = df3.to_json()
            session['df1a'] = df1a.to_json()  # Raw data for debugging or re-processing

            # Redirect to Frametime setup
            return redirect(url_for('structured_data.display_frametime'))

        return render_template('upload_schedule.html', message='Invalid file type. Only PDF allowed')

    return render_template('upload_schedule.html')  # Render the upload page


@structured_data.route('/frametime', methods=['GET', 'POST'])
def display_frametime():
    if request.method == 'POST':
        # Load the current frametime
        df1b = get_frametime()

        # Process the form inputs
        for index, row in df1b.iterrows():
            day = row['day']
            # Check if the "Off Day" checkbox was selected
            if f"off_day_{day}" in request.form:
                df1b.at[index, 'ft_start'] = "OFF DAY"
                df1b.at[index, 'ft_end'] = "OFF DAY"
            else:
                # Otherwise, save the provided start and end times
                df1b.at[index, 'ft_start'] = request.form.get(f"start_{day}", "08:00")
                df1b.at[index, 'ft_end'] = request.form.get(f"end_{day}", "16:00")

        # Save the updated frametime back to the session
        save_frametime(df1b)

        # Redirect based on the action
        action = request.form.get("action", "")
        if action == "Go Back":
            return redirect(url_for('structured_data.upload_schedule'))
        elif action == "Save and Move Forward":
            return redirect(url_for('structured_data.edit_schedule'))


    # Handle GET requests
    df1b = get_frametime()
    return render_template('frametime.html', df1b=df1b)



@app.route("/frametime", methods=["GET", "POST"])
def set_frametime():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "back":
            return redirect(url_for("upload_schedule"))  # Redirect to the base URL

        # Update the frametime with form data
        update_frametime(request.form)


@structured_data.route('/edit_schedule', methods=['GET', 'POST'])
def edit_schedule():
    if request.method == 'POST':
        # Load df3 from the session
        if 'df3' in session:
            df3 = pd.read_json(session['df3'])
        else:
            return redirect(url_for('structured_data.display_frametime'))  # Redirect if df3 is not available

        # Update the 'day' column based on the form data
        for index in range(len(df3)):
            new_day = request.form.get(f"day_{index}", df3.at[index, 'day'])
            df3.at[index, 'day'] = new_day

        # Save the updated df3 back to the session
        session['df3'] = df3.to_json()

        # Create df4 as a copy of the updated df3
        df4 = df3.copy()
      


        # Sort df4 by 'day' and then by 'start'
        day_order = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "REMOVE"]
        df4['day'] = pd.Categorical(df4['day'], categories=day_order, ordered=True)  # Set custom sort order for days
        df4['start'] = pd.to_datetime(df4['start'], format='%H:%M', errors='coerce')  # Convert 'start' to datetime
        df4 = df4.sort_values(by=['day', 'start']).reset_index(drop=True)  # Sort by 'day' and 'start'

        # Convert 'start' back to string for display purposes
        df4['start'] = df4['start'].dt.strftime('%H:%M').fillna("")
        # Save df4 to the session
        session['df4'] = df4.to_json()

        # Create filtered DataFrames for each day (df4a to df4f) only for days in df4
        unique_days = df4['day'].unique()  # Get the unique days present in df4

        days_mapping = {
            "MONDAY": "df4a",
            "TUESDAY": "df4b",
            "WEDNESDAY": "df4c",
            "THURSDAY": "df4d",
            "FRIDAY": "df4e",
            "REMOVE": "df4f"
        }

        # Iterate through the mapping and filter only if the day exists in df4
        for day, df_name in days_mapping.items():
            if day in unique_days:
                filtered_df = df4[df4['day'] == day].copy()
                session[df_name] = filtered_df.to_json()  # Save the filtered DataFrame to the session

        # Handle button actions
        action = request.form.get('action', '')
        if action == 'back':
            return redirect(url_for('structured_data.display_frametime'))  # Go back to /frametime
        elif action == 'save_forward':
            # Redirect to /df4a (schedule for Monday) if it exists; otherwise, handle dynamically
            if 'df4a' in session:
                return redirect(url_for('structured_data.monday_schedule'))
            else:
                return redirect(url_for('structured_data.display_frametime'))  # Fall back if no Monday data exists


    # Handle GET requests
    if 'df3' in session:
        df3 = pd.read_json(session['df3'])
    else:
        return redirect(url_for('structured_data.display_frametime'))  # Redirect if df3 is not available

    return render_template('edit_schedule.html', df3=df3)



@structured_data.route('/df4', methods=['GET'])
def display_df4():
    if 'df4' in session:
        df4 = pd.read_json(session['df4'])
        return render_template('tables/df_template.html', df=df4, title='Final Schedule (df4)')
    else:
        return "Data not available."

@structured_data.route('/df4a', methods=['GET'])
def display_df4a():
    if 'df4a' in session:
        df4a = pd.read_json(session['df4a'])
        return render_template('tables/df_template.html', df=df4a, title='Monday Activities (df4a)')
    else:
        return "Data not available for Monday."

@structured_data.route('/df4b', methods=['GET'])
def display_df4b():
    if 'df4b' in session:
        df4b = pd.read_json(session['df4b'])
        return render_template('tables/df_template.html', df=df4b, title='Tuesday Activities (df4b)')
    else:
        return "Data not available for Tuesday."

@structured_data.route('/df4c', methods=['GET'])
def display_df4c():
    if 'df4c' in session:
        df4c = pd.read_json(session['df4c'])
        return render_template('tables/df_template.html', df=df4c, title='Wednesday Activities (df4c)')
    else:
        return "Data not available for Wednesday."

@structured_data.route('/df4d', methods=['GET'])
def display_df4d():
    if 'df4d' in session:
        df4d = pd.read_json(session['df4d'])
        return render_template('tables/df_template.html', df=df4d, title='Thursday Activities (df4d)')
    else:
        return "Data not available for Thursday."

@structured_data.route('/df4e', methods=['GET'])
def display_df4e():
    if 'df4e' in session:
        df4e = pd.read_json(session['df4e'])
        return render_template('tables/df_template.html', df=df4e, title='Friday Activities (df4e)')
    else:
        return "Data not available for Friday."

@structured_data.route('/df4f', methods=['GET'])
def display_df4f():
    if 'df4f' in session:
        df4f = pd.read_json(session['df4f'])
        return render_template('tables/df_template.html', df=df4f, title='Removed Activities (df4f)')
    else:
        return "Data not available for Removed Activities."

@structured_data.route('/monday_schedule', methods=['GET', 'POST'])
def monday_schedule():
    if request.method == 'POST':
        # Retrieve df4a from session
        if 'df4a' in session:
            df4a = pd.read_json(session['df4a'])
        else:
            return "Error: df4a is not available."

        # Update df4a with form data
        for index in range(len(df4a)):
            df4a.at[index, 'type'] = request.form.get(f"type_{index}", df4a.at[index, 'type'])
            df4a.at[index, 'start'] = request.form.get(f"start_{index}", df4a.at[index, 'start'])
            df4a.at[index, 'end'] = request.form.get(f"end_{index}", df4a.at[index, 'end'])

        # Save the updated df4a back to the session
        session['df4a'] = df4a.to_json()

        # Redirect to the same page to show updated data
        return redirect(url_for('structured_data.monday_schedule'))

    # Handle GET request
    if 'df4a' in session:
        df4a = pd.read_json(session['df4a'])
        # Filter df4a for Monday's schedule
        df4a_monday = df4a[df4a['day'] == "MONDAY"]
    else:
        return "Error: df4a is not available."

    # Render the Monday schedule
    return render_template('monday_schedule.html', df4a=df4a_monday)

@structured_data.route('/df1c', methods=['GET'])
def display_df1c():
    # Check if df1c exists in the session
    if 'df1c' in session:
        df1c = pd.read_json(session['df1c'])  # Load df1c from session
        return render_template('tables/df_template.html', df=df1c, title='Frametime Summary (df1c)')
    else:
        # Redirect to /frametime if df1c does not exist
        return redirect(url_for('structured_data.display_frametime'))


if __name__ == "__main__":
    app.run(debug=True)
