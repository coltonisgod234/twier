from boolcaps import true
from dataclasses import dataclass
from flask import request, Response, make_response
import random
from db import tables
import sqlalchemy
from flask import session
 
TOKEN_COOKIE_NAME = "twier_token"

# hopefully no JS anymore
# JS_PRELOAD = {}
# for (root, _, files) in os.walk("js/"):
#     for file in files:
#         with open(root+file, "r") as f:
#             data = f.read()
#             JS_PRELOAD[file] = data
# 
# print(f"Javascript modules: {JS_PRELOAD.keys()}")

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
    
    def into_kwargs(self) -> dict:
        return {
            "session": self.session,
        }
    
    @classmethod
    def default(self):
        return FrontendData(
            None,
        )

def get_frontend_data():
    # token = request.authorization.token
    t = token()
    if t == None:
        return FrontendData.default()

    try: name = tables.User.transaction_by_bearer(t, lambda user, _: user.name)
    except sqlalchemy.exc.NoResultFound:
        return FrontendData.default()
    
    except Exception as e:
        return FrontendData({
            "greeting": "server error (log out and log back in!)",
            "name": f"the error is: {e.__repr__()}"
        })
        
    if name == None:
        return FrontendData.default()
    
    greeting = random.choice(GREETINGS)
    
    return FrontendData(
        session = UserSession(
            name = name,
            greeting = greeting,
        ),
    )

def endpoint():
    data = get_frontend_data()
    return data.into_kwargs()

def token() -> str | None:
    return request.cookies.get(TOKEN_COOKIE_NAME)

def set_token(s: str, resp: Response):
    resp.set_cookie(
        key         = TOKEN_COOKIE_NAME,
        value       = s,
        samesite    = "strict",
        httponly    = true,
        # secure      = false,
    )
    
def with_token(s: str, resp: str, status: int = 200):
    resp = make_response(resp, status)
    set_token(s, resp)
    return resp
