from flask import request, render_template, send_from_directory, Response, make_response
from dataclasses import dataclass
from db import tables
import random
from enum import Enum
import sqlalchemy
import os
from boolcaps import true, false

TOKEN_COOKIE_NAME = "twier_token"

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

def token() -> str | None:
    return request.cookies.get(TOKEN_COOKIE_NAME)

def set_token(s: str, resp: Response):
    resp.set_cookie(
        TOKEN_COOKIE_NAME,
        s,
        samesite=true,
        httponly=true,
        secure=false,
    )
    
def with_token(s: str, resp: str, status: int = 200):
    resp = make_response(resp, status)
    set_token(s, resp)
    return resp

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
        return with_token(
            
            render_template("signup.html", **endpoint(["login.js", "cookie.js"])),
            200
        )

    @app.route("/frontend/login")
    def frontend_login():
        return render_template("login.html",  **endpoint(["cookie.js", "login.js"]))
    
    @app.route("/frontend/account")
    def frontend_account_page():
        user = tables.User.transaction_by_bearer(request.authorization.token, lambda user, _: user.to_dict_api())

        return render_template(
            "account/settings.html",
            user=user,
            **endpoint(["cookie.js", "logout.js"])
        )

        # return render_template("account/settings.html", **endpoint(["cookie.js", "logout.js"]))
    
    @app.route("/frontend/user/<name>")
    def frontend_user_by_name(name: str):
        try: user = tables.User.transaction_by_name(name, lambda user, _: user.to_dict_api())
        except Exception:
            return "not found", 404

        return render_template(
            "account/user.html",
            user=user,
            **endpoint([])
        )

    @app.route("/frontend/status")
    def frontend_stats():
        from routes.api.routes_progress import get_progress
        return render_template(
            "coolstuff/progress.html",
            progress=get_progress(),
            **endpoint([])
        )
        
    @app.route("/frontend/search")
    def frontend_search():
        return render_template(
            "search/search.html",
            **endpoint([])
        )
    
    # TODO: enable bfcache on this page and this page only!
    @app.route("/searched", methods=["GET"])
    def frontend_searched():
        from routes.api.routes_search import flask_args_to_search, search
        search_data = flask_args_to_search()
        search_results = search(search_data)
        
        return render_template(
            "search/results.html",
            search_results=search_results,
            **endpoint([])
        )

    @app.route("/frontend/config/bans")
    def frontend_get_bans():
        return send_from_directory("config", "bans.txt")
    
    @app.route("/frontend/config/dictionary")
    def frontend_get_dictionary():
        return send_from_directory("config", "dictionary.txt")
    
    @app.route("/frontend/config/unclaimables")
    def frontend_get_unclaimables():
        return send_from_directory("config", "unclaimable.txt")
    

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
