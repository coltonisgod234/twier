from dataclasses import dataclass
from flask import Flask
from typing import Type

class ContentFmt:
    _type: str

@dataclass
class FmtJSON(ContentFmt):
    json: dict
    _type: str = "application/json"

class Content:
    type: str
    fmt: ContentFmt
    
    def __init__(self, fmt: ContentFmt | dict):
        # special case for dicts
        if isinstance(fmt, dict):
            fmt = FmtJSON(fmt)

        self.type = fmt._type
        self.fmt = fmt

@dataclass
class SchEndpoint:
    path: str
    method: str

    req: Content
    res: Content
    
    codes: list[int]
    
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

@dataclass
class SchError:  # JSON object, client knows what this is. Just not specified here
    codes: list[int]

class SchOptional:
    '''
    Either `null` or undefined is allowed for this value
    '''

def wrap_error_endpoint(
    errors: list[int],
    inner: dict
) -> Content:
    keys = list(inner.keys)

    x = {
        "error": [SchOptional, SchError(errors)]
    }
    x.update(inner)
    return Content(FmtJSON(x))