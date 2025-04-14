# external
from openai import OpenAI
from pinecone import Pinecone

# internal
from models import Setting, Repository

setting = Setting()
pc = Pinecone(api_key=setting.pinecone_api_key, pool_threads=30)
index = pc.Index(host=setting.pinecone_host)
openai_client = OpenAI(api_key=setting.openai_api_key)


def embed_text(text: str) -> list[float]:
    text = text.replace("\n", " ")
    try:
        response = openai_client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error embedding text: {e}")
        raise Exception("Something went wrong")


async def parallel_upsert(repositories: list[Repository]) -> None:
    try:
        pinecone_records = []
        for repository in repositories:
            vector = embed_text(repository.description)
            pinecone_records.append(
                {
                    "id": repository.id,
                    "values": vector,
                    "metadata": {
                        "full_name": repository.full_name,
                        "description": repository.description,
                        "language": repository.language,
                        "stargazers_count": repository.stargazers_count,
                    },
                }
            )
        index.upsert(vectors=pinecone_records)
        return None
    except Exception as e:
        print(f"Error in parallel upsert: {e}")
        raise Exception("Something went wrong")
