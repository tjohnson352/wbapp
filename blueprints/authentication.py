# auth.py
import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from helpers.auth_functions import get_db_connection
from helpers.database_functions import setup_database, view_database, setup_school_table
import secrets
import sqlite3
from datetime import timedelta
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

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')

        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access for rows
        cursor = conn.cursor()

        # Fetch user details from the database
        cursor.execute("SELECT * FROM user_auth WHERE login_id = ?", (email,))
        user = cursor.fetchone()

        if user is None:
            flash("Email not found. Try again or register an account.", "error")
            conn.close()
            return redirect(url_for('auth_bp.login'))

        # Check if the user_id exists in the database
        cursor.execute("SELECT user_id FROM user_auth WHERE user_id = ?", (user['user_id'],))
        result = cursor.fetchone()

        if not result:
            flash("Account not found. Check 'Email Address' or 'Register' an account.", "error")
            conn.close()
            return redirect(url_for('auth_bp.login'))

        login_attempts = user['login_attempts']
        stored_password_hash = user['password_hash']
        temp_password_hash = user['temp_password']  # Read temp_password from the database

        # Decide which password hash to use for authentication
        if temp_password_hash:  # Temporary password exists
            password_hash_to_use = temp_password_hash
            print("[INFO] Using temporary password for authentication.")
        else:  # Use stored password
            password_hash_to_use = stored_password_hash
            print("[INFO] Using stored password for authentication.")

        # Check if the account is locked
        if login_attempts >= 3:
            flash("Your account is locked. Please reset your password to regain access.", "error")
            conn.close()
            return redirect(url_for('auth_bp.reset_password'))  # Redirect to reset-password page

        # Authenticate the user
        if check_password_hash(password_hash_to_use, password):
            flash("Login successful!", "success")
            print("Login successful!")

            # Reset login attempts and clear temp_password if it was used
            cursor.execute("UPDATE user_auth SET login_attempts = 0, temp_password = NULL WHERE user_id = ?", (user['user_id'],))
            conn.commit()

            # Save user session and redirect to the dashboard
            session['user_id'] = user['user_id']
            session.permanent = True  # Enable session timeout
            conn.close()
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
                flash("Your account is locked. Please reset your password to regain access.", "error")
                conn.close()
                return redirect(url_for('auth_bp.reset_password'))  # Redirect to reset-password page

            conn.close()
            return redirect(url_for('auth_bp.login'))

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

    # Fetch the school names from the database
    schools = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT school_name FROM schools")
        schools = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        flash("An error occurred while retrieving the school list. Please try again later.", "error")

    # Fetch random security questions
    security_questions = get_random_security_questions()
    
    if request.method == 'POST':
        # Safely retrieve form inputs with default values
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Privacy consent
        privacy_consent = request.form.get('privacy_consent', None)

        # Check if privacy consent was provided
        if not privacy_consent:
            flash("You must agree to the Privacy Policy to create an account.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)
        
        # Security questions and answers
        question1 = request.form.get('security_question_1', '').strip()
        answer1 = request.form.get('security_answer_1', '').strip()
        question2 = request.form.get('security_question_2', '').strip()
        answer2 = request.form.get('security_answer_2', '').strip()
        question3 = request.form.get('security_question_3', '').strip()
        answer3 = request.form.get('security_answer_3', '').strip()

        # Sveriges Lärare Membership & Roles
        sl_member = 0  # Default value for Sveriges Lärare membership
        lokalombud = 0  # Default value for Lokalombud
        skyddsombud = 0  # Default value for Skyddsombud
        forhandlingsombud = 0  # Default value for Förhandlingsombud
        huvudskyddsombud = 0  # Default value for Huvudskyddsombud
        styrelseledamot = 0  # Default value for Styrelseledamot

        # Update variables based on form inputs
        if request.form.get('sl_member', '0') == '1':  
            sl_member = 1

        selected_roles = request.form.getlist('sl_roles')

        if 'Lokalombud' in selected_roles:
            lokalombud = 1
        if 'Skyddsombud' in selected_roles:
            skyddsombud = 1
        if 'Förhandlingsombud' in selected_roles:
            forhandlingsombud = 1
        if 'Huvudskyddsombud' in selected_roles:
            huvudskyddsombud = 1
        if 'Styrelseledamot' in selected_roles:
            styrelseledamot = 1

        # Validate required fields
        if not all([first_name, last_name, email, school, password, confirm_password, question1, answer1, question2, answer2, question3, answer3]):
            flash("Please complete all fields.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Password validation
        password_regex = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$')
        if not password_regex.match(password):
            flash("Password must be at least 6 characters long, with letters, numbers, and a special character.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)

        # Save user data to the database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT user_id FROM users WHERE login_id = ?", (email,))
            if cursor.fetchone():
                flash(f"An account for {email} exists. Click 'Reset' if you forgot the password.", "error")
                return render_template('login.html', schools=schools, form_data=request.form)

            # Insert into `users` table with privacy_consent
            cursor.execute("""
                INSERT INTO users (first_name, last_name, login_id, school_id, consent)
                VALUES (?, ?, ?, (SELECT school_id FROM schools WHERE school_name = ?), ?)
            """, (first_name, last_name, email, school, privacy_consent == 'on'))

            user_id = cursor.lastrowid  # Get the generated user_id

            # Insert into `sl_member_level` table
            cursor.execute("""
                INSERT INTO sl_member_level (user_id, sl_member, lokalombud, skyddsombud, 
                                            forhandlingsombud, huvudskyddsombud, styrelseledamot)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, sl_member, lokalombud, skyddsombud, forhandlingsombud, huvudskyddsombud, styrelseledamot))


            # Insert into `user_auth` table
            cursor.execute("""
                INSERT INTO user_auth (user_id, login_id, password_hash, security_question_1, security_answer_1, 
                                       security_question_2, security_answer_2, security_question_3, security_answer_3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email, generate_password_hash(password),
                question1, generate_password_hash(answer1),
                question2, generate_password_hash(answer2),
                question3, generate_password_hash(answer3),
            ))

            conn.commit()
            conn.close()

            # Store user_id in session
            session['user_id'] = user_id

            flash("Account created! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash("An error occurred during registration. Please try again later.", "error")

    return render_template('register.html', schools=schools, security_questions=security_questions, form_data=request.form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection() 
        cursor = conn.cursor()

        try: 
            cursor.execute("SELECT user_id FROM users WHERE login_id = ?", (email,))
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

                    flash("Password reset successful! You can now log in with your new password.", "success")
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

