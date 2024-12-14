from flask import Blueprint, render_template, session, current_app
from datetime import datetime
import pandas as pd
import inspect
 

updated_schedule_blueprint = Blueprint('updated_schedule', __name__, url_prefix='/updated_schedule')

@updated_schedule_blueprint.route('/', methods=['GET'])
def display_schedule():
    print(f"XXXYYY {inspect.currentframe().f_lineno}")

    """Display the updated schedule based on df2d."""
    try:
        # Load df2d from session
        df2d_json = session.get('df2d')
        print(f"XXXYYY {inspect.currentframe().f_lineno}")
        if not df2d_json:
            return render_template('updated_schedule.html', error="No schedule data found.")

        # Convert JSON to DataFrame
        df2d = pd.read_json(df2d_json)

        # Create events for the schedule
        calendar_events = []
        for _, row in df2d.iterrows():
            try:
                start_time = datetime.strptime(row['start_time'], "%H%M")
                end_time = datetime.strptime(row['end_time'], "%H%M")
                calendar_events.append({
                    "title": row['activities'],
                    "start": start_time.strftime("%H:%M"),
                    "end": end_time.strftime("%H:%M"),
                    "day": row['day'],
                    "type": row['type']
                })
            except Exception as e:
                current_app.logger.error(f"Error creating event: {e}")
 
        # Render the schedule
        return render_template('updated_schedule.html', events=calendar_events)

    except Exception as e:
        current_app.logger.error(f"Error displaying schedule: {e}")
        return render_template('updated_schedule.html', error="An error occurred while displaying the schedule.")
