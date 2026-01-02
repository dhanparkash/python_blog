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


UPLOAD_FOLDER = r"E:\pythonprojects\python_blog\static\images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- DATABASE ----------
init_db()
create_admin()


# ---------- BLUEPRINTS ----------
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)  # frontend

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
