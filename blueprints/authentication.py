# auth.py
import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from helpers.auth_functions import get_db_connection
from werkzeug.security import generate_password_hash


auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Track login attempts in session
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Connect to the database and fetch the user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            # Email not found
            flash("The email address is not found. Please try again or register an account.", "error")
            return redirect(url_for('auth_bp.login'))

        stored_password_hash = user['password_hash']
        if not check_password_hash(stored_password_hash, password):
            # Increment failed login attempts
            session['login_attempts'] += 1

            if session['login_attempts'] >= 5:
                # Lockout logic after 5 failed attempts
                flash("Too many failed attempts. Your account is locked. Please contact ies@sverigeslarare.se to reset your password.", "error")
                return redirect(url_for('auth_bp.login'))

            # Calculate remaining attempts
            remaining_attempts = 5 - session['login_attempts']
            flash(f"Invalid email or password. {remaining_attempts} login attempts remaining.", "error")
            return redirect(url_for('auth_bp.login'))

        # Successful login
        session['login_attempts'] = 0  # Reset login attempts
        session['email'] = user['email']
        session['user_name'] = user['user_name']
        session['user_id'] = user['id']
        flash("Login successful!", "success")
        return redirect(url_for('home.home'))

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Ensure the database and tables are set up
    from helpers.database_functions import setup_database, view_database, setup_school_table
    setup_database()
    setup_school_table()
    view_database()

    # Fetch the school names from the database
    schools = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT school_name FROM schools")
        schools = [row[0] for row in cursor.fetchall()]  # Fetch all school names
        conn.close()
    except Exception as e:
        flash("An error occurred while retrieving the school list. Please try again later.", "error")
        print(f"Error: {e}")

    if request.method == 'POST':
        # Safely retrieve form inputs with default values
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate required fields
        if not all([first_name, last_name, email, school, password, confirm_password]):
            flash("All fields are required. Please fill in all the details.", "error")
            return render_template('register.html', schools=schools)

        # Ensure the selected school is valid
        if school not in schools:
            flash("Please select a valid school from the dropdown.", "error")
            return render_template('register.html', schools=schools)

        # Password validation (e.g., length, alphanumeric)
        password_regex = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$')
        if not password_regex.match(password):
            flash("Password must be at least 6 characters long, alphanumeric, and include at least one special character.", "error")
            return render_template('register.html', schools=schools)

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('register.html', schools=schools)

        # Save user data to the database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("An account with this email already exists. Please log in.", "error")
                return render_template('register.html', schools=schools)

            # Insert user data
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, school_id, consent)
                VALUES (?, ?, ?, ?, ?)
            """, (first_name, last_name, email, school, True))

            user_id = cursor.lastrowid

            # Insert authentication data
            cursor.execute("""
                INSERT INTO user_auth (user_id, password_hash)
                VALUES (?, ?)
            """, (user_id, generate_password_hash(password)))

            conn.commit()
            conn.close()

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash("An error occurred during registration. Please try again later.", "error")
            print(f"Error: {e}")

    return render_template('register.html', schools=schools)

