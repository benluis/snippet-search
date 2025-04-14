# external
from flask import Flask, render_template, request
from pinecone import QueryResponse

# internal
from get_data import (
    extract_keywords,
    search_github,
    search_pinecone,
)
from process_data import parallel_upsert
from models import Repository, SearchParams

app: Flask = Flask(__name__)


@app.route("/", methods=["GET"])
def home() -> str:
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search() -> str:
    query: str = request.args.get("q", "")

    search_params: SearchParams = extract_keywords(query)
    github_results: list[Repository] = search_github(search_params, limit=10)
    parallel_upsert(github_results)
    pinecone_results: QueryResponse = search_pinecone(query, top_k=5)

    return render_template(
        "results.html",
        query=query,
        pinecone_results=pinecone_results.matches if pinecone_results else [],
        github_results=github_results,
    )


if __name__ == "__main__":
    app.run(debug=True)
