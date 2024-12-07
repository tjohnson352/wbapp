from flask import Flask, request, redirect, url_for, render_template_string
import fitz  # PyMuPDF
import io
import pandas as pd
from flair.models import SequenceTagger
from flair.data import Sentence
from collections import Counter
import re
from datetime import datetime

app = Flask(__name__)

# Load the Flair NER model
tagger = SequenceTagger.load("flair/ner-english")

# Initialize global DataFrames
df_time = pd.DataFrame(columns=["text"])
df_table = pd.DataFrame(columns=["Activity", "Start time", "End time", "Total time (min)", "Total time (hr)"])
df_classification = pd.DataFrame()  # DataFrame to hold the final classified data
df_summary = pd.DataFrame()  # DataFrame to hold the summary of classifications
df_frametime = pd.DataFrame()  # DataFrame to hold the frametime schedule

def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_most_common_name(text):
    sentence = Sentence(text)
    tagger.predict(sentence)
    names = [entity.text for entity in sentence.get_spans('ner') if entity.tag == 'PER']
    
    if names:
        name_counts = Counter(names)
        most_common_name = name_counts.most_common(1)[0][0]
        return most_common_name
    return "No name found"

def process_dash_lines(df):
    combined_text = []
    skip_next = False
    
    for i, row in enumerate(df["text"]):
        if skip_next:
            skip_next = False
            continue
        
        if row.strip() == "-":
            if i > 0 and i < len(df) - 1:
                combined_text[-1] += " - " + df.iloc[i + 1]["text"].strip()
                skip_next = True
        elif row.endswith("-"):
            joiner = "-" if re.search(r"[A-Za-z]-$", row) else " - "
            combined_text.append(row.rstrip("-") + joiner + df.iloc[i + 1]["text"].strip())
            skip_next = True
        else:
            combined_text.append(row)

    return pd.DataFrame({"text": combined_text})

def filter_short_lines(df):
    return df[df["text"].str.len() > 6]

def create_time_based_df(df):
    time_pattern = re.compile(r"^\d{1,2}:\d{2}\s?-\s?\d{1,2}:\d{2}$")
    time_format_pattern = re.compile(r"\d{1,2}:\d{2}$")
    processed_lines = []

    for i, line in enumerate(df["text"]):
        if 9 <= len(line) <= 13 and time_pattern.match(line.strip()):
            if i > 0:
                concatenated = df.iloc[i - 1]["text"] + " " + line
                processed_lines.append(concatenated)
            else:
                processed_lines.append(line)
        elif time_format_pattern.search(line.strip()[-5:]):
            processed_lines.append(line)
        else:
            processed_lines.append("N/A")
    
    return pd.DataFrame({"text": [line for line in processed_lines if line != "N/A"]})

