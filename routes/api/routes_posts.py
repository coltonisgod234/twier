from flask import request, make_response
from db.tables import User, Session, Post, WordsAlreadyTaken, BannedWordsUsed, IlligalContent
from routes.base import SchEndpoint, SchPost, wrap_error_endpoint, Content, SchListOf

class v1_PostCreate(SchEndpoint):
    method = "POST"
    path = "/api/v1/post/create"
    
    auth = "token"
    codes = [200, 409, 500]
    
    req = Content({
        "content": [str]
    })

    res = wrap_error_endpoint([3, 7], {})
    
    def view():        
        auth = request.authorization.token
        content = request.json["content"]

        try: create_post(auth, content)
        except WordsAlreadyTaken as w:
            return make_response({
                "error": "words already used",
                "wordlist": w.words,
                "errornum": 1
            }, 409)

        except BannedWordsUsed:
            return {
                "error": "you said a no no word",
                "errornum": 3
            }

        except IlligalContent:
            return make_response({
                "error": "illigal content in post",
                "errornum": 7
            })
            
        else:
            return {
                "error": None
            }

class v1_UserGetPosts(SchEndpoint):
    method = "GET"
    path = "/api/v1/users/<name>/posts"
    
    codes = [200, 404]
    
    res = Content({
        "posts": [SchListOf(SchPost)]
    })
    
    def view(name: str):
        return {
            "posts": Post.get_posts_of_user_by_name(name)
        }

class v1_GetRecentPosts(SchEndpoint):
    method = "GET"
    path = "/api/v1/posts/most_recent/<n>"
    
    codes = [200]
    
    res = Content({
        "posts": [SchListOf(SchPost)]
    })
    
    def view(n: int):
        return {
            "posts": Post.get_most_recent_posts(n)
        }

def create_endpoints(app):
    v1_PostCreate.register_to(app)
    v1_UserGetPosts.register_to(app)
    v1_GetRecentPosts.register_to(app)

def all_endpoints():
    return [
        v1_PostCreate,
        v1_GetRecentPosts,
        v1_UserGetPosts
    ]

def create_post(auth: str, content: str):
    with Session() as session:
        stmt = session.query(User) \
            .where(User.session == auth)

        user: User = session.execute(stmt).scalar_one()

        try:
            post = user.create_and_validate_post_object(content, session)
            session.add(post)
            session.commit()

        except BannedWordsUsed as e:
            session.delete(user)
            session.commit()
            raise e
        
        except IlligalContent as e:
            raise e

        except Exception as e:
            raise e

    return {
        "error": None
    }
