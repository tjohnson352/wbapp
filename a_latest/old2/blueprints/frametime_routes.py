from flask import Blueprint, render_template, request, redirect, url_for
from services.frametime_service import get_frametime, save_frametime, handle_frametime_action

frametime_routes = Blueprint('frametime_routes', __name__)

@frametime_routes.route('/setup', methods=['GET', 'POST'])
def setup_frametime():
    """
    Route to set up frametime for the schedule.
    """
    df1b = get_frametime()
    if request.method == 'POST':
        action = handle_frametime_action(request.form)
        save_frametime(df1b)
        if action == "back":
            return redirect(url_for('schedule_routes.upload_schedule'))
        elif action == "forward":
            return redirect(url_for('schedule_routes.edit_schedule'))

    return render_template('frametime.html', df1b=df1b)
