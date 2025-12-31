from admin.routes import admin_bp, init_db, create_admin
from main_app.routes import main_bp
import os
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Initialize DB and Admin
init_db()
create_admin()

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")  # admin routes
app.register_blueprint(main_bp, url_prefix="")        # front-end

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
