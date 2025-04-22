# external
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from typing import Optional


class Setting(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    github_token: str
    openai_api_key: str
    pinecone_api_key: str
    pinecone_host: str
    supabase_url: str
    supabase_key: str


class Repository(BaseModel):
    id: str
    full_name: str
    html_url: str
    description: str
    language: str
    stargazers_count: int


class SearchParams(BaseModel):
    keywords: list[str]
    languages: list[str] = []


class SearchResult(dict):
    pinecone_results: list[dict]
    github_results: list[Repository]


class PKCEPair(BaseModel):
    code_verifier: str
    code_challenge: str


class UserInfo(BaseModel):
    id: str
    email: str
    name: str


class AuthResponse(BaseModel):
    authenticated: bool
    user: UserInfo = None
