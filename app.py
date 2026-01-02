import os
from flask import Flask
from admin_app.routes import admin_bp, init_db, create_admin
from main_app.routes import main_bp
# ---------- CREATE APP ----------
app = Flask(
    __name__,
    static_folder="main_app/static",
    template_folder="main_app/templates"
)

# ---------- SECRET KEY ----------
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)

# Init DB
init_db()

if __name__ == "__main__":
    app.run(debug=True)
