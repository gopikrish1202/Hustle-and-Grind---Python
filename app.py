from flask import Flask

app = Flask(__name__)

@app.route("/") #def endpoint
def home():
    return "<h1>Task Manager is running!</h1><p>Lesson 2 complete - Gopi</p>"

if __name__ == "__main__":
    app.run(debug=True)