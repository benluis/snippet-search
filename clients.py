# external
import httpx
from openai import AsyncOpenAI
from pinecone import PineconeAsyncio
from supabase import acreate_client

# internal
from models import Setting


openai_client = None
pinecone_index = None
http_client = None
github_token = None
supabase_client = None


async def setup_clients():
    global supabase_client, openai_client, pinecone_index, http_client, github_token

    settings = Setting()

    supabase_client = await acreate_client(settings.supabase_url, settings.supabase_key)

    http_client = httpx.AsyncClient()
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
