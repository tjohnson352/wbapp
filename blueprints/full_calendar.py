from flask import Blueprint, render_template, jsonify

full_calendar_blueprint = Blueprint('full_calendar', __name__)

# Mock data for events
events = [
    {
        "id": 1,
        "title": "Science Lab",
        "start": "2024-12-10T08:00:00",
        "end": "2024-12-10T09:00:00",
        "color": "blue"
    },
    {
        "id": 2,
        "title": "Hallway Duty",
        "start": "2024-12-10T11:45:00",
        "end": "2024-12-10T12:05:00",
        "color": "green"
    },
    {
        "id": 3,
        "title": "Department Meeting",
        "start": "2024-12-11T08:20:00",
        "end": "2024-12-11T09:25:00",
        "color": "purple"
    },
    {
        "id": 4,
        "title": "Tutorial-Surgeries",
        "start": "2024-12-11T14:00:00",
        "end": "2024-12-11T14:20:00",
        "color": "orange"
    },
]

@full_calendar_blueprint.route('/calendar')
def calendar():
    """Render the calendar page."""
    return render_template('full_calendar.html')

@full_calendar_blueprint.route('/api/events')
def api_events():
    """Provide event data as JSON."""
    return jsonify(events)
