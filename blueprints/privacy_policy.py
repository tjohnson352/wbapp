from flask import Blueprint, render_template, abort
import os

# Define the blueprint
privacy_policy_blueprint = Blueprint('privacy_policy', __name__)

@privacy_policy_blueprint.route('/privacy_policy')
def privacy_policy():
    """
    Dynamically reads the privacy policy from privacy_policy.txt
    and renders it in the privacy_policy.html template.
    """
    try:
        # Path to the privacy_policy.txt file
        file_path = os.path.join('helpers', 'privacy_policy.txt')

        # Check if the file exists
        if not os.path.exists(file_path):
            abort(404, description="Privacy Policy file not found.")

        # Read the contents of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            policy_content = file.read()

        # Render the content into the HTML template
        return render_template('privacy_policy.html', policy_content=policy_content)

    except Exception as e:
        # Handle any errors that occur
        return f"An error occurred while loading the privacy policy: {e}", 500
