import os
from flask import Flask
from admin.routes import admin_bp, init_db, create_admin
from main_app.routes import main_bp

app = Flask(__name__)

# Secret key (Render-safe)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Initialize database and admin user
init_db()
create_admin()

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
