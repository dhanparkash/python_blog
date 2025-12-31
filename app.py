import os
import sqlite3
from admin.routes import admin_bp, create_admin
from main_app.routes import main_bp

from flask import Flask

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Create DB if not exists
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin", "users.db")
if not os.path.exists(DB_NAME):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.commit()
    conn.close()

# Ensure admin exists
create_admin()

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)
