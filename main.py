# external
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pinecone import QueryResponse
import uvicorn

# internal
from get_data import extract_keywords, search_github, search_pinecone
from process_data import parallel_upsert
from models import Repository, SearchParams

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")):
    search_params: SearchParams = await extract_keywords(q)
    github_results: list[Repository] = await search_github(search_params, limit=10)
    await parallel_upsert(github_results)
    pinecone_results: QueryResponse = await search_pinecone(q, top_k=5)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "query": q,
            "pinecone_results": pinecone_results.matches if pinecone_results else [],
            "github_results": github_results,
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
