from flask import Flask,  render_template

app = Flask(__name__)

@app.route("/") #def endpoint
def home():
    return render_template("home.html", name="Gopi") #(source data, parameters)
if __name__ == "__main__":
    app.run(debug=True)