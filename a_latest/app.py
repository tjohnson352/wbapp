# app.py
from flask import Flask
from services.time_handling import format_time


# Create a Flask application instance
app = Flask(__name__)

# Set the secret key for session management
app.secret_key = 'your_secret_key_here'  # Replace 'your_secret_key_here' with a secure key

# Custom filter to format time
@app.template_filter('format_time')
def format_time_filter(value):
    return format_time(value)

# Register Blueprints
from blueprints.upload_schedule import upload_schedule_bp
from blueprints.dataframe_view import dataframe_view_bp
#from blueprints.set_frametime import set_frametime_bp
#from blueprints.structure_data import structure_data_bp
#from blueprints.clean_data import clean_data_bp

app.register_blueprint(upload_schedule_bp, url_prefix='/')
app.register_blueprint(dataframe_view_bp)
#app.register_blueprint(set_frametime_bp, url_prefix='/set_frametime')
#app.register_blueprint(structure_data_bp, url_prefix='/structure_data')
#app.register_blueprint(clean_data_bp, url_prefix='/clean_data')

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
