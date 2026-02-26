from flask import request, render_template, send_from_directory, make_response, redirect
from db import tables
import sqlalchemy
from routes.frontend.frontend_common import *

def create_endpoints(app):
    @app.route("/")
    def twier():
        return render_template(
            "index.html",
            posts=tables.Post.get_most_recent_posts(50),
            **endpoint()
        )
        
    @app.route("/frontend/post/new")
    def frontend_new_post():
        return render_template("posts/new.html", **endpoint())
    
    @app.route("/frontend/post/new/form", methods=["POST"])
    def frontend_new_post_form():
        from routes.api.routes_posts import create_post
        
        try:
            auth = token()
            content = request.form["content"]
            create_post(auth, content)
            return redirect("/", code=303)

        except AttributeError:
            return render_template("posts/error.html", error={"message": "missing content or authorization"})
        
        except tables.IlligalContent:
            return render_template("posts/error.html", error={"message": "illigal content"})
        
        except tables.BannedWordsUsed:
            return render_template("posts/error.html", error={"message": "your account has been banned for using a word on the blocklist"})
        
        except tables.WordsAlreadyTaken as w:
            return render_template(
                "posts/conflict_prompt.html",
                words=w.words,
                **endpoint()
            )
            
    @app.route("/frontend/do/logout")
    def frontend_do_logout():
        try:
            def payload(u, s):
                u.logout()
                s.commit()

            tok = token()
            tables.User.transaction_by_bearer(tok, payload)
            
            return render_template("login/loggedout.html")
        except sqlalchemy.exc.NoResultFound:
            return redirect("/")
    
    @app.route("/frontend/do/delete_account", methods=["POST"])
    def frontend_do_delete_account():
        from sqlalchemy import select
    
        tok = token()
        uname = request.form["username"]
        passwd = request.form["password"]

        with tables.Session() as sess:
            stmt = select(tables.User) \
                .where(tables.User.session == tok) \
                .where(tables.User.name == uname)
                
            user = sess.scalar(stmt)
            
            if not user:
                return render_template("signup/delete_account_error.html", error_message="user doesn't exist", error_code=404)

            if not user.check_login_str(passwd):
                return render_template("signup/delete_account_error.html", error_message="incorrect verification password", error_code=401)

            sess.delete(user)
            sess.commit()
            return render_template("signup/delete_account_success.html")

    @app.route("/frontend/post/conflict")
    def frontend_conflict():
        from json import loads
        error = request.args.get("w")
        wl = loads(error)

        return render_template(
            "posts/conflict_prompt.html",
            words=wl,
            **endpoint()
        )

    @app.route("/frontend/signup")
    def frontend_signup():
        return render_template("signup/signup.html", **endpoint())

    @app.route("/frontend/signup/form", methods=["POST"])
    def frontend_signup_form():
        try:
            name = request.form["username"]
            passwd = request.form["passwd"]
            tables.User.add_user(name, passwd)
            
            return redirect("/", code=303)
            
        except AttributeError:
            return render_template("signup/error.html", error={"message": "credentials not found"})
            
        except sqlalchemy.exc.IntegrityError:
            return render_template("signup/error.html", error={"message": "username already taken"})

    @app.route("/frontend/login")
    def frontend_login():
        return render_template("login/login.html",  **endpoint())

    @app.route("/frontend/login/form", methods=["POST"])
    def frontend_login_form():
        try:
            passwd = request.form["passwd"]
            name = request.form["username"]

            def payload(u: tables.User, s):
                token = u.login_str(passwd)
                s.commit()

                resp = make_response(redirect("/"))

                set_token(token, resp)
                
                return resp

            return tables.User.transaction_by_name(name, payload)

        except AttributeError as w:
            from traceback import format_exc
            return render_template("login/error.html", error={
                "message": f"request missing credentials",
                "tb": format_exc()
            })

        except PermissionError:
            return render_template("login/error.html", error={"message": "incorrect password"}), 401
        
        except sqlalchemy.exc.NoResultFound:
            return render_template("login/error.html", error={"message": "username not found"}), 404

        except Exception as e:
            print(e)
            return render_template("login/error.html", error={"message": f"internal server error: {e}"}), 500

    @app.route("/frontend/account")
    def frontend_account_page():
        try:
            user = tables.User.transaction_by_bearer(token(), lambda user, _: user.to_dict_api())

            return render_template(
                "account/settings.html",
                user=user,
                **endpoint()
            )
        except sqlalchemy.exc.NoResultFound:
            return redirect("/")

    @app.route("/frontend/user/<name>")
    def frontend_user_by_name(name: str):
        try: user = tables.User.transaction_by_name(name, lambda user, _: user.to_dict_api())
        except Exception:
            return "not found", 404

        return render_template(
            "account/user.html",
            user=user,
            **endpoint()
        )

    @app.route("/frontend/status")
    def frontend_stats():
        from routes.api.routes_progress import get_progress
        return render_template(
            "coolstuff/progress.html",
            progress=get_progress(),
            **endpoint()
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
