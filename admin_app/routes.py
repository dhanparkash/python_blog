from flask import Blueprint, request, redirect, url_for, flash, render_template, session, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

# ------------------ CONFIGURATION ------------------

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
    static_folder="static",
    static_url_path="/admin/static"
)

DB_NAME = os.path.join(os.getcwd(), "users.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ DATABASE HELPERS ------------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # USERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    # PAGES TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # POSTS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            thumbnail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def create_admin():
    conn = get_db()
    # Check if this specific email exists
    admin = conn.execute("SELECT * FROM users WHERE email=?", ("yash@gmail.com",)).fetchone()
    
    hashed_pw = generate_password_hash("admin123")
    
    if not admin:
        # Create new if doesn't exist
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "yash@gmail.com", hashed_pw, "admin")
        )
        print("Admin user created: yash@gmail.com / admin123")
    else:
        # Update existing admin to ensure password is correct
        conn.execute(
            "UPDATE users SET password=?, role='admin' WHERE email=?",
            (hashed_pw, "yash@gmail.com")
        )
        print("Admin user password reset to admin123")
        
    conn.commit()
    conn.close()

def is_admin():
    if "user_id" not in session:
        return False
    conn = get_db()
    user = conn.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return user and user["role"] == "admin"

# ------------------ AUTH ROUTES ------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session.update({
                "user_id": user["id"],
                "user_name": user["name"],
                "user_email": user["email"],
                "user_role": user["role"]
            })
            flash("Login successful!", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("login.html")

@admin_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    conn = get_db()
    u_res = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
    a_res = conn.execute("SELECT COUNT(*) AS total FROM users WHERE role='admin'").fetchone()
    conn.close()

    return render_template(
        "dashboard.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("user_role"),
        total_users=u_res["total"] if u_res else 0,
        total_admins=a_res["total"] if a_res else 0
    )

@admin_bp.route("/logout")
def logout():
    # 1. Clear all session data
    session.clear()
    
    # 2. Explicitly remove the session cookie from the response
    response = redirect(url_for("admin.login"))
    response.set_cookie('session', '', expires=0) 
    
    flash("Logged out successfully", "info")
    return response


# ------------------ USER MANAGEMENT ------------------

@admin_bp.route("/users")
def users():
    conn = get_db()
    all_users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    # Remove "admin/" because the file is sitting directly in templates/
    return render_template("users.html", users=all_users)

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



# ------------------ BLOG POSTS ------------------

@admin_bp.route("/posts")
def admin_posts():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("posts.html", posts=posts)

@admin_bp.route("/add-post", methods=["GET", "POST"])
def add_post():
    if request.method == "POST":
        title, slug, content = request.form["title"], request.form["slug"], request.form["content"]
        thumbnail = None
        file = request.files.get("thumbnail")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            thumbnail = filename

        conn = get_db()
        conn.execute("INSERT INTO posts (title, slug, content, thumbnail) VALUES (?, ?, ?, ?)",
                    (title, slug, content, thumbnail))
        conn.commit()
        conn.close()
        flash("Post added", "success")
        return redirect(url_for("admin.admin_posts"))
    return render_template("add_post.html")

@admin_bp.route("/edit-post/<int:id>", methods=["GET", "POST"])
def edit_post(id):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone()

    if not post:
        conn.close()
        flash("Post not found", "danger")
        return redirect(url_for("admin.admin_posts"))

    if request.method == "POST":
        title = request.form.get("title")
        slug = request.form.get("slug")
        content = request.form.get("content")

        # Safely access existing thumbnail
        thumbnail = post["thumbnail"] if "thumbnail" in post.keys() else None
        
        file = request.files.get("thumbnail")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            thumbnail = filename

        conn.execute("""
            UPDATE posts
            SET title=?, slug=?, content=?, thumbnail=?
            WHERE id=?
        """, (title, slug, content, thumbnail, id))

        conn.commit()
        conn.close()
        flash("Post updated successfully", "success")
        return redirect(url_for("admin.admin_posts"))

    conn.close()
    return render_template("edit_post.html", post=post)

@admin_bp.route("/delete-post/<int:id>")
def delete_post(id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Post deleted", "success")
    return redirect(url_for("admin.admin_posts"))

# ------------------ PAGES MANAGEMENT ------------------

@admin_bp.route("/pages")
def pages_view():  
    """Endpoint: admin.pages_view"""
    conn = get_db()
    pages = conn.execute("SELECT * FROM pages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages.html", pages=pages)

@admin_bp.route("/add-page", methods=["GET", "POST"])
def add_page_view():
    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        content = request.form["content"].strip()
        
        # --- Handle Thumbnail ---
        thumbnail = None
        file = request.files.get("thumbnail")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            thumbnail = filename

        conn = get_db()
        try:
            conn.execute("INSERT INTO pages (title, slug, content, thumbnail) VALUES (?, ?, ?, ?)", 
                         (title, slug, content, thumbnail))
            conn.commit()
            flash("Page added with thumbnail", "success")
            return redirect(url_for("admin.pages_view"))
        except sqlite3.IntegrityError:
            flash("Slug exists", "danger")
        finally:
            conn.close()
    return render_template("add_page.html")

@admin_bp.route("/edit-page/<int:id>", methods=["GET", "POST"])
def edit_page_view(id):
    conn = get_db()
    page = conn.execute("SELECT * FROM pages WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        content = request.form["content"].strip()
        
        # Keep old thumbnail by default
        thumbnail = page["thumbnail"]

        # Check for new upload
        file = request.files.get("thumbnail")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            thumbnail = filename

        conn.execute("UPDATE pages SET title=?, slug=?, content=?, thumbnail=? WHERE id=?", 
                     (title, slug, content, thumbnail, id))
        conn.commit()
        conn.close()
        flash("Page updated", "success")
        return redirect(url_for("admin.pages_view"))
    
    conn.close()
    return render_template("edit_page.html", page=page)

@admin_bp.route("/delete-page/<int:id>")
def delete_page_view(id):
    """Endpoint: admin.delete_page_view"""
    conn = get_db()
    conn.execute("DELETE FROM pages WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Page deleted", "info")
    return redirect(url_for("admin.pages_view")) # FIXED: was admin.pages
