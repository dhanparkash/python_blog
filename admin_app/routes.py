from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates"  # relative to admin_app/
)


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


# ---------- PAGES ----------

@admin_bp.route("/pages")
def pages():
    conn = get_db()
    pages = conn.execute("SELECT * FROM pages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages.html", pages=pages)


@admin_bp.route("/add-page", methods=["GET", "POST"])
def add_page():
    if request.method == "POST":
        title = request.form["title"]
        slug = request.form["slug"]
        content = request.form["content"]

        conn = get_db()
        conn.execute(
            "INSERT INTO pages (title, slug, content) VALUES (?,?,?)",
            (title, slug, content)
        )
        conn.commit()
        conn.close()
        flash("Page added successfully", "success")
        return redirect(url_for("admin.pages"))

    return render_template("add_page.html")


@admin_bp.route("/edit-page/<int:id>", methods=["GET", "POST"])
def edit_page(id):
    conn = get_db()
    page = conn.execute("SELECT * FROM pages WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        slug = request.form["slug"]
        content = request.form["content"]

        conn.execute(
            "UPDATE pages SET title=?, slug=?, content=? WHERE id=?",
            (title, slug, content, id)
        )
        conn.commit()
        conn.close()
        flash("Page updated", "success")
        return redirect(url_for("admin.pages"))

    conn.close()
    return render_template("edit_page.html", page=page)


@admin_bp.route("/delete-page/<int:id>")
def delete_page(id):
    conn = get_db()
    conn.execute("DELETE FROM pages WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Page deleted", "info")
    return redirect(url_for("admin.pages"))




# ---------- BLOG POSTS ----------

@admin_bp.route("/posts")
def admin_posts():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("posts.html", posts=posts)


@admin_bp.route("/add-post", methods=["GET", "POST"])
def add_post():
    # Only admins can add posts
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        content = request.form["content"].strip()

        if not title or not slug or not content:
            flash("All fields are required", "danger")
            return render_template("add_post.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO posts (title, slug, content) VALUES (?, ?, ?)",
                (title, slug, content)
            )
            conn.commit()
            flash("Post added successfully!", "success")
            return redirect(url_for("admin.admin_posts"))
        except sqlite3.IntegrityError:
            flash("Slug already exists. Use a unique slug.", "danger")
        finally:
            conn.close()

    return render_template("add_post.html")


@admin_bp.route("/edit-post/<int:id>", methods=["GET", "POST"])
def edit_post(id):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        slug = request.form["slug"]
        content = request.form["content"]

        conn.execute(
            "UPDATE posts SET title=?, slug=?, content=? WHERE id=?",
            (title, slug, content, id)
        )
        conn.commit()
        conn.close()
        flash("Post updated", "success")
        return redirect(url_for("admin.admin_posts"))

    conn.close()
    return render_template("edit_post.html", post=post)


@admin_bp.route("/delete-post/<int:id>")
def delete_post(id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Post deleted", "info")
    return redirect(url_for("admin.admin_posts"))


# BLOG LIST
@admin_bp.route("/blog")
def blog():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("blog.html", posts=posts)


# BLOG DETAIL
@admin_bp.route("/blog/<slug>")
def blog_detail(slug):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE slug=?", (slug,)).fetchone()
    conn.close()

    if not post:
        abort(404)

    return render_template("blog_detail.html", post=post)


# ---------- PAGES ----------

# List all pages
@admin_bp.route("/pages")
def pages_view():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    conn = get_db()
    pages = conn.execute("SELECT * FROM pages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages.html", pages=pages)


# Add new page
@admin_bp.route("/add-page", methods=["GET", "POST"])
def add_page_view():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        content = request.form["content"].strip()

        if not title or not slug or not content:
            flash("All fields are required", "danger")
            return render_template("add_page.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO pages (title, slug, content) VALUES (?, ?, ?)",
                (title, slug, content)
            )
            conn.commit()
            flash("Page added successfully!", "success")
            return redirect(url_for("admin.pages_view"))
        except sqlite3.IntegrityError:
            flash("Slug already exists. Use a unique slug.", "danger")
        finally:
            conn.close()

    return render_template("add_page.html")


# Edit page
@admin_bp.route("/edit-page/<int:id>", methods=["GET", "POST"])
def edit_page_view(id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    conn = get_db()
    page = conn.execute("SELECT * FROM pages WHERE id=?", (id,)).fetchone()

    if not page:
        conn.close()
        flash("Page not found", "danger")
        return redirect(url_for("admin.pages_view"))

    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        content = request.form["content"].strip()

        if not title or not slug or not content:
            flash("All fields are required", "danger")
            return render_template("edit_page.html", page=page)

        try:
            conn.execute(
                "UPDATE pages SET title=?, slug=?, content=? WHERE id=?",
                (title, slug, content, id)
            )
            conn.commit()
            flash("Page updated successfully!", "success")
            return redirect(url_for("admin.pages_view"))
        except sqlite3.IntegrityError:
            flash("Slug already exists. Use a unique slug.", "danger")
            return render_template("edit_page.html", page=page)
        finally:
            conn.close()

    conn.close()
    return render_template("edit_page.html", page=page)


# Delete page
@admin_bp.route("/delete-page/<int:id>")
def delete_page_view(id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("admin.dashboard"))

    conn = get_db()
    conn.execute("DELETE FROM pages WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Page deleted successfully!", "info")
    return redirect(url_for("admin.pages_view"))


def init_db():
    conn = sqlite3.connect(DB_NAME)

    # USERS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # PAGES
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # BLOG POSTS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
