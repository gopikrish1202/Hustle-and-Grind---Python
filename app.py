import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-change-later"

DATABASE = "task_manager.db"

def get_db():
    conn = sqlite3.connect(DATABASE) #connection establish
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

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
    # conn.execute("""
    # CREATE TABLE IF NOT EXISTS notes (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     user_id INTEGER NOT NULL,
    #     note TEXT NOT NULL,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    # )
    # """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priority TEXT NOT NULL DEFAULT 'Medium',
        is_done INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)


    conn.commit()
    conn.close()

init_db()

def require_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


def get_task(conn, task_id):
    return conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"]),
    ).fetchone()


# @app.route("/", methods=["GET", "POST"])
# def home():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     conn = get_db()

#     if request.method == "POST":
#         note = request.form["note"].strip()
#         if not note:
#             flash("Note cannot be empty.")
#         else:
#             conn.execute(
#                 "INSERT INTO notes (user_id, note) VALUES (?, ?)",
#                 (session["user_id"], note),
#             )
#             conn.commit()
#             conn.close()
#             flash("Note saved.")
#             return redirect(url_for("home"))

#     notes = conn.execute(
#         "SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC",
#         (session["user_id"],),
#     ).fetchall()
#     conn.close()
#     return render_template("home.html", email=session["user_email"], notes=notes)



@app.route("/")
def list_tasks():
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    from datetime import date

    task_filter = request.args.get("filter", "all")
    conn = get_db()
    if task_filter == "pending":
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND is_done = 0 ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
    elif task_filter == "done":
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND is_done = 1 ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
    elif task_filter == "overdue":
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND is_done = 0 "
            "AND due_date IS NOT NULL AND due_date != '' AND due_date < ? "
            "ORDER BY due_date ASC",
            (session["user_id"], date.today().isoformat()),
        ).fetchall()
    else:
        task_filter = "all"
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
    conn.close()
    return render_template("tasks.html", tasks=tasks, task_filter=task_filter)

@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    conn = get_db()
    task = get_task(conn, task_id)   # <-- get_task invoked here
    if task is None:
        conn.close()
        flash("Task not found.")
        return redirect(url_for("list_tasks"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        due_date = request.form["due_date"].strip() or None
        priority = request.form["priority"]
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        if not title:
            flash("Title is required.")
            conn.close()
            return render_template(
                "task_form.html", task=task, form_action=url_for("edit_task", task_id=task_id)
            )
        conn.execute(
            "UPDATE tasks SET title = ?, description = ?, due_date = ?, priority = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (title, description, due_date, priority, task_id, session["user_id"]),
        )
        conn.commit()
        conn.close()
        flash("Task updated.")
        return redirect(url_for("list_tasks"))

    conn.close()
    return render_template(
        "task_form.html", task=task, form_action=url_for("edit_task", task_id=task_id)
    )


@app.route("/tasks/new", methods=["GET", "POST"])
def new_task():
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        due_date = request.form["due_date"].strip() or None
        priority = request.form["priority"]
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        if not title:
            flash("Title is required.")
            return render_template("task_form.html", task=None, form_action=url_for("new_task"))

        conn = get_db()
        conn.execute(
            "INSERT INTO tasks (user_id, title, description, due_date, priority) "
            "VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], title, description, due_date, priority),
        )
        conn.commit()
        conn.close()
        flash("Task created.")
        return redirect(url_for("list_tasks"))

    return render_template("task_form.html", task=None, form_action=url_for("new_task"))


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
            return redirect(url_for("list_tasks"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear() #cookies removed
    flash("Logged out.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
