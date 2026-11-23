import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# Needed to sign the session cookie. In production (AWS) this will come
# from an environment variable, never from code.
app.secret_key = "dev-secret-change-later"

# --- MongoDB Atlas connection -------------------------------------------
# load_dotenv() reads the .env file in the project folder (dev only).
# .env holds MONGO_URI, the connection string from Atlas. It is in
# .gitignore, so it never goes to git. Never paste it in chat.
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set. Copy .env.example to .env and fill in "
        "your Atlas connection string."
    ) #error - manually throw

MONGO_DB = os.environ.get("MONGO_DB", "task_manager")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB]
users_col = db["users"] #column
tasks_col = db["tasks"]
notes_col = db["notes"]


def init_db():
    """Check the cluster is reachable and prepare the collections.

    MongoDB has no CREATE TABLE: a collection appears when the first
    document is inserted. The one thing we do create up front is a
    unique index on users.email, so the same email cannot register twice.
    """
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        raise RuntimeError(
            "Could not reach MongoDB Atlas. Check MONGO_URI in .env, "
            "and that your IP is whitelisted in Atlas -> Network Access."
        )
    users_col.create_index("email", unique=True)


init_db()


def now_ist_str():
    """Current time in IST as a string, e.g. '2026-11-20 21:45:17'.

    MongoDB stores real datetimes as UTC, so we store IST as text
    instead, so Atlas shows the IST time directly.
    """
    return datetime.now(timezone.utc).astimezone(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d %H:%M:%S")


def current_user_id():
    """ObjectId of the logged-in user, or None if the session is stale.

    After the SQLite -> MongoDB switch, an old session cookie holds a
    number (1, 2, ...) instead of an ObjectId string. That is not a
    valid user any more; returning None logs the user out cleanly.
    """
    try:
        return ObjectId(session["user_id"])
    except (InvalidId, TypeError, KeyError):
        return None


def require_login():
    """True if logged in, else redirect to login. Used at the top of routes."""
    if "user_id" not in session or current_user_id() is None:
        session.clear()
        return redirect(url_for("login"))
    return None


def to_task(doc):
    """MongoDB document -> dict the templates already expect.

    Templates use task['id']; MongoDB stores the id as _id (an ObjectId).
    This adds a plain string 'id' and leaves every other field alone,
    so no template has to change.
    """
    if doc is None:
        return None
    d = dict(doc)
    d["id"] = str(doc["_id"])
    return d


def get_task(task_id):
    # Ownership check in the query itself: a task is only found if it
    # belongs to the logged-in user. Trying another user's id returns None.
    try:
        oid = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None
    return to_task(
        tasks_col.find_one({"_id": oid, "user_id": current_user_id()})
    )


# The notes home page is parked, not deleted: the tasks list is the
# landing page now (same choice as the SQLite version). To bring notes
# back, uncomment this route and point login() at home again.
# @app.route("/", methods=["GET", "POST"])
# def home():
#     redirect_to_login = require_login()
#     if redirect_to_login:
#         return redirect_to_login
#
#     uid = current_user_id()
#
#     if request.method == "POST":
#         note = request.form["note"].strip()
#         if not note:
#             flash("Note cannot be empty.")
#         else:
#             notes_col.insert_one(
#                 {
#                     "user_id": uid,
#                     "note": note,
#                     "created_at": now_ist_str(),
#                 }
#             )
#             flash("Note saved.")
#             # Post/Redirect/Get: after a POST, redirect so a browser
#             # refresh does not insert the same note twice.
#             return redirect(url_for("home"))
#
#     notes = list(
#         notes_col.find({"user_id": uid}).sort("_id", -1)
#     )
#     return render_template("home.html", email=session["user_email"], notes=notes)


@app.route("/")
def list_tasks():
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    uid = current_user_id()
    task_filter = request.args.get("filter", "all")
    query = {"user_id": uid}
    sort = [("position", 1), ("_id", -1)]
    if task_filter == "pending":
        query["is_done"] = False
    elif task_filter == "done":
        query["is_done"] = True
    elif task_filter == "overdue":
        # due_date is stored as "YYYY-MM-DD" text (or None when empty),
        # so a plain string comparison finds dates before today.
        query["is_done"] = False
        query["due_date"] = {"$ne": None, "$lt": date.today().isoformat()}
        sort = [("due_date", 1)]
    else:
        task_filter = "all"
    tasks = [to_task(doc) for doc in tasks_col.find(query).sort(sort)]
    return render_template("tasks.html", tasks=tasks, task_filter=task_filter)


@app.route("/tasks/new", methods=["GET", "POST"])
def new_task():
    today = date.today().isoformat()
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        due_date = request.form["due_date"].strip() or None
        if due_date and due_date < today:
            flash("Due date cannot be in the past.")
            return render_template("task_form.html", task=None, form_action=url_for("new_task"), today=today)
        priority = request.form["priority"]
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        if not title:
            flash("Title is required.")
            return render_template("task_form.html", task=None,
                       form_action=url_for("new_task"), today=today)

        uid = current_user_id()
        # New tasks go to the top of the list: one less than the
        # smallest position this user has, so the order stays newest-first
        # until the user drags tasks around.
        first = tasks_col.find_one({"user_id": uid}, sort=[("position", 1)])
        position = (first["position"] - 1) if first else 0
        now = now_ist_str()
        tasks_col.insert_one(
            {
                "user_id": uid,
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "is_done": False,
                "position": position,
                "created_at": now,
                "updated_at": now,
            }
        )
        flash("Task created.")
        return redirect(url_for("list_tasks"))

    return render_template("task_form.html", task=None,
                       form_action=url_for("new_task"), today=today)



@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    today = date.today().isoformat()
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    task = get_task(task_id)
    if task is None:
        flash("Task not found.")
        return redirect(url_for("list_tasks"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        due_date = request.form["due_date"].strip() or None
        if due_date and due_date < today:
            flash("Due date cannot be in the past.")
            return render_template("task_form.html", task=task,
                                   form_action=url_for("edit_task", task_id=task_id),
                                   today=today)
        priority = request.form["priority"]
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        if not title:
            flash("Title is required.")
            return render_template("task_form.html", task=task,
                                   form_action=url_for("edit_task", task_id=task_id),
                                   today=today)
        now = now_ist_str()
        tasks_col.update_one(
            {"_id": ObjectId(task_id), "user_id": current_user_id()},
            {
                "$set": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                    "priority": priority,
                    "updated_at": now,
                }
            },
        )
        flash("Task updated.")
        return redirect(url_for("list_tasks"))

    return render_template("task_form.html", task=task,
                           form_action=url_for("edit_task", task_id=task_id),
                           today=today)



@app.route("/tasks/<task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    task = get_task(task_id)
    if task is None:
        flash("Task not found.")
        return redirect(url_for("list_tasks"))
    tasks_col.update_one(
        {"_id": ObjectId(task_id), "user_id": current_user_id()},
        {"$set": {"is_done": not task["is_done"]}},
    )
    return redirect(url_for("list_tasks"))


@app.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    task = get_task(task_id)
    if task is None:
        flash("Task not found.")
        return redirect(url_for("list_tasks"))
    tasks_col.delete_one({"_id": ObjectId(task_id), "user_id": current_user_id()})
    flash("Task deleted.")
    return redirect(url_for("list_tasks"))


@app.route("/tasks/reorder", methods=["POST"])
def reorder_tasks():
    """Save a dragged new order. The page sends JSON: {"order": ["...", "..."]}.

    Only the logged-in user's own task ids are accepted; any other id
    in the list is ignored. Tasks not in the list keep their order
    after the listed ones.
    """
    redirect_to_login = require_login()
    if redirect_to_login:
        return redirect_to_login

    data = request.get_json(silent=True) or {}
    uid = current_user_id()
    own_ids = [
        str(doc["_id"])
        for doc in tasks_col.find({"user_id": uid}).sort(
            [("position", 1), ("_id", -1)]
        )
    ]
    wanted = []
    for tid in data.get("order", []):
        try:
            ObjectId(tid)
        except (InvalidId, TypeError):
            continue
        if tid in own_ids and tid not in wanted:
            wanted.append(tid)
    rest = [tid for tid in own_ids if tid not in wanted]
    for pos, tid in enumerate(wanted + rest):
        tasks_col.update_one(
            {"_id": ObjectId(tid), "user_id": uid},
            {"$set": {"position": pos}},
        )
    return jsonify({"ok": True})


@app.route("/register", methods=["GET", "POST"])
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
            try:
                now = now_ist_str()
                users_col.insert_one(
                    {
                        "email": email,
                        "password_hash": generate_password_hash(password),
                        "created_at": now,
                    }
                )
            except DuplicateKeyError:
                flash("That email is already registered. Try logging in.")
                return render_template("register.html")
            flash("Account created. Now log in.")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = users_col.find_one({"email": email})

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            session["user_email"] = user["email"]
            return redirect(url_for("list_tasks"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
