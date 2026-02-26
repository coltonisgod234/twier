from sqlalchemy import select
from dataclasses import dataclass
from db.tables import Session
from routes.api.search.clauses import *

@dataclass
class SearchData:
    root: SearchClauseBase
    ty: Type

def search(data: SearchData):
    # prepare query
    query = select(data.ty)

    if True:
        fname = data.root._fieldname_
        if fname == None:
            query = data.root.query(None, query)

        else:
            field = getattr(data.ty, fname)
            query = data.root.query(field, query)
        
    # make the search
    with Session() as session:
        sql_res = session.execute(query).scalars().all()
        results = []
        for item in sql_res:
            results.append(item.to_dict_api())

        return results

def create_endpoints(app):
    @app.route("/api/v1/search", methods=["POST"])
    def api1_search_json():
        '''
        searches via JSON
        '''
        from flask import request
        return search_api_json(json_to_search(json))

def search_api_json(data) -> dict:
    try:
        return search(data)
    
    except InvalidQueryFor as e:
        return {
            "error": {
                "msg": "invalid query type",
                "num": 8,
                "offender": e.problem
            }
        }, 400
        
    except InvalidClauseType as e:
        return {
            "error": {
                "msg": "invalid clause type",
                "num": 11,
                "offender": e.problem
            }
        }, 400
        
    except AttributeError as e:
        return {
            "error": {
                "msg": "not even Colton knows what this error is",
                "num": -2,
                "offender": f"Some Python error: {e.__repr__()}"
            }
        }

class InvalidQueryFor(Exception):
    def __init__(self, problem: str, *args):
        self.problem = problem
        super().__init__(*args)

class InvalidClauseType(Exception):
    def __init__(self, problem: str, *args):
        self.problem = problem
        super().__init__(*args)


def json_to_search(json: dict) -> SearchData:
    '''
    # JSON format
    {
        "type": [content type],
        "value": [JSON value representing clause]
    }
    '''
    return SearchData(
        root    = value_from_dict(json["value"]),
        ty      = query_type_from_str(json["type"])
    )

def clause_from_params(ty, args, field) -> SearchClauseBase:
    # block certain fields
    if isinstance(field, str):
        if field in ["password", "session"]:
            raise ValueError("Illegal field name!")

    x = ty(*args)
    x._fieldname_ = field
    return x

def clause_from_json(json: dict) -> SearchClauseBase:
    '''
    # JSON format
    ```
    {
        "type": [clause id],
        "params": [
            {
                "type": [typeid],
                "value": [corresponding JSON data type]
            }
        ],
        "field": [field name]
    }
    ```
    
    ## Clause names
    * `like(str)`: SQL `like` operation
    * `eq(any)`: equals operation
    * `gt(int | float)`: greater-than operation
    * `lt(int | float)`: less-than operation
    * `not(clause)`: applies `not` to it's subclause
    * `all(list[clause])`
    
    ## Type IDs
    * `string`: data is a free-form string.
    * `int`: data is a 64-bit integer.
    * `float`: data is a 64-bit float.
    * `null`: there is no data, the `value` key can be omitted
    * `clause`: data is a JSON object representing another, sub-clause.
    * `list`: JSON list, in the same format as `params`
    '''
    ty = clause_type_from_str(json["type"])
    args = search_args_from_params(json["params"])
    field = json["field"]
    
    return clause_from_params(ty, args, field)

def search_args_from_params(json: list[dict]):
    args_out = []
    for par in json:
        args_out.append(value_from_dict(par))
        
    return args_out        

def value_from_dict(json: dict):
    arg_t = json["type"]
    arg_v = None

    match arg_t:  # special coersions happen in this match
        case "string" | "int" | "float": arg_v = json["value"]
        case "clause": arg_v = clause_from_json(json["value"])
        case "list": arg_v = search_args_from_params(json["value"])
        case _: raise TypeError
        
    return arg_v

def clause_type_from_str(s: str) -> Type:
    match s:
        case "like": return SearchClauseLike
        case "all": return SearchClauseAll
        case "limit": return SearchClauseLimit
        case "not": return SearchClauseNot
        case "gt": return SearchClauseGt
        case "ge": return SearchClauseGe
        case "lt": return SearchClauseLt
        case "le": return SearchClauseLe
        case "eq": return SearchClauseEq
        case other: raise InvalidClauseType(other)
    
def query_type_from_str(s: str) -> Type:
    from db.tables import User, Post, Word
    
    query_for = None
    match s:
        case "user": query_for = User
        case "post": query_for = Post
        case "word": query_for = Word
        case other: raise InvalidQueryFor(other)
        
    return query_for

def flask_args_to_search():
    from flask import request
    
    query_for = query_type_from_str(request.form["for"])
    
