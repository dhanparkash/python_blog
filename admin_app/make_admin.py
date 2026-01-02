import sqlite3

conn = sqlite3.connect("users.db")
conn.execute("UPDATE users SET role='admin' WHERE email='yash@gmail.com'")
conn.commit()
conn.close()

print("You are now admin")