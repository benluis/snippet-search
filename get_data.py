# built-in
import json
import requests

# external
from openai import OpenAI
from pinecone import Pinecone, QueryResponse

# internal
from process_data import embed_text
from models import SearchParams, Repository, Setting


setting = Setting()
openai_client = OpenAI(api_key=setting.openai_api_key)
pc = Pinecone(api_key=setting.pinecone_api_key, pool_threads=30)
index = pc.Index(host=setting.pinecone_host)


async def extract_keywords(nl_query: str) -> SearchParams:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract search parameters from this query about code. Return a JSON with 'keywords' and 'languages'.",
                },
                {"role": "user", "content": nl_query},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "extract_params",
                        "description": "Extract search parameters",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "languages": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["keywords", "languages"],
                        },
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": "extract_params"}},
        )

        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        keywords = args.get("keywords")
        languages = args.get("languages", [])
        return SearchParams(keywords=keywords, languages=languages)
    except Exception as e:
        print(f"Error extracting search parameters: {e}")
        raise Exception("Something went wrong")


async def search_github(
    search_params: SearchParams, limit: int = 10
) -> list[Repository]:
    base_url: str = "https://api.github.com/search/repositories"
    headers: dict[str, str] = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {setting.github_token}",
    }

    query = " ".join(search_params.keywords)
    if search_params.languages:
        for lang in search_params.languages:
            query += f" language:{lang}"

    params: dict[str, str | int] = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        repo_data = response.json().get("items", [])
        repos: list[Repository] = []
        for repo in repo_data:
            repos.append(
                Repository(
                    id=str(repo["id"]),
                    full_name=repo["full_name"],
                    html_url=repo["html_url"],
                    description=repo.get("description", ""),
                    language=repo.get("language", "unknown"),
                    stargazers_count=repo.get("stargazers_count", 0),
                )
            )
        return repos
    else:
        print(f"Error fetching GitHub repositories: {response.status_code}")
        raise Exception("Something went wrong")


async def search_pinecone(query_text: str, top_k: int = 3) -> QueryResponse:
    try:
        query_vector: list[float] = embed_text(query_text)
        if query_vector is None:
            print("Failed to generate query embedding.")
            raise Exception("Something went wrong")

        results: QueryResponse = index.query(
            vector=query_vector, top_k=top_k, namespace="", include_metadata=True
        )
        return results
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        raise Exception("Something went wrong")
