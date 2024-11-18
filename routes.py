from flask import Blueprint, Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
import pandas as pd
from services.pdf_service import extract_raw_text_from_pdf  # Import updated function
from services.data_service import clean_data  # Import the data cleaning function
from services.frametime_service import handle_frametime_action, get_frametime, update_frametime, save_frametime, submit_frametime
from services.schedule_service import create_df6, get_df6, save_df6
import uuid
from io import StringIO
import re
import logging

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
    if 'raw_data' in session:
        df1 = pd.read_json(session['raw_data'])
        return render_template('tables/df_template.html', df=df1, title='Raw Data Overview')
    else:
        return "Data not available."

@upload_blueprint.route('/df2')
def display_df2():
    if 'df2' in session:
        df2 = pd.read_json(session['df2'])
        return render_template('tables/df_template.html', df=df2, title='Cleaned Data Overview (df2)')
    return redirect(url_for('upload.upload_schedule'))

@upload_blueprint.route('/df3', methods=['GET'])
def display_df3():
    if 'df3' in session:
        df3 = pd.read_json(session['df3'])
        return render_template('tables/df_template.html', df=df3, title='Structured Data Overview (df3)')
    else:
        return "Data not available."

@upload_blueprint.route('/df4', methods=['GET'])
def display_df4():
    if 'df4' in session:
        df4 = pd.read_json(session['df4'])
        return render_template('tables/df_template.html', df=df4, title='Frametime Data Overview (df4)')
    else:
        return "Data not available."

@upload_blueprint.route('/df5', methods=['GET'])
def display_df5():
    if 'df5' in session:
        df5 = pd.read_json(session['df5'])
        return render_template('tables/df_template.html', df=df5, title='Metadata Overview (df5)')
    else:
        return "Data not available."

@upload_blueprint.route('/df6', methods=['GET'])
def display_df6():
    if 'df6' in session:
        df6 = pd.read_json(session['df6'])
        
        # Ensure 'start_time' and 'end_time' are properly formatted as strings
        df6["start_time"] = df6["start_time"].apply(lambda x: str(x).strip() if isinstance(x, str) else "")
        df6["end_time"] = df6["end_time"].apply(lambda x: str(x).strip() if isinstance(x, str) else "")

        return render_template('tables/df_template.html', df=df6, title='Schedule Data Overview (df6)')
    else:
        return "Data not available."

    
@upload_blueprint.route('/df7', methods=['GET'])
def display_df7():
    if 'df7' in session:
        # Load df7 from session
        df7 = pd.read_json(session['df7'])
        df7["start_time"] = pd.to_datetime(df7["start_time"], errors='coerce').dt.strftime('%H:%M')
        df7["end_time"] = pd.to_datetime(df7["end_time"], errors='coerce').dt.strftime('%H:%M')
        return render_template('tables/df_template.html', df=df7, title='Daily Activities Overview (df7)')
    else:
        return "Data not available."

# Function to create day-specific HTML files for df7_1 to df7_5
def create_day_specific_files(df7):
    day_mapping = {"MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5}
    for day, num in day_mapping.items():
        df_day = df7[df7['day'].str.upper() == day].copy()

        # Always create file, even if empty
        if df_day.empty:
            logging.info(f"No data available for {day}, creating empty HTML file.")
            df_day = pd.DataFrame(columns=['activity_type', 'activity_name', 'start_time', 'end_time', 'gap'])
        
        # Add GAP column
        df_day['gap'] = df_day['activity_type'].apply(lambda x: "GAP" if x.upper() == "TEACHING" else "")
        df_day = df_day[['activity_type', 'activity_name', 'start_time', 'end_time', 'gap']]  # Select specific columns
        file_path = f"templates/tables/df7_{num}.html"

        # Write the DataFrame to HTML file with the same format as the others
        try:
            rendered_html = render_template('df_template.html', df=df_day, title=f"Day Specific Overview - {day}")
            with open(file_path, 'w') as f:
                f.write(rendered_html)
            logging.info(f"Successfully created {file_path}")
        except Exception as e:
            logging.error(f"Failed to create {file_path}: {e}")

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
            raw_data = extract_raw_text_from_pdf(file_path)
            df1 = pd.DataFrame(raw_data, columns=["Content"])
            df2, df5, df3 = clean_data(df1)

            # Save processed data to session
            session['df5'] = df5.to_json()
            session['df2'] = df2.to_json()
            session['df3'] = df3.to_json()
            session['raw_data'] = df1.to_json()  # Raw data for debugging or re-processing
            session['update_stage'] = 'day'

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
        return redirect(url_for('upload.display_updates'))

    # If it's a GET request, get the current frametime and render it
    df4 = get_frametime()
    save_frametime(df4)  # Ensure default frametime is saved in the session
    return render_template('frametime.html', df4=df4)

@upload_blueprint.route('/updates', methods=['GET', 'POST']) # update schedule information
def display_updates():
    # Get the current update stage from session, default to "day"
    update_stage = session.get('update_stage', 'day')

    if request.method == 'POST':
        df6 = get_df6()
        if df6 is None or df6.empty:
            logging.error("df6 is not available or empty.")
            return "Data not available."

        # Update the 'Day' or 'Type' fields based on the current update stage
        for index, row in df6.iterrows():
            if update_stage == 'day':
                day_value = request.form.get(f"day_{index}", "")
                if day_value:
                    df6.at[index, 'day'] = day_value
            elif update_stage == 'type':
                type_value = request.form.get(f"type_{index}", "")
                if type_value:
                    df6.at[index, 'activity_type'] = type_value

        # Save changes to the session
        save_df6(df6)

        # Move to the next update stage
        if update_stage == 'day':
            session['update_stage'] = 'type'
        elif update_stage == 'type':
            # After saving types, create df7 without "REMOVE" rows
            df7 = df6[df6['day'].str.upper() != 'REMOVE']

            # Sort df7 by 'Day' and 'Start' columns
            day_order = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}
            df7['DayOrder'] = df7['day'].str.upper().map(day_order)  # Map day names to integers
            df7['StartTime'] = pd.to_datetime(df7['start_time'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
            df7 = df7.sort_values(by=['DayOrder', 'StartTime']).drop(columns=['DayOrder'])

            # Save df7 to session
            session['df7'] = df7.to_json()

            # Automatically create df7_1 to df7_5 HTML files for each day
            create_day_specific_files(df7)

            return redirect(url_for('upload.display_df7'))

        # Reload the updates page
        return redirect(url_for('upload.display_updates'))

    # Handle GET request
    if 'df6' not in session and 'df3' in session:
        df3 = pd.read_json(StringIO(session['df3']))
        if df3.empty:
            logging.error("df3 is empty or not available to create df6.")
            return "Error: df3 is empty or not available to create the schedule."
        df6 = create_df6(df3)
        save_df6(df6)
    else:
        df6 = get_df6()

    if df6 is None or df6.empty:
        logging.error("df6 is not available or empty when attempting to display updates.")
        return "Data not available."

    return render_template('updates.html', df6=df6, update_stage=update_stage)




@app.route("/frametime", methods=["GET", "POST"])
def set_frametime():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "back":
            return redirect(url_for("upload_schedule"))  # Redirect to the base URL
        elif action == "forward":
            return redirect(url_for("display_updates"))  # Proceed to the updates page

        # Update the frametime with form data
        update_frametime(request.form)

if __name__ == "__main__":
    app.run(debug=True)


