
#########
@auth_bp.route("/confirm-elected-officers", methods=["GET", "POST"])
def confirm_elected_officers():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Handle Form Submission (POST Request)
    if request.method == "POST":
        try:
            # Allow `user_id == 1` to verify others without restrictions
            user_id = session.get("user_id")  # Assuming `session` contains the logged-in user's ID
            if user_id != 2:
                flash("You do not have permission to verify officers.", "error")
                return redirect(url_for("auth_bp.confirm_elected_officers"))

            for field_name, value in request.form.items():
                if value == "on":  # Checkbox checked
                    target_user_id = field_name.split("_")[1]  # Extract user_id (e.g., lokalombud_5 -> 5)
                    role_column = field_name.split("_")[0]  # Extract role name (e.g., lokalombud_5 -> lokalombud)

                    # Ensure only requested roles (value == 1) are updated
                    cursor.execute(
                        f"UPDATE verify_officer SET {role_column} = 2 WHERE user_id = ? AND {role_column} = 1",
                        (target_user_id,)
                    )

            conn.commit()  # Commit changes to the database
            flash("Officer verification updated successfully.", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
        finally:
            conn.close()
        return redirect(url_for("auth_bp.confirm_elected_officers"))

    # Step 2: Retrieve Users Who Requested Clearance (value == 1)
    try:
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.last_name, m.school_name,
                   v.lokalombud, v.skyddsombud, v.forhandlingsombud, v.huvudskyddsombud, v.styrelseledamot
            FROM users u
            JOIN meta1 m ON u.user_id = m.user_id
            JOIN verify_officer v ON u.user_id = v.user_id
            WHERE v.lokalombud = 1 OR v.skyddsombud = 1 OR v.forhandlingsombud = 1 OR v.huvudskyddsombud = 1 OR v.styrelseledamot = 1
        """)
        officers = cursor.fetchall()  # Fetch results
    except Exception as e:
        officers = []  # Default to empty if an error occurs
        flash(f"An error occurred while retrieving officer data: {str(e)}", "error")
    finally:
        conn.close()

    # Step 3: Render the Template
    return render_template("confirm-elected-officers.html", officers=officers)

