from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "users.db"

# ------------------ DATABASE ------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.commit()
    conn.close()

import sqlite3
conn = sqlite3.connect("users.db")
print(conn.execute("PRAGMA table_info(users)").fetchall())
print(conn.execute("SELECT email, role FROM users").fetchall())
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
    user = conn.execute(
        "SELECT role FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    return user and user["role"] == "admin"


# ------------------ ROUTES ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]   # 🔥 IMPORTANT LINE

            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        email=session["user_email"],
        role=session["user_role"]
    )




@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))




@app.route("/users")
def users():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template("users.html", users=users)



@app.route("/edit-user/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()

    if not user:
        conn.close()
        flash("User not found", "danger")
        return redirect(url_for("users"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        conn.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (name, email, id)
        )
        conn.commit()
        conn.close()

        flash("User updated successfully", "success")
        return redirect(url_for("users"))

    conn.close()
    return render_template("edit_user.html", user=user)



@app.route("/delete-user/<int:id>")
def delete_user(id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    if id == session["user_id"]:
        flash("You cannot delete your own account", "warning")
        return redirect(url_for("users"))

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("User deleted successfully", "info")
    return redirect(url_for("users"))

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current = request.form["current"]
        new = request.form["new"]

        conn = get_db()
        user = conn.execute(
            "SELECT password FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if not check_password_hash(user["password"], current):
            flash("Current password incorrect", "danger")
            return redirect(url_for("change_password"))

        hashed = generate_password_hash(new)
        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hashed, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Password updated successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")


# ------------------ INIT ------------------
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
