from dataclasses import dataclass, field
from flask import Flask
from typing import Type

class ContentFmt:
    _type: str

class FmtJSON(ContentFmt):
    _type: str = "application/json"

    def __init__(self, json: dict | SchListOf):
        self.json = json
        
    def __repr__(self):
        return self.json.__repr__()
    
    def _dict(self):
        d = {}
        for k, v in self.json.items():
            if   v == str: d[k] = "string"
            elif v == int: d[k] = "integer"
            elif v == float: d[k] = "float"
            elif v == SchOptional: d[k] = "optional"
            elif v == SchUser: d[k] = "user"
            elif v == SchPost: d[k] = "post"
            elif v == SchWord: d[k] = "word"
            elif v == SchError: d[k] = "error"
            elif v == SchListOf: d[k] = f"list of {v.type}"

        return d

class Content:
    type: str
    fmt: ContentFmt
    
    def __init__(self, fmt: ContentFmt | dict):
        # special case for dicts
        conv_fmt = fmt
        if isinstance(fmt, dict) or isinstance(fmt, SchListOf):
            conv_fmt = FmtJSON(fmt)

        elif not isinstance(fmt, ContentFmt):
            raise TypeError("need something that is a subclass of ContentFmt")

        self.type = conv_fmt._type
        self.fmt = conv_fmt
        
    def _to_dict(self):
        return self.fmt._dict()

    def __repr__(self):
        return self.fmt.__repr__()

@dataclass
class SchListOf:
    type: Type
    
    def __repr__(self):
        ty = self.type.__repr__(self.type)
        return f"list of {ty}"

@dataclass
class SchEndpoint:
    path: str
    method: str

    req: Content | None = None
    res: Content | None = None

    codes: list[int] = field(default_factory=lambda: [200, 500])
    
    cookies: list[str] = field(default_factory=lambda: [])
    auth: str | None = None

    @classmethod
    def view(self, /):
        ...
        
    remarks: str | None = None

    @classmethod
    def register_to(self, app: Flask):
        app.add_url_rule(
            rule        = self.path,
            endpoint    = self.path,
            view_func   = self.view,
            methods     = [self.method],
        )
    
    def _to_dict(self) -> dict:
        req = self.req._to_dict() if self.req is not None else None
        res = self.res._to_dict() if self.res is not None else None

        return {
            "path": self.path,
            "method": self.method,
            "req": req,
            "res": res,
            "codes": self.codes,
            # "cookies": self.cookies,
            "auth": self.auth
        }

class SchUser:
    def __repr__(self):
        return "user"

class SchPost:
    def __repr__(self):
        return "post"

class SchWord: 
    def __repr__(self):
        return "word"
@dataclass
class SchError:  # JSON object, client knows what this is. Just not specified here
    codes: list[int]

class SchOptional:
    '''
    Either `null` or undefined is allowed for this value
    '''
    def __repr__(self):
        return "(optional field)"

def wrap_error_endpoint(
    errors: list[int],
    inner: dict
) -> Content:
    x = {
        "error": [SchOptional, SchError(errors)]
    }
    x.update(inner)
    return Content(FmtJSON(x))