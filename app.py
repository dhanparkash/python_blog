from flask import Flask, request, render_template_string
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# HTML form
form_html = '''
<h2>Student Grade Form</h2>
<form method="post">
  Name: <input type="text" name="name" required><br><br>
  Email: <input type="email" name="email" required><br><br>
  Marks: <input type="number" name="marks" required><br><br>
  <input type="submit">
</form>
'''

# Email credentials
EMAIL = "yash.dhiman@girlpowertalk.com"
PASSWORD = "pqgd rmbr bjjd fkqt"  # Gmail App Password

def send_email(name, email, marks, grade):
    msg = EmailMessage()
    msg["Subject"] = "Student Grade Result"
    msg["From"] = EMAIL
    msg["To"] = email
    msg.set_content(f"""
Student Name: {name}
Student Email: {email}
Marks: {marks}
Grade: {grade}
""")

    # Send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

@app.route("/", methods=["GET", "POST"])
def grade_form():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        marks = int(request.form["marks"])

        # Grade logic
        if marks >= 90:
            grade = "A"
        elif marks >= 80:
            grade = "B"
        elif marks >= 70:
            grade = "C"
        elif marks >= 50:
            grade = "D"
        else:
            grade = "F"

        send_email(name, email ,marks, grade)

        return "<h3>Email sent successfully!</h3>"

    return render_template_string(form_html)

if __name__ == "__main__":
    app.run(debug=True)
