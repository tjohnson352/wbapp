from flask import Blueprint, request, render_template_string, session
import fitz  # PyMuPDF
import pandas as pd
from ..helpers import extract_text_from_pdf, clean_text_lines, identify_time_frames

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET', 'POST'])
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

        return render_template_string('''
        <html>
        <head>
            <meta charset="UTF-8">
            ...
        </head>
        <body>
            <h1>Review, Edit, and Save Extracted Schedule Data</h1>
            ...
        </body>
        </html>
        ''', df_filtered=df_filtered)

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
