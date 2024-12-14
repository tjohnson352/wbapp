from flask import Flask, render_template, redirect, flash, session
from flask_session import Session
import os
from blueprints.home import home_blueprint
from blueprints.edit_schedule import edit_schedule_blueprint
from blueprints.dataframe_view import dataframe_view_bp
from blueprints.updated_schedule import updated_schedule_blueprint
from blueprints.full_calendar import full_calendar_blueprint
from blueprints.meta1 import meta1_blueprint


# Initialize the Flask app
app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_USE_SIGNER'] = True

# Initialize the server-side session
Session(app)

# Register blueprints
app.register_blueprint(home_blueprint)
app.register_blueprint(meta1_blueprint)
app.register_blueprint(edit_schedule_blueprint)
app.register_blueprint(dataframe_view_bp)
app.register_blueprint(full_calendar_blueprint)
app.register_blueprint(updated_schedule_blueprint)

# Set the upload folder for temporary PDFs
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Optional: If you have a feedback route, uncomment below
# from helpers.submit_feedback import submit_feedback
# app.add_url_rule('/submit-feedback', view_func=submit_feedback, methods=['POST'])

# Optional: Clear session selectively at the end of each request
@app.teardown_request
def clear_session(exception=None):
    """
    Clear non-essential session data at the end of each request,
    while retaining critical keys for functionality.
    """
    essential_keys = ['user_id', 'role']  # Add keys you want to keep
    for key in list(session.keys()):
        if key not in essential_keys:
            session.pop(key, None)

if __name__ == '__main__':
    app.run(debug=True)
