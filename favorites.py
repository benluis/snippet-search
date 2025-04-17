# external
from fastapi import Request, Response, HTTPException
from fastapi.responses import RedirectResponse

# internal
import clients
from auth import get_user_info
from models import Repository, AuthResponse


async def add_favorite(request: Request) -> dict[str, bool]:
    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        data = await request.json()
        repo_id: str = data.get("repo_id")
        repo_data: dict = data.get("repo_data")

        if not repo_id or not repo_data:
            raise HTTPException(status_code=400, detail="Missing required data")

        repository: Repository = Repository(
            id=repo_id,
            full_name=repo_data.get("full_name"),
            html_url=repo_data.get("url"),
            description=repo_data.get("description"),
            language=repo_data.get("language"),
            stargazers_count=repo_data.get("stars"),
        )

        await clients.supabase_client.table("favorites").insert(
            {
                "user_id": auth_response.user.id,
                "repo_id": repository.id,
                "repo_full_name": repository.full_name,
                "repo_url": repository.html_url,
                "repo_description": repository.description,
                "repo_language": repository.language,
                "repo_stars": repository.stargazers_count,
            }
        ).execute()

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def remove_favorite(request: Request, repo_id: str) -> dict[str, bool]:
    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        await clients.supabase_client.table("favorites").delete().eq(
            "repo_id", repo_id
        ).eq("user_id", auth_response.user.id).execute()

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_favorites(request: Request) -> list[Repository] | RedirectResponse:
    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            return RedirectResponse(url="/")

        supabase_response = (
            await clients.supabase_client.table("favorites")
            .select("*")
            .eq("user_id", auth_response.user.id)
            .execute()
        )

        favorites_data = supabase_response.data

        repositories: list[Repository] = []

        for item in favorites_data:
            repositories.append(
                Repository(
                    id=item["repo_id"],
                    full_name=item["repo_full_name"],
                    html_url=item["repo_url"],
                    description=item["repo_description"],
                    language=item["repo_language"],
                    stargazers_count=item["repo_stars"],
                )
            )
        return repositories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
