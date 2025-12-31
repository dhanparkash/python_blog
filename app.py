from flask import Flask
from admin.routes import admin_bp, init_db, create_admin
from main_app.routes import main_bp
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Initialize DB and Admin
init_db()
create_admin()

# Register Blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp, url_prefix="")  # front-end

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
