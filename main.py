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
from models import AuthResponse, Repository, SearchResult


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
    auth_response = await get_user_info(request)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "auth": auth_response},
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")) -> HTMLResponse:
    content: SearchResult = await handle_search(request, q)
    auth_response = await get_user_info(request)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "query": q,
            "pinecone_results": content.get("pinecone_results", []),
            "github_results": content.get("github_results", []),
            "auth": auth_response,
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

    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header:
        return repositories
    else:
        auth_response = await get_user_info(request)
        return templates.TemplateResponse(
            "favorites.html",
            {"request": request, "favorites": repositories, "auth": auth_response},
        )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
