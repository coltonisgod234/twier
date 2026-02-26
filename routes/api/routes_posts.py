from flask import request, make_response
from db.tables import User, Session, Post, WordsAlreadyTaken, BannedWordsUsed, IlligalContent
from sqlalchemy.exc import IntegrityError

def create_endpoints(app):
    @app.route("/api/v1/post/create", methods=["POST"])
    def api_v1_post_create():        
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

    @app.route("/api/v1/users/<name>/posts")
    def api_v1_user_get_posts(name: str):
        return Post.get_posts_of_user_by_name(name)

    @app.route("/api/v1/posts/most_recent/<n>")
    def api_v1_get_recent_posts(n: int):
        return Post.get_most_recent_posts(n)

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
