from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Blueprint
admin_bp = Blueprint("admin", __name__, template_folder="templates")

# DB path
DB_NAME = os.path.join(os.getcwd(), "users.db")

# ------------------ DATABASE ------------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

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

    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_admins = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='admin'"
    ).fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        email=session["user_email"],
        role=session["user_role"],
        total_users=total_users,
        total_admins=total_admins
    )


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
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()

    if not user:
        conn.close()
        flash("User not found", "danger")
        return redirect(url_for("admin.users"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form.get("password")  # optional
        role = request.form["role"]

        if password:
            hashed = generate_password_hash(password)
            conn.execute(
                "UPDATE users SET name=?, email=?, password=?, role=? WHERE id=?",
                (name, email, hashed, role, id)
            )
        else:
            conn.execute(
                "UPDATE users SET name=?, email=?, role=? WHERE id=?",
                (name, email, role, id)
            )

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


@admin_bp.route("/add-user", methods=["GET", "POST"])
def add_user():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, password, role)
            )
            conn.commit()
            flash("User added successfully", "success")
            return redirect(url_for("admin.users"))
        except sqlite3.IntegrityError:
            flash("Email already exists", "danger")
        finally:
            conn.close()

    return render_template("add_user.html")


@admin_bp.route("/page")
def page():
    return render_template("pages.html")

@admin_bp.route("/add-page", methods=["GET", "POST"])
def add_page():
    if not is_admin():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        flash("Page created (demo)", "success")
        return redirect(url_for("admin.pages"))

    return render_template("add_page.html")
