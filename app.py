from flask import Flask, session
from flask_session import Session
import os
from datetime import timedelta
from routes import upload_blueprint
from flask_sqlalchemy import SQLAlchemy
import logging
from utils import format_time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Set up SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Register the custom filter
app.jinja_env.filters['format_time'] = format_time

# Session Configuration
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_SQLALCHEMY_TABLE'] = 'flask_sessions'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
Session(app)

# Create the sessions table
with app.app_context():
    db.create_all()

# Configuration for file uploads
UPLOAD_FOLDER = '/tmp/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Logging
logging.basicConfig(level=logging.INFO)

# Register blueprint
app.register_blueprint(upload_blueprint, url_prefix='/')

# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found. Please check the URL.", 404

@app.errorhandler(500)
def internal_error(e):
    return "An unexpected error occurred. Please try again later.", 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
