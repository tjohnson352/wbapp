from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from blueprints.authentication import get_random_security_questions

account_bp = Blueprint('account_bp', __name__)

import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    
    # Query already retrieves the correct school_name without needing school_id
    cursor.execute("""
        SELECT 
            u.user_id, 
            u.first_name, 
            u.last_name, 
            auth.login_id,
            s.school_name,                -- Automatically determined by JOIN
            u.consent, 
            u.created_at, 
            u.updated_at, 
            sl.sl_member, 
            sl.lokalombud, 
            sl.skyddsombud, 
            sl.forhandlingsombud, 
            sl.huvudskyddsombud, 
            sl.styrelseledamot,
            m.middle_manager, 
            m2.work_percent,
            auth.security_question_1, 
            auth.security_answer_1, 
            auth.security_question_2, 
            auth.security_answer_2, 
            auth.security_question_3, 
            auth.security_answer_3
        FROM users u
        LEFT JOIN user_auth auth ON u.user_id = auth.user_id
        LEFT JOIN schools s ON u.school_id = s.school_id
        LEFT JOIN sl_member_level sl ON u.user_id = sl.user_id
        LEFT JOIN meta1 m ON u.user_id = m.user_id
        LEFT JOIN meta2 m2 ON u.user_id = m2.user_id
        WHERE u.user_id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    conn.close()

    # If no user found, return None
    if not user:
        return None

    # Build user info with auto-determined school_name
    user_data = {
        "user_id":             user[0],
        "first_name":          user[1],
        "last_name":           user[2],
        "login_id":            user[3],
        "school_name":         user[4],   # Automatically fetched
        "consent":             user[5],
        "created_at":          user[6],
        "updated_at":          user[7],
        "sl_member":           user[8],
        "lokalombud":          user[9],
        "skyddsombud":         user[10],
        "forhandlingsombud":   user[11],
        "huvudskyddsombud":    user[12],
        "styrelseledamot":     user[13],
        "middle_manager":      user[14],
        "work_percent":        user[15],
        "security_question_1": user[16],
        "security_answer_1":   user[17],
        "security_question_2": user[18],
        "security_answer_2":   user[19],
        "security_question_3": user[20],
        "security_answer_3":   user[21],
    }
    
    return user_data






# **1. View My Account Page**
@account_bp.route('/account', methods=['GET'])
def view_account():
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for("auth_bp.login"))

    user = get_user(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth_bp.login"))

    # Fetch new security questions for dropdown selection
    security_questions = get_random_security_questions()

    # Fetch stored security answers
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT security_answer_1, security_answer_2, security_answer_3 
        FROM user_auth WHERE user_id = ?
    """, (user_id,))
    security_answers = cursor.fetchone()
    conn.close()

    # Include answers if they exist
    user["security_answer_1"] = security_answers[0] if security_answers else ""
    user["security_answer_2"] = security_answers[1] if security_answers else ""
    user["security_answer_3"] = security_answers[2] if security_answers else ""

    return render_template("view_my_account.html", user=user, security_questions=security_questions)

# **2. Update Email**
@account_bp.route('/update_email', methods=['POST'])
def update_email():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    new_email = request.form.get("new_email").strip()
    if not new_email:
        return jsonify({"error": "Email cannot be empty"}), 400

    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT user_id FROM users WHERE login_id = ?", (new_email,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return jsonify({"error": "Email already in use"}), 400

    # Update email
    cursor.execute("UPDATE users SET login_id = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_email, user_id))
    conn.commit()
    conn.close()
    
    flash("Email updated successfully!", "success")
    return redirect(url_for('account_bp.view_account'))


# **3. Change Password**
@account_bp.route('/update_password', methods=['POST'])
def update_password():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    current_password = request.form.get("current_password").strip()
    new_password = request.form.get("new_password").strip()

    if not current_password or not new_password:
        return jsonify({"error": "Both fields are required"}), 400

    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Fetch the stored password hash
    cursor.execute("SELECT password_hash FROM user_auth WHERE user_id = ?", (user_id,))
    user_auth = cursor.fetchone()
    if not user_auth:
        conn.close()
        return jsonify({"error": "User authentication data not found"}), 400

    stored_password_hash = user_auth[0]
    if not check_password_hash(stored_password_hash, current_password):
        conn.close()
        return jsonify({"error": "Current password is incorrect"}), 400

    # Update password
    new_password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE user_auth SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", 
                   (new_password_hash, user_id))
    conn.commit()
    conn.close()

    flash("Password updated successfully!", "success")
    return redirect(url_for('account_bp.view_account'))


# **4. Update Security Questions**
@account_bp.route('/update_security_questions', methods=['POST'])
def update_security_questions():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    security_questions = get_random_security_questions()

    security_question_1 = request.form.get("security_question_1").strip()
    security_answer_1 = request.form.get("security_answer_1").strip()
    security_question_2 = request.form.get("security_question_2").strip()
    security_answer_2 = request.form.get("security_answer_2").strip()
    security_question_3 = request.form.get("security_question_3").strip()
    security_answer_3 = request.form.get("security_answer_3").strip()

    if not all([security_question_1, security_answer_1, security_question_2, security_answer_2, security_question_3, security_answer_3]):
        return jsonify({"error": "All fields are required"}), 400

    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE user_auth 
        SET security_question_1 = ?, security_answer_1 = ?, 
            security_question_2 = ?, security_answer_2 = ?, 
            security_question_3 = ?, security_answer_3 = ?, 
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?""",
        (security_question_1, security_answer_1, security_question_2, security_answer_2, security_question_3, security_answer_3, user_id))
    
    conn.commit()
    conn.close()

    flash("Security questions updated successfully!", "success")
    return redirect(url_for('account_bp.view_account'))