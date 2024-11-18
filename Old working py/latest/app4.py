from flask import Flask, request, redirect, url_for, render_template_string, session
import fitz  # PyMuPDF
import pandas as pd
from collections import Counter
import re
from datetime import datetime, timedelta
import os
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)

def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def clean_text_lines(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines

def identify_time_frames(df):
    # Regex pattern to match time frames like hh:mm - hh:mm or h:mm-h:mm
    time_frame_pattern = re.compile(r'\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b')
    lone_dash_pattern = re.compile(r'^-$')
    end_dash_pattern = re.compile(r'-$')
    
    # Apply regex to identify rows containing time frames, lone dash, or end dash
    def label_row(text):
        if time_frame_pattern.search(text):
            return 'time'
        elif lone_dash_pattern.match(text):
            return 'lone dash'
        elif end_dash_pattern.match(text):
            return 'end dash'
        else:
            return ''
    
    df['time_dash'] = df['text'].apply(label_row)
    
    # Append the next row to rows with an 'end dash'
    rows = df.to_dict('records')
    updated_rows = []
    skip_next = False
    lone_dash_found = False
    lone_dash_start_index = -1
    lone_dash_end_index = -1
    for i in range(len(rows)):
        if skip_next:
            skip_next = False
            continue
        if rows[i]['time_dash'] == 'end dash' and i < len(rows) - 1:
            rows[i]['text'] += ' ' + rows[i + 1]['text']
            skip_next = True
        elif rows[i]['time_dash'] == 'lone dash':
            lone_dash_found = True
            lone_dash_start_index = i - 1 if i > 0 else -1
            updated_rows.append(rows[i])
            continue
        elif lone_dash_found and rows[i]['time_dash'] == 'time':
            rows[i]['time_dash'] = 'lone_dash_time'
            lone_dash_end_index = i - 1 if i > 0 else -1
            lone_dash_found = False
        updated_rows.append(rows[i])
    
    # Update the labels for lone_dash_start and lone_dash_end
    if lone_dash_start_index >= 0:
        updated_rows[lone_dash_start_index]['time_dash'] = 'lone_dash_start'
    if lone_dash_end_index >= 0:
        updated_rows[lone_dash_end_index]['time_dash'] = 'lone_dash_end'
    
    # Concatenate text for rows between lone_dash_start and lone_dash_end and record in a new column
    df = pd.DataFrame(updated_rows)
    df['extracted_activities'] = ''
    lone_dash_start_indices = df[df['time_dash'] == 'lone_dash_start'].index.tolist()
    for start_index in lone_dash_start_indices:
        end_index = df[(df.index > start_index) & (df['time_dash'] == 'lone_dash_end')].index.min()
        if not pd.isna(end_index):
            concatenated_text = ''.join(df.loc[start_index:end_index, 'text'])
            lone_dash_time_index = df[(df.index > start_index) & (df['time_dash'] == 'lone_dash_time')].index.min()
            if not pd.isna(lone_dash_time_index):
                concatenated_text += ' ' + df.at[lone_dash_time_index, 'text']
            df.at[start_index, 'extracted_activities'] = concatenated_text
    
    # Find the teacher's name (most repeated text in 'text' column)
    text_counter = Counter(df['text'])
    teacher_name, _ = text_counter.most_common(1)[0]
    
    # Find the school name (second to last row in 'text' column)
    school_name = df.iloc[-2]['text'] if len(df) > 1 else ''
    
    # Record school name in row 1 of 'extracted_activities' and teacher name in row 2
    if len(df) > 0:
        df.at[0, 'extracted_activities'] = school_name
    if len(df) > 1:
        df.at[1, 'extracted_activities'] = teacher_name
    
    # Concatenate text from above for rows with 'time' and text length <= 13
    for idx in df[(df['time_dash'] == 'time') & (df['text'].str.len() <= 13)].index:
        if idx > 0:
            concatenated_text = df.at[idx - 1, 'text'] + ' ' + df.at[idx, 'text']
            df.at[idx, 'extracted_activities'] = concatenated_text
    
    # If 'extracted_activities' is empty and 'time_dash' is 'time' or 'end dash', copy 'text' to 'extracted_activities'
    for idx in df[(df['extracted_activities'] == '') & (df['time_dash'].isin(['time', 'end dash']))].index:
        df.at[idx, 'extracted_activities'] = df.at[idx, 'text']
    
    # Add new columns 'activities', 'time_span', 'start_time', 'end_time', and 'minutes'
    df['activities'] = ''
    df['time_span'] = ''
    df['start_time'] = ''
    df['end_time'] = ''
    df['minutes'] = ''
    
    # Record 'extracted_activities' row 1 into 'activities' column
    if len(df) > 0:
        df.at[0, 'activities'] = df.at[0, 'extracted_activities']
    
    # Create name_code from teacher's name and record in 'activities' column
    if len(df) > 1:
        teacher_name_parts = teacher_name.split()
        name_code = ''.join([part[:2].capitalize() for part in teacher_name_parts])
        df.at[1, 'activities'] = name_code
    
    # Split extracted_activities into activities, time_span, start_time, end_time, and calculate minutes
    for idx in df[df['extracted_activities'] != ''].index:
        extracted_text = df.at[idx, 'extracted_activities']
        time_match = time_frame_pattern.search(extracted_text)
        if time_match:
            time_span = time_match.group()
            activity_text = extracted_text.replace(time_span, '').strip()
            df.at[idx, 'time_span'] = time_span
            df.at[idx, 'activities'] = activity_text
            # Split time_span into start_time and end_time
            times = time_span.split('-')
            if len(times) == 2:
                start_time_str = times[0].strip()
                end_time_str = times[1].strip()
                df.at[idx, 'start_time'] = start_time_str
                df.at[idx, 'end_time'] = end_time_str
                # Calculate minutes
                start_time = datetime.strptime(start_time_str, '%H:%M')
                end_time = datetime.strptime(end_time_str, '%H:%M')
                time_diff = end_time - start_time
                total_minutes = int(time_diff.total_seconds() / 60)
                df.at[idx, 'minutes'] = total_minutes
    
    # Convert all column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Create a new DataFrame with selected columns and exclude rows with empty data
    df_filtered = df[['activities', 'start_time', 'end_time', 'minutes']]
    df_filtered = df_filtered[(df_filtered != '').all(axis=1)]
    df_filtered = df_filtered.sort_values(by='activities')
    
    return df, df_filtered

def format_time(value):
    try:
        # If value is already in HH:MM format
        return datetime.strptime(value, '%H:%M').strftime('%H:%M')
    except ValueError:
        try:
            # If value is an integer-like hour (e.g., '8' or '12')
            return datetime.strptime(value, '%H').strftime('%H:%M')
        except ValueError:
            return value

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded.", 400
        
        file = request.files['file']
        
        if file.filename == '':
            return "No selected file.", 400
        
        # Extract the uploaded PDF's text and clean lines
        extracted_text = extract_text_from_pdf(file)
        clean_lines = clean_text_lines(extracted_text)

        # Create DataFrame from the cleaned lines
        df_time = pd.DataFrame({"text": clean_lines})

        # Identify rows containing time frames, lone dash, or end dash
        df_time, df_filtered = identify_time_frames(df_time)
        
        session['df_filtered'] = df_filtered.to_json()

        # Render the filtered DataFrame to HTML with editable features
        df_filtered_html = df_filtered.to_html(classes='table table-striped', index=False)
        editable_html = '''
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Roboto', sans-serif;
                }
                .bold-text {
                    font-weight: 700;
                }
                .table-header {
                    background-color: #f2f2f2;
                    text-align: left;
                }
                .table-cell {
                    padding: 10px;
                }
            </style>
            <title>Review, Edit, and Save Extracted Schedule Data</title>
        </head>
        <body>
            <h1 class="bold-text">Review, Edit, and Save Extracted Schedule Data</h1>
            <p>Please review the schedule data below and make any necessary edits:</p>
            <ul>
                <li>To <span class="bold-text">delete an activity</span>, check the box in the "Delete" column.</li>
                <li><span class="bold-text">Classify each activity</span> using the dropdown in the "Classification" column.</li>
                <li><span class="bold-text">Edit activity names</span> directly in the "Activity" column, if needed.</li>
                <li><span class="bold-text">Adjust start or end times</span> by modifying the respective columns.</li>
            </ul>
            <form method="post" action="/save_edits">
                <table class="table table-striped" style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr class="table-header">
                            <th class="table-cell" style="width: 5%;">Delete</th>
                            <th class="table-cell" style="width: 15%;">Classification</th>
                            <th class="table-cell" style="width: 25%;">Activity</th>
                            <th class="table-cell" style="width: 15%;">Start Time</th>
                            <th class="table-cell" style="width: 15%;">End Time</th>
                            <th class="table-cell" style="width: 10%;">Minutes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for index, row in df_filtered.iterrows() %}
                        <tr>
                            <td class="table-cell"><input type="checkbox" name="delete_{{ index }}"></td>
                            <td class="table-cell">
                                <select name="classification_{{ index }}" style="padding: 5px;">
                                    <option value="Lesson">Lesson</option>
                                    <option value="Break">Break</option>
                                    <option value="Other">Other</option>
                                </select>
                            </td>
                            <td class="table-cell"><input type="text" name="activities_{{ index }}" value="{{ row['activities'] }}" style="width: 90%; padding: 5px;"></td>
                            <td class="table-cell"><input type="text" name="start_time_{{ index }}" value="{{ row['start_time'] }}" style="width: 80%; padding: 5px;"></td>
                            <td class="table-cell"><input type="text" name="end_time_{{ index }}" value="{{ row['end_time'] }}" style="width: 80%; padding: 5px;"></td>
                            <td class="table-cell">{{ row['minutes'] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                <div style="margin-top: 20px; text-align: center;">
                    <input type="submit" value="Save Edits" style="padding: 10px 20px; font-size: 16px;">
                </div>
            </form>
        </body>
        </html>
        '''
        return render_template_string(editable_html, df_filtered=df_filtered)

    # Initial page for file upload
    return '''
    <html>
    <body>
        <h2>Upload a PDF to Extract Text</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Extract Text">
        </form>
    </body>
    </html>
    '''

@app.route('/save_edits', methods=['POST'])
def save_edits():
    df_filtered = pd.read_json(session['df_filtered'])
    edited_rows = []
    for index, row in df_filtered.iterrows():
        if f'delete_{index}' in request.form:
            continue
        activity = request.form.get(f'activities_{index}', row['activities'])
        start_time = format_time(request.form.get(f'start_time_{index}', row['start_time']))
        end_time = format_time(request.form.get(f'end_time_{index}', row['end_time']))
        classification = request.form.get(f'classification_{index}', 'Other')
        minutes = row['minutes']
        edited_rows.append({'activities': activity, 'start_time': start_time, 'end_time': end_time, 'minutes': minutes, 'classification': classification})
    df_edited = pd.DataFrame(edited_rows)
    session['df_edited'] = df_edited.to_json()
    df_edited_html = df_edited.to_html(classes='table table-striped', index=False)
    return f'''
    <html>
    <body>
        <h2>Edited Data</h2>
        {df_edited_html}
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)
