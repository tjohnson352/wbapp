# helpers/report_table_generator.py

import pandas as pd
from flask import session
from io import StringIO

def report_table():
    """
    Generates a summary report table based on variables stored in the session
    and saves a formatted DataFrame with 'Attribute', 'Details', and 'Explanation' columns to the session in JSON format.
    """
    # Define user-friendly column names and their explanations
    columns = {
        'full_name': {
            'name': 'Full Name',
            'explanation': 'The full name of the teacher or staff member.'
        },
        'school_name': {
            'name': 'School Name',
            'explanation': 'The name of the school where the individual works.'
        },
        'work_percent': {
            'name': 'Work Percentage (%)',
            'explanation': 'The contracted percentage of full-time work (e.g., 100% for full-time, 50% for part-time).'
        },
        'middle_management': {
            'name': 'Middle Management (Yes/No)',
            'explanation': 'Indicates if the individual has a middle management role (e.g., HoD, HoY, Coordinator). This includes a 1.5–2 hour reduction in teaching time.'
        },
        'ft_days': {
            'name': 'Scheduled Days',
            'explanation': 'The days of the week when the individual is scheduled to work.'
        },
        'off_days': {
            'name': 'Off Days',
            'explanation': 'The days of the week when the individual is not scheduled to work.'
        },
        'planning_time': {
            'name': 'Planning Time (hrs)',
            'explanation': 'Unscheduled time allocated for lesson planning, grading, and other non-teaching tasks.'
        },
        'total_break_time': {
            'name': 'Total Break Time (hrs)',
            'explanation': 'The total time allocated for breaks during the work schedule. Added onto contractual frametime.'
        },
        'total_general_duty_time': {
            'name': 'Total General Duty Time (hrs)',
            'explanation': 'The time spent on general duties such as hallway monitoring, meetings, or recess duties.'
        },
        'total_teach_time': {
            'name': 'Total Teaching Time (hrs)',
            'explanation': 'The total hours spent on teaching activities in the schedule.'
        },
        'contract_teachtime': {
            'name': 'Contractual Teaching Time (hrs)',
            'explanation': 'The teaching time specified in the contract, based on the work percentage.'
        },
        'adjusted_contract_teach_time': {
            'name': 'Adjusted Teaching Time (hrs)',
            'explanation': 'The teaching time after any adjustments (e.g., middle management reduction).'
        },
        'contract_frametime': {
            'name': 'Contractual Frametime (hrs)',
            'explanation': 'The total time specified in the contract, including teaching and non-teaching duties.'
        },
        'contract_frametime_with_breaks': {
            'name': 'Frametime with Breaks (hrs)',
            'explanation': 'The total frametime, including additional time allocated for scheduled breaks.'
        },
        'assigned_frametime': {
            'name': 'Assigned Frametime (hrs)',
            'explanation': 'The actual time assigned in the schedule for all activities.'
        },
        'overtime_teach': {
            'name': 'Overtime Teaching (hrs)',
            'explanation': 'The additional teaching hours beyond the contractual or adjusted teaching time.'
        },
        'over_framtime': {
            'name': 'Over Frametime (hrs)',
            'explanation': 'The additional frametime hours beyond the contractual frametime (with breaks).'
        },
        'total_overtime': {
            'name': 'Total Overtime (hrs)',
            'explanation': 'The combined total of overtime teaching and over frametime hours. Teachers should report this as overtime pay when submitting your monthly work time on ies.medvind.visma.com.'
        }
    }

    # Retrieve data from session
    data = {key: session.get(key) for key in columns}

    # Ensure all required columns are in the data
    for column in columns:
        if column not in data:
            raise KeyError(f"Missing required column in session data: {column}")

    # Prepare the DataFrame with three columns: 'Attribute', 'Details', and 'Explanation'
    formatted_data = [
        {
            'Attribute': columns[key]['name'],
            'Details': data[key],
            'Explanation': columns[key]['explanation']
        }
        for key in columns
    ]

    # Create the DataFrame
    df = pd.DataFrame(formatted_data)

    # Save the DataFrame to the session in JSON format
    session['report_table'] = df.to_json(orient='split')


# helpers/report_table_generator.py

def generate_plain_text_report():
    """
    Generate a plain text report with right-aligned attributes
    and save it to the session.
    """
    # Define report attributes and values
    report_data = [
        ("Name:", session.get('full_name', 'N/A')),
        ("School:", session.get('school_name', 'N/A')),
        ("Work Percentage:", f"{session.get('work_percent', 'N/A')}%"),
        ("Middle Management:", 
         "Yes: Middle managers get 1.5 hrs teaching time reduction" if session.get('middle_management') == "Yes" else "No"),
        ("Scheduled Days:", ", ".join(session.get('ft_days', []))),
        ("Off Days:", ", ".join(session.get('off_days', []))),
        ("Planning:", f"{session.get('planning_time', 'N/A')} hrs"),
        ("Breaks:", f"{session.get('total_break_time', 'N/A')} hrs"),
        ("General/Duties:", f"{session.get('total_general_duty_time', 'N/A')} hrs"),
        ("Assigned teaching:", f"{session.get('total_teach_time', 'N/A')} hrs"),
        ("Contract teaching:", f"{session.get('contract_teachtime', 'N/A')} hrs"),
        ("Teaching adjustment:", f"{session.get('adjusted_contract_teach_time-contract_teachtime', 'N/A')} hrs"),
        ("Contract Frametime:", f"{session.get('contract_frametime', 'N/A')} hrs"),
        ("Contract FT + Breaks:", f"{session.get('contract_frametime_with_breaks', 'N/A')} hrs"),
        ("Assigned Frametime:", f"{session.get('assigned_frametime', 'N/A')} hrs"),
        ("Overtime (teaching):", f"{session.get('overtime_teach', 'N/A')} hrs"),
        ("Overtime (FT):", f"{session.get('over_framtime', 'N/A')} hrs"),
        ("Overtime (total):", f"{session.get('total_overtime', 'N/A')} hrs")
    ]

    # Determine the maximum width for alignment
    max_attr_width = max(len(item[0]) for item in report_data)

    # Create the report lines with right-aligned attributes
    report_lines = [
        f"{attr:>{max_attr_width}} {value}"
        for attr, value in report_data
    ]

    # Join the lines into a single string
    plain_text_report = "\n".join(report_lines)

    # Save the report to the session
    session['plain_text_report'] = plain_text_report