def create_df_table(df):
    data = []
    
    for line in df["text"]:
        match = re.search(r"(.+?)\s*(\d{1,2}:\d{2})\s?-\s?(\d{1,2}:\d{2})", line)
        if match:
            activity = match.group(1).strip()
            start_time = match.group(2).strip()
            end_time = match.group(3).strip()
            
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            delta = (end_dt - start_dt).total_seconds() / 60
            total_time_min = int(delta)
            total_time_hr = round(total_time_min / 60, 2)
            
            data.append({
                "Activity": activity,
                "Start time": start_time,
                "End time": end_time,
                "Total time (min)": total_time_min,
                "Total time (hr)": total_time_hr
            })
    
    df_table = pd.DataFrame(data).sort_values(by="Activity").reset_index(drop=True)
    return df_table

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global df_time, df_table
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded.", 400
        
        file = request.files['file']
        
        if file.filename == '':
            return "No selected file.", 400
        
        # Extract the uploaded PDF's text
        extracted_text = extract_text_from_pdf(file)
        lines = [line for line in extracted_text.splitlines() if line.strip()]
        df_time = pd.DataFrame({"text": lines})
        
        df_time = df_time[df_time['text'].str.strip().str.len() != 2]

        most_common_name = extract_most_common_name(extracted_text)
        name_parts = most_common_name.split() if most_common_name != "No name found" else []
        
        if name_parts:
            df_time = df_time[~df_time['text'].str.contains('|'.join(name_parts), case=False)]

        df_time = process_dash_lines(df_time)
        df_time = filter_short_lines(df_time)
        df_time = create_time_based_df(df_time)

        df_table = create_df_table(df_time)

        classifications = ["Lesson", "Break", "Other"]

        # Render the form including frametime and middle management input
        table_html = render_template_string('''
        <html>
        <body>
            <h2>Upload Details</h2>
            <form action="{{ url_for('save_classifications') }}" method="post" enctype="multipart/form-data">
                <h3>Frametime Schedule</h3>
                <table border="1">
                    <tr>
                        <th>Day</th>
                        <th>Start Time (hh:mm)</th>
                        <th>End Time (hh:mm)</th>
                    </tr>
                    {% for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] %}
                    <tr>
                        <td>{{ day }}</td>
                        <td><input type="text" name="start_time_{{ day }}" placeholder="08:00" required></td>
                        <td><input type="text" name="end_time_{{ day }}" placeholder="16:00" required></td>
                    </tr>
                    {% endfor %}
                </table>
                
                <h3>Middle Management Role</h3>
                <label for="role">Select if you have an additional role:</label>
                <select name="role" id="role">
                    <option value="None">None</option>
                    <option value="HoD">Head of Department (HoD)</option>
                    <option value="HoY">Head of Year (HoY)</option>
                </select>

                <h3>Upload and Classification</h3>
                <p>Most common name detected: {{ most_common_name }}</p>
                
                <table border="1">
                    <tr>
                        <th>Classification</th>
                        <th>Activity</th>
                        <th>Start time</th>
                        <th>End time</th>
                        <th>Total time (min)</th>
                        <th>Total time (hr)</th>
                        <th>Delete</th>
                    </tr>
                    {% for idx, row in df_table.iterrows() %}
                    <tr>
                        <td>
                            <select name="classification_{{ idx }}">
                                {% for classification in classifications %}
                                <option value="{{ classification }}">{{ classification }}</option>
                                {% endfor %}
                            </select>
                        </td>
                        <td>{{ row['Activity'] }}</td>
                        <td><input type="text" name="start_time_{{ idx }}" value="{{ row['Start time'] }}"></td>
                        <td><input type="text" name="end_time_{{ idx }}" value="{{ row['End time'] }}"></td>
                        <td>{{ row['Total time (min)'] }}</td>
                        <td>{{ row['Total time (hr)'] }}</td>
                        <td><input type="checkbox" name="delete_{{ idx }}"></td>
                    </tr>
                    {% endfor %}
                </table>
                <button type="submit">Save Classifications</button>
            </form>
        </body>
        </html>
        ''', df_table=df_table, classifications=classifications, most_common_name=most_common_name)

        return table_html

    # Initial page for file upload and additional inputs
    return '''
    <html>
    <body>
        <h2>Upload a PDF and Enter Your Schedule</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Extract Text">
        </form>
    </body>
    </html>
    '''


@app.route('/save_classifications', methods=['POST'])
def save_classifications():
    global df_table, df_classification, df_summary

    updated_rows = []
    for idx in range(len(df_table)):
        classification = request.form.get(f"classification_{idx}")
        start_time = request.form.get(f"start_time_{idx}")
        end_time = request.form.get(f"end_time_{idx}")
        delete = request.form.get(f"delete_{idx}")  # Checkbox value

        # Skip row if 'Delete' checkbox is checked
        if delete:
            continue

        # Update row with new classification and time modifications
        row = df_table.iloc[idx].copy()
        row["Classification"] = classification
        row["Start time"] = start_time
        row["End time"] = end_time

        # Recalculate total time based on modified start and end times
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = datetime.strptime(end_time, "%H:%M")
        delta = (end_dt - start_dt).total_seconds() / 60
        row["Total time (min)"] = int(delta)
        row["Total time (hr)"] = round(delta / 60, 2)

        updated_rows.append(row)

    # Save the classified data in df_classification
    df_classification = pd.DataFrame(updated_rows)

    # Create df_summary to show total time for each classification
    df_summary = df_classification.groupby("Classification").agg({
        "Total time (min)": "sum",
        "Total time (hr)": "sum"
    }).reset_index()

    # Display confirmation and updated table along with summary
    return f'''
    <html>
    <body>
        <h2>Classifications saved successfully!</h2>
        <p>The classified data is saved in the DataFrame <strong>df_classification</strong>.</p>
        {df_classification.to_html(index=False)}
        <h2>Summary of Classifications</h2>
        <p>Below is a summary of total time for each classification.</p>
        {df_summary.to_html(index=False)}
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)
