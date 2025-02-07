from flask import Blueprint, render_template, request, session, flash, redirect, url_for

meta1_blueprint = Blueprint('meta1', __name__)

@meta1_blueprint.route('/meta1', methods=['GET', 'POST'])
def meta1():
    """Handle additional metadata inputs."""
    if request.method == 'POST':
        try:
            # Collect the work percentage and middle manager status
            work_percent = request.form.get('work_percent', '100')  # Default is 100%
            middle_manager = request.form.get('middle_manager', 'no')  # Default is no

            # Validate work percentage
            work_percent = int(work_percent)
            if work_percent < 0 or work_percent > 100:
                flash('Work percentage must be between 0 and 100.', 'error')
                return render_template('meta1.html', work_percent=work_percent, middle_manager=middle_manager)

            # Store values in session
            session['work_percent'] = work_percent
            session['middle_manager'] = middle_manager

            return redirect('/days')  # Proceed to the next step (defined elsewhere)

        except ValueError:
            flash('Invalid input. Please enter a valid percentage.', 'error')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')

    # For GET requests, display the form with default values
    return render_template('meta1.html', work_percent=100, middle_manager='no')
