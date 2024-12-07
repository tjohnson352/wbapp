from flask import render_template
import os

def generate_html_from_template(df, title, output_file):
    """
    Generate an HTML file from a DataFrame using a Jinja2 template.

    :param df: Pandas DataFrame to render in the template
    :param title: Title to display in the generated HTML
    :param output_file: Path to save the generated HTML file
    """
    try:
        # Render the HTML content using the template
        rendered_html = render_template('tables/df_template.html', df=df, title=title)

        # Ensure the directory for the output file exists
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write the rendered HTML to the output file
        with open(output_file, 'w') as f:
            f.write(rendered_html)

        print(f"Successfully generated HTML: {output_file}")
    except Exception as e:
        print(f"Error generating HTML: {e}")

def format_time(value):
    """Format time strings to HH:MM without dates or seconds."""
    try:
        if isinstance(value, str) and ":" in value:
            hours, minutes = value.split(":")[:2]
            return f"{int(hours):02d}:{int(minutes):02d}"
        return value  # Return as-is if not a valid time string
    except Exception as e:
        return value  # Fallback in case of errors
