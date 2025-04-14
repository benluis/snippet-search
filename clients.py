# external
import httpx
from openai import AsyncOpenAI
from pinecone import PineconeAsyncio

# internal
from models import Setting


openai_client = None
pinecone_index = None
http_client = None
github_token = None


async def setup_clients():
    global openai_client, pinecone_index, http_client, github_token

    settings = Setting()

    http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        timeout=30.0,
    )

    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key, http_client=http_client
    )

    pc_async = PineconeAsyncio(api_key=settings.pinecone_api_key)
    pinecone_index = pc_async.IndexAsyncio(host=settings.pinecone_host)

    github_token = settings.github_token


async def close_clients():
    global http_client
    if http_client:
        await http_client.aclose()
