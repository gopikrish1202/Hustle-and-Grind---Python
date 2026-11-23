"""Step 1 of Lesson 8: prove this PC can reach your MongoDB Atlas cluster.

Run:  python test_mongo.py

It prints only the server version and database names — never your
connection string or password. Paste that output back.

If it fails, the error tells you which of the three usual causes it is:
- wrong password in .env -> authentication failed
- your IP is not whitelisted -> connection timed out
  (Atlas -> Network Access -> Add IP Address -> Add Current IP)
- cluster paused or wrong host -> could not resolve / timed out
"""
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.environ.get("MONGO_URI")
if not uri:
    print("MONGO_URI is not set. Did you create the .env file?")
    print("Copy .env.example to .env and fill in your Atlas connection string.")
    raise SystemExit(1)

print("Connecting to your Atlas cluster...")
client = MongoClient(uri, serverSelectionTimeoutMS=10000)
print("Ping:", client.admin.command("ping"))
print("Server version:", client.server_info()["version"])
print("Databases you can see:", client.list_database_names())
print("Connected OK. Your PC can reach the cluster.")
