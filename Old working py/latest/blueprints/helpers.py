import fitz
from datetime import datetime
import pandas as pd
import re
from collections import Counter


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