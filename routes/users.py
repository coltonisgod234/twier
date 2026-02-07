from flask import request, make_response
from db import tables
import sqlalchemy

def create_endpoints(app):
    @app.route("/user/add", methods=["POST"])
    def add_user():
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
    
    @app.route("/users/<name>/login", methods=["POST"])
    def login():
        json = request.json
        
        passwd = json["passwd"]
