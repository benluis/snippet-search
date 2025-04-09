# main.py

# built-in
import os
from typing import Dict, List, Optional, Any, Union

# external
from flask import Flask, render_template, request, redirect, url_for, Response
from dotenv import load_dotenv
from pinecone import QueryResponse

# internal
from get_data import extract_keywords, search_github, search_pinecone
from process_data import create_records, parallel_upsert

load_dotenv()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home() -> str:
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search() -> str:
    query: str = request.args.get('q', '')

    search_params: Dict[str, Any] = extract_keywords(query)

    search_query: str = f"{search_params['keywords']}"
    if search_params.get('languages'):
        search_query += f" language:{search_params['languages']}"

    github_results: List[Dict[str, Any]] = search_github(search_query, limit=10)
    records: List[Dict[str, Any]] = create_records(github_results)
    if records:
        parallel_upsert(records)

    pinecone_results: Optional[QueryResponse] = search_pinecone(query, top_k=5)

    return render_template(
        'results.html',
        query=query,
        pinecone_results=pinecone_results.matches if pinecone_results else [],
        github_results=github_results
    )

if __name__ == '__main__':
    app.run(debug=True)