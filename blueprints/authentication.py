# auth.py
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from helpers.auth_functions import get_db_connection
from helpers.database_functions import setup_database, view_database, setup_school_table
import secrets
import sqlite3
import random
import string
import datetime
import random


auth_bp = Blueprint('auth_bp', __name__)

def generate_temp_password(length=6):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    setup_database()
    setup_school_table()
    view_database()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row  # Enables dictionary-like access for rows
            cursor = conn.cursor()

            # Fetch user details from the database
            cursor.execute("SELECT * FROM user_auth WHERE login_id = ?", (email,))
            user = cursor.fetchone()

            if user is None:
                flash("Email not found. Try again or register an account.", "error")
                return redirect(url_for('auth_bp.login'))

            login_attempts = user['login_attempts']
            stored_password_hash = user['password_hash']
            temp_password_hash = user['temp_password']  # Read temp_password from the database

            # Decide which password hash to use for authentication
            password_hash_to_use = temp_password_hash if temp_password_hash else stored_password_hash

            # Check if the account is locked
            if login_attempts >= 3:
                flash("Your account is locked. Please reset your password to regain access.", "error")
                return redirect(url_for('auth_bp.reset_password'))  # Redirect to reset-password page

            # Authenticate the user
            if check_password_hash(password_hash_to_use, password):
                flash("Login successful!", "success")

                # Reset login attempts and clear temp_password if it was used
                cursor.execute("UPDATE user_auth SET login_attempts = 0, temp_password = NULL WHERE user_id = ?", (user['user_id'],))
                conn.commit()

                # Save user session and redirect to the dashboard
                session['user_id'] = user['user_id']
                session['is_admin'] = user['is_admin']
                session.permanent = True  # Enable session timeout
                return redirect(url_for('auth_bp.dashboard'))

            else:
                # Increment login attempts after failed login
                login_attempts += 1
                cursor.execute("UPDATE user_auth SET login_attempts = ? WHERE user_id = ?", (login_attempts, user['user_id']))
                conn.commit()

                remaining_attempts = 3 - login_attempts
                if remaining_attempts > 0:
                    flash(f"Invalid email or password. {remaining_attempts} login attempts remaining.", "error")
                else:
                    flash("Your account is locked. Please reset your password.", "error")
                    return redirect(url_for('auth_bp.reset_password'))

                return redirect(url_for('auth_bp.login'))

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                flash("The server is being updated, please try again in a moment.", "error")
            else:
                flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for('auth_bp.login'))

        finally:
            conn.close()  # Ensure the database connection closes

    return render_template('login.html')

    
