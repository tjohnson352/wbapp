# upload_schedule.py

from flask import Blueprint, request, session, jsonify, render_template, redirect
import pandas as pd
import os
import fitz  # PyMuPDF library for extracting text from PDFs
from blueprints.structure_data import structure_data
from blueprints.user_updates import daily_activities

# Initialize blueprint for handling schedule uploads
upload_schedule_bp = Blueprint('upload_schedule', __name__, url_prefix='/')

# Define the route to handle file upload requests (URL: /)
@upload_schedule_bp.route('/', methods=['GET', 'POST'])
def upload_schedule():
    message = None  # Initialize error message
    
    if request.method == 'POST':
        # Retrieve the work percentage from the form
        work_percent = request.form.get('work_percent', None)
        print("Work percent:", work_percent)
        if not work_percent:
            message = '<span style="color: red; font-style: italic; font-size: 0.8em;">Please enter your work percentage.</span>'
            return render_template('upload_form.html', message=message)

        try:
            # Convert work_percent to an integer and validate it
            work_percent = int(work_percent)
            if work_percent < 0 or work_percent > 100:
                message = '<span style="color: red; font-style: italic; font-size: 0.8em;">Work percentage must be between 0 and 100.</span>'
                return render_template('upload_form.html', message=message)
                
            
            # Save work_percent in session
            session['work_percent'] = work_percent
            
            # Handle file upload
            if 'file' in request.files:
                file = request.files['file']
                
                if file.filename == '':  # No file selected
                    message = '<span style="color: red; font-style: italic; font-size: 0.8em;">No file chosen. Please select a file to upload.</span>'
                    return render_template('upload_form.html', message=message)

                # Start a new session only when a new file is uploaded
                session.clear()  # Clear the session
                session['new_session'] = True  # Create a new session ID

                try:
                    # Extract text from the uploaded PDF and create a DataFrame (df1)
                    data = []
                    with fitz.open(stream=file.read(), filetype='pdf') as pdf:
                        for page_num in range(pdf.page_count):
                            page = pdf.load_page(page_num)
                            text = page.get_text()
                            lines = text.splitlines()
                            cleaned_lines = [line.strip() for line in lines if line.strip()]
                            data.extend(cleaned_lines)

                    if data:
                        df1 = pd.DataFrame(data, columns=['Content'])
                    else:
                        df1 = pd.DataFrame(columns=['Content'])

                    # Process and save df1a for use in the /day route
                    df1a, df1b = structure_data(df1)
                    print(df1b)

                    session['df1a'] = df1a.to_json()

                    # Redirect to the /day route
                    return redirect('/frametime')

                except Exception as e:
                    message = f'<span style="color: red; font-weight: bold;">Error: {str(e)}</span>'
                    return render_template('upload_form.html', message=message)
        except ValueError:
            message = '<span style="color: red; font-style: italic; font-size: 0.8em;">Work percentage must be a valid number.</span>'
            return render_template('upload_form.html', message=message)
        
        print(session.keys())

    # For GET request, display the upload form
    return render_template('upload_form.html', message=message)



def update_schedule():
    try:
        # Retrieve updated data from the frontend
        updated_data = request.json['updated_data']
        # Convert the updated data back into a DataFrame
        df2b = pd.DataFrame(updated_data)

        return jsonify({'message': 'Schedule updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@upload_schedule_bp.route('/save_schedule', methods=['POST'])
def save_schedule():
    """Save the modified schedule and render the view-only page."""
    try:
        # Retrieve updated data from the request
        updated_data = request.json['updated_data']

        # Convert the updated data back into a DataFrame
        df2b = pd.DataFrame(updated_data)

        # Save the final schedule in session or temporary storage
        session['df2b'] = df2b.to_json()

        # Render the view-only page
        return jsonify({'message': 'Schedule saved successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_schedule_bp.route('/view_day', methods=['GET'])
def view_day():
    """Display the saved schedule without editing options."""
    if 'df2b' in session:
        # Retrieve the saved schedule
        df2b = pd.read_json(session['df2b'])
        df2b['start_time'] = pd.to_datetime(df2b['start_time']).dt.strftime('%H:%M')
        df2b['end_time'] = pd.to_datetime(df2b['end_time']).dt.strftime('%H:%M')

        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'DELETE']
        df2b['day'] = pd.Categorical(df2b['day'], categories=days_order, ordered=True)
        df2b = df2b.sort_values(by=['day', 'start_time'])

        print("EEE")
        print(df2b)

        # Render the saved schedule page
        return render_template('saved_schedule.html', table=df2b)

    else:
        # Redirect to the upload page if no saved schedule exists
        return redirect('/')

@upload_schedule_bp.route('/day', methods=['GET'])
def edit_day():
    """Render day.html using df2b if available, otherwise process df1a into df2a."""
    try:
        # Check if df2b is in the session
        if 'df2b' in session:
            try:
                # Load df2b from the session
                df2b = pd.read_json(session['df2b'])
                df2b['start_time'] = pd.to_datetime(df2b['start_time']).dt.strftime('%H:%M')
                df2b['end_time'] = pd.to_datetime(df2b['end_time']).dt.strftime('%H:%M')

                # Render day.html with df2b
                return render_template('day.html', table=df2b)
            except Exception as e:
                return jsonify({'error': f"Error processing df2b: {str(e)}"}), 500

        # If df2b is not in the session, check for df1a
        if 'df1a' in session:
            # Load df1a from the session
            df1a = pd.read_json(session['df1a'])

            # Process df1a into df2a
            df2a = daily_activities(df1a)
            session['df2a'] = df2a.to_json()

            df2a['start_time'] = pd.to_datetime(df2a['start_time']).dt.strftime('%H:%M')
            df2a['end_time'] = pd.to_datetime(df2a['end_time']).dt.strftime('%H:%M')


            # Render day.html with df2a
            return render_template('day.html', table=df2a)

        # Redirect to the upload page if neither df2b nor df1a is found
        return redirect('/')
    
    except Exception as e:
        return jsonify({'error': f"Error processing data: {str(e)}"}), 500

@upload_schedule_bp.route('/frametime', methods=['GET', 'POST'])
def frametime():
    """Render the frametime input form and process submissions."""
    if request.method == 'POST':
        try:
            # Collect frametime input from the form
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            frametime_data = []

            for day in days:
                start_time = request.form.get(f"{day}_start")
                end_time = request.form.get(f"{day}_end")
                frametime_data.append({'day': day, 'start_time': start_time, 'end_time': end_time})

            # Save frametime data to DataFrame and session
            df2c = pd.DataFrame(frametime_data)
            session['df2c'] = df2c.to_json()

            # Redirect to a confirmation or view page
            return redirect('/day')

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Render the frametime form
    print("CCCC")
    print("Session df2c:", session.get('df2c'))
    return render_template('frametime.html')


@upload_schedule_bp.route('/view_frametime', methods=['GET'])
def view_frametime():
    """Display the saved frametime."""
    if 'df2c' in session:
        # Retrieve the frametime data
        df2c = pd.read_json(session['df2c'])
        df2c['start_time'] = pd.to_datetime(df2c['start_time']).dt.strftime('%H:%M')
        df2c['end_time'] = pd.to_datetime(df2c['end_time']).dt.strftime('%H:%M')

        # Render a table view of the frametime data
        print(df2c)
        return render_template('view_frametime.html', table=df2c)
    else:
        return redirect('/frametime')


@upload_schedule_bp.route('/session_info')
def session_info():
    keys = list(session.keys())  # Get all keys in the session
    return jsonify({"Session Variables": keys})