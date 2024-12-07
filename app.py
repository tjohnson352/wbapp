from flask import Flask, render_template, redirect, flash
import os
from blueprints.home import home_blueprint
from blueprints.edit_schedule import edit_schedule_blueprint
from blueprints.dataframe_view import dataframe_view_bp
#from blueprints.finalize_schedule import finalize_schedule_blueprint
#from blueprints.report_generation import report_generation_blueprint
#from helpers.submit_feedback import submit_feedback

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for managing sessions

# Register blueprints
app.register_blueprint(home_blueprint)
app.register_blueprint(edit_schedule_blueprint)
app.register_blueprint(dataframe_view_bp)

#app.register_blueprint(finalize_schedule_blueprint)
#app.register_blueprint(report_generation_blueprint)

# Set the upload folder for temporary PDFs
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Register submit feedback route
#app.add_url_rule('/submit-feedback', view_func=submit_feedback, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
