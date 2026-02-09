from flask import Flask, render_template
from boolcaps import true, false
from routes.api import routes_users, routes_posts
from routes.frontend import frontend_base

app = Flask(__name__)

routes_users.create_endpoints(app)
routes_posts.create_endpoints(app)
frontend_base.create_endpoints(app)


# app requires us to delete the bfcache for it to work
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.run(
    "0.0.0.0",
    8080,
    debug=true,
    threaded=false,
    processes=16
)
