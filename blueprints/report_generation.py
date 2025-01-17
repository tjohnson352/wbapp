from fpdf import FPDF
from flask import Blueprint, send_file, session
import pandas as pd
from io import StringIO
import os

report_blueprint = Blueprint('report', __name__)

# Function to prepare schedules for the PDF report
def prepare_schedules(day_dfs, ft_days):
    """
    Prepares schedules for inclusion in the PDF by filtering out OFF days and formatting data.

    Parameters:
        day_dfs (dict): Dictionary of day-specific DataFrames (df3a, df3b, etc.).
        ft_days (list): List of days in the session.

    Returns:
        tuple: Filtered and formatted schedules by day, included days, and OFF days.
    """
    schedules = {}
    included_days = []
    off_days = []

    for day, df in day_dfs.items():
        # Check if the day is OFF
        if df.empty or (not df.empty and df.iloc[0]['timespan'] == "00:00 - 00:00"):
            off_days.append(day)
        else:
            included_days.append(day)

            # Format data for inclusion in PDF
            formatted_df = df[['timespan', 'activities', 'type', 'minutes', 'issues']].copy()

            # Modify FRAMETIME rows
            for idx, row in formatted_df.iterrows():
                if row['type'] == 'FRAMETIME':
                    timespan_split = row['timespan'].split(' - ')
                    formatted_df.at[idx, 'timespan'] = timespan_split[0]  # Take only the first half of the timespan
                    formatted_df.at[idx, 'minutes'] = "---"  # Replace minutes with '---' for FRAMETIME

            formatted_df.rename(columns={'issues': 'Issues Found'}, inplace=True)  # Rename column for clarity
            schedules[day] = formatted_df

    # Include only days from ft_days that are not OFF
    included_days = [day for day in ft_days if day in included_days]
    off_days = [day for day in ft_days if day in off_days]

    return schedules, included_days, off_days

# Custom PDF class to manage report generation
class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_left_margin(15)  # Set left margin
        self.set_right_margin(15)  # Set right margin
        self.set_font("Arial", size=10)  # Default font is Arial, size 10

    def add_title(self, title):
        self.set_font("Arial", style='B', size=14)
        self.cell(0, 10, txt=title, ln=True, align='C')  # Full-page centered title

    def add_metadata(self, full_name, school_name, included_days, off_days):
        """
        Adds teacher metadata to the PDF report in two aligned columns.

        Parameters:
            full_name (str): The teacher's full name.
            school_name (str): The name of the school.
            included_days (list): List of workdays.
            off_days (list or str): List of off days or the string "None".
        """
        self.ln(6)  # Add some vertical spacing before metadata

        # Define label and value widths
        label_width = 30
        value_width = 150

        # Teacher
        self.set_font("Arial", style='B', size=10)
        self.cell(label_width, 10, "Teacher:", align='L')
        self.set_font("Arial", size=10)
        self.cell(value_width, 10, full_name, ln=True)

        # School
        self.set_font("Arial", style='B', size=10)
        self.cell(label_width, 10, "School:", align='L')
        self.set_font("Arial", size=10)
        self.cell(value_width, 10, school_name, ln=True)

        # Workdays
        self.set_font("Arial", style='B', size=10)
        self.cell(label_width, 10, "Workdays:", align='L')
        self.set_font("Arial", size=10)
        self.cell(value_width, 10, ", ".join(included_days), ln=True)

        # Off Days
        self.set_font("Arial", style='B', size=10)
        self.cell(label_width, 10, "Off Days:", align='L')
        self.set_font("Arial", size=10)
        self.cell(value_width, 10, ", ".join(off_days) if off_days != "none" else "None", ln=True)

    def add_schedule(self, day, schedule):
        self.set_font("Arial", style='B', size=10)
        self.ln(10)  # Add space before each day's schedule
        self.cell(0, 10, txt=f"Schedule for {day}", ln=True)

        # Column widths
        col_widths = [30, 50, 40, 20, 40]  # Adjusted widths: [Time, Activities, Type, Minutes, Issues Found]

        # Add table headers with dark gray background and white bold text
        self.set_fill_color(64, 64, 64)  # Dark gray background
        self.set_text_color(255, 255, 255)  # White text
        self.set_font("Arial", style='B', size=10)
        self.cell(col_widths[0], 8, "Time", border=1, fill=True, align='C')
        self.cell(col_widths[1], 8, "Activities", border=1, fill=True, align='C')
        self.cell(col_widths[2], 8, "Type", border=1, fill=True, align='C')
        self.cell(col_widths[3], 8, "Minutes", border=1, fill=True, align='C')
        self.cell(col_widths[4], 8, "Issues Found", border=1, fill=True, align='C')
        self.ln()

        # Add rows with alternating row colors and bold `type`
        self.set_font("Arial", size=10)
        self.set_text_color(0, 0, 0)  # Reset text color to black
        fill = False  # Track whether to fill row with color
        for _, row in schedule.iterrows():
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)  # Alternate colors
            row_type = row['type'].lower().capitalize()
            self.set_font("Arial", style='B' if row_type in ["Teaching", "General/Duty", "Break"] else '', size=10)

            self.cell(col_widths[0], 8, row['timespan'], border=1, fill=True, align='R')
            self.cell(col_widths[1], 8, row['activities'], border=1, fill=True, align='L')
            self.cell(col_widths[2], 8, row_type, border=1, fill=True, align='C')
            self.cell(col_widths[3], 8, str(row['minutes']), border=1, fill=True, align='C')
            self.cell(col_widths[4], 8, row['Issues Found'] if pd.notnull(row['Issues Found']) else "", border=1, fill=True, align='L')
            self.ln()
            fill = not fill  # Toggle fill for next row

# Function to generate the complete PDF report
def generate_pdf_with_schedules(full_name, school_name, explanations, schedules, included_days, off_days, output_path):
    pdf = PDFReport()
    pdf.add_page()
    pdf.add_title("Work Schedule Analysis")

    # Add teacher and school metadata on one line
    pdf.add_metadata(full_name, school_name, included_days, off_days)

    # Add schedules
    for day, schedule in schedules.items():
        pdf.add_schedule(day, schedule)

    # Add explanations
    for section, content in explanations.items():
        pdf.add_section(section, content)

    # Save the PDF
    pdf.output(output_path)




def off_days(ft_days):
    """
    Determines the off days based on the provided ft_days list.

    Parameters:
        ft_days (list): List of days considered as workdays (e.g., ['Monday', 'Tuesday']).

    Returns:
        list or str: A list of off days (e.g., ['Wednesday', 'Thursday', 'Friday']),
                     or "none" if all days are in ft_days.
    """
    all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    off_days_list = [day for day in all_days if day not in ft_days]

    # If no off days exist, return the string "none"
    return "none" if not off_days_list else off_days_list
