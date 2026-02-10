from flask import request, make_response
from db import tables
import sqlalchemy

def create_endpoints(app):
    @app.route("/api/v1/user/add", methods=["POST"])
    def api1_user_add():
        json = request.json

        user    = json["username"]
        passwd  = json["passwd"]
        
        try: tables.User.add_user(user, passwd)
        except sqlalchemy.exc.IntegrityError:
            return make_response({
                "error": "username already taken"
            }, 400)

        except Exception as e:
            return make_response({
                "error": f"Python error: {e.__repr__()}"
            }, 500)

        return {
            "error": None,
        }

    @app.route("/api/v1/users/<name>/login", methods=["POST"])
    def api1_user_login(name: str):
        json = request.json

        passwd = json["passwd"]

        try: resp = tables.User.login(name, bytes(passwd, encoding="utf-8"))
        except PermissionError:
            return make_response({
                "error": "incorrect password"
            }, 401)
            
        except Exception as e:
            print(e)
            return make_response({
                "error": f"Python error: {e.__repr__()}"
            }, 500)

        return {
            "error": None,
            "token": resp,
        }

    @app.route("/api/v1/session/logout", methods=["POST"])
    def api1_session_logout():
        token = request.authorization.token
        def payload(user: tables.User, session):
            user.session = None
            session.commit()
    
        try: tables.User.transaction_by_bearer(token, payload)
        except sqlalchemy.exc.NoResultFound:
            pass

        return {
            "error": None
        }

    @app.route("/api/v1/users/<name>")
    def api1_users_info(name: str):
        def payload(user: tables.User, _):
            return user.to_dict_api()

        try: return tables.User.transaction_by_name(name, payload)
        except sqlalchemy.exc.NoResultFound:
            return make_response({
                "error": "user not found",
                "errornum": 4
            }, 404)
