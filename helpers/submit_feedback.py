from flask import request, session, flash, redirect
import os

def submit_feedback():
    rating = request.form.get('rating')
    issue_faced = request.form.get('issue_faced')
    issue_description = request.form.get('issue_description')
    permission_to_save = request.form.get('permission_to_save')

    # Handle feedback rating (store in a database or log)
    # Placeholder for storing feedback
    print(f"User Rating: {rating}")
    print(f"Issue Faced: {issue_faced}")
    if issue_description:
        print(f"Issue Description: {issue_description}")

    # Save the PDF if an issue is reported and permission is granted
    if issue_faced == 'yes' and permission_to_save == 'yes':
        uploaded_pdf = session.get('uploaded_pdf')
        if uploaded_pdf:
            feedback_directory = 'feedback_issues'
            if not os.path.exists(feedback_directory):
                os.makedirs(feedback_directory)
            pdf_filename = f"issue_{session['session_id']}_{uploaded_pdf.filename}"
            uploaded_pdf.save(os.path.join(feedback_directory, pdf_filename))
            flash('Thank you for your feedback! We have saved your schedule to help improve the app.', 'success')
        else:
            flash('Error: Could not save the PDF for analysis.', 'error')

    return redirect('/')
