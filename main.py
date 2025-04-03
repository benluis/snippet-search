# main.py
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from get_data import extract_keywords, search_github, search_pinecone
from process_data import create_records, parallel_upsert

load_dotenv()
app = Flask(__name__)
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('home'))

    search_params = extract_keywords(query)

    search_query = f"{search_params['keywords']}"
    if search_params.get('languages'):
        search_query += f" language:{search_params['languages']}"

    github_results = search_github(search_query, limit=10)
    records = create_records(github_results)
    if records:
        parallel_upsert(records)

    pinecone_results = search_pinecone(query, top_k=5)

    return render_template(
        'results.html',
        query=query,
        pinecone_results=pinecone_results.matches,
        github_results=github_results
    )

if __name__ == '__main__':
    app.run(debug=True)