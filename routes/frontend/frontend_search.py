from routes.frontend.frontend_common import endpoint
from flask import render_template, request
from routes.api.routes_search import search_api_json, json_to_search

def create_endpoints(app):
    @app.route("/frontend/search")
    def frontend_search():
        return render_template(
            "search/search.html",
            **endpoint()
        )

    @app.route("/frontend/searched", methods=["POST"])
    def frontend_searched():
        data = json_to_search(request.json)
        searched = search_api_json(data)
        
        return render_template(
            "search/results.html",
            results=searched,
            type=request.json["type"],
            **endpoint()
        )
