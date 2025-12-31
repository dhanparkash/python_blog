from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Blueprint
admin_bp = Blueprint("admin", __name__, template_folder="templates")

# DB path
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure admin exists
def create_admin():
    conn = get_db()
    admin = conn.execute("SELECT * FROM users WHERE role='admin'").fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            ("Admin","yash@gmail.com",generate_password_hash("admin123"),"admin")
        )
        conn.commit()
    conn.close()

def is_admin():
    if "user_id" not in session:
        return False
    conn = get_db()
    user = conn.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return user and user["role"] == "admin"

# ------------------ ROUTES ------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            flash("Login successful!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password", "danger")
    return render_template("login.html")


@admin_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
    return render_template("dashboard.html", 
                           name=session["user_name"], 
                           email=session["user_email"], 
                           role=session["user_role"])


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/users")
def users():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("users.html", users=users)


@admin_bp.route("/edit-user/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    if not user:
        conn.close()
        flash("User not found", "danger")
        return redirect(url_for("admin.users"))
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        conn.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, id))
        conn.commit()
        conn.close()
        flash("User updated successfully", "success")
        return redirect(url_for("admin.users"))
    conn.close()
    return render_template("edit_user.html", user=user)


@admin_bp.route("/delete-user/<int:id>")
def delete_user(id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))
    if id == session["user_id"]:
        flash("You cannot delete your own account", "warning")
        return redirect(url_for("admin.users"))
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
    if request.method == "POST":
        current = request.form["current"]
        new = request.form["new"]
        conn = get_db()
        user = conn.execute("SELECT password FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user or not check_password_hash(user["password"], current):
            flash("Current password incorrect", "danger")
            return redirect(url_for("admin.change_password"))
        hashed = generate_password_hash(new)
        conn.execute("UPDATE users SET password=? WHERE id=?", (hashed, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Password updated successfully", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("change_password.html")
