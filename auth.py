# built-in
import base64
import hashlib
import os

# external
from fastapi import Request, Response, HTTPException, Query
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

# internal
from models import PKCEPair, UserInfo, AuthResponse
import clients


def generate_pkce_pair() -> PKCEPair:
    random_bytes: bytes = os.urandom(32)
    code_verifier: str = (
        base64.urlsafe_b64encode(random_bytes).rstrip(b"=").decode("utf-8")
    )

    hashed: bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()

    code_challenge: str = base64.urlsafe_b64encode(hashed).rstrip(b"=").decode("utf-8")

    return PKCEPair(code_verifier=code_verifier, code_challenge=code_challenge)


async def signin(request: Request) -> RedirectResponse:
    try:
        base_url: str = str(request.base_url)
        redirect_url: str = f"{base_url}auth/callback"

        referer: str = request.headers.get("referer", "/")

        pkce_pair: PKCEPair = generate_pkce_pair()

        params: dict[str, str] = {
            "provider": "google",
            "redirect_to": redirect_url,
            "code_challenge": pkce_pair.code_challenge,
            "code_challenge_method": "s256",
        }

        auth_base: str = f"{clients.supabase_client.auth._url}/authorize"
        auth_url: str = f"{auth_base}?{urlencode(params)}"

        response: RedirectResponse = RedirectResponse(url=auth_url)
        response.set_cookie(
            "code_verifier", pkce_pair.code_verifier, httponly=True, secure=True
        )

        response.set_cookie("auth_redirect", referer, httponly=True, secure=True)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Authentication initialization failed: {str(e)}"
        )


async def handle_callback(request: Request, code: str = Query(...)) -> RedirectResponse:
    try:
        code_verifier = request.cookies.get("code_verifier")
        redirect_to: str = request.cookies.get("auth_redirect", "/")

        if not code or not code_verifier:
            raise HTTPException(status_code=400, detail="Missing code or code_verifier")

        session_response = await clients.supabase_client.auth.exchange_code_for_session(
            {"auth_code": code, "code_verifier": code_verifier}
        )

        session = session_response.session
        if not session:
            raise HTTPException(status_code=401, detail="Failed to create session")

        response: RedirectResponse = RedirectResponse(url=redirect_to, status_code=302)

        response.set_cookie(
            "access_token",
            session.access_token,
            httponly=True,
            secure=True,
            max_age=86400,
            samesite="none",
        )
        response.set_cookie(
            "refresh_token",
            session.refresh_token,
            httponly=True,
            secure=True,
            max_age=86400,
            samesite="none",
        )

        response.delete_cookie(key="auth_redirect")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Authentication callback failed: {str(e)}"
        )


async def signout(response: Response) -> RedirectResponse:
    try:
        redirect_response: RedirectResponse = RedirectResponse(url="/")
        redirect_response.delete_cookie(key="access_token")
        redirect_response.delete_cookie(key="refresh_token")
        return redirect_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signout failed: {str(e)}")


async def get_user_info(request: Request) -> AuthResponse:
    access_token = request.cookies.get("access_token")
    if not access_token:
        return AuthResponse(authenticated=False)

    try:
        user = await clients.supabase_client.auth.get_user(access_token)
        user_info: UserInfo = UserInfo(
            id=user.user.id,
            email=user.user.email,
            name=user.user.user_metadata.get("full_name", user.user.email),
        )
        return AuthResponse(authenticated=True, user=user_info)
    except Exception:
        return AuthResponse(authenticated=False)
