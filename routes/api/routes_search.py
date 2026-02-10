from db.tables import Session, Post, User
from dataclasses import dataclass
from sqlalchemy import select

@dataclass
class PostsSearchData:
    content_include_keywords: list[str]
    content_exclude_keywords: list[str]

    author_name_include_keywords: list[str]
    author_name_exclude_keywords: list[str]
    
    __form__ = {
        "POSTS_content_include_keywords": "content_include_keywords",
        "POSTS_content_exclude_keywords": "content_exclude_keywords",
        "POSTS_author_name_include_keywords": "author_name_include_keywords",
        "POSTS_author_name_exclude_keywords": "author_name_exclude_keywords"
    }

@dataclass
class UsersSearchData:
    username_include_keywords: list[str]
    username_exclude_keywords: list[str]
    
    posts_content_include_keywords: list[str]
    posts_content_exclude_keywords: list[str]
    
    __form__ = {
        "USERS_username_include_keywords": "username_include_keywords",
        "USERS_username_exclude_keywords": "username_exclude_keywords",
        "USERS_posts_content_include_keywords": "posts_content_include_keywords",
        "USERS_posts_content_exclude_keywords": "posts_content_exclude_keywords"
    }

@dataclass
class SearchData:
    posts: PostsSearchData | None
    users: UsersSearchData | None
    words: None
    
    limit: int

###################
# BEGIN DUMB SHIT #
###################

def search_posts_stmt(data: dict):
    stmt = select(Post)
    
    if keywords := data["content_include_keywords"]:
        for keyword in keywords:
            stmt = stmt.where(Post.content.like(keyword))
            
    if keywords := data["content_exclude_keywords"]:
        for keyword in keywords:
            stmt = stmt.where(Post.content.not_like(keyword))

    like_keywords = data["author_name_include_keywords"] or []
    unlike_keywords = data["author_name_exclude_keywords"] or []
    if like_keywords or unlike_keywords:
        stmt = stmt.join(Post.author)

        for keyword in like_keywords:
            stmt = stmt.where(User.name.like(keyword))
            
        for keyword in unlike_keywords:
            stmt = stmt.where(User.name.not_like(keyword))
    
    return stmt

def search_users_stmt(data: dict):
    stmt = select(User)
    
    if keywords := data["username_include_keywords"]:
        for keyword in keywords:
            stmt = stmt.where(User.name.like(keyword))
            
    if keywords := data["username_exclude_keywords"]:
        for keyword in keywords:
            stmt = stmt.where(User.name.not_like(keyword))

    return stmt

######################
# END STUPID SHIT    #
######################

def search(data: SearchData):
    with Session() as session:
        # build the query
        users = []
        posts = []
        words = []

        # posts
        if data.posts:
            stmt = search_posts_stmt(data.posts).limit(data.limit)
            results = session.execute(stmt).all()
            posts = list(res[0].to_dict_api() for res in results)

        # users
        if data.users:
            stmt = search_users_stmt(data.users).limit(data.limit)
            results = session.execute(stmt).all()  # no idea why I need to call it like this
            users = list(res[0].to_dict_api() for res in results)

        return {
            "posts": posts,
            "users": users,
            "words": words
        }

def create_endpoints(app):
    @app.route("/api/v1/search", methods=["POST"])
    def api1_search_json():
        '''
        searches via JSON
        '''
        from flask import request
        
        return search(request.json)
    
    def api1_search_form():
        '''
        searches via form data
        '''
        data = flask_args_to_search()
        return search(data)

def flask_args_to_search() -> SearchData:
    from flask import request

    posts = {}
    for (k, v) in PostsSearchData.__form__.items():
        posts[v] = request.args.get(k)
    
    users = {}
    for (k, v) in UsersSearchData.__form__.items():
        users[v] = request.args.get(k)
    
    data = SearchData(
        posts,
        users,
        None,
        request.args.get("limit", default=10)
    )
    
    return data
