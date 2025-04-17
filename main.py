# external
from fastapi import FastAPI, Request, Query, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

# internal
import clients
from search import handle_search
from auth import signin, handle_callback, signout, get_user_info
from favorites import add_favorite, remove_favorite, get_favorites
from models import AuthResponse, SearchResult
from converter import (
    handle_repo_exploration,
    handle_file_fetch,
    handle_repo_conversion,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await clients.setup_clients()
    yield
    await clients.close_clients()


app: FastAPI = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates: Jinja2Templates = Jinja2Templates(directory="templates")


@app.get("/auth/signin")
async def auth_signin(request: Request) -> RedirectResponse:
    return await signin(request)


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = Query(None)) -> RedirectResponse:
    return await handle_callback(request, code)


@app.get("/auth/signout")
async def auth_signout(response: Response) -> RedirectResponse:
    return await signout(response)


@app.get("/auth/user")
async def auth_get_user(request: Request) -> AuthResponse:
    return await get_user_info(request)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    auth_response: AuthResponse = await get_user_info(request)
    return templates.TemplateResponse(
        "index.html", {"request": request, "auth": auth_response}
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")) -> HTMLResponse:
    if not q or q.strip() == "":
        return templates.TemplateResponse("index.html", {"request": request})

    auth_response: AuthResponse = await get_user_info(request)
    results: SearchResult = await handle_search(request, q)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "query": q,
            "auth": auth_response,
            "pinecone_results": results.get("pinecone_results", []),
            "github_results": results.get("github_results", []),
        },
    )


@app.post("/favorites/add")
async def favorites_add(request: Request) -> dict[str, bool]:
    return await add_favorite(request)


@app.delete("/favorites/remove/{repo_id}")
async def favorites_remove(request: Request, repo_id: str) -> dict[str, bool]:
    return await remove_favorite(request, repo_id)


@app.get("/favorites")
async def favorites_get(request: Request):
    repositories = await get_favorites(request)
    if isinstance(repositories, RedirectResponse):
        return repositories

    auth_response: AuthResponse = await get_user_info(request)
    return templates.TemplateResponse(
        "favorites.html",
        {"request": request, "favorites": repositories, "auth": auth_response},
    )


@app.get("/repo-convert", response_class=HTMLResponse)
async def repo_convert_page(request: Request) -> HTMLResponse:
    auth_response = await get_user_info(request)
    return templates.TemplateResponse(
        "repo_convert.html", {"request": request, "auth": auth_response}
    )


@app.post("/repo-convert/explore")
async def repo_explore(request: Request) -> dict:
    return await handle_repo_exploration(request)


@app.post("/repo-convert/fetch-file")
async def fetch_file(request: Request) -> dict:
    return await handle_file_fetch(request)


@app.post("/repo-convert/convert")
async def repo_convert(request: Request) -> dict:
    return await handle_repo_conversion(request)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
