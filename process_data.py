# process_data.py

# built-in
import os
import itertools
from typing import List, Dict, Any, Tuple, Iterable, TypeVar, Iterator

# external
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")

T = TypeVar("T")


def embed_text(text: str) -> List[float]:
    text = text.replace("\n", " ")
    openai_client = OpenAI(api_key=openai_api_key)

    try:
        response = openai_client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error embedding text: {e}")
        return [0] * 1536


def create_records(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in data:
        description: str = (
            item.get("description")
            or item.get("full_name")
            or f"Repository {item['id']}"
        )

        embedding: List[float] = embed_text(description[:200])

        if embedding is not None:
            record: Dict[str, Any] = {
                "id": str(item["id"]),
                "values": embedding,
                "metadata": {
                    "description": description[:200],
                    "language": item.get("language", "unknown"),
                    "url": item["html_url"],
                    "stars": item.get("stargazers_count", 0),
                    "full_name": item.get("full_name", ""),
                },
            }
            records.append(record)
    return records


def chunks(iterable: Iterable[T], batch_size: int = 200) -> Iterator[Tuple[T, ...]]:
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def parallel_upsert(
    records: List[Dict[str, Any]], batch_size: int = 200, max_parallel: int = 30
) -> int:
    try:
        pc_parallel = Pinecone(api_key=pinecone_api_key, pool_threads=max_parallel)
        index_parallel = pc_parallel.Index(host=pinecone_host)

        total_upserted: int = 0
        for batch in chunks(records, batch_size=batch_size):
            response = index_parallel.upsert(vectors=batch)
            total_upserted += response.upserted_count

        return total_upserted

    except Exception as e:
        print(f"Error in parallel upsert: {e}")
        return 0
