from flask import request, make_response
from db import tables
from dataclasses import dataclass
import sqlalchemy
from routes.base import SchEndpoint, SchError, SchOptional, Content, wrap_error_endpoint, SchUser

@dataclass
class v1_UserAdd(SchEndpoint):
    method = "POST"
    path   = "/api/v1/user/add"
    req    = Content({
        "username": [str],
        "passwd": [str],
    })
    
    res    = Content({
        "error": [SchOptional, SchError([-2, 6])],
        "token": [SchOptional, str]
    })

    codes = [200, 400, 500]
    
    def view():
        json = request.json

        user    = json["username"]
        passwd  = json["passwd"]
        
        try: tables.User.add_user(user, passwd)
        except sqlalchemy.exc.IntegrityError:
            return make_response({
                "error": {
                    "msg": "username already taken",
                    "num": 6
                }
            }, 400)

        except Exception as e:
            return make_response({
                "error": {
                    "msg": f"Python error: {e.__repr__()}",
                    "num": -2
                }
            }, 500)

        return {
            "error": None,
        }

@dataclass
class v1_UserLogin(SchEndpoint):
    method = "POST"
    path = "/api/v1/users/<name>/login"
    
    req = Content({
        "passwd": [str]
    })
    
    res = wrap_error_endpoint([-1, 10], {
        "token": [str]
    })
    
    codes = [200, 401, 500]
    
    def view(name: str):
        json = request.json

        passwd = json["passwd"]

        def payload(u: tables.User, s):
            try:
                resp = u.login_str(passwd)
                s.commit()
                return {
                    "error": None,
                    "token": resp,
                }

            except PermissionError:
                return make_response({
                    "error": {
                        "msg": "incorrect password",
                        "num": 10
                    }
                }, 401)
                
            except Exception as e:
                print(e)
                return make_response({
                    "error": {
                        "msg": f"Python error: {e.__repr__()}",
                        "num": -1
                    }
                }, 500)
            
        return tables.User.transaction_by_name(name, payload)

@dataclass
class v1_SessionLogout(SchEndpoint):
    method = "POST"
    path = "/api/v1/session/logout"
    
    req = None
    res = Content({
        "error": [SchError([])]
    })
    
    codes = [200, 400, 500]  # TODO: might be wrong
    
    auth = "token"
    
    def view():
        token = request.authorization.token
        def payload(user: tables.User, session):
            user.logout()
            session.commit()
    
        try: tables.User.transaction_by_bearer(token, payload)
        except sqlalchemy.exc.NoResultFound:
            pass

        return {
            "error": None,
        }

class v1_UserInfo(SchEndpoint):
    method = "GET"
    path = "/api/v1/users/<name>"
    
    res = wrap_error_endpoint([4], {
        "info": [SchUser]
    })
    
    codes = 404

    def view(name: str):
        def payload(user: tables.User, _):
            return {
                "info": user.to_dict_api()
            }

        try: return tables.User.transaction_by_name(name, payload)
        except sqlalchemy.exc.NoResultFound:
            return make_response({
                "error": {
                    "msg": "user not found",
                    "num": 4
                }
            }, 404)

def create_endpoints(app):
    v1_UserAdd.register_to(app)
    v1_UserLogin.register_to(app)
    v1_SessionLogout.register_to(app)
    v1_UserInfo.register_to(app)
