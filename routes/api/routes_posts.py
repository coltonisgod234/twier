from flask import request, make_response
from db.tables import User, Session, Post, WordsAlreadyTakenException, BannedWordsUsed
from sqlalchemy.exc import IntegrityError

def create_endpoints(app):
    @app.route("/api/v1/post/create", methods=["POST"])
    def api_v1_post_create():
        auth = request.authorization.token
        content = request.json["content"]
        print(request.json)

        with Session() as session:
            stmt = session.query(User) \
                .where(User.session == auth)

            user: User = session.execute(stmt).scalar_one()

            try:
                post = user.create_and_validate_post_object(content, session)
                session.add(post)
                session.commit()
            except WordsAlreadyTakenException as w:
                return make_response({
                    "error": "words already used",
                    "wordlist": w.words,
                    "errornum": 1
                }, 409)
            
            except BannedWordsUsed:
                session.delete(user)
                session.commit()
                return {
                    "error": "you said a no no word",
                    "errornum": 3
                }

        return {
            "error": None
        }

    @app.route("/api/v1/users/<name>/posts")
    def api_v1_user_get_posts(name: str):
        return Post.get_posts_of_user_by_name(name)

    @app.route("/api/v1/posts/most_recent/<n>")
    def api_v1_get_recent_posts(n: int):
        return Post.get_most_recent_posts(n)
