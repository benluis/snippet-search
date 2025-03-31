# get_data.py
import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from process_data import chunks

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(host=pinecone_host)
openai_client = OpenAI(api_key=openai_api_key)

def extract_keywords(nl_query):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Extract search parameters from this query about code. Return a JSON with 'keywords' (main functionality) and 'languages' (programming languages mentioned)."},
                {"role": "user", "content": nl_query}
            ],
            response_format={"type": "json_object"},
            max_tokens=200
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error extracting search parameters: {e}")
        return {"keywords": nl_query, "languages": None}

def search_github(query, limit=10):
    base_url = "https://api.github.com/search/repositories"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Error fetching GitHub repositories: {response.status_code}")
        return []

def search_pinecone(query_text, top_k=3):
    try:
        results = index.search_records(
            namespace="",
            query={
                "inputs": {"text": query_text},
                "top_k": top_k
            }
        )
        return results
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        return None