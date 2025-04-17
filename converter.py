# built-in
import os

# external
from fastapi import Request, HTTPException

# internal
import clients
from auth import get_user_info
from models import AuthResponse


async def handle_code_conversion(request: Request) -> dict:
    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        data = await request.json()
        source_code = data.get("source_code")
        source_language = data.get("source_language")
        target_language = data.get("target_language")

        if not source_code or not source_language or not target_language:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: source_code, source_language, or target_language",
            )

        converted_code = await convert_code(
            source_code, source_language, target_language
        )

        return {
            "converted_code": converted_code,
            "source_language": source_language,
            "target_language": target_language,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def convert_code(
    source_code: str, source_language: str, target_language: str
) -> str:
    try:
        prompt = f"""
        Convert the following {source_language} code to {target_language}.
        Maintain the same functionality and logic.
        Add necessary comments to explain the code.

        {source_language} code:
        ```
        {source_code}
        ```
        """

        response = await clients.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code conversion assistant. Convert code from one language to another while maintaining the same functionality.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        converted_code = response.choices[0].message.content

        if "```" in converted_code:
            code_blocks = converted_code.split("```")
            if len(code_blocks) >= 3:
                code_content = code_blocks[1].strip()
                if "\n" in code_content:
                    lines = code_content.split("\n")
                    if not lines[0].strip().startswith("#") and not lines[
                        0
                    ].strip().startswith("//"):
                        code_content = "\n".join(lines[1:])
                return code_content

        return converted_code

    except Exception as e:
        print(f"Error converting code: {e}")
        raise RuntimeError(f"Failed to convert code: {str(e)}")


async def get_repo_tree(repo_url: str) -> list[dict]:

    try:
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 5 or parts[2] != "github.com":
            raise ValueError("Invalid GitHub repository URL")

        owner = parts[3]
        repo = parts[4]

        token: str = clients.github_token
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }

        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = await clients.http_client.get(base_url, headers=headers)
        response.raise_for_status()
        repo_data = response.json()
        default_branch = repo_data.get("default_branch", "main")

        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        response = await clients.http_client.get(tree_url, headers=headers)
        response.raise_for_status()

        tree_data = response.json()

        files = [
            item for item in tree_data.get("tree", []) if item.get("type") == "blob"
        ]

        return files
    except Exception as e:
        print(f"Error fetching repository tree: {e}")
        raise RuntimeError(f"Failed to fetch repository tree: {str(e)}")


async def get_file_content(repo_url: str, file_path: str) -> dict:

    try:
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 5 or parts[2] != "github.com":
            raise ValueError("Invalid GitHub repository URL")

        owner = parts[3]
        repo = parts[4]

        token: str = clients.github_token
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }

        content_url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        )
        response = await clients.http_client.get(content_url, headers=headers)
        response.raise_for_status()

        content_data = response.json()

        if content_data.get("size", 0) > 1000000:
            raise ValueError("File too large to convert")

        content = content_data.get("content", "")

        import base64

        decoded_content = base64.b64decode(content.replace("\n", "")).decode("utf-8")

        _, file_extension = os.path.splitext(file_path)
        language = detect_language(file_extension)

        return {
            "path": file_path,
            "content": decoded_content,
            "language": language,
            "repo_url": repo_url,
        }
    except Exception as e:
        print(f"Error fetching file content: {e}")
        raise RuntimeError(f"Failed to fetch file content: {str(e)}")


def detect_language(file_extension: str) -> str:
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".java": "java",
        ".c": "c",
        ".cpp": "c++",
        ".cs": "c#",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".rs": "rust",
    }

    return extension_map.get(file_extension.lower(), "unknown")


async def handle_repo_exploration(request: Request) -> dict:

    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        data = await request.json()
        repo_url = data.get("repo_url")

        if not repo_url:
            raise HTTPException(status_code=400, detail="Missing repository URL")

        files = await get_repo_tree(repo_url)

        return {
            "files": files,
            "repo_url": repo_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def handle_file_fetch(request: Request) -> dict:

    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        data = await request.json()
        repo_url = data.get("repo_url")
        file_path = data.get("file_path")

        if not repo_url or not file_path:
            raise HTTPException(
                status_code=400, detail="Missing repository URL or file path"
            )

        file_data = await get_file_content(repo_url, file_path)

        return file_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def handle_repo_conversion(request: Request) -> dict:

    try:
        auth_response: AuthResponse = await get_user_info(request)
        if not auth_response.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")

        data = await request.json()
        repo_url = data.get("repo_url")
        file_path = data.get("file_path")
        source_language = data.get("source_language")
        target_language = data.get("target_language")

        if not repo_url or not file_path or not source_language or not target_language:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: repo_url, file_path, source_language, or target_language",
            )

        file_data = await get_file_content(repo_url, file_path)

        converted_code = await convert_code(
            file_data["content"], source_language, target_language
        )

        return {
            "converted_code": converted_code,
            "source_language": source_language,
            "target_language": target_language,
            "file_path": file_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
