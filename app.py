import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-change-later"

DATABASE = "task_manager.db"

def get_db():
    conn = sqlite3.connect(DATABASE) #connection establish
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    conn.commit()
    conn.close()

init_db()

@app.route("/") #always - default routing - login success page of home
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", email=session["user_email"])



@app.route("/register", methods=["GET", "POST"]) #get - view, #post- create
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm = request.form["confirm"]
        if "@" not in email:
            flash("Please enter a valid email address.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        elif password != confirm:
            flash("Passwords do not match.")
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                flash("That email is already registered. Try logging in.")
                conn.close()
                return render_template("register.html")
            conn.close()
            flash("Account created. Now log in.")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone() #columns all
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            return redirect(url_for("home"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear() #cookies removed
    flash("Logged out.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
