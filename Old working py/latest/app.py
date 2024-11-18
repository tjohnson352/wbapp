from flask import Flask, request, redirect, url_for, render_template_string, render_template, session
import fitz  # PyMuPDF
import pandas as pd
from collections import Counter
import re
from datetime import datetime, timedelta
import os
import tempfile
from blueprints.helpers import extract_text_from_pdf, clean_text_lines, identify_time_frames, format_time
from blueprints.edit.routes import edit_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Register the edit blueprint
app.register_blueprint(edit_bp, url_prefix='/edit')

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
            <form method="post" action="/edit/save_edit">  <!-- Updated the form action -->
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

if __name__ == "__main__":
    app.run(debug=True)
