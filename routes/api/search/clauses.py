from typing import Type
from sqlalchemy import Select, ClauseElement
from dataclasses import dataclass
# from functools import wraps
# def search_clause(cls):
#     prev_init = cls.__init__
#     @wraps(prev_init)
#     def __init__(self, *args, _fieldname_: str, **kwargs):
#         prev_init(self, *args, **kwargs)
#         self._fieldname_ = _fieldname_
#     cls.__init__ = __init__
#     return cls

class SearchClauseBase:
    def boolean_clauses(self, entry: Type) -> list[ClauseElement]:
        '''
        Returns a list of SQLAlchemy clause elements.
        '''
        return []

    def apply_query_mutations(self, entry: Type, query: Select) -> Select:
        '''
        Mutates query in non-whereclause ways, such as `.limit()`
        '''
        return query

    def query(self, field, query: Select) -> Select:
        # for simple field-based clauses
        if field is not None:
            query = query.where(field.like(self.like))
        else:
            # for composite clauses that know what to do themselves
            query = self.apply_query_mutations(field, query)
        return query

@dataclass
class SearchClauseLike(SearchClauseBase):
    '''
    Preforms the SQL `like` operation
    '''
    like: str
    
    def boolean_clauses(self, entry):
        return [entry.like(self.like)]

@dataclass
class SearchClauseLimit(SearchClauseBase):
    '''
    Takes an integer as input and applies that as a limit to its query.
    '''
    num: int

    def apply_query_mutations(self, _, query):
        return query.limit(self.num)

class SearchClauseAll(SearchClauseBase):
    '''
    takes each clause from its list of arguments and applies them.
    This results in the bitwise `AND` operation
    '''
    def boolean_clauses(self, entry):
        result = []
        for clause in self.clauses:
            result.extend(clause.boolean_clauses(entry))

        return result

    def apply_query_mutations(self, entry, query: Select) -> Select:
        for clause in self.clauses:
            query = clause.apply_query_mutations(entry, query)

        return query
    
    def __init__(self, *args):
        self.clauses: list[SearchClauseBase] = args

@dataclass
class SearchClauseNot(SearchClauseBase):
    inner: SearchClauseBase

    def boolean_clauses(self, entry):
        return [~clause for clause in self.inner.boolean_clauses(entry)]

    def apply_query_mutations(self, entry, query: Select) -> Select:
        return self.inner.apply_query_mutations(entry, query)

def __math_op_class(name: str, operation_fname: str):
    def __init__(self, imm):
        self.imm = imm
        
    def boolean_clauses(self, entry) -> list[ClauseElement]:
        return [entry[operation_fname]()]
        
    return type(
        name,
        (SearchClauseBase,),
        {
            "__init__": __init__,
            "boolean_clauses": boolean_clauses,
        }
    )

SearchClauseGt = __math_op_class("SearchClauseGt", "__gt__")
SearchClauseLt = __math_op_class("SearchClauseGt", "__lt__")
SearchClauseGe = __math_op_class("SearchClauseGt", "__ge__")
SearchClauseLe = __math_op_class("SearchClauseGt", "__le__")
SearchClauseEq = __math_op_class("SearchClauseGt", "__eq__")
    