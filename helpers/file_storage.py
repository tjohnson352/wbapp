import os
from werkzeug.utils import secure_filename


def validate_and_save_uploaded_file(uploaded_file, upload_folder, max_file_size_mb=5):
    """
    Validates and saves an uploaded file to the specified folder.

    Args:
        uploaded_file: The uploaded file from a Flask request.
        upload_folder: The folder where the file should be saved.
        max_file_size_mb: Maximum allowed file size in MB.

    Returns:
        str: The path to the saved file.

    Raises:
        ValueError: If the file is invalid or too large.
    """
    if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
        raise ValueError('Invalid file type. Please upload a PDF file.')

    # Validate file size
    uploaded_file.seek(0, os.SEEK_END)
    file_size_mb = uploaded_file.tell() / (1024 * 1024)
    uploaded_file.seek(0)
    if file_size_mb > max_file_size_mb:
        raise ValueError(f'The uploaded file is too large. Max size is {max_file_size_mb} MB.')

    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)

    # Save file with a secure filename
    filename = secure_filename(uploaded_file.filename)
    filepath = os.path.join(upload_folder, filename)
    uploaded_file.save(filepath)

    return filepath
