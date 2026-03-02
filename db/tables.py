from sqlalchemy import create_engine, Integer, String, LargeBinary, select, ForeignKey, desc, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from boolcaps import true, false
from bcrypt import hashpw, checkpw, gensalt
import secrets
import string
from typing import Callable

engine = create_engine("sqlite:///db.sqlite", echo=true)
Session = sessionmaker(bind=engine)

class APISafeProto:
    def to_dict_api(self) -> dict:
        raise NotImplementedError("to_dict_api() not implemented")

class WordsAlreadyTaken(Exception):
    def __init__(self, words, *args):
        super().__init__(*args)
        self.words = words
        
class BannedWordsUsed(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class IlligalContent(Exception): pass

class Base(DeclarativeBase): pass

class User(Base, APISafeProto):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=true)
    name: Mapped[str] = mapped_column(String, unique=true)
    password: Mapped[bytes] = mapped_column(LargeBinary(60), unique=false)
    session: Mapped[bytes] = mapped_column(String(96), unique=true, nullable=true)

    words: Mapped[list["Word"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"  # don't know why I need this
    )

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan"  # I think I get why I need this a lil more now...
    )

    def logout(self):
        self.session = None

    @classmethod
    def add_user(self, name: str, passwd: str):
        hash = hashpw(bytes(passwd, encoding="utf-8"), gensalt())

        with Session() as session:
            user = User(name=name, password=hash, session=None)
            if len(name) > 20:
                return
            session.add(user)
            session.commit()

    def to_dict_api(self) -> dict:
        posts = []
        for post in self.posts:
            posts.append({
                "content": post.content,
                "id": post.id,
            })

        words = []
        for word in self.words:
            words.append({
                # Removed because it's redundant
                # "owner": {
                #     "name": word.user.name,
                #     "id": word.user.id
                # },
                "word": word.word
            })

        return {
            "id": self.id,
            "name": self.name,
            "words": words,
            "posts": posts,
        }

    def to_dict_norecurse(self) -> dict:
        return {
            "id": self.id,
            "name": self.name
        }

    def check_login_raw(self, passwd: bytes) -> bool:
        return checkpw(passwd, self.password)
    
    def check_login_str(self, passwd: str) -> bool:
        return checkpw(bytes(passwd, encoding="utf-8"), self.password)
        
    def login_str(self, passwd: str) -> str:
        """
        Output is guaranteed to be printable, that is, serializable into JSON.
        """
        possibly_use_this_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(96))
        if self.check_login_str(passwd):
            self.session = possibly_use_this_token
            return possibly_use_this_token

        else:
            raise PermissionError

    @classmethod
    def transaction_by_name(self, name: str, closure):
        with Session() as session:
            stmt = select(User) \
                .where(User.name == name)

            user = session.execute(stmt).scalar_one()

            return closure(user, session)

    @classmethod
    def transaction_by_bearer(self, token: str, closure):
        with Session() as session:
            stmt = select(User) \
                .where(User.session == token)

            user = session.execute(stmt).scalar_one()

            return closure(user, session)

    @classmethod
    def check_login_by_bearer(self, token: str) -> bool:
        # doesn't check for collisions, we live dangerously
        with Session() as session:
            stmt = select(User).where(User.token == token)

            user = session.execute(stmt).scalar_one_or_none()
            if user == None:
                return false

            else:
                return true

    def create_and_validate_post_object(self, content: str, session):
        '''
        creates, validates, and ensures soundness of a Post object.
        
        All words in `content` are added to the user's `words` field, and
        therefore the `words` table.
        
        Posts are always lowercase
        '''
        if len(content.strip()) == 0:
            raise IlligalContent

        content = content.lower()
        words = split_content_into_words(content)

        # ensure we can actually claim them
        from config import config

        # validation
        stmt = select(Word).where(
            Word.word.in_(words),
            Word.user_id != self.id
        )

        if set(words).issubset(config.BANNED_WORDS):
            # ban the guy
            raise BannedWordsUsed()

        possibly_words = session.execute(stmt).all()

        if possibly_words:
            # AtributeError: w.user
            print(possibly_words.__repr__())
            word_strings = list({
                "word": w[0].word,
                "owner": w[0].user.name
            } for w in possibly_words)
            raise WordsAlreadyTaken(word_strings)

        # where we make the thing
        else:
            # word_objects = list(Word(user=self, word=s) for s in words)

            # ugly version of this that GPT wrote
            # stmt = insert(Word).values(word_objects)
            stmt = insert(Word).values([{
                "user_id": self.id,
                "word": w
            } for w in words if w not in config.BANNED_CLAIMS])
            stmt = stmt.prefix_with("OR IGNORE")  # SQLite will skip duplicates
            session.execute(stmt)

            # inserts will NOT show up until the next query! Which is fine

            # create the post
            post = Post(content=content, author=self)
            return post

def split_content_into_words(s: str) -> list[str]:
    import re
    return re.findall("[A-z0-9]+", s)

class Post(Base, APISafeProto):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=true)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped[User] = relationship(back_populates="posts")

    content: Mapped[str] = mapped_column(String(160))

    @classmethod
    def get_posts_of_user_by_name(self, name: str):
        with Session() as session:
            # Get the user first
            query = session.query(User) \
                .where(User.name == name)

            user: User = session.execute(query).scalar_one()

            return list(post.to_dict_api() for post in user.posts)

    @classmethod
    def get_most_recent_posts(self, n: int):
        with Session() as session:
            query = session.query(Post) \
                .order_by(desc(Post.id)) \
                .limit(n)

            posts: list[Post] = session.execute(query).scalars().all()

            return list(post.to_dict_api() for post in posts)
        
    def to_dict_api(self):
        return {
            "id": self.id,
            "author": self.author.to_dict_norecurse(),
            "content": self.content
        }

# thanks GPT!
class Word(Base, APISafeProto):
    __tablename__ = "words"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=true,
    )
    word: Mapped[str] = mapped_column(
        String,
        primary_key=true,
        index=true,
        unique=true
    )

    user: Mapped[User] = relationship(back_populates="words")

    def __repr__(self):
        return f"Word('{self.word}', by={self.user.__repr__()})"

    def to_dict_api(self):
        return {
            "word": self.word,
            "owner": self.user.to_dict_norecurse(),
        }

Base.metadata.create_all(engine)
