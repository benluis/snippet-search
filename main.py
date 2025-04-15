# external
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pinecone import QueryResponse
import uvicorn

# internal
from models import SearchParams, Repository
import clients
from utils import (
    extract_keywords,
    search_github,
    search_pinecone,
    parallel_upsert,
)
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await clients.setup_clients()
    yield
    await clients.close_clients()


app: FastAPI = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")):
    try:
        search_params: SearchParams = await extract_keywords(q)

        github_results: list[Repository] = await search_github(search_params, limit=10)
        await parallel_upsert(github_results)
        pinecone_results: QueryResponse = await search_pinecone(q, top_k=5)

        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": q,
                "pinecone_results": pinecone_results.matches,
                "github_results": github_results,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