def generate_plain_text_schedule():
    """
    Generate a plain text schedule in a tabular format and save it to the session.
    """
    # Retrieve relevant session data
    ft_days = session.get('ft_days', [])
    df_names = session.get('df_names', [])
    raw_dataframes = session.get('dataframes', {})

    # Convert JSON strings back to DataFrames
    dataframes = {}
    for key, value in raw_dataframes.items():
        if value:  # Check if value is not None
            try:
                dataframes[key] = pd.read_json(StringIO(value))
            except Exception as e:
                print(f"Error loading DataFrame {key}: {e}")

    # Placeholder for plain text schedule
    schedule_lines = []

    # Function to wrap text while keeping words whole
    def wrap_text(text, width):
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + (1 if current_line else 0) > width:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + (1 if current_line else 0)

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    # Map ft_days to DataFrames
    for day, df_name in zip(ft_days, df_names):
        if df_name in dataframes:
            # Load the DataFrame for the day
            df = dataframes[df_name]

            # Add day header
            schedule_lines.append(f"--- {day.upper()} ---")

            # Add table header with updated "Issues Found"
            header = f"{'Timespan':<15} {'Activity':<20} {'Type':<15} {'Minutes':<10} {'Issues Found':<30}"
            schedule_lines.append(header)
            schedule_lines.append("-" * len(header))

            # Populate rows
            for _, row in df.iterrows():
                # Process timespan
                timespan = row.get('timespan', 'N/A')
                if timespan != 'N/A' and ' - ' in timespan:
                    start, end = timespan.split(' - ')
                    if row.get('activities', '').lower() == 'start work':
                        timespan = f"{start} - XXXXX"
                    elif row.get('activities', '').lower() == 'end work':
                        timespan = f"XXXXX - {end}"
                
                # Process minutes
                minutes = "---" if row.get('activities', '').lower() in ['start work', 'end work'] else str(row.get('minutes', 'N/A'))

                # Other fields
                activity = row.get('activities', 'N/A')[:30]  # Truncate to 30 chars
                activity_type = row.get('type', 'N/A')
                issues = row.get('issues', 'none')  # Full issues text

                # Append the main row
                schedule_lines.append(
                    f"{timespan:<15} {activity:<20} {activity_type:<15} {minutes:<10}"
                )

                # Wrap long "Issues Found" into additional rows
                if len(issues) > 30:
                    wrapped_issues = wrap_text(issues, 30)
                    for i, line in enumerate(wrapped_issues):
                        if i == 0:
                            # Append the first line of "Issues Found" to the main row
                            schedule_lines[-1] += f" {line:<30}"
                        else:
                            # Append subsequent lines of "Issues Found" as new rows
                            schedule_lines.append(
                                f"{'':<15} {'':<20} {'':<15} {'':<10} {line:<30}"
                            )
                else:
                    # Append short "Issues Found" directly to the main row
                    schedule_lines[-1] += f" {issues:<30}"

            schedule_lines.append("\n")  # Add a blank line between days
        else:
            schedule_lines.append(f"--- {day.upper()} ---")
            schedule_lines.append("No schedule available for this day.\n")

    # Join lines and save to session
    plain_text_schedule = "\n".join(schedule_lines)
    session['plain_text_schedule'] = plain_text_schedule


from fpdf import FPDF

def generate_pdf():
    """
    Generate a professionally styled PDF report combining plain_text_report and plain_text_schedule.
    """
    # Initialize the PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Set font for the header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Weekly Schedule Report', ln=True, align='C')
    pdf.ln(10)  # Add some space

    # Add the Summary Report
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Summary Report', ln=True)
    pdf.ln(5)  # Add some space
    pdf.set_font('Arial', '', 12)
    
    for line in session['plain_text_report'].split('\n'):
        pdf.cell(0, 8, line, ln=True)

    pdf.ln(10)  # Add space before the schedule

    # Add the Weekly Schedule
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Weekly Schedule', ln=True)
    pdf.ln(5)  # Add some space
    pdf.set_font('Arial', '', 12)

    # Parse the schedule lines
    for line in session['plain_text_schedule'].split('\n'):
        if line.startswith("---"):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, line, ln=True)
            pdf.set_font('Arial', '', 12)
        elif line.startswith("Timespan"):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, line, ln=True)
            pdf.set_font('Arial', '', 12)
        elif line.strip() == "":
            pdf.ln(5)  # Add spacing for blank lines
        else:
            pdf.cell(0, 8, line, ln=True)

    # Save the PDF
    pdf_file_path = "/mnt/data/weekly_schedule_report_updated.pdf"
    pdf.output(pdf_file_path)
    return pdf_file_path
