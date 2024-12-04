@display_blueprint.route('/edit_schedule', methods=['GET', 'POST'])
def edit_schedule():
    """Route to edit the schedule."""
    if 'df3' not in session:
        return "Data not available for editing."

    df3 = pd.read_json(session['df3'])

    if request.method == 'POST':
        # Update df3 based on form inputs
        for index in range(len(df3)):
            df3.at[index, 'type'] = request.form.get(f"type_{index}", df3.at[index, 'type'])
            df3.at[index, 'start'] = request.form.get(f"start_{index}", df3.at[index, 'start'])
            df3.at[index, 'end'] = request.form.get(f"end_{index}", df3.at[index, 'end'])

        # Save the updated DataFrame to the session
        session['df3'] = df3.to_json()

        # Optionally redirect or confirm changes
        return "Schedule updated successfully!"

    # Drop the 'day' column and render the template
    df3 = df3.drop(columns=['day'], errors='ignore')
    return render_template('edit_schedule.html', df3=df3)
