Schedule Upload Web App

Overview

This web application allows teachers to upload their teaching schedules in PDF format. The app provides a comprehensive overview of the schedule by extracting and analyzing the data to summarize key time allocations and assess how well it aligns with the collective agreement.

The application is built using Flask and is modular to ensure easy maintenance and scalability. The main features implemented so far include a PDF upload form, data extraction, and instructional guidance on how to download the schedule from SchoolSoft.

Features

PDF Upload Functionality: Teachers can upload their schedules in PDF format, which is processed for further analysis.

Instructional Guidance: The application includes step-by-step instructions to help teachers download their schedules from SchoolSoft and upload them to the web app.

Modular Structure: The application is structured in a modular way to improve maintainability. Key functionalities are separated into different files for better code organization.

Schedule Updates: Allows teachers to update and classify activities on their schedules, including assigning "Day" and "Type" fields to ensure proper alignment.

File Structure

The project is organized into different modules and directories for clarity and modularity:

project_root/
│
├── app.py                          # Main application entry point, registers routes
├── routes/                         # Contains route definitions
│   └── routes.py                   # Handles PDF upload and other related routes
├── services/                       # Service modules for data processing
│   ├── data_service.py             # Handles data cleaning and structuring
│   ├── frametime_service.py        # Handles frametime data processing
│   ├── pdf_service.py              # Handles PDF data extraction
│   └── schedule_service.py         # Handles schedule updates
├── templates/                      # HTML templates for the web interface
│   ├── upload_schedule.html        # Template for the PDF upload page
│   ├── frametime.html              # Template for viewing and editing frametime (df4)
│   ├── updates.html                # Template for viewing and updating schedule (df6)
│   ├── structure.html              # Template for displaying data structure
│   ├── base.html                   # Base template for shared HTML layout
│   └── tables/                     # Directory for tables like df1, df2, df3, df4, df5, df6, df7, df8
│       ├── df1.html
│       ├── df2.html
│       ├── df3.html
│       ├── df4.html
│       ├── df5.html
│       ├── df6.html
│       ├── df7.html
│       └── df8.html
├── static/                         # Static files (CSS, JS, images)
├── instance/                       # Stores SQLite sessions
│   └── sessions.sqlite             # Session database
├── README.md                       # Documentation for the project
└── tree.txt                        # Text representation of the file structure

Key Files

``: The main entry point of the application. It registers the blueprint for the upload routes.

``: Contains the routes for uploading PDF files, displaying different DataFrames, and updating schedules. It includes error handling for missing files, incorrect file types, and successful uploads.

``: Contains service modules for data processing, PDF extraction, and schedule updates.

``: Contains the HTML templates used for displaying different pages, including uploading schedules, viewing frametime, and updating schedule details.

Routes Overview

Here is a list of the primary routes available in the application, categorized into general operations and DataFrame displays:

General Operations

Upload Schedule

Route: //

Methods: GET, POST

Description: Handles uploading of the schedule PDF. It starts a new session, extracts data from the PDF, and stores DataFrames (df1, df2, df3, df5) in the session.

Display Frametime

Route: /frametime

Methods: GET, POST

Description: Displays or updates the frame time (df4). If it is a POST request, the frame time data is updated using the user input from the form.

Display Updates (Day/Type Update Stage)

Route: /updates

Methods: GET, POST

Description: Displays and handles updates to the schedule's "Day" and "Type" columns (df6). It updates the current stage and moves to the next after each update (e.g., from "day" to "type").

DataFrame Displays

``: Displays raw schedule data extracted from the uploaded PDF.

``: Displays cleaned and structured schedule data extracted from df1.

``: Displays structured schedule data, with activities split, including time spans.

``: Displays or edits the frame time (df4), which stores planning/preparation time information.

``: Displays metadata (e.g., teacher's name and school name) extracted from df1.

``: Displays the schedule update view for modifying "Day" and "Type" fields of activities.

``: Displays the final validated schedule after removing rows with "REMOVE" in the "Day" column, sorted by day and start time.

``: Displays an additional view of the validated schedule with all activities grouped by day and sorted by start time.

DataFrames Used in the Application

``: Stores raw data extracted from the uploaded PDF schedule. This DataFrame is used for capturing the initial schedule information in a line-by-line format.

``: A cleaned and restructured version of df1. This DataFrame organizes the data to make it more readable and usable for further processing.

``: Stores structured data with split activities, including start and end times, and calculates the duration in minutes. This DataFrame represents the schedule with extracted time spans and activities.

``: Stores frametime information (planning/preparation time) provided by the user for each day of the week. This helps track the time allocated for planning compared to actual lessons.

``: Stores metadata, specifically the teacher's name and school name, extracted from df1. This DataFrame helps provide context for the schedule data.

``: Represents the initial version of the schedule that allows teachers to update the "Day" and "Type" fields for each activity.

``: A cleaned-up version of df6, excluding rows marked with "REMOVE" in the "Day" column and sorted by day and start time.

``: A final view of the schedule, sorted by day and then by start time, used for additional review.

How to Run the Application

Prerequisites

Python 3.6 or higher

Flask

Setup Instructions

Clone the Repository: Clone this repository to your local machine.

git clone <repository-url>

Install Dependencies: Install the required packages using pip.

pip install Flask Werkzeug

Run the Application: Navigate to the project root directory and run the Flask app.

python app.py

Access the Web App: Open your web browser and navigate to http://127.0.0.1:5000/upload to use the application.

Using the Web App

Download Schedule from SchoolSoft:

Log in to SchoolSoft.

Navigate to "My Schedule" in the left menu.

Click the PDF icon to download your schedule.

Upload the Schedule:

Use the form on the upload page to select and upload the PDF file.

The app will process the file and display a confirmation message once uploaded successfully.

Edit and Update Schedule:

After uploading, review the extracted schedule.

Update "Day" and "Type" fields as needed and save changes.

Future Enhancements

Advanced PDF Data Extraction: Improvement of PDF data extraction to better handle various formatting issues.

Enhanced Error Handling: Provide more detailed error messages for different failure scenarios during upload and processing.

User Authentication: Add user authentication to manage multiple teachers uploading schedules.

License

This project is licensed under the MIT License.

Contribution

Contributions are welcome! Feel free to open issues or submit pull requests to improve the application.

