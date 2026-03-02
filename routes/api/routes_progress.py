from db.tables import Session, Word
from routes.base import SchEndpoint
from config.config import DICTIONARY
from decimal import Decimal, getcontext

class v1_Progress(SchEndpoint):
    method = "GET"
    path = "/api/v1/progress"

    res = {
        "claims": {
            "num": [int],
            "max": [int],
            "percente": [Decimal]
        }
    }
    
    def view():
        return get_progress()

def create_endpoints(app):
    v1_Progress.register_to(app)

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
