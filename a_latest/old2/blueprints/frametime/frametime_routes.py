from flask import Blueprint, request, render_template, session, redirect, url_for
import pandas as pd
from services.frametime_service import get_frametime, save_frametime

frametime_blueprint = Blueprint('frametime', __name__)

@frametime_blueprint.route('/', methods=['GET', 'POST'])
def display_frametime():
    """Handles the display and editing of frametime."""
    if request.method == 'POST':
        df1b = get_frametime()

        # Process the form inputs
        for index, row in df1b.iterrows():
            day = row['day']
            if f"off_day_{day}" in request.form:
                df1b.at[index, 'ft_start'] = "OFF DAY"
                df1b.at[index, 'ft_end'] = "OFF DAY"
            else:
                df1b.at[index, 'ft_start'] = request.form.get(f"start_{day}", "08:00")
                df1b.at[index, 'ft_end'] = request.form.get(f"end_{day}", "16:00")

        save_frametime(df1b)

        action = request.form.get("action", "")
        if action == "Go Back":
            return redirect(url_for('upload.upload_schedule'))
        elif action == "Save and Move Forward":
            return redirect(url_for('display.display_data', key='df3'))

    df1b = get_frametime()
    return render_template('frametime.html', df1b=df1b)
