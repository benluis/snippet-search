# get_data.py
import os
import requests
import json
import asyncio
import aiohttp
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(host=pinecone_host)
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

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


async def batch_upsert(records, batch_size=200):
    batches = [
        records[i:i + batch_size]
        for i in range(0, len(records), batch_size)
    ]

    async_results = [
        index.upsert_records(records=batch, namespace="", async_req=True)
        for batch in batches
    ]

    [async_result.get() for async_result in async_results]

    return len(records)


def search_pinecone(query_text, top_k=3):
    results = index.search(
        query={
            "top_k": top_k,
            "inputs": {
                "text": query_text
            }
        },
        namespace=""
    )
    return results