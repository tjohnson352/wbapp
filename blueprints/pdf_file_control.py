from fpdf import FPDF
from flask import send_file

@app.route('/generate-report', methods=['GET'])
def generate_report():
    try:
        # Read explanations
        explanations = read_explanation_file("helpers/explanation.txt")

        # Prepare schedules
        filtered_schedules = prepare_schedules(day_dfs)

        # Generate the PDF
        output_path = "output_report.pdf"
        generate_pdf_with_schedules(explanations, filtered_schedules, output_path)

        # Send the PDF as a downloadable file
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


# Function to read the explanation file
def read_explanation_file(filepath):
    """
    Reads the explanation text file and returns its content as a dictionary for easy integration into the report.
    """
    content = {}
    current_section = None

    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("####"):
                # Extract the section title (remove the '#### ' prefix)
                current_section = line[4:].strip()
                content[current_section] = []
            elif current_section:
                # Append the line to the current section
                content[current_section].append(line)

    # Convert list of lines to single string for each section
    for section in content:
        content[section] = "\n".join(content[section])
    
    return content

# Function to prepare schedules for the PDF report
def prepare_schedules(day_dfs):
    """
    Prepares schedules for inclusion in the PDF by filtering out OFF days and formatting data.

    Parameters:
        day_dfs (dict): Dictionary of day-specific DataFrames (df3a, df3b, etc.).

    Returns:
        dict: Filtered and formatted schedules by day.
    """
    schedules = {}
    for day, df in day_dfs.items():
        # Filter out days with frametime OFF
        if not df.empty and df.iloc[0]['timespan'] != "00:00 - 00:00":
            # Format data for inclusion in PDF
            formatted_df = df[['timespan', 'activities', 'type', 'issues']].copy()
            schedules[day] = formatted_df
    return schedules

# Custom PDF class to manage report generation
class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def add_title(self, title):
        self.set_font("Arial", style='B', size=16)
        self.cell(200, 10, txt=title, ln=True, align='C')

    def add_section(self, title, content):
        self.set_font("Arial", style='B', size=14)
        self.ln(10)  # Add some space
        self.cell(0, 10, txt=title, ln=True)
        self.set_font("Arial", size=12)
        self.multi_cell(0, 10, content)

    def add_schedule(self, day, schedule):
        self.set_font("Arial", style='B', size=14)
        self.ln(10)  # Add space before each day
        self.cell(0, 10, txt=f"Schedule for {day}", ln=True)

        # Add color-coded table headers
        self.set_fill_color(200, 200, 200)  # Light gray background
        self.set_font("Arial", style='B', size=12)
        self.cell(40, 10, "Timespan", border=1, fill=True, align='C')
        self.cell(80, 10, "Activities", border=1, fill=True, align='C')
        self.cell(40, 10, "Type", border=1, fill=True, align='C')
        self.cell(30, 10, "Issues", border=1, fill=True, align='C')
        self.ln()

        # Add rows with color coding
        self.set_font("Arial", size=12)
        for _, row in schedule.iterrows():
            # Apply color based on type
            if row['type'] == 'TEACHING':
                self.set_fill_color(230, 255, 230)  # Light green
            elif row['type'] == 'GENERAL/DUTY':
                self.set_fill_color(255, 255, 200)  # Light yellow
            else:
                self.set_fill_color(255, 230, 230)  # Light red (e.g., violations)

            self.cell(40, 10, row['timespan'], border=1, fill=True, align='C')
            self.cell(80, 10, row['activities'], border=1, fill=True, align='L')
            self.cell(40, 10, row['type'], border=1, fill=True, align='C')
            self.cell(30, 10, row['issues'] if pd.notnull(row['issues']) else "", border=1, fill=True, align='L')
            self.ln()

# Function to generate the complete PDF report
def generate_pdf_with_schedules(explanations, schedules, output_path):
    pdf = PDFReport()
    pdf.add_page()
    pdf.add_title("Weekly Schedule Report")

    # Add explanations
    for section, content in explanations.items():
        pdf.add_section(section, content)

    # Add schedules
    for day, schedule in schedules.items():
        pdf.add_schedule(day, schedule)

    # Save the PDF
    pdf.output(output_path)
