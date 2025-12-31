from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from email.message import EmailMessage
import smtplib

# THIS NAME MUST MATCH what you import in app.py
main_bp = Blueprint("main", __name__, template_folder="templates")

# =====================
# EMAIL CONFIG
# =====================
EMAIL = "dhanparkashdhiman7@gmail.com"
PASSWORD = "tynx ilex vlso brxf"  # Gmail App Password

def send_contact_email(name, email, message):
    msg = EmailMessage()
    msg["Subject"] = "New Contact Form Message"
    msg["From"] = EMAIL
    msg["To"] = "dhanparkashdhiman7@gmail.com"  # send to yourself

    msg.set_content(f"""
New contact form submission:

Name: {name}
Email: {email}

Message:
{message}
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)


# =====================
# BLOG DATA
# =====================

# Fake blog data
posts = [
    {
        "id": 1,
        "slug": "my-first-blog",
        "title": "My First Blog Post",
        "post_thumb": "images/finance.webp",
        "content": "Lorem Ipsum is simply dummy text of the printing and typesetting industry."
    },
    {
        "id": 2,
        "slug": "my-second-blog",
        "title": "My Second Blog Post",
                "post_thumb": "images/contact-us.jpg",
        "content": "This is my second blog post using Flask."
    },
    {
        "id": 3,
        "slug": "my-third-blog",
        "title": "My Third Blog Post",
                "post_thumb": "images/images.jpg",
        "content": "Lorem Ipsum is simply dummy text of the printing and typesetting industry."
    },
    {
        "id": 4,
        "slug": "my-forth-blog",
        "title": "Learning Flask",
                "post_thumb": "images/mobile.png",
        "content": "Flask is simple and powerful for small projects."
    }
]


# =====================
# ROUTES
# =====================
@app.route("/")
def home():
    return render_template("home.html", title="Home")

@app.route("/blog")
def blog():
    return render_template("blog.html", var_post=posts, title="Blog")

@app.route("/blog/<slug>")
def post(slug):
    post = next((p for p in posts if p["slug"] == slug), None)
    if not post:
        abort(404)
    return render_template("post.html", post=post, title=post["title"])

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("All fields are required", "danger")
            return redirect(url_for("contact"))

        send_contact_email(name, email, message)
        flash("Message sent successfully!", "success")

        return redirect(url_for("contact"))

    return render_template("contact.html", title="Contact Us")

if __name__ == "__main__":
    app.run(debug=True)
