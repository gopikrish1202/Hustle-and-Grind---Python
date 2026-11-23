"""One-time copy of your SQLite data into MongoDB Atlas. Run once.

Run:  python migrate_sqlite_to_mongo.py

It reads task_manager.db (users, notes, tasks) and inserts them into
the MongoDB database named in .env. Users are matched by email, so
running it twice does not create duplicates — already-migrated users
(and their notes/tasks) are skipped.

Your SQLite file is not changed or deleted.
"""
import os
import sqlite3

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

SQLITE_DB = "task_manager.db"


def main():
    uri = os.environ.get("MONGO_URI")
    if not uri:
        print("MONGO_URI is not set. Create the .env file first.")
        raise SystemExit(1)
    db = MongoClient(uri)[os.environ.get("MONGO_DB", "task_manager")]

    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row

    # Does the tasks table already have the Lesson 7 position column?
    task_cols = [r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()]
    has_position = "position" in task_cols

    users_moved = notes_moved = tasks_moved = 0
    for user in conn.execute("SELECT * FROM users"):
        existing = db.users.find_one({"email": user["email"]})
        if existing:
            print(f"Skipping {user['email']}: already in MongoDB.")
            continue
        new_user_id = db.users.insert_one(
            {
                "email": user["email"],
                "password_hash": user["password_hash"],
                "created_at": user["created_at"],
            }
        ).inserted_id
        users_moved += 1

        for note in conn.execute(
            "SELECT * FROM notes WHERE user_id = ?", (user["id"],)
        ):
            db.notes.insert_one(
                {
                    "user_id": new_user_id,
                    "note": note["note"],
                    "created_at": note["created_at"],
                }
            )
            notes_moved += 1

        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
        for pos, task in enumerate(rows):
            db.tasks.insert_one(
                {
                    "user_id": new_user_id,
                    "title": task["title"],
                    "description": task["description"],
                    "due_date": task["due_date"],
                    "priority": task["priority"],
                    "is_done": bool(task["is_done"]),
                    # Keep the dragged order if it exists, else newest-first.
                    "position": task["position"] if has_position else pos,
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"],
                }
            )
            tasks_moved += 1

    conn.close()
    print(f"Done. Users: {users_moved}, notes: {notes_moved}, tasks: {tasks_moved}.")


if __name__ == "__main__":
    main()
