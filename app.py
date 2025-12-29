from flask import Flask, render_template, abort
from datetime import datetime



# Fake blog data
posts = [
    {
        "id": 1,
        "title": "My First Blog Post",
        "content": "This is my first blog post using Flask."
    },
    {
        "id": 2,
        "title": "Learning Flask",
        "content": "Flask is simple and powerful for small projects."
    }
]

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/blog")
def blog():
    return render_template("blog.html", posts=posts)

@app.route("/blog/<int:post_id>")
def post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        abort(404)
    return render_template("post.html", post=post)

if __name__ == "__main__":
    app.run(debug=True)
