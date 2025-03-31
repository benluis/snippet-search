# process_data.py
import os
import itertools
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
openai_client = OpenAI(api_key=openai_api_key)

def embed_text(text):
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error embedding text: {e}")
        return None

def create_records(data):
    records = []
    for item in data:
        record = {
            "_id": item["id"],
            "embedding": embed_text(item["description"]),
            "chunk_text": item["description"],
        }
        if record["embedding"] is not None:
            records.append(record)
    return records


def chunks(iterable, batch_size=200):
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))

def parallel_upsert(records, batch_size=200, max_parallel=30):
    try:
        pc_parallel = Pinecone(api_key=pinecone_api_key, pool_threads=max_parallel)
        index_parallel = pc_parallel.Index(host=pinecone_host)

        async_results = [
            index_parallel.upsert_records(records=batch, async_req=True)
            for batch in chunks(records, batch_size=batch_size)
        ]

        total_upserted = 0
        for async_result in async_results:
            response = async_result.get()
            total_upserted += response.upserted_count

        return total_upserted

    except Exception as e:
        print(f"Error in parallel upsert: {e}")
        return 0