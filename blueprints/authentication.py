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


auth_bp = Blueprint('auth_bp', __name__)

from datetime import timedelta
from flask import session, redirect, url_for, flash, render_template, request
from werkzeug.security import check_password_hash
import sqlite3
import random
import string

# Function to generate a new temporary password
def generate_temp_password(length=6):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Initialize database and ensure setup
    setup_database()
    setup_school_table()

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')

        # Connect to the database and fetch the user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_auth WHERE login_id = ?", (email,))
        user = cursor.fetchone()

        if user is None:
            # Email not found
            flash("The email address is not found. Please try again or register an account.", "error")
            conn.close()
            return redirect(url_for('auth_bp.login'))

        # Extract user details
        stored_password_hash = user['password_hash']
        temp_password_hash = user.get('temp_password')
        login_attempts = user['login_attempts']
        print(f"[DEBUG] Temporary password for user {email}: {temp_password_hash}")


        # Check if account is locked
        if login_attempts >= 3:
            print("login_attempts", login_attempts)
            # Regenerate and store a temporary password
            new_temp_password = generate_temp_password()
            print(f"[DEBUG] Generated temporary password: {new_temp_password}")

            cursor.execute(
                "UPDATE user_auth SET temp_password = ?, login_attempts = 3 WHERE user_id = ?",
                (generate_password_hash(new_temp_password), user['user_id'])
            )
            conn.commit()

            flash("Too many failed attempts. A new temporary password has been sent to your email.", "error")
            conn.close()
            return redirect(url_for('auth_bp.reset_password'))

        # Check if the entered password matches either the stored or temporary password
        if not (check_password_hash(stored_password_hash, password) or 
                (temp_password_hash and check_password_hash(temp_password_hash, password))):
            # Increment login attempts
            login_attempts += 1
            cursor.execute("UPDATE user_auth SET login_attempts = ? WHERE user_id = ?", 
                           (login_attempts, user['user_id']))
            conn.commit()

            remaining_attempts = 3 - login_attempts
            flash(f"Invalid email or password. {remaining_attempts} login attempts remaining.", "error")
            conn.close()
            return redirect(url_for('auth_bp.login'))

        # Successful login
        session['login_attempts'] = 0  # Reset session login attempts
        session['user_id'] = user['user_id']
        session.permanent = True  # Enable session timeout

        # Reset login attempts and clear the temporary password in the database
        cursor.execute("UPDATE user_auth SET login_attempts = 0, temp_password = NULL WHERE user_id = ?", 
                       (user['user_id'],))
        conn.commit()
        conn.close()

        flash("Login successful!", "success")
        return redirect(url_for('dashboard_bp.dashboard'))  # Redirect to the dashboard

    return render_template('login.html')




@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Ensure the database and tables are set up
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
        print(f"Error: {e}")

    if request.method == 'POST':
        # Safely retrieve form inputs with default values
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Security questions and answers
        question1 = request.form.get('security_question_1', '').strip()
        answer1 = request.form.get('security_answer_1', '').strip()
        question2 = request.form.get('security_question_2', '').strip()
        answer2 = request.form.get('security_answer_2', '').strip()
        question3 = request.form.get('security_question_3', '').strip()
        answer3 = request.form.get('security_answer_3', '').strip()

        # Validate required fields
        if not all([first_name, last_name, email, school, password, confirm_password, question1, answer1, question2, answer2, question3, answer3]):
            flash("All fields are required. Please fill in all the details.", "error")
            return render_template('register.html', schools=schools, form_data=request.form)

        # Ensure the selected school is valid
        if school not in schools:
            flash("Please select a valid school from the dropdown.", "error")
            return render_template('register.html', schools=schools, form_data=request.form)

        # Password validation
        password_regex = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$')
        if not password_regex.match(password):
            flash("Password must be at least 6 characters long, alphanumeric, and include at least one special character.", "error")
            return render_template('register.html', schools=schools, form_data=request.form)

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('register.html', schools=schools, form_data=request.form)

        temp_password = generate_temp_password()

        # Save user data to the database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT user_id FROM users WHERE login_id = ?", (email,))
            if cursor.fetchone():
                flash("An account with this email already exists. Please log in.", "error")
                return render_template('register.html', schools=schools, form_data=request.form)

            # Insert into `users` table
            cursor.execute("""
                INSERT INTO users (first_name, last_name, login_id, school_id, consent)
                VALUES (?, ?, ?, (SELECT school_id FROM schools WHERE school_name = ?), ?)
            """, (first_name, last_name, email, school, True))
            user_id = cursor.lastrowid  # Get the generated user_id

            # Insert into `user_auth` table
            cursor.execute("""
                INSERT INTO user_auth (user_id, login_id, password_hash, security_question_1, security_answer_1, 
                                       security_question_2, security_answer_2, security_question_3, security_answer_3, temp_password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email, generate_password_hash(password),
                question1, generate_password_hash(answer1),
                question2, generate_password_hash(answer2),
                question3, generate_password_hash(answer3),
                generate_password_hash(temp_password)
            ))

            conn.commit()
            conn.close()

            # Store user_id in session
            session['user_id'] = user_id

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash("An error occurred during registration. Please try again later.", "error")
            print(f"Error: {e}")

    # Render the form with any previously entered data if the page is reloaded
    return render_template('register.html', schools=schools, form_data=request.form)



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

                try:
                    cursor.execute("INSERT INTO reset_tokens (user_id, token) VALUES (?, ?)", (user['user_id'], token))
                    conn.commit()
                except sqlite3.IntegrityError:
                    cursor.execute("UPDATE reset_tokens SET token = ? WHERE user_id = ?", (token, user['user_id']))
                    conn.commit()

                return redirect(url_for('auth_bp.reset_password_security_questions', token=token))
            else:
                flash("Email not found.", "error")

        except sqlite3.Error as e: # Add error handling
            flash(f"A database error occurred: {e}", "error")
            conn.rollback() # Rollback in case of an error
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

