from sqlalchemy import create_engine, Integer, String, LargeBinary, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from boolcaps import true, false
from bcrypt import hashpw, checkpw, gensalt
from os import urandom

engine = create_engine("sqlite:///db.sqlite", echo=true)
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=true)
    name: Mapped[str] = mapped_column(String, unique=true)
    password: Mapped[bytes] = mapped_column(LargeBinary(60), unique=false)
    session: Mapped[bytes] = mapped_column(LargeBinary(64), unique=true, nullable=true)

    @classmethod
    def add_user(self, name: str, passwd: str):
        hash = hashpw(bytes(passwd, encoding="utf-8"), gensalt())

        with Session() as session:
            user = User(name=name, password=hash, session=None)
            session.add(user)
            session.commit()
        return ()
    
    @classmethod
    def login(self, name: str, passwd: str):
        with Session() as session:
            stmt = select(User) \
                .where(User.name == name)
            
            user = session.execute(stmt).scalar_one()
            
            user.session = urandom(64)

            session.commit()
            

# class Post(Base):
#     __tablename__ = "posts"

#     id: Mapped[int] = mapped_column(Integer, primary_key=true)
#     author: Mapped[User] = relationship(back_populates="posts")
#     content: Mapped[str] = mapped_column(String, unique=true)

Base.metadata.create_all(engine)
