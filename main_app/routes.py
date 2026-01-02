from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from email.message import EmailMessage
import smtplib
import sqlite3
import os

main_bp = Blueprint("main", __name__, template_folder="templates")

DB_NAME = os.path.join(os.getcwd(), "users.db")

# ---------- EMAIL ----------
EMAIL = "dhanparkashdhiman7@gmail.com"
PASSWORD = "tynx ilex vlso brxf"  # move to env later

def send_contact_email(name, email, message):
    msg = EmailMessage()
    msg["Subject"] = "New Contact Form Message"
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg.set_content(
        f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

# ---------- DB ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- HOME ----------
@main_bp.route("/")
def home():
    return render_template("home.html")

# Blog list page
@main_bp.route("/blog")
def blog():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("blog.html", posts=posts)

# Blog detail page
@main_bp.route("/blog/<slug>")
def blog_detail(slug):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE slug=?", (slug,)).fetchone()
    conn.close()

    if not post:
        abort(404)

    return render_template("blog_detail.html", post=post)

# ---------- PAGES (CMS) ----------
@main_bp.route("/<slug>")
def page(slug):
    conn = get_db()
    page = conn.execute("SELECT * FROM pages WHERE slug=?", (slug,)).fetchone()
    conn.close()

    if not page:
        abort(404)

    return render_template("page.html", page=page)


# ---------- CONTACT ----------
@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("All fields are required", "danger")
            return redirect(url_for("main.contact"))

        send_contact_email(name, email, message)
        flash("Message sent successfully!", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html")


# ---------- About Us ----------
@main_bp.route("/about")
def about():
    return render_template("about.html")
