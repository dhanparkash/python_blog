from flask import Flask, render_template, abort
from datetime import datetime

app = Flask(__name__)

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
    return render_template("post.html", post=post,  title=post["title"])

@app.route("/about")
def about():
     return render_template("about.html", title="About")

@app.route("/contact")
def contact():
     return render_template("contact.html", title="Contact")

if __name__ == "__main__":
    app.run(debug=True)
