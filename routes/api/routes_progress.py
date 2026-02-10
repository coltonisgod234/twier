from db.tables import Session, Post, Word, User
from config.config import DICTIONARY
from decimal import Decimal, getcontext

# TODO: do a thing

def create_routes(app):
    @app.route("/api/v1/progress")
    def api_get_progress():
        return get_progress()

def get_progress():
    with Session() as session:
        getcontext().prec = 500

        claims_num = session.query(Word).count()
        claims_max = len(DICTIONARY)
        claims = {
            "num": claims_num,
            "max": claims_max,
            "percent": Decimal(claims_num) / Decimal(claims_max)
        }

        return {
            "claims": claims,
        }
