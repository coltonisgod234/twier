from flask import request, render_template
from dataclasses import dataclass
from db import tables
import random
from enum import Enum
import sqlalchemy
import os

# non-hotreloadadable
JS_PRELOAD = {}
for (root, _, files) in os.walk("js/"):
    for file in files:
        with open(root+file, "r") as f:
            data = f.read()
            JS_PRELOAD[file] = data

print(f"Javascript modules: {JS_PRELOAD.keys()}")

GREETINGS = ["yo", "wsg", "hey"]

@dataclass
class UserSession:
    # something like "s1wc"
    name: str
    
    # something like "yo"
    greeting: str

@dataclass
class FrontendData:
    session: UserSession
    scripts: list[str]
    
    def into_kwargs(self) -> dict:
        return {
            "session": self.session,
            "__modules__": self.scripts
        }
    
    @classmethod
    def default(self):
        return FrontendData(
            None,
            None
        )

def get_frontend_data(requirements: list[str]):
    scripts = create_scripts_header(requirements)

    # token = request.authorization.token
    token = request.cookies.get("twier_token")
    if token == None:
        return FrontendData(None, scripts)

    try: name = tables.User.transaction_by_bearer(token, lambda user, _: user.name)
    except sqlalchemy.exc.NoResultFound:
        return FrontendData(None, scripts)
    
    except Exception as e:
        return FrontendData({
            "greeting": "server error (log out and log back in!)",
            "name": f"the error is: {e.__repr__()}"
        }, scripts)
        
    if name == None:
        return FrontendData.default()
    
    greeting = random.choice(GREETINGS)
    
    return FrontendData(
        session = UserSession(
            name = name,
            greeting = greeting
        ),
        scripts = scripts
    )

def endpoint(requirements: list[str]):
    data = get_frontend_data(requirements)
    return data.into_kwargs()

def create_endpoints(app):
    @app.route("/")
    def twier():
        return render_template(
            "index.html",
            posts=tables.Post.get_most_recent_posts(50),
            **endpoint(["cookie.js"])
        )
        
    @app.route("/frontend/post/new")
    def frontend_new_post():
        return render_template("posts/new.html", **endpoint(["cookie.js", "post.js"]))
    
    @app.route("/frontend/post/conflict")
    def frontend_conflict():
        from json import loads
        error = request.args.get("w")
        wl = loads(error)

        return render_template(
            "posts/conflict_prompt.html",
            words=wl,
            **endpoint([])
        )

    @app.route("/frontend/signup")
    def frontend_signup():
        return render_template("signup.html", **endpoint(["login.js", "cookie.js"]))

    @app.route("/frontend/login")
    def frontend_login():
        return render_template("login.html",  **endpoint(["cookie.js", "login.js"]))
    
    @app.route("/frontend/account")
    def frontend_account_page():
        return render_template("account/settings.html", **endpoint(["cookie.js", "logout.js"]))

    @app.route("/frontend/status")
    def frontend_stats():
        from decimal import Decimal, getcontext
        getcontext().prec = 100000  # set precision

        MAX_POSTS = 27**160
        current_posts = 0
        with tables.Session() as session:
            current_posts = session.query(tables.Post).count()
            
        percent = Decimal(current_posts) / Decimal(MAX_POSTS)

        return render_template(
            "coolstuff/progress.html",
            progress={
                # "max_posts": 95**160,
                # case insensitive version
                "max_posts": MAX_POSTS,
                "current_posts": current_posts,
                "percent": percent,
                "percent_scientific_approximate": f"{percent:.30E}"
            },
            **endpoint([])
        )

# def create_route(
#     app,
#     route_name: str,
#     path: str,
#     modules: list[str],
#     handler
# ):
#     '''a system of bundling needed Javascript files into there instead'''
#     app.add_url_rule(
#         path,
#         route_name,
#         create_scripts_header        
#     )

def create_scripts_header(modules: list[str]):
    scripts = []
    for js in modules:
        scripts.append(JS_PRELOAD[js])

    return scripts
