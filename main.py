from flask import Flask, render_template
from boolcaps import true
from routes import users

app = Flask(__name__)

users.create_endpoints(app)

@app.route("/")
def a():
    return render_template("index.html")

@app.route("/signup")
def b():
    return render_template("signup.html")

app.run(
    "0.0.0.0",
    8080,
    debug=true
)
