# external
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from typing import Optional


class Setting(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    github_token: str
    openai_api_key: str
    pinecone_api_key: str
    pinecone_host: str


class Repository(BaseModel):
    id: str
    full_name: str
    html_url: str
    description: str
    language: str
    stargazers_count: int


class VectorRecord(BaseModel):
    id: str
    values: list[float]
    metadata: dict = Field(default_factory=dict)


class SearchParams(BaseModel):
    keywords: list[str]
    languages: Optional[list[str]]
