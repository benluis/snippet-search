# get_data.py

# built-in
import os
import json
from typing import Dict, List, Any, Optional

# external
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, QueryResponse

# internal
from process_data import embed_text

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")


def extract_keywords(nl_query: str) -> Dict[str, Any]:
    openai_client = OpenAI(api_key=openai_api_key)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Extract search parameters from this query about code. Return a JSON with 'keywords' (main functionality) and 'languages' (programming languages mentioned).",
                },
                {"role": "user", "content": nl_query},
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error extracting search parameters: {e}")
        return {"keywords": nl_query, "languages": None}


def search_github(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    base_url: str = "https://api.github.com/search/repositories"
    headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    params: Dict[str, Any] = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Error fetching GitHub repositories: {response.status_code}")
        return []


def search_pinecone(query_text: str, top_k: int = 3) -> QueryResponse:
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(host=pinecone_host)
    try:
        query_vector: List[float] = embed_text(query_text)
        if query_vector is None:
            print("Failed to generate query embedding.")
            return None

        results: QueryResponse = index.query(
            vector=query_vector, top_k=top_k, namespace="", include_metadata=True
        )
        return results
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        return QueryResponse(matches=[], namespace="")
