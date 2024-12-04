from flask import Blueprint, request, session, render_template_string, redirect, url_for
import pandas as pd
from datetime import datetime, timedelta

edit_bp = Blueprint('edit', __name__)

@edit_bp.route('/save_edit', methods=['POST'])
def save_edits():
    df_filtered_json = session.get('df_filtered')
    if not df_filtered_json:
        return "No schedule data available to edit.", 400
    
    # Load the filtered DataFrame from session
    df_filtered = pd.read_json(df_filtered_json)
    edited_rows = []

    # Loop through each row of df_filtered to get the updated information
    for index, row in df_filtered.iterrows():
        if f'delete_{index}' in request.form:
            continue

        # Retrieve edited values from the form
        activity = request.form.get(f'activities_{index}', row['activities'])
        classification = request.form.get(f'classification_{index}', 'Other')
        
        # Extract and format start and end times to only have HH:MM (strip date and seconds)
        def format_time(time_str):
            try:
                # If the time is given as a datetime-like string (e.g., "2024-11-11 08:00:00"), parse it and format as HH:MM
                parsed_time = pd.to_datetime(time_str)
                return parsed_time.strftime('%H:%M')
            except ValueError:
                try:
                    # If the time is given in H or HH format, convert it to HH:00
                    return datetime.strptime(time_str, '%H').strftime('%H:%M')
                except ValueError:
                    return time_str  # If parsing fails, return as-is

        # Apply formatting to start and end times
        start_time = format_time(request.form.get(f'start_time_{index}', row['start_time']))
        end_time = format_time(request.form.get(f'end_time_{index}', row['end_time']))

        # Calculate the updated "Edited_min" based on the new start and end times
        try:
            # Parse start and end times to calculate duration
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = datetime.strptime(end_time, '%H:%M')
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            edited_min = int((end_dt - start_dt).total_seconds() / 60)
        except ValueError:
            edited_min = 0  # Default value if there's an error

        # Append the updated row to the edited_rows list
        edited_rows.append({
            'activities': activity,
            'classification': classification,
            'start_time': start_time,
            'end_time': end_time,
            'Edited_min': edited_min
        })
        
    # Create a new DataFrame from the edited rows
    df_edited = pd.DataFrame(edited_rows)

    # Debug: Print the edited DataFrame to verify the changes
    print("Edited DataFrame after recalculating Edited_min:")
    print(df_edited)

    # Store the updated edited DataFrame back in session
    session['df_edited'] = df_edited.to_json()

    return redirect(url_for('edit.view_edited_data'))

@edit_bp.route('/view_edited', methods=['GET'])
def view_edited_data():
    df_edited_json = session.get('df_edited')
    if not df_edited_json:
        return "No edited data available.", 400

    # Load the DataFrame from JSON
    df_edited = pd.read_json(df_edited_json)

    # Debug: Print the DataFrame to verify correct retrieval
    print("DataFrame to be displayed after edits:")
    print(df_edited)

    # Handle empty DataFrame properly
    if df_edited.empty:
        return "No edited data available.", 400

    # Render the DataFrame as a table including the Edited_min column
    return render_template_string('''
    <html>
    <body>
        <h2>Edited Data</h2>
        <table class="table table-striped" border="1">
            <thead>
                <tr>
                    <th>Activities</th>
                    <th>Classification</th>
                    <th>Start Time</th>
                    <th>End Time</th>
                    <th>Edited Minutes</th>  <!-- Display recalculated Edited Minutes -->
                </tr>
            </thead>
            <tbody>
                {% for index, row in df_edited.iterrows() %}
                <tr>
                    <td>{{ row['activities'] }}</td>
                    <td>{{ row['classification'] }}</td>
                    <td>{{ row['start_time'] }}</td>
                    <td>{{ row['end_time'] }}</td>
                    <td>{{ row['Edited_min'] }}</td>  <!-- Display only Edited_min -->
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    ''', df_edited=df_edited)
