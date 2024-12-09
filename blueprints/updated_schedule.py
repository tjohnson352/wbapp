from flask import Blueprint, render_template, session, current_app
import pandas as pd
from datetime import datetime

updated_schedule_blueprint = Blueprint('updated_schedule', __name__, url_prefix='/updated_schedule')

@updated_schedule_blueprint.route('/', methods=['GET'])
def display_schedule():
    """Display the updated schedule based on df2d."""
    try:
        # Load df2d from session
        df2d_json = session.get('df2d')
        if not df2d_json:
            return render_template('updated_schedule.html', error="No schedule data found.")

        # Convert JSON to DataFrame
        df2d = pd.read_json(df2d_json)

        # Prepare events for FullCalendar
        events = []
        for _, row in df2d.iterrows():
            try:
                start_time = datetime.strptime(row['timespan'].split('-')[0].strip(), "%H:%M")
                end_time = datetime.strptime(row['timespan'].split('-')[1].strip(), "%H:%M")
                day_mapping = {
                    "Monday": 0,
                    "Tuesday": 1,
                    "Wednesday": 2,
                    "Thursday": 3,
                    "Friday": 4,
                }
                # Only include weekdays
                day_index = day_mapping.get(row['day'], None)
                if day_index is not None:
                    events.append({
                        "title": f"{row['activities']} ({row['type']})",
                        "start": f"2024-12-{8 + day_index}T{start_time.strftime('%H:%M')}",
                        "end": f"2024-12-{8 + day_index}T{end_time.strftime('%H:%M')}",
                        "description": f"{row['minutes']} minutes"
                    })
            except Exception as e:
                current_app.logger.error(f"Error creating event: {e}")

        # Render the schedule
        return render_template('updated_schedule.html', events=events)

    except Exception as e:
        current_app.logger.error(f"Error displaying schedule: {e}")
        return render_template('updated_schedule.html', error="An error occurred while displaying the schedule.")