# Function to get random security questions
def get_random_security_questions():
    """
    Reads the security questions from a text file and selects 10 random questions.
    """
    file_path = "helpers/security_questions.txt"
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            questions = [line.strip() for line in file if line.strip()]

        if len(questions) < 10:
            raise ValueError("Not enough questions in the file to select 10.")

        return random.sample(questions, 10)
    
    except FileNotFoundError:
        print("Error: Security questions file not found.")
        return []
    except ValueError as e:
        print(f"Error: {e}")
        return []



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    setup_database()
    setup_school_table()
    insert_debug_data()

    # Fetch available schools
    schools = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT school_name FROM schools ORDER BY school_name")
        schools = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        flash("An error occurred while retrieving the school list.", "error")

    # Fetch security questions
    security_questions = get_random_security_questions()
    
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        privacy_consent = request.form.get('privacy_consent', None)

        # Validate Privacy Consent
        if not privacy_consent:
            flash("You must agree to the Privacy Policy to create an account.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Validate required fields
        if not all([first_name, last_name, email, school, password, confirm_password]):
            flash("All fields are required.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Password validation
        password_regex = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$')
        if not password_regex.match(password):
            flash("Password must be at least 6 characters long with letters, numbers, and a special character.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Security questions & answers
        question1, answer1 = request.form.get('security_question_1', '').strip(), request.form.get('security_answer_1', '').strip()
        question2, answer2 = request.form.get('security_question_2', '').strip(), request.form.get('security_answer_2', '').strip()
        question3, answer3 = request.form.get('security_question_3', '').strip(), request.form.get('security_answer_3', '').strip()

        if not all([question1, answer1, question2, answer2, question3, answer3]):
            flash("Security questions must be answered.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Sveriges Lärare Membership & Roles (default 0)
        sl_roles = {
            'sl_member': 0,
            'lokalombud': 0,
            'skyddsombud': 0,
            'forhandlingsombud': 0,
            'huvudskyddsombud': 0,
            'styrelseledamot': 0
        }

        # Update based on user selection
        if request.form.get('sl_member', '0') == '1':  
            sl_roles['sl_member'] = 1

        selected_roles = request.form.getlist('sl_roles')
        for role in selected_roles:
            if role in sl_roles:
                sl_roles[role] = 1

        # Determine is_admin value based on roles
        is_admin = 0  # Default to regular user

        if sl_roles['sl_member'] == 1:
            is_admin = 1  # Set to member
            print("is_admin=",is_admin)


        # Check if any officer role is selected
        officer_roles = ['lokalombud', 'skyddsombud', 'forhandlingsombud', 'huvudskyddsombud', 'styrelseledamot']
        if any(sl_roles[role] == 1 for role in officer_roles):
            is_admin = 2  # Set to unverified officer
            print("is_admin=",is_admin)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ✅ Ensure the email does not already exist
            cursor.execute("SELECT user_id FROM user_auth WHERE login_id = ?", (email,))
            if cursor.fetchone():
                flash(f"An account for {email} already exists.", "error")
                return render_template('register.html', schools=schools, form_data=request.form)

            # ✅ Ensure the school exists in the database
            cursor.execute("SELECT school_id FROM schools WHERE school_name = ?", (school,))
            school_data = cursor.fetchone()
            if not school_data:
                flash("Invalid school selection.", "error")
                return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)
            
            school_id = school_data[0]

            # ✅ Insert into `users` table FIRST to generate `user_id`
            cursor.execute("""
                INSERT INTO users (first_name, last_name, school_id, consent)
                VALUES (?, ?, ?, ?)
            """, (first_name, last_name, school_id, 1))
            
            user_id = cursor.lastrowid  # Get the generated user_id

            # ✅ Insert into `user_auth`
            cursor.execute("""
                INSERT INTO user_auth (user_id, login_id, password_hash, security_question_1, security_answer_1, 
                                    security_question_2, security_answer_2, security_question_3, security_answer_3, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email, generate_password_hash(password),
                question1, generate_password_hash(answer1),
                question2, generate_password_hash(answer2),
                question3, generate_password_hash(answer3),
                is_admin  # Include is_admin value
            ))

            # ✅ Insert into `sl_member_level`
            cursor.execute("""
                INSERT INTO sl_member_level (user_id, sl_member, lokalombud, skyddsombud, forhandlingsombud, huvudskyddsombud, styrelseledamot)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, sl_roles['sl_member'], sl_roles['lokalombud'], sl_roles['skyddsombud'],
                  sl_roles['forhandlingsombud'], sl_roles['huvudskyddsombud'], sl_roles['styrelseledamot']))

            # ✅ Insert into `verify_officer` if any officer role is requested
            if any(sl_roles.values()):
                cursor.execute("""
                    INSERT INTO verify_officer (user_id, lokalombud, skyddsombud, forhandlingsombud, huvudskyddsombud, styrelseledamot)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, sl_roles['lokalombud'], sl_roles['skyddsombud'], sl_roles['forhandlingsombud'],
                      sl_roles['huvudskyddsombud'], sl_roles['styrelseledamot']))

            conn.commit()
            conn.close()

            # ✅ Store `user_id` in session
            session['user_id'] = user_id

            flash("Account created! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))

        except Exception as e:
            flash("An error occurred during registration.", "error")

    return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection() 
        cursor = conn.cursor()

        try: 
            cursor.execute("SELECT user_id FROM user_auth WHERE login_id = ?", (email,))
            user = cursor.fetchone()

            if user:
                token = secrets.token_urlsafe(32)
                created_at = datetime.datetime.now()  # Store the current timestamp

                try:
                    # Insert new token with timestamp or update existing token
                    cursor.execute(
                        "INSERT INTO reset_tokens (user_id, token, created_at) VALUES (?, ?, ?)",
                        (user['user_id'], token, created_at)
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    cursor.execute(
                        "UPDATE reset_tokens SET token = ?, created_at = ? WHERE user_id = ?",
                        (token, created_at, user['user_id'])
                    )
                    conn.commit()

                # Redirect to the next step with the token
                return redirect(url_for('auth_bp.reset_password_security_questions', token=token))
            else:
                flash("Email not found.", "error")

        except sqlite3.Error as e:  # Add error handling
            flash(f"A database error occurred: {e}", "error")
            conn.rollback()  # Rollback in case of an error
        finally:
            conn.close()  # Close the connection in the finally block

    return render_template('reset-password.html')

@auth_bp.route('/dashboard', methods=['GET'])
def dashboard():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('auth_bp.login'))

    # Render the dashboard template for logged-in users
    return render_template('dashboard.html')

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth_bp.login'))


from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

@auth_bp.route('/reset-password-security-questions/<token>', methods=['GET', 'POST'])
def reset_password_security_questions(token):
    try:
        # Validate the reset token
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM reset_tokens WHERE token = ?", (token,))
        user = cursor.fetchone()

        if not user:
            flash("Invalid or expired token. Please request a new password reset.", "error")
            return redirect(url_for('auth_bp.reset_password'))

        user_id = user[0]

        # Fetch user's security questions and question index
        cursor.execute("""
            SELECT security_question_1, security_question_2, security_question_3,
                   security_answer_1, security_answer_2, security_answer_3, question_index
            FROM user_auth WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            flash("No security questions found for this user. Contact support.", "error")
            return redirect(url_for('auth_bp.reset_password'))

        # Unpack questions, answers, and question index
        question_list = [
            (result[0], result[3]),  # (question_1, answer_1)
            (result[1], result[4]),  # (question_2, answer_2)
            (result[2], result[5])   # (question_3, answer_3)
        ]
        question_index = session.get('question_index', result[6])  # Read from session or DB
        print("qI1: ", question_index)

        # Check if the question index exceeds available questions
        if question_index >= len(question_list):
            cursor.execute("UPDATE user_auth SET question_index = ? WHERE user_id = ?", (question_index, user_id))
            conn.commit()
            conn.close()
            print("qi2: ", question_index)
            flash("Too many failed attempts. Please email ies@sverigeslarare.se with 'WebApp Password Reset' in the subject.", "error")
            
            new_temp_password = generate_temp_password()
            print(f"[DEBUG] Generated temporary password: {new_temp_password}")

            cursor.execute(
                "UPDATE user_auth SET temp_password = ? WHERE user_id = ?",
                (generate_password_hash(new_temp_password), user['user_id'])
            )
            conn.commit()
            return redirect(url_for('auth_bp.reset_password'))

        # Get the current question and hashed answer
        current_question, hashed_answer = question_list[question_index]

        if request.method == 'POST':
            # Validate the answer
            provided_answer = request.form.get('security_answer', '').strip()
            if check_password_hash(hashed_answer, provided_answer):
                # Correct answer: proceed to password reset
                new_password = request.form.get('new_password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()

                # Validate new passwords
                if new_password != confirm_password:
                    flash("Passwords do not match. Try again.", "error")
                elif len(new_password) < 6:
                    flash("Password must be at least 6 characters long.", "error")
                else:
                    # Reset password and reset login_attempts in the database
                    cursor.execute("""
                        UPDATE user_auth
                        SET password_hash = ?, login_attempts = 0, question_index = 0
                        WHERE user_id = ?
                    """, (generate_password_hash(new_password), user_id))
                    conn.commit()

                    # Remove reset token
                    cursor.execute("DELETE FROM reset_tokens WHERE user_id = ?", (user_id,))
                    conn.commit()

                    conn.close()

                    # Clear session variables related to the reset process
                    session.pop('question_index', None)

                    flash("Password reset was successfully!", "success")
                    return redirect(url_for('auth_bp.login'))
            else:
                # Incorrect answer: increment question index
                question_index += 1
                session['question_index'] = question_index  # Update session
                cursor.execute("UPDATE user_auth SET question_index = ? WHERE user_id = ?", (question_index, user_id))
                conn.commit()

                if question_index < len(question_list):  # Check to avoid index out of range
                    flash("Incorrect answer. Please try the next question.", "error")
                    print("qI: ", question_index)
                    return redirect(url_for('auth_bp.reset_password_security_questions', token=token))

        # Render the security question form
        session['question_index'] = question_index  # Ensure question_index is in session
        print("qI3: ", question_index)
        cursor.execute("UPDATE user_auth SET question_index = ? WHERE user_id = ?", (question_index, user_id))
        conn.commit()  # Commit any updates to the question index
        conn.close()  # Ensure the connection is closed after all operations
        return render_template('reset-password-security-questions.html', question=current_question)

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('auth_bp.reset_password'))

@auth_bp.route("/confirm-elected-officers", methods=["GET", "POST"])
def confirm_elected_officers():

    # Insert test data (only for debugging)
    insert_debug_data()

        # Step 1: Get user_id from session and connect to the database
    user_id = session.get("user_id")  # Retrieve user_id from the session
    if not user_id:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for("auth_bp.login"))

    # Establish a database connection
    conn = get_db_connection()

    # Step 2: Retrieve users who have requested verification (value == 1)
    query = """
        SELECT u.user_id, u.first_name, u.last_name, s.school_name,
               v.lokalombud, v.skyddsombud, v.forhandlingsombud, v.huvudskyddsombud, v.styrelseledamot
        FROM users u
        JOIN schools s ON u.school_id = s.school_id  -- Corrected JOIN to retrieve school_name
        JOIN verify_officer v ON u.user_id = v.user_id
        WHERE v.lokalombud = 1 OR v.skyddsombud = 1 OR v.forhandlingsombud = 1 OR v.huvudskyddsombud = 1 OR v.styrelseledamot = 1
        ORDER BY s.school_name ASC, u.last_name ASC, u.first_name ASC
    """

    # Execute the query and fetch all rows
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()  # Close the database connection
    

    # Create a DataFrame from the rows
    import pandas as pd
    df_verify = pd.DataFrame(rows, columns=[
        "user_id", "first_name", "last_name", "school_name", 
        "lokalombud", "skyddsombud", "forhandlingsombud", "huvudskyddsombud", "styrelseledamot"
    ])

    session['df_verify'] = df_verify.to_json()

    # Convert DataFrame to a list of dictionaries for rendering in HTML
    officers_list = df_verify.to_dict(orient="records")

    # Return a valid response by rendering the template
    return render_template("confirm-elected-officers.html", officers=officers_list)


import datetime
import random

def insert_debug_data():
    """Inserts test data into users and verify_officer tables for debugging purposes."""
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    try:
        # Generate current timestamp
        current_time = datetime.datetime.now()

        # Insert 20 test users with school_id ranging from 1 to 48
        users_data = [
            (2, 'John', 'Doe', 1, 1, current_time, current_time),
            (3, 'Jane', 'Smith', 5, 1, current_time, current_time),
            (4, 'Alice', 'Johnson', 10, 1, current_time, current_time),
            (5, 'Bob', 'Williams', 15, 1, current_time, current_time),
            (6, 'Charlie', 'Brown', 20, 1, current_time, current_time),
            (7, 'David', 'Taylor', 25, 1, current_time, current_time),
            (8, 'Emma', 'White', 30, 1, current_time, current_time),
            (9, 'Frank', 'Harris', 35, 1, current_time, current_time),
            (10, 'Grace', 'Martin', 40, 1, current_time, current_time),
            (11, 'Henry', 'Thompson', 45, 1, current_time, current_time),
            (12, 'Ivy', 'Garcia', 3, 1, current_time, current_time),
            (13, 'Jack', 'Martinez', 8, 1, current_time, current_time),
            (14, 'Katie', 'Lopez', 12, 1, current_time, current_time),
            (15, 'Leo', 'Gonzalez', 18, 1, current_time, current_time),
            (16, 'Mia', 'Clark', 22, 1, current_time, current_time),
            (17, 'Nathan', 'Lewis', 28, 1, current_time, current_time),
            (18, 'Olivia', 'Walker', 33, 1, current_time, current_time),
            (19, 'Paul', 'Hall', 38, 1, current_time, current_time),
            (20, 'Quinn', 'Allen', 42, 1, current_time, current_time),
            (21, 'Rachel', 'Young', 48, 1, current_time, current_time),

            # Additional 10 users with 0 in all officer roles
            (22, 'Steve', 'Adams', 6, 1, current_time, current_time),
            (23, 'Hannah', 'Baker', 11, 1, current_time, current_time),
            (24, 'Lucas', 'Carter', 16, 1, current_time, current_time),
            (25, 'Sophia', 'Davis', 21, 1, current_time, current_time),
            (26, 'Ryan', 'Evans', 26, 1, current_time, current_time),
            (27, 'Zoe', 'Foster', 31, 1, current_time, current_time),
            (28, 'Tyler', 'Gibson', 36, 1, current_time, current_time),
            (29, 'Amelia', 'Henderson', 41, 1, current_time, current_time),
            (30, 'Ethan', 'Jackson', 46, 1, current_time, current_time),
            (31, 'Lily', 'King', 47, 1, current_time, current_time),
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO users (user_id, first_name, last_name, school_id, consent, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, users_data)


        # Insert verification requests for officer roles (20 with officer roles, 10 with all zeros)
        officer_data = [
            (2, 1, 0, 0, 0, 1, 0),
            (3, 0, 1, 1, 0, 0, 0),
            (4, 1, 1, 0, 0, 0, 0),
            (5, 0, 0, 1, 1, 0, 0),
            (6, 1, 0, 0, 1, 0, 0),
            (7, 0, 1, 1, 0, 0, 0),
            (8, 0, 0, 0, 1, 1, 0),
            (9, 1, 1, 0, 0, 0, 0),
            (10, 0, 0, 1, 1, 1, 0),
            (11, 1, 0, 0, 0, 0, 0),
            (12, 0, 1, 0, 1, 0, 0),
            (13, 0, 0, 1, 1, 0, 0),
            (14, 1, 1, 1, 0, 0, 0),
            (15, 0, 0, 0, 1, 1, 0),
            (16, 1, 0, 1, 0, 0, 0),
            (17, 0, 1, 0, 1, 1, 0),
            (18, 1, 1, 1, 0, 0, 0),
            (19, 0, 0, 1, 1, 0, 0),
            (20, 1, 0, 0, 1, 1, 0),
            (21, 0, 1, 1, 0, 0, 0),

            # Additional 10 users with 0 in all officer roles
            (22, 0, 0, 0, 0, 0, 0),
            (23, 0, 0, 0, 0, 0, 0),
            (24, 0, 0, 0, 0, 0, 0),
            (25, 0, 0, 0, 0, 0, 0),
            (26, 0, 0, 0, 0, 0, 0),
            (27, 0, 0, 0, 0, 0, 0),
            (28, 0, 0, 0, 0, 0, 0),
            (29, 0, 0, 0, 0, 0, 0),
            (30, 0, 0, 0, 0, 0, 0),
            (31, 0, 0, 0, 0, 0, 0),
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO verify_officer (user_id, lokalombud, skyddsombud, forhandlingsombud, huvudskyddsombud, styrelseledamot, verified) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, officer_data)

        conn.commit()
        print("Debug data inserted successfully.")

    except Exception as e:
        print(f"Error inserting debug data: {e}")

    finally:
        conn.close()

