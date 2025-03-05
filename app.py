from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import csv
import datetime
import smtplib
import random
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management
def get_user_by_uid(uid):
    try:
        with open("users.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["UID"] == uid:
                    return {
                        "UID": row["UID"],
                        "Name": row["Name"],
                        "Email": row["Email"],
                        "Gender": row["Gender"],
                        "Phone": row["Phone"],
                        "Address": row["Address"],
                        "Date of Birth": row["Date of Birth"]
                    }
    except FileNotFoundError:
        return None
    return None

# Secure Email OTP Sending Function
def send_otp_email(email, otp):
    sender_email = "sambhavkaoffice@gmail.com"
    sender_password = "yahgwzatzgdsvqbw"  # Use your Google App Password
    subject = "Your OTP for Login"
    body = f"Your OTP is {otp}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("✅ OTP sent successfully!")
    except Exception as e:
        print("❌ Error sending OTP:", e)

# Route for home page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        otp = str(random.randint(100000, 999999))
        send_otp_email(email, otp)
        session["otp"] = otp
        return "✅ OTP sent to your email!"

    return render_template("login.html")

@app.route("/verify", methods=["POST"])
def verify():
    entered_otp = request.form.get("otp")

    if "otp" in session and session["otp"] == entered_otp:
        session["logged_in"] = True
        return jsonify({"success": "OTP Verified!", "redirect": url_for("index")})
    
    return jsonify({"error": "Invalid OTP!"}), 400

@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect("/")

# Function to get current gold price
def get_gold_price():
    return 6000  # Assume ₹6000 per gram for now

# Function to read investments from CSV
def read_investments():
    try:
        with open("investments.csv", "r") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []

# Function to write investments to CSV
def write_investments(data):
    with open("investments.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["user_id", "grams", "invested_amount", "date"])
        writer.writeheader()
        writer.writerows(data)

# Route for gold page
@app.route("/gold")
def gold():
    return render_template("gold.html")

@app.route("/profile")
def profile():
    if "logged_in" in session and session["logged_in"]:
        return render_template("profile.html")
    else:
        return redirect(url_for("login"))
    
# API endpoint for gold transactions
@app.route("/api", methods=["POST"])
def api():
    data = request.json
    action = data.get("action")
    user_id = data.get("user_id")

    # Get current gold price
    if action == "gold_price":
        return jsonify({"gold_price_per_gram": get_gold_price()})

    # Invest in gold
    elif action == "invest":
        investment_amount = float(data.get("investment_amount", 0))
        gold_price = get_gold_price()
        grams = investment_amount / gold_price
        investments = read_investments()

        investments.append({"user_id": user_id, "grams": grams, "invested_amount": investment_amount, "date": str(datetime.date.today())})
        write_investments(investments)

        return jsonify({"message": f"Invested ₹{investment_amount}. You now own {grams:.2f}g of gold."})

    # Check balance
    elif action == "balance":
        investments = read_investments()
        total_grams = sum(float(i["grams"]) for i in investments if i["user_id"] == user_id)
        return jsonify({"total_grams": total_grams, "message": f"You own {total_grams:.2f}g of gold."})

    # Withdraw investment
    elif action == "withdraw":
        investments = [i for i in read_investments() if i["user_id"] != user_id]
        write_investments(investments)
        return jsonify({"message": "Gold investment withdrawn successfully."})

    return jsonify({"error": "Invalid request"}), 400

if __name__ == "__main__":
    app.run(debug=True)
